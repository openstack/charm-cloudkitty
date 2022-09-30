# Cloudkitty

Cloudkitty charm - Openstack Rating as a Service

## Overview

This charm provides a way to deploy Cloudkitty - Openstack Rating as a Service module - in Openstack

**What is CloudKitty ?**

CloudKitty is a generic solution for the chargeback and rating of a cloud. Provides a metric-based rating for cloud administrators allowing them to create rating rules to the collected data.


**CloudKitty usage**

With Cloudkitty, it is possible to:

* Collect metrics from OpenStack (through Gnocchi).
* Apply rating rules to the previous metrics.
* Retrieve the rated information, grouped by scope and/or by metric type.

However, it is not possible to:

* Limit resources in other OpenStack services.
* Add taxes, convert between currencies, etc...

CloudKitty associates a price to a metric for a given period, the price is mapped according to end-user needs.


## Configuration

Cloudkitty charm configuration options

* `debug`\
to run service in debug mode change debug config value
    ```
    juju config cloudkitty debug=true
    ```
* `region`\
set the openstack cloud region, if value required to be changed preferably to specify in a bundle
    ```
    cloudkitty:
        charm: ch:cloudkity
        options:
            region: MyRegion
    ```

To display all configuration option information run `juju config
cloudkitty`. If the application is not deployed then see the charm's
[configuration file](config.yaml).

## Deployment

Deploy cloudkitty charm

```
juju deploy cloudkitty --channel edge
```

Or in a bundle
```
applications:
  cloudkitty:
    charm: ch:cloudkitty
    channel: edge
    num_units: 1
    series: jammy
```

## Relations

Cloudkitty charm supports the following relations.

MySQL relation - relation to [mysql-operator](https://github.com/canonical/mysql-operator) charm - provides database storage for the cloudkitty service.

**NOTE:** This charm is not backward compatible with legacy `mysql-innodb-cluster` charm

```
juju deploy mysql --channel edge
juju relate cloudkitty mysql
```

Keystone relation - provides identity management.

```
juju deploy keystone
juju relate cloudkitty keystone
```

Gnocchi relation - provides metrics collector service.
```
juju deploy gnocchi
juju relate cloudkitty gnocchi
```

RabbitMQ relation - provides messages queue service.
```
juju deploy rabbitmq-server
juju relate cloudkitty rabbitmq-server
```

## Actions
This section lists Juju [actions](https://jaas.ai/docs/actions) supported by the charm. Actions allow specific operations to be performed on a per-unit basis.

* `restart-services`\
restarts `cloudkitty-{api,processor}` services in the unit.

    ```
    juju run-action --wait cloudkitty/leader restart-services
    ```

## Usage

To interact with the service we should use the built-in openstack cloudkitty client in the [openstackclients package](https://snapcraft.io/openstackclients)

Check clients usage like this

```
openstack rating --help
```

First enable `hashmap` module
```
$ openstack rating module enable hashmap
```

Then start by creating a service called image for example
```
$ openstack rating hashmap service create image
```

Create a field called `flavor_id` as an example, and associate it with the service using the service ID
```
$ openstack rating hashmap field create <SERVICE_ID> flavor_id
```

Map the field with a value of the specific field, a flavor id
```
$ openstack flavor list
+---------+-----------+-------+------+-----------+-------+-----------+
| ID      | Name      |   RAM | Disk | Ephemeral | VCPUs | Is Public |
+---------+-----------+-------+------+-----------+-------+-----------+
| 123abc  | m1.tiny   |   512 |    8 |        40 |     1 | True      |
+---------+-----------+-------+------+-----------+-------+-----------+
```

Create the mapping of type `flat` and let's assign a cost of `1.2`
```
$ openstack rating hashmap mapping create --type flat --field-id <FIELD_ID> --value 123abc 1.2
```

Finally check the summary report
```
$ openstack rating summary get
```

## TO-DO

This charm is under development not yet stable, the following list provides pending features

* Enable TLS support using [[TLS interface]](https://opendev.org/openstack/charm-ops-interface-tls-certificates/src/branch/master/interface_tls_certificates/ca_client.py)

* InfluxDB relation required for [storage v2](https://docs.openstack.org/cloudkitty/latest/admin/configuration/storage.html#influxdb-v2)

* Cloudkitty dashboard charm relation

* High availability


## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.

Follow Openstack best practices for [Software contributions](https://docs.openstack.org/charm-guide/latest/community/software-contrib/index.html) in charm development.


# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-cloudkitty].

For general charm questions refer to the [OpenStack Charm Guide][cg].

<!-- LINKS -->
[cg]: https://docs.openstack.org/charm-guide
[lp-bugs-charm-cloudkitty]: https://bugs.launchpad.net/charm-cloudkitty/+filebug

