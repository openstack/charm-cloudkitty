#!/usr/bin/env python3

# Copyright 2020 Canonical Ltd.
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

"""Module containing shared code to be used in a charms units tests."""

from ops.testing import Harness


def add_base_identity_service_relation(harness: Harness) -> str:
    """Add identity-service relation."""
    rel_id = harness.add_relation("identity-service", "keystone")
    harness.add_relation_unit(rel_id, "keystone/0")
    harness.update_relation_data(
        rel_id, "keystone/0", {"ingress-address": "10.0.0.33"}
    )
    return rel_id


def add_identity_service_relation_response(
    harness: Harness, rel_id: str
) -> None:
    """Add id service data to identity-service relation."""
    harness.update_relation_data(
        rel_id,
        "keystone",
        {
            "admin-domain-id": "admindomid1",
            "admin-project-id": "adminprojid1",
            "admin-user-id": "adminuserid1",
            "api-version": "3",
            "auth-host": "keystone.local",
            "auth-port": "12345",
            "auth-protocol": "http",
            "internal-host": "keystone.internal",
            "internal-port": "5000",
            "internal-protocol": "http",
            "service-domain-name": "servicedom",
            "service-domain_id": "svcdomid1",
            "service-host": "keystone.service",
            "service-password": "svcpass1",
            "service-port": "5000",
            "service-protocol": "http",
            "service-project-name": "svcproj1",
            "service-project-id": "svcprojid1",
            "service-user-name": "svcuser1",
        },
    )


def add_complete_identity_relation(harness: Harness) -> None:
    """Add complete Identity relation."""
    rel_id = add_base_identity_service_relation(harness)
    add_identity_service_relation_response(
        harness,
        rel_id)
    return rel_id


def add_base_database_service_relation(harness: Harness) -> str:
    """Add database relation."""
    rel_id = harness.add_relation("database", "mysql")
    harness.add_relation_unit(rel_id, "mysql/0")
    harness.update_relation_data(
        rel_id, "mysql/0", {"ingress-address": "10.0.0.33"}
    )
    return rel_id


def add_database_service_relation_response(
    harness: Harness, rel_id: str
) -> None:
    """Add database data to database relation."""
    harness.update_relation_data(
        rel_id,
        "mysql",
        {
            'endpoints': 'juju-unit-1:3306',
            'password': 'strongpass',
            'read-only-endpoints': 'juju-unit-2:3306',
            'username': 'dbuser',
            'version': '8.0.30-0ubuntu0.20.04.2'
        },
    )


def add_complete_database_relation(harness: Harness) -> None:
    """Add complete Database relation."""
    rel_id = add_base_database_service_relation(harness)
    add_database_service_relation_response(
        harness,
        rel_id)
    return rel_id


def add_base_metric_service_relation(harness: Harness) -> int:
    """Add metric-service relation."""
    rel_id = harness.add_relation("metric-service", "gnocchi")
    harness.add_relation_unit(rel_id, "gnocchi/0")
    harness.update_relation_data(
        rel_id, "gnocchi/0", {
            "egress-subnets": "10.0.0.1/32",
            "ingress-address": "10.0.0.1",
            "private-address": "10.0.0.1",
        }
    )
    return rel_id


def add_metric_service_relation_response(
    harness: Harness, rel_id: str
) -> None:
    """Add gnocchi data to metric-service relation."""
    harness.update_relation_data(
        rel_id, "gnocchi/0", {
            "gnocchi_url": "http://10.0.0.1:8041",
        }
    )


def add_complete_metric_relation(harness: Harness) -> int:
    """Add complete metric-service relation."""
    rel_id = add_base_metric_service_relation(harness)
    add_metric_service_relation_response(harness, rel_id)
    return rel_id


def add_base_rabbitmq_relation(harness: Harness) -> int:
    """Add rabbitmq relation."""
    rel_id = harness.add_relation("amqp", "rabbitmq-server")
    harness.add_relation_unit(rel_id, "rabbitmq-server/0")
    harness.update_relation_data(
        rel_id, "rabbitmq-server/0", {
            "egress-subnets": "10.0.0.1/32",
            "ingress-address": "10.0.0.1",
            "private-address": "10.0.0.1",
        }
    )
    return rel_id


def add_rabbitmq_relation_response(
    harness: Harness, rel_id: str
) -> None:
    """Add rabbitmq data to amqp relation."""
    harness.update_relation_data(
        rel_id, "rabbitmq-server/0", {
            "user": "cloudkitty",
            "vhost": "cloudkitty",
            "password": "strong_password",
            "hostname": "10.0.0.1",
        }
    )


def add_complete_rabbitmq_relation(harness: Harness) -> int:
    """Add complete rabbitmq relation."""
    rel_id = add_base_rabbitmq_relation(harness)
    add_rabbitmq_relation_response(harness, rel_id)
    return rel_id
