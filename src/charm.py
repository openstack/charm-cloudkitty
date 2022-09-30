#!/usr/bin/env python3

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import subprocess

from pathlib import Path

from ops_openstack.core import OSBaseCharm

from ops.framework import StoredState
from ops.main import main

from ops.model import (
    ActiveStatus
)

from charmhelpers.core import templating
from charmhelpers.core.host import restart_on_change

from charmhelpers.contrib.openstack import templating as os_templating

from charms.openstack_libs.v0.keystone_requires import (
    KeystoneRequires
)

from charms.openstack_libs.v0.gnocchi_requires import (
    GnocchiRequires
)

from charms.openstack_libs.v0.rabbitmq_requires import (
    RabbitMQRequires
)

from charms.data_platform_libs.v0.database_requires import (
    DatabaseRequires
)

from charms.operator_libs_linux.v1.systemd import (
    service_restart
)

logger = logging.getLogger(__name__)


class CloudkittyCharm(OSBaseCharm):
    """Charm the service."""
    _stored = StoredState()

    PACKAGES = [
        'cloudkitty-api',
        'cloudkitty-processor'
    ]

    REQUIRED_RELATIONS = [
        'database',
        'identity-service',
        'metric-service',
        'amqp'
    ]

    CONFIG_FILE_OWNER = 'cloudkitty'
    CONFIG_FILE_GROUP = 'cloudkitty'
    CONFIG_DIR = Path('/etc/cloudkitty')
    CONFIG_FILE = 'cloudkitty.conf'
    CONFIG_PATH = CONFIG_DIR / CONFIG_FILE

    SERVICES = ['cloudkitty-api', 'cloudkitty-processor']
    RESTART_MAP = {
        str(CONFIG_PATH): SERVICES
    }

    release = 'yoga'

    def __init__(self, framework):
        super().__init__(framework)
        super().register_status_check(self.status_check)

        self._app_name = self.model.app.name
        self._address = None

        self._stored.is_started = True

        self.identity_service = KeystoneRequires(
            charm=self,
            relation_name='identity-service',
            service_endpoints=[{
                'service_name': self._app_name,
                'internal_url': self.service_url('internal'),
                'public_url': self.service_url('public'),
                'admin_url': self.service_url('public')
            }],
            region=self.model.config['region']
        )

        self.metric_service = GnocchiRequires(
            charm=self,
            relation_name='metric-service'
        )

        self.rabbitmq = RabbitMQRequires(
            charm=self,
            relation_name='amqp',
            username=self._app_name,
            vhost=self._app_name,
        )

        self.database = DatabaseRequires(
            charm=self,
            relation_name='database',
            database_name=self._app_name
        )

        self.framework.observe(self.on.config_changed,
                               self._on_config_changed)
        self.framework.observe(self.identity_service.on.ready,
                               self._on_identity_service_ready)
        self.framework.observe(self.metric_service.on.ready,
                               self._on_metric_service_ready)
        self.framework.observe(self.database.on.database_created,
                               self._on_database_created)
        self.framework.observe(self.rabbitmq.on.ready,
                               self._on_amqp_ready)
        self.framework.observe(self.on.restart_services_action,
                               self._on_restart_services_action)

    @property
    def protocol(self):
        return 'http'

    @property
    def host(self) -> str:
        if self._address is None:
            binding = self.model.get_binding('public')
            self._address = binding.network.bind_address
        return str(self._address)

    @property
    def port(self) -> int:
        return 8889

    def service_url(self, _) -> str:
        return f'{self.protocol}://{self.host}:{self.port}'

    def status_check(self):
        return ActiveStatus()

    @restart_on_change(RESTART_MAP)
    def _render_config(self, _) -> str:
        """Render configuration

        Render related services configuration into
        cloudkitty configuration file
        """
        _template_loader = os_templating.get_loader(
            'templates/',
            self.release
        )

        _context = {
            'options': self.model.config,
            'identity_service': self.identity_service,
            'metric_service': self.metric_service,
            'databases': self.database.fetch_relation_data(),
            'rabbitmq': self.rabbitmq,
        }

        return templating.render(
            source=self.CONFIG_FILE,
            target=self.CONFIG_PATH,
            context=_context,
            template_loader=_template_loader,
            owner=self.CONFIG_FILE_OWNER,
            group=self.CONFIG_FILE_GROUP,
            perms=0o640
        )

    def _bootstrap_db(self):
        """Bootstrap Database

        On this function we handle the execution of
        the storage initialization and then dbsync upgrade.
        If any of the command fails it will return a non-zero
        value and unit falls into error state.

        This method is only executed on the leader unit.
        """
        if not self.model.unit.is_leader():
            logger.info('unit is not leader, skipping bootstrap db')
            return

        logger.info('starting cloudkitty db migration')

        commands = [
            ['cloudkitty-storage-init'],
            ['cloudkitty-dbsync', 'upgrade']
        ]

        for cmd in commands:
            logger.info(f"executing {cmd} command")
            subprocess.check_call(cmd)

    def _on_config_changed(self, event):
        """ Handle config changed event.
        """
        self._render_config(event)
        self.update_status()

    def _on_identity_service_ready(self, event):
        """ Handle identity-service relation ready event.
        """
        self._render_config(event)
        self.update_status()

    def _on_metric_service_ready(self, event):
        """ Handle metric-service relation ready event.
        """
        self._render_config(event)
        self.update_status()

    def _on_database_created(self, event):
        """ Handle Database created event.
        """
        self._render_config(event)
        self._bootstrap_db()
        self.update_status()

    def _on_amqp_ready(self, event):
        """ Handle RabbitMQ relation ready event.
        """
        self._render_config(event)
        self.update_status()

    def _on_restart_services_action(self, event):
        """ Restart cloudkitty services action.
        """
        event.log(f"restarting services {', '.join(self.SERVICES)}")
        for service in self.SERVICES:
            if service_restart(service):
                event.fail(f"Failed to restart service: {service}")


if __name__ == "__main__":
    main(CloudkittyCharm)
