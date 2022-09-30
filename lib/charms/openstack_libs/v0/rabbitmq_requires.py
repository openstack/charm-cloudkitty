# Copyright 2022 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""RabbitMQRequires module.

This library contains the Requires for handling the rabbitmq interface.

Import `RabbitMQRequires` in your charm, with the charm object and the
relation name:
    - self
    - "amqp"

Two events are also available to respond to:
    - connected
    - ready
    - goneaway

A basic example showing the usage of this relation follows:

```
from charms.openstack_libs.v0.rabbitmq_requires import RabbitMQRequires

class RabbitMQClientCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        # RabbitMQ Requires
        self.rabbitmq = RabbitMQRequires(
            self, "amqp",
            username = "my-user",
            vhost = "my-vhost",
        )
        self.framework.observe(
            self.rabbitmq.on.connected,
            self._on_amqp_connected)
        self.framework.observe(
            self.rabbitmq.on.ready,
            self._on_amqp_ready)
        self.framework.observe(
            self.rabbitmq.on.goneaway,
            self._on_amqp_goneaway)

    def _on_amqp_connected(self, event):
        '''React to the RabbitMQRequires connected event.

        This event happens when a RabbitMQRequires relation is added to the
        model before credentials etc have been provided.
        '''
        # Do something before the relation is complete
        pass

    def _on_amqp_ready(self, event):
        '''React to the RabbitMQ ready event.

        The RabbitMQRequires interface will use the provided config for the
        request to the identity server.
        '''
        # RabbitMQRequires Relation is ready. Do something with the
        # completed relation.
        pass

    def _on_amqp_goneaway(self, event):
        '''React to the RabbitMQ goneaway event.

        This event happens when an RabbitMQ relation is removed.
        '''
        # RabbitMQRequires Relation has goneaway. shutdown services or suchlike
        pass
```
"""

import logging

from ops.framework import EventBase, EventSource, Object, ObjectEvents
from ops.model import Relation

logger = logging.getLogger(__name__)

# The unique Charmhub library identifier, never change it
LIBID = "dae9fea1f8894b6295f0161b7ef7b7dc"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1


class RabbitMQConnectedEvent(EventBase):
    """RabbitMQ connected Event."""

    pass


class RabbitMQReadyEvent(EventBase):
    """RabbitMQ ready for use Event."""

    pass


class RabbitMQGoneAwayEvent(EventBase):
    """RabbitMQ relation has gone-away Event."""

    pass


class RabbitMQServerEvents(ObjectEvents):
    """Events class for `on`."""

    connected = EventSource(RabbitMQConnectedEvent)
    ready = EventSource(RabbitMQReadyEvent)
    goneaway = EventSource(RabbitMQGoneAwayEvent)


class RabbitMQRequires(Object):
    """Requires side interface for rabbitmq interface type."""

    on = RabbitMQServerEvents()

    def __init__(self, charm, relation_name: str, username: str, vhost: str):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name
        self._username = username
        self._vhost = vhost

        self.framework.observe(
            self.charm.on[relation_name].relation_joined,
            self._on_rabbitmq_relation_joined,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_changed,
            self._on_rabbitmq_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_departed,
            self._on_rabbitmq_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_broken,
            self._on_rabbitmq_relation_broken,
        )

    def _on_rabbitmq_relation_joined(self, event):
        """Rabbitmq relation joined."""
        logging.debug("RabbitMQ on_joined")
        self.on.connected.emit()
        self.register()

    def _on_rabbitmq_relation_changed(self, event):
        """Rabbitmq relation changed."""
        logging.debug("RabbitMQ on_changed")
        try:
            self.password
            self.on.ready.emit()
        except AttributeError:
            pass

    def _on_rabbitmq_relation_broken(self, event):
        """Rabbitmq relation broken."""
        logging.debug("RabbitMQ on_broken")
        self.on.goneaway.emit()

    @property
    def _rabbitmq_rel(self) -> Relation:
        """The RabbitMQ relation."""
        return self.framework.model.get_relation(self.relation_name)

    @property
    def hostname(self) -> str:
        """Return the hostname."""
        return self._get_data("hostname")

    @property
    def password(self) -> str:
        """Return the password."""
        return self._get_data("password")

    @property
    def username(self) -> str:
        """Return the username."""
        return self._username

    @property
    def vhost(self) -> str:
        """Return the vhost."""
        return self._vhost

    def _get_remote_unit_data(self, key: str) -> str:
        """Return the value for the given key from remote app data."""
        for unit in self._rabbitmq_rel.units:
            data = self._rabbitmq_rel.data[unit]
            return data.get(key)

    def _get_data(self, key: str) -> str:
        """Return the value for the given key."""
        return self._get_remote_unit_data(key)

    def register(self) -> None:
        """Request access to the RabbitMQ server."""
        relation_data = {
            "username": self.username,
            "vhost": self.vhost,
        }
        unit_data = self._rabbitmq_rel.data[self.charm.unit]
        unit_data.update(relation_data)
