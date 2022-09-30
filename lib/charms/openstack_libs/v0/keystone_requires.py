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

"""KeystoneRequires module.

This library contains the Requires for handling the keystone interface.

Import `KeystoneRequires` in your charm, with the charm object and the
relation name:
    - self
    - "identity-service"

Also provide additional parameters to the charm object:
    - service
    - internal_url
    - public_url
    - admin_url
    - region

Two events are also available to respond to:
    - connected
    - ready
    - goneaway

A basic example showing the usage of this relation follows:

```
from charms.openstack_libs.v0.keystone_requires import KeystoneRequires

class IdentityServiceClientCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        # IdentityService Requires
        self.identity_service = KeystoneRequires(
            self, "identity-service",
            service = "my-service"
            internal_url = "http://internal-url"
            public_url = "http://public-url"
            admin_url = "http://admin-url"
            region = "region"
        )
        self.framework.observe(
            self.identity_service.on.connected,
            self._on_identity_service_connected)
        self.framework.observe(
            self.identity_service.on.ready,
            self._on_identity_service_ready)
        self.framework.observe(
            self.identity_service.on.goneaway,
            self._on_identity_service_goneaway)

    def _on_identity_service_connected(self, event):
        '''React to the KeystoneRequires connected event.

        This event happens when a KeystoneRequires relation is added to the
        model before credentials etc have been provided.
        '''
        # Do something before the relation is complete
        pass

    def _on_identity_service_ready(self, event):
        '''React to the IdentityService ready event.

        The KeystoneRequires interface will use the provided config for the
        request to the identity server.
        '''
        # KeystoneRequires Relation is ready. Do something with the
        # completed relation.
        pass

    def _on_identity_service_goneaway(self, event):
        '''React to the IdentityService goneaway event.

        This event happens when an IdentityService relation is removed.
        '''
        # KeystoneRequires Relation has goneaway. shutdown services or suchlike
        pass
```
"""

import json
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


class KeystoneConnectedEvent(EventBase):
    """Keystone connected Event."""

    pass


class KeystoneReadyEvent(EventBase):
    """Keystone ready for use Event."""

    pass


class KeystoneGoneAwayEvent(EventBase):
    """Keystone relation has gone-away Event."""

    pass


class KeystoneServerEvents(ObjectEvents):
    """Events class for `on`."""

    connected = EventSource(KeystoneConnectedEvent)
    ready = EventSource(KeystoneReadyEvent)
    goneaway = EventSource(KeystoneGoneAwayEvent)


class KeystoneRequires(Object):
    """Requires side interface for keystone interface type."""

    on = KeystoneServerEvents()

    _backwards_compat_remaps = {
        "admin-user-name": "admin_user",
        "service-user-name": "service_username",
        "service-project-name": "service_tenant",
        "service-project-id": "service_tenant_id",
        "service-domain-name": "service_domain",
    }

    def __init__(
        self, charm, relation_name: str, service_endpoints: list, region: str
    ):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name
        self.service_endpoints = service_endpoints
        self.region = region
        self.framework.observe(
            self.charm.on[relation_name].relation_joined,
            self._on_keystone_relation_joined,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_changed,
            self._on_keystone_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_departed,
            self._on_keystone_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_broken,
            self._on_keystone_relation_broken,
        )

    def _on_keystone_relation_joined(self, event):
        """Keystone relation joined."""
        logging.debug("Keystone on_joined")
        self.on.connected.emit()
        self.register_services(self.service_endpoints, self.region)

    def _on_keystone_relation_changed(self, event):
        """Keystone relation changed."""
        logging.debug("Keystone on_changed")
        try:
            self.service_password
            self.on.ready.emit()
        except AttributeError:
            pass

    def _on_keystone_relation_broken(self, event):
        """Keystone relation broken."""
        logging.debug("Keystone on_broken")
        self.on.goneaway.emit()

    @property
    def _keystone_rel(self) -> Relation:
        """The Keystone relation."""
        return self.framework.model.get_relation(self.relation_name)

    def _get_remote_app_data(self, key: str) -> str:
        """Return the value for the given key from remote app data."""
        data = self._keystone_rel.data[self._keystone_rel.app]
        return data.get(key)

    def _get_remote_unit_data(self, key: str) -> str:
        """Return the value for the given key from remote unit data."""
        # NOTE: deal with remapping and transpose of
        #       "-" -> "_" for backwards compatibility
        _legacy_key = self._backwards_compat_remaps.get(
            key, key.replace("-", "_")
        )
        for unit in self._keystone_rel.units:
            data = self._keystone_rel.data[unit]
            if _legacy_key in data:
                return data[_legacy_key]

    def get_data(self, key: str) -> str:
        """Return the value for the given key.

        This method will inspect the application data bag first
        and then fallback to per-unit databags for backwards
        compatibility.
        """
        return self._get_remote_app_data(key) or self._get_remote_unit_data(
            key
        )

    @property
    def api_version(self) -> str:
        """Return the api_version."""
        return self.get_data("api-version")

    @property
    def auth_host(self) -> str:
        """Return the auth_host."""
        return self.get_data("auth-host")

    @property
    def auth_port(self) -> str:
        """Return the auth_port."""
        return self.get_data("auth-port")

    @property
    def auth_protocol(self) -> str:
        """Return the auth_protocol."""
        return self.get_data("auth-protocol")

    @property
    def internal_host(self) -> str:
        """Return the internal_host."""
        return self.get_data("internal-host")

    @property
    def internal_port(self) -> str:
        """Return the internal_port."""
        return self.get_data("internal-port")

    @property
    def internal_protocol(self) -> str:
        """Return the internal_protocol."""
        return self.get_data("internal-protocol")

    @property
    def admin_domain_name(self) -> str:
        """Return the admin_domain_name."""
        return self.get_data("admin-domain-name")

    @property
    def admin_domain_id(self) -> str:
        """Return the admin_domain_id."""
        return self.get_data("admin-domain-id")

    @property
    def admin_project_name(self) -> str:
        """Return the admin_project_name."""
        return self.get_data("admin-project-name")

    @property
    def admin_project_id(self) -> str:
        """Return the admin_project_id."""
        return self.get_data("admin-project-id")

    @property
    def admin_user_name(self) -> str:
        """Return the admin_user_name."""
        return self.get_data("admin-user-name")

    @property
    def admin_user_id(self) -> str:
        """Return the admin_user_id."""
        return self.get_data("admin-user-id")

    @property
    def service_domain_name(self) -> str:
        """Return the service_domain_name."""
        return self.get_data("service-domain-name")

    @property
    def service_domain_id(self) -> str:
        """Return the service_domain_id."""
        return self.get_data("service-domain-id")

    @property
    def service_host(self) -> str:
        """Return the service_host."""
        return self.get_data("service-host")

    @property
    def service_password(self) -> str:
        """Return the service_password."""
        return self.get_data("service-password")

    @property
    def service_port(self) -> str:
        """Return the service_port."""
        return self.get_data("service-port")

    @property
    def service_protocol(self) -> str:
        """Return the service_protocol."""
        return self.get_data("service-protocol")

    @property
    def service_project_name(self) -> str:
        """Return the service_project_name."""
        return self.get_data("service-project-name")

    @property
    def service_project_id(self) -> str:
        """Return the service_project_id."""
        return self.get_data("service-project-id")

    @property
    def service_user_name(self) -> str:
        """Return the service_user_name."""
        return self.get_data("service-user-name")

    @property
    def service_user_id(self) -> str:
        """Return the service_user_id."""
        return self.get_data("service-user-id")

    @property
    def internal_auth_url(self) -> str:
        """Return the internal_auth_url."""
        return self.get_data("internal-auth-url")

    @property
    def admin_auth_url(self) -> str:
        """Return the admin_auth_url."""
        return self.get_data("admin-auth-url")

    @property
    def public_auth_url(self) -> str:
        """Return the public_auth_url."""
        return self.get_data("public-auth-url")

    def register_services(self, service_endpoints: list, region: str) -> None:
        """Request access to the Keystone server."""
        # NOTE:
        # backward compatibility with keystone machine charm
        # only supports single endpoint type registration
        relation_data = {
            "service": service_endpoints[0]["service_name"],
            "public_url": service_endpoints[0]["public_url"],
            "internal_url": service_endpoints[0]["internal_url"],
            "admin_url": service_endpoints[0]["admin_url"],
            "region": region,
        }
        unit_data = self._keystone_rel.data[self.charm.unit]
        unit_data.update(relation_data)

        # NOTE:
        # Forward compatibility with keystone k8s operator
        if self.model.unit.is_leader():
            logging.debug("Requesting service registration")
            app_data = self._keystone_rel.data[self.charm.app]
            app_data["service-endpoints"] = json.dumps(
                service_endpoints, sort_keys=True
            )
            app_data["region"] = region
