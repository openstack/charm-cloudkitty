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

"""GnocchiRequires module.

This library contains the Requires for handling the gnocchi interface.

In order to use `GnocchiRequires` in your charm,
add the relation interface in the `metadata.yaml` file:
```
requires:
  metric-service:
    interface: gnocchi
```

Also provide additional parameters to the charm object:
    - region

Two events are also available to respond to:
    - connected
    - ready
    - goneaway

A basic example showing the usage of this relation follows:

```
from charms.openstack_libs.v0.gnocchi_requires import GnocchiRequires

class GnochiClientCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)

        # Gnochi Requires
        self.metric_service = GnocchiRequires(
            self, "metric-service"
            region = "region"
        )

        # Event handlers
        self.framework.observe(
            self.metric_service.on.connected,
            self._on_metric_service_connected)
        self.framework.observe(
            self.metric_service.on.ready,
            self._on_metric_service_ready)
        self.framework.observe(
            self.metric_service.on.goneaway,
            self._on_metric_service_goneaway)

    def _on_metric_service_connected(self, event):
        '''React to the GnocchiRequires connected event.

        This event happens when a GnocchiRequires relation is added to the
        model before credentials etc have been provided.
        '''
        # Do something before the relation is complete
        pass

    def _on_metric_service_ready(self, event):
        '''React to the Gnochi ready event.

        The GnocchiRequires interface will use the provided config for the
        request to the metric server.
        '''
        # GnocchiRequires Relation is ready. Do something with the
        # completed relation.
        pass

    def _on_metric_service_goneaway(self, event):
        '''React to the Gnochi goneaway event.

        This event happens when an Gnochi relation is removed.
        '''
        # GnocchiRequires Relation has goneaway. shutdown services or suchlike
        pass
```
"""

import logging

from ops.framework import EventBase, EventSource, Object, ObjectEvents
from ops.model import Relation

# The unique Charmhub library identifier, never change it
LIBID = "bdc4aef454524b6eaa90501b3c9d500c"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1


class GnocchiConnectedEvent(EventBase):
    """Gnocchi connected Event."""

    pass


class GnocchiReadyEvent(EventBase):
    """Gnocchi ready for use Event."""

    pass


class GnocchiGoneAwayEvent(EventBase):
    """Gnocchi relation has gone-away Event."""

    pass


class GnocchiServerEvents(ObjectEvents):
    """Events class for `on`."""

    connected = EventSource(GnocchiConnectedEvent)
    ready = EventSource(GnocchiReadyEvent)
    goneaway = EventSource(GnocchiGoneAwayEvent)


class GnocchiRequires(Object):
    """Requires side interface for gnocchi interface type."""

    on = GnocchiServerEvents()

    def __init__(self, charm, relation_name: str):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name

        self.framework.observe(
            self.charm.on[relation_name].relation_joined,
            self._on_gnocchi_relation_joined,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_changed,
            self._on_gnocchi_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_departed,
            self._on_gnocchi_relation_changed,
        )
        self.framework.observe(
            self.charm.on[relation_name].relation_broken,
            self._on_gnocchi_relation_broken,
        )

    def _on_gnocchi_relation_joined(self, event):
        """Gnocchi relation joined."""
        logging.debug("Gnocchi on_joined")
        self.on.connected.emit()

    def _on_gnocchi_relation_changed(self, event):
        """Gnocchi relation changed."""
        logging.debug("Gnocchi on_changed")
        try:
            self.gnocchi_url
            self.on.ready.emit()
        except AttributeError:
            pass

    def _on_gnocchi_relation_broken(self, event):
        """Gnocchi relation broken."""
        logging.debug("Gnocchi on_broken")
        self.on.goneaway.emit()

    @property
    def _gnocchi_rel(self) -> Relation:
        """The Gnocchi relation."""
        return self.framework.model.get_relation(self.relation_name)

    def _get_remote_unit_data(self, key: str) -> str:
        """Return the value for the given key from remote app data."""
        for unit in self._gnocchi_rel.units:
            data = self._gnocchi_rel.data[unit]
            return data.get(key)

    def get_data(self, key: str) -> str:
        """Return the value for the given key."""
        return self._get_remote_unit_data(key)

    @property
    def gnocchi_url(self) -> str:
        """Return the gnocchi_url."""
        return self.get_data("gnocchi_url")
