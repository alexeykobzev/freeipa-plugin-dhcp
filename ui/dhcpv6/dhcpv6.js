// Copyright © 2016 Jeffery Harrell <jefferyharrell@gmail.com>
// See file 'LICENSE' for use and warranty information.
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

define(
    ['freeipa/ipa', 'freeipa/menu', 'freeipa/phases', 'freeipa/reg', 'freeipa/rpc', 'freeipa/net'],
    function(IPA, menu, phases, reg, rpc, NET) {


        var exp = IPA.dhcpv6 = {};


//// Validators ///////////////////////////////////////////////////////////////


        IPA.dhcpv6range_validator = function(spec) {

            spec = spec || {};
            spec.message = spec.message || 'Range must be of the form x.x.x.x y.y.y.y, where x.x.x.x is the first IP address in the pool and y.y.y.y is the last IP address in the pool.';
            var that = IPA.validator(spec);

            that.validate = function(value) {
                if (IPA.is_empty(value)) return that.true_result();

                that.address_type = 'IPv4';

                var components = value.split(" ");
                if (components.length != 2) {
                    return that.false_result();
                }

                var start = NET.ip_address(components[0]);
                var end = NET.ip_address(components[1]);

                if (!start.valid || start.type != 'v4-quads' || !end.valid || end.type != 'v4-quads') {
                    return that.false_result();
                }

                return that.true_result();
            };

            that.dhcpv6range_validate = that.validate;
            return that;
        };


        IPA.dhcpv6range_subnet_validator = function(spec) {
            spec = spec || {};
            spec.message = spec.message || 'Invalid IP range.';
            var that = IPA.validator(spec);

            that.validate = function(value, context) {
                if (context.container.rangeIsValid) {
                    return that.true_result();
                }
                that.message = context.container.invalidRangeMessage;
                return that.false_result();
            }

            that.dhcpv6range_subnet_validate = that.validate;
            return that;
        };


//// Factories ////////////////////////////////////////////////////////////////


        IPA.dhcpv6.dhcpv6pool_adder_dialog = function(spec) {
            spec = spec || {};
            var that = IPA.entity_adder_dialog(spec);

            that.previous_dhcpv6range = [];

            that.rangeIsValid = false;
            that.invalidRangeMessage = "Invalid IP range."

            that.create_content = function() {
                that.entity_adder_dialog_create_content();
                var dhcpv6range_widget = that.fields.get_field('dhcpv6range').widget;
                dhcpv6range_widget.value_changed.attach(that.dhcpv6range_changed);
            };

            that.dhcpv6range_changed = function() {

                var dhcpv6range_widget = that.fields.get_field('dhcpv6range').widget;
                var dhcpv6range = dhcpv6range_widget.get_value();
                var name_widget = that.fields.get_field('cn').widget;
                var name = name_widget.get_value();

                if (name.length == 0) {
                    name_widget.update(dhcpv6range);
                }

                if (name.length > 0 && name[0] == that.previous_dhcpv6range) {
                    name_widget.update(dhcpv6range);
                }

                that.previous_dhcpv6range = dhcpv6range;

                var firstValidationResult = that.fields.get_field('dhcpv6range').validators[0].validate(that.fields.get_field('dhcpv6range').get_value()[0])

                if (firstValidationResult.valid) {
                    setValidFlagCommand = rpc.command({
                        entity: 'dhcpv6pool',
                        method: 'is_valid',
                        args: that.pkey_prefix.concat([dhcpv6range]),
                        options: {},
                        retry: false,
                        on_success: that.setValidFlag
                    });
                    setValidFlagCommand.execute();
                }
            }

            that.setValidFlag = function(data, text_status, xhr) {
                that.rangeIsValid = data.result.result;
                that.invalidRangeMessage = data.result.value;
                that.validate();
            }

            return that;
        }


//// dhcpv6service //////////////////////////////////////////////////////////////


        var make_dhcpv6service_spec = function() {
            return {
                name: 'dhcpv6service',
                defines_key: false,
                facets: [
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'domainname',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainnameservers',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainsearch',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'defaultleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'maxleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                ]
                            },
                            {
                                name: 'dhcpv6parameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'dhcpprimarydn',
                                        read_only: true,
                                        formatter: 'dn'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpsecondarydn',
                                        read_only: true,
                                        formatter: 'dn'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements',
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption',
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            };
        };
        exp.dhcpv6service_entity_spec = make_dhcpv6service_spec();


//// dhcpv6subnet ///////////////////////////////////////////////////////////////


        var make_dhcpv6subnet_spec = function() {
            return {
                name: 'dhcpv6subnet',
                facet_groups: ['settings', 'dhcpv6poolfacetgroup', 'dhcpv6groupfacetgroup', 'dhcpv6hostfacetgroup'],
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                            'dhcpv6netmask',
                            'dhcpcomments'
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'router',
                                        flags: ['w_if_no_aci'],
                                        validators: [ 'ip_v4_address' ]
                                    }
                                ]
                            },
                            {
                                name: 'dhcpv6parameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'cn',
                                        read_only: true
                                    },
                                    {
                                        name: 'dhcpv6netmask',
                                        read_only: true
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ],
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcpv6poolfacetgroup',
                        nested_entity: 'dhcpv6pool',
                        search_all_entries: true,
                        label: 'DHCP Pools',
                        tab_label: 'DHCP Pools',
                        name: 'dhcpv6pools',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcpcomments'
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcpv6groupfacetgroup',
                        nested_entity: 'dhcpv6subnetgroup',
                        search_all_entries: true,
                        label: 'DHCP Groups',
                        tab_label: 'DHCP Groups',
                        name: 'dhcpv6subnetgroups',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcpcomments'
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcpv6hostfacetgroup',
                        nested_entity: 'dhcpv6subnethost',
                        search_all_entries: true,
                        label: 'DHCP Hosts',
                        tab_label: 'DHCP Hosts',
                        name: 'dhcpv6subnethost',
                        columns: [
                            'cn',
                            'dhcphwaddress',
                            'dhcpcomments'
                        ]
                    }
                ],
                adder_dialog: {
                    method: 'add_cidr',
                    fields: [
                        {
                            name: 'networkaddr',
                            label: 'Subnet/Prefix',
                            validators: [ 'network' ]
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments'
                        }
                    ]
                }
            };
        };
        exp.dhcpv6subnet_entity_spec = make_dhcpv6subnet_spec();


//// dhcpv6pool /////////////////////////////////////////////////////////////////


        var make_dhcpv6pool_spec = function() {
            return {
                name: 'dhcpv6pool',
                facet_groups: ['settings', 'dhcpv6poolhostfacetgroup'],
                containing_entity: 'dhcpv6subnet',
                facets: [
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'defaultleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'maxleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'checkbox',
                                        name: 'permitknownclients',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'checkbox',
                                        name: 'permitunknownclients',
                                        flags: ['w_if_no_aci']
                                    },
                                ]
                            },
                            {
                                name: 'dhcpv6parameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'cn'
                                    },
                                    {
                                        name: 'dhcpv6range',
                                        read_only: true
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpv6permitlist'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcpv6poolhostfacetgroup',
                        nested_entity: 'dhcpv6poolhost',
                        search_all_entries: true,
                        label: 'DHCP Hosts',
                        tab_label: 'DHCP Hosts',
                        name: 'dhcpv6poolhosts',
                        columns: [
                            'cn',
                            'dhcphwaddress',
                            'dhcpcomments'
                        ]
                    }
                ],
                adder_dialog: {
                    $factory: IPA.dhcpv6.dhcpv6pool_adder_dialog,
                    fields: [
                        {
                            name: 'dhcpv6range',
                            validators: [
                                {
                                    $type: 'dhcpv6range',
                                },
                                {
                                    $type: 'dhcpv6range_subnet',
                                },
                            ]
                        },
                        {
                            name: 'cn'
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments'
                        }
                    ]
                }
            };
        };
        exp.dhcpv6pool_entity_spec = make_dhcpv6pool_spec();


//// dhcgroup /////////////////////////////////////////////////////////////////


        var make_dhcpv6group_spec = function(element_name,containing_entity) {
            return {
                name: element_name,
                facet_groups: ['settings', element_name + 'hostfacetgroup'],
                containing_entity: containing_entity,
                facets: [
                    {
                        $type: 'search',
                        tab_label: 'DHCP Groups',
                        columns: [
                            'cn',
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'router',
                                        flags: ['w_if_no_aci'],
                                        validators: [ 'ip_v6_address' ]
                                    },
                                    {
                                        name: 'domainname',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainnameservers',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainsearch',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'defaultleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'maxleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    }
                                ]
                            },
                            {
                                name: 'dhcpv6parameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'cn'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: element_name + 'hostfacetgroup',
                        nested_entity: element_name + 'host',
                        search_all_entries: true,
                        label: 'DHCP Hosts',
                        tab_label: 'DHCP Hosts',
                        name: element_name + 'hosts',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcpv6hwaddress',
                            'dhcpcomments'
                        ]
                    }
                ],
                standard_association_facets: true,
                adder_dialog: {
                    $factory: IPA.dhcpv6.dhcpv6group_adder_dialog,
                    fields: [
                        {
                            name: 'cn'
                        },
                        {
                            name: 'domainname',
                            flags: ['w_if_no_aci']
                        },
                        {
                            $type: 'multivalued',
                            name: 'domainnameservers',
                            flags: ['w_if_no_aci']
                        },
                        {
                            $type: 'multivalued',
                            name: 'domainsearch',
                            flags: ['w_if_no_aci']
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments'
                        }
                    ]
                }
            };
        };
        exp.dhcpv6group_entity_spec = make_dhcpv6group_spec('dhcpv6group', '');
        exp.dhcpv6subnetgroup_entity_spec = make_dhcpv6group_spec('dhcpv6subnetgroup', 'dhcpv6subnet');
        exp.dhcpv6groupgroup_entity_spec = make_dhcpv6group_spec('dhcpv6groupgroup', 'dhcpv6group');
        exp.dhcpv6poolgroup_entity_spec = make_dhcpv6group_spec('dhcpv6poolgroup', 'dhcpv6pool');

//// dhcpv6sharednetwork ///////////////////////////////////////////////////////////////


        var make_dhcpv6sharednetwork_spec = function() {
            return {
                name: 'dhcpv6sharednetwork',
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'settings',
                                fields: [
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ],
                    }
                ],
                adder_dialog: {
                    fields: [
                        {
                            $type: 'entity_select',
                            name: 'cn',
                            other_entity: 'host',
                            other_field: 'fqdn',
                            required: true
                        }
                    ]
                }
            };
        };
        exp.dhcpv6sharednetwork_entity_spec = make_dhcpv6sharednetwork_spec();

//// dhcpv6host /////////////////////////////////////////////////////////////////

        var make_dhcpv6host_spec = function(element_name,containing_entity) {
            return {
                name: element_name,
                facet_groups: ['settings'],
                containing_entity: containing_entity,
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                             {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'cn',
                                        read_only: true
                                    },
                                    {
                                        name: 'macaddress',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'ipaddress',
                                        flags: ['w_if_no_aci'],
                                        validators: [ 'ip_v6_address' ]
                                    },
                                ]
                            },
                            {
                                name: 'settings',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ],
                    }
                ],
                adder_dialog: {
                    fields: [
                        {
                            name: 'cn',
                            flags: ['w_if_no_aci'],
                            required: true
                        },
                        {
                            $type: 'entity_select',
                            name: 'fqdn',
                            other_entity: 'host',
                            other_field: 'fqdn',
                            required: true
                        },
                        {
                            name: 'macaddress',
                            flags: ['w_if_no_aci'],
                            required: true
                        },
                        {
                            name: 'ipaddress',
                            flags: ['w_if_no_aci'],
                            validators: [ 'ip_v6_address' ]
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments'
                        }
                    ]
                }
            };
        };
        exp.dhcpv6host_entity_spec = make_dhcpv6host_spec('dhcpv6host', '');
        exp.dhcpv6grouphost_entity_spec = make_dhcpv6host_spec('dhcpv6grouphost', 'dhcpv6group');
        exp.dhcpv6subnethost_entity_spec = make_dhcpv6host_spec('dhcpv6subnethost', 'dhcpv6subnet');
        exp.dhcpv6subnetgrouphost_entity_spec = make_dhcpv6host_spec('dhcpv6subnetgrouphost', 'dhcpv6subnetgroup');
        exp.dhcpv6poolhost_entity_spec = make_dhcpv6host_spec('dhcpv6poolhost', 'dhcpv6pool');

//// dhcpv6server ///////////////////////////////////////////////////////////////


        var make_dhcpv6server_spec = function() {
            return {
                name: 'dhcpv6server',
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'cn',
                                        read_only: true
                                    },
                                    {
                                        name: 'dhcpdelayedserviceparameter'
                                    },
                                    {
                                        name: 'dhcpversion'
                                    },
                                    {
                                        name: 'dhcphashbucketassignment'
                                    },
                                    {
                                        name: 'dhcpimplementation'
                                    },
                                    {
                                        name: 'dhcpmaxclientleadtime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'dhcpfailoverendpointstate'
                                    },
                                    {
                                        name: 'dhcphashbucketassignment'
                                    },
                                ]
                            },
                            {
                                name: 'settings',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ],
                    }
                ],
                adder_dialog: {
                    fields: [
                        {
                            $type: 'entity_select',
                            name: 'cn',
                            other_entity: 'host',
                            other_field: 'fqdn',
                            required: true
                        }
                    ]
                }
            };
        };
        exp.dhcpv6server_entity_spec = make_dhcpv6server_spec();

//// dhcpv6failoverpeer ///////////////////////////////////////////////////////////////


        var make_dhcpv6failoverpeer_spec = function() {
            return {
                name: 'dhcpv6failoverpeer',
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'settings',
                                fields: [
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcpoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'dhcpcomments'
                                    }
                                ]
                            }
                        ],
                    }
                ],
                adder_dialog: {
                    fields: [
                        {
                            $type: 'entity_select',
                            name: 'cn',
                            other_entity: 'host',
                            other_field: 'fqdn',
                            required: true
                        }
                    ]
                }
            };
        };
        exp.dhcpv6failoverpeer_entity_spec = make_dhcpv6failoverpeer_spec();


//// exp.register /////////////////////////////////////////////////////////////


        exp.register = function() {
            var dhcpv6 = 'dhcpv6'

            var v = reg.validator;
            v.register('dhcpv6range', IPA.dhcpv6range_validator);
            v.register('dhcpv6range_subnet', IPA.dhcpv6range_subnet_validator);

            var e = reg.entity;
            e.register({type: dhcpv6 +'service', spec: exp.dhcpv6service_entity_spec});
            e.register({type: dhcpv6 +'subnet', spec: exp.dhcpv6subnet_entity_spec});
            e.register({type: dhcpv6 +'pool', spec: exp.dhcpv6pool_entity_spec});
            e.register({type: dhcpv6 +'group', spec: exp.dhcpv6group_entity_spec});
            e.register({type: dhcpv6 +'subnetgroup', spec: exp.dhcpv6subnetgroup_entity_spec});
            e.register({type: dhcpv6 +'grouproup', spec: exp.dhcpv6groupgroup_entity_spec});
            e.register({type: dhcpv6 +'sharednetwork', spec: exp.dhcpv6sharednetwork_entity_spec});
            e.register({type: dhcpv6 +'host', spec: exp.dhcpv6host_entity_spec});
            e.register({type: dhcpv6 +'grouphost', spec: exp.dhcpv6grouphost_entity_spec});
            e.register({type: dhcpv6 +'subnethost', spec: exp.dhcpv6subnethost_entity_spec});
            e.register({type: dhcpv6 +'subnetgrouphost', spec: exp.dhcpv6subnetgrouphost_entity_spec});
            e.register({type: dhcpv6 +'poolhost', spec: exp.dhcpv6poolhost_entity_spec});
            e.register({type: dhcpv6 +'server', spec: exp.dhcpv6server_entity_spec});
            e.register({type: dhcpv6 +'failoverpeer', spec: exp.dhcpv6failoverpeer_entity_spec});
        }


//// menu spec ////////////////////////////////////////////////////////////////


        var make_dhcpv6_menu_spec = function(menu_name, menu_lable, menu_entity) {
            return {
                   name: menu_name,
                    label: menu_lable,
                    children: [
                        {
                            entity: menu_entity + 'service',
                            label: 'Configuration'
                        },
                        {
                            entity: menu_entity + 'subnet',
                            label: 'Subnets',
                            children: [
                                {
                                    entity: menu_entity + 'pool',
                                    lable: 'Pool',
                                    hidden: true,
                                    children: [
                                        {
                                            entity: menu_entity + 'poolhost',
                                            label: 'Host',
                                            hidden: true
                                        }
                                    ]
                                },
                                {
                                    entity: menu_entity + 'subnetgroup',
                                    label: 'Group',
                                    hidden: true,
                                    children: [
                                        {
                                            entity: menu_entity + 'subnetgrouphost',
                                            label: 'Host',
                                            hidden: true
                                        }
                                    ]
                                },
                                {
                                    entity: menu_entity + 'subnethost',
                                    label: 'Host',
                                    hidden: true
                                }
                            ]
                        },
                        {
                            entity: menu_entity + 'host',
                            label: 'Hosts'
                        },
                        {
                            entity: menu_entity + 'group',
                            label: 'Groups',
                            children: [
                                {
                                    entity: menu_entity + 'grouphost',
                                    label: 'Host',
                                    hidden: true
                                }
                            ]
                        },
                        {
                            entity: menu_entity + 'sharednetwork',
                            label: 'Shared Network'
                        },
                        {
                            entity: menu_entity + 'server',
                            label: 'Servers'
                        },
                        {
                            entity: menu_entity + 'failoverpeer',
                            label: 'Failoverpeer'
                        }
                    ]
                }
            }
        exp.dhcpv6_menu_spec = make_dhcpv6_menu_spec('dhcpv6','DHCP IPv6', 'dhcpv6');

        exp.add_menu_items = function() {
            network_services_item = menu.query({name: 'network_services'});
            if (network_services_item.length > 0) {
                menu.add_item( exp.dhcpv6_menu_spec, 'network_services' );
            }
        };


//// customize_host_ui ////////////////////////////////////////////////////////


        exp.customize_host_ui = function() {
            var adder_dialog = IPA.host.entity_spec.adder_dialog;
            var fields = adder_dialog.sections[1].fields;
            var macaddress_field_spec = {
                $type: 'multivalued',
                name: 'macaddress'
            }
            fields.splice(2, 0, macaddress_field_spec)
        };


//// phases ///////////////////////////////////////////////////////////////////


       // phases.on('customization', exp.customize_host_ui);
        phases.on('registration', exp.register);
        phases.on('profile', exp.add_menu_items, 20);

        return exp;

    }
);