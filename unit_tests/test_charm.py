# Copyright 2021 OpenStack Charmers
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing


import sys

sys.path.append('lib')
sys.path.append('src')
sys.path.append('unit_tests')

import charm
import unittest
import test_utils

from unittest.mock import (
    patch,
    call,
    Mock
)
from ops.testing import Harness


class TestCloudkittyCharm(charm.CloudkittyCharm):
    """
    Workaround until 'network-get' call gets mocked
    See https://github.com/canonical/operator/issues/456
    See https://github.com/canonical/operator/issues/222
    """
    @property
    def host(self):
        return '10.0.0.10'


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(TestCloudkittyCharm)

        self.harness.set_leader(True)
        self.harness.disable_hooks()

        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @patch('charmhelpers.core.host.mkdir')
    @patch('charmhelpers.core.host.write_file')
    def assertContent(self, expected_entries, _write_file, _mkdir):
        # check rendered content
        content = self.harness.charm._render_config(Mock())
        for entry in expected_entries:
            self.assertIn(entry, content)

    @patch('ops_openstack.core.apt_update')
    @patch('ops_openstack.core.apt_install')
    def test_on_install(self, _install, _update):
        self.harness.charm.on_install(Mock())
        _update.assert_called_with(fatal=True)
        _install.assert_called_with(TestCloudkittyCharm.PACKAGES, fatal=True)

    def test_config_changed(self):
        # change application config
        self.harness.update_config({'debug': True})

        # check rendered content
        self.assertContent(['debug = True'])

    def test_identity_service_relation(self):
        # add identity-service relation
        test_utils.add_complete_identity_relation(self.harness)

        # check rendered content
        expected_entries = [
            'auth_protocol = http',
            'auth_uri = http://keystone.local:5000/v3',
            'auth_url = http://keystone.local:12345/v3',
            'project_domain_name = servicedom',
            'user_domain_name = servicedom',
            'identity_uri = http://keystone.local:5000/v3',
            'project_name = svcproj1',
            'username = svcuser1',
            'password = svcpass1',
            'region_name = RegionOne'
        ]
        self.assertContent(expected_entries)

    def test_database_relation(self):
        # add database relation
        test_utils.add_complete_database_relation(self.harness)

        # check rendered content
        expected_entries = [
            'mysql+pymysql://dbuser:strongpass@juju-unit-1:3306/cloudkitty'
        ]

        self.assertContent(expected_entries)

    @patch('subprocess.check_call', autospec=True)
    def test_database_migration(self, _check_call):
        self.harness.charm._bootstrap_db()

        calls = [
            call(['cloudkitty-storage-init']),
            call(['cloudkitty-dbsync', 'upgrade'])
        ]
        _check_call.assert_has_calls(calls)

    def test_gnocchi_relation(self):
        test_utils.add_complete_metric_relation(self.harness)

        # check rendered content
        expected_entries = [
            'gnocchi_endpoint = http://10.0.0.1:8041'
        ]

        self.assertContent(expected_entries)

    def test_rabbitmq_relation(self):
        test_utils.add_complete_rabbitmq_relation(self.harness)

        # check rendered content
        url = 'rabbit://cloudkitty:strong_password@10.0.0.1:5672/cloudkitty'

        expected_entries = [
            '[oslo_messaging_notifications]',
            'driver = messagingv2',
            'transport_url = ' + url,
        ]

        self.assertContent(expected_entries)
