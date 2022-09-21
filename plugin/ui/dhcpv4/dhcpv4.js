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


        var exp = IPA.dhcp = {};


//// Validators ///////////////////////////////////////////////////////////////


        IPA.dhcprange_validator = function(spec) {

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

            that.dhcprange_validate = that.validate;
            return that;
        };


        IPA.dhcprange_subnet_validator = function(spec) {
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

            that.dhcprange_subnet_validate = that.validate;
            return that;
        };


//// Factories ////////////////////////////////////////////////////////////////


        IPA.dhcp.dhcppool_adder_dialog = function(spec) {
            spec = spec || {};
            var that = IPA.entity_adder_dialog(spec);

            that.previous_dhcprange = [];

            that.rangeIsValid = false;
            that.invalidRangeMessage = "Invalid IP range."

            that.create_content = function() {
                that.entity_adder_dialog_create_content();
                var dhcprange_widget = that.fields.get_field('dhcprange').widget;
                dhcprange_widget.value_changed.attach(that.dhcprange_changed);
            };

            that.dhcprange_changed = function() {

                var dhcprange_widget = that.fields.get_field('dhcprange').widget;
                var dhcprange = dhcprange_widget.get_value();
                var name_widget = that.fields.get_field('cn').widget;
                var name = name_widget.get_value();

                if (name.length == 0) {
                    name_widget.update(dhcprange);
                }

                if (name.length > 0 && name[0] == that.previous_dhcprange) {
                    name_widget.update(dhcprange);
                }

                that.previous_dhcprange = dhcprange;

                var firstValidationResult = that.fields.get_field('dhcprange').validators[0].validate(that.fields.get_field('dhcprange').get_value()[0])

                if (firstValidationResult.valid) {
                    setValidFlagCommand = rpc.command({
                        entity: 'dhcppool',
                        method: 'is_valid',
                        args: that.pkey_prefix.concat([dhcprange]),
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


//// dhcpservice //////////////////////////////////////////////////////////////


        var make_dhcpservice_spec = function() {
            return {
                name: 'dhcpservice',
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
                                name: 'dhcpparameters',
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
        exp.dhcpservice_entity_spec = make_dhcpservice_spec();


//// dhcpsubnet ///////////////////////////////////////////////////////////////


        var make_dhcpsubnet_spec = function() {
            return {
                name: 'dhcpsubnet',
                facet_groups: ['settings', 'dhcppoolfacetgroup', 'dhcpgroupfacetgroup', 'dhcphostfacetgroup'],
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                            'dhcpnetmask',
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
                                    },
                                    {
                                        name: 'dhcprange',
                                        label: 'Range',
                                        validators: [
                                            {
                                                $type: 'dhcprange',
                                            },
                                            // {
                                            //     $type: 'dhcprange_subnet',
                                            // },
                                        ]
                                    },
                                    {
                                        $type: 'multivalued',
                                        flags: ['w_if_no_aci'],
                                        name: 'domainnameserver',
                                        validators: [ 'ip_v4_address' ]
                                    },
                                ]
                            },
                            {
                                name: 'dhcpparameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'cn',
                                        read_only: true
                                    },
                                    {
                                        name: 'dhcpnetmask',
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
                        facet_group: 'dhcppoolfacetgroup',
                        nested_entity: 'dhcppool',
                        search_all_entries: true,
                        label: 'DHCP Pools',
                        tab_label: 'DHCP Pools',
                        name: 'dhcppools',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcpcomments'
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcpgroupfacetgroup',
                        nested_entity: 'dhcpsubnetgroup',
                        search_all_entries: true,
                        label: 'DHCP Groups',
                        tab_label: 'DHCP Groups',
                        name: 'dhcpsubnetgroups',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcpcomments'
                        ]
                    },
                    {
                        $type: 'nested_search',
                        facet_group: 'dhcphostfacetgroup',
                        nested_entity: 'dhcpsubnethost',
                        search_all_entries: true,
                        label: 'DHCP Hosts',
                        tab_label: 'DHCP Hosts',
                        name: 'dhcpsubnethost',
                        columns: [
                            {
                                name: 'cn'
                            },
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
                            name: 'dhcprange',
                            label: 'Range',
                            validators: [
                                {
                                    $type: 'dhcprange',
                                },
                                // {
                                //     $type: 'dhcprange_subnet',
                                // },
                            ],
                            required: false
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments'
                        }
                    ]
                }
            };
        };
        exp.dhcpsubnet_entity_spec = make_dhcpsubnet_spec();


//// dhcppool /////////////////////////////////////////////////////////////////


        var make_dhcppool_spec = function() {
            return {
                name: 'dhcppool',
                facet_groups: ['settings', 'dhcppoolhostfacetgroup'],
                containing_entity: 'dhcpsubnet',
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
                                name: 'dhcpparameters',
                                label: 'DHCP Parameters',
                                fields: [
                                    {
                                        name: 'cn'
                                    },
                                    {
                                        name: 'dhcprange',
                                        read_only: true
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'dhcppermitlist'
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
                        facet_group: 'dhcppoolhostfacetgroup',
                        nested_entity: 'dhcppoolhost',
                        search_all_entries: true,
                        label: 'DHCP Hosts',
                        tab_label: 'DHCP Hosts',
                        name: 'dhcppoolhosts',
                        columns: [
                            {
                                name: 'cn'
                            },
                            'dhcphwaddress',
                            'dhcpcomments'
                        ]
                    }
                ],
                adder_dialog: {
                    $factory: IPA.dhcp.dhcppool_adder_dialog,
                    fields: [
                        {
                            name: 'dhcprange',
                            validators: [
                                {
                                    $type: 'dhcprange',
                                },
                                // {
                                //     $type: 'dhcprange_subnet',
                                // },
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
        exp.dhcppool_entity_spec = make_dhcppool_spec();


//// dhcgroup /////////////////////////////////////////////////////////////////


        var make_dhcpgroup_spec = function(element_name,containing_entity) {
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
                                        validators: [ 'ip_v4_address' ]
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
                                name: 'dhcpparameters',
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
                            'dhcphwaddress',
                            'dhcpcomments'
                        ]
                    }
                ],
                standard_association_facets: true,
                adder_dialog: {
                    $factory: IPA.dhcp.dhcpgroup_adder_dialog,
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
        exp.dhcpgroup_entity_spec = make_dhcpgroup_spec('dhcpgroup', '');
        exp.dhcpsubnetgroup_entity_spec = make_dhcpgroup_spec('dhcpsubnetgroup', 'dhcpsubnet');
        exp.dhcpgroupgroup_entity_spec = make_dhcpgroup_spec('dhcpgroupgroup', 'dhcpgroup');
        exp.dhcppoolgroup_entity_spec = make_dhcpgroup_spec('dhcppoolgroup', 'dhcppool');

//// dhcpsharednetwork ///////////////////////////////////////////////////////////////


        var make_dhcpsharednetwork_spec = function() {
            return {
                name: 'dhcpsharednetwork',
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
        exp.dhcpsharednetwork_entity_spec = make_dhcpsharednetwork_spec();

//// dhcphost /////////////////////////////////////////////////////////////////

        var make_dhcphost_spec = function(element_name,containing_entity) {
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
                                        name: 'hostname',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'macaddress',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'ipaddress',
                                        flags: ['w_if_no_aci'],
                                        validators: [ 'ip_v4_address' ]
                                    },
                                    {
                                        name: 'dhcpclientid'
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
                            name: 'hostname',
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
                            validators: [ 'ip_v4_address' ]
                        },
                        {
                            $type: 'textarea',
                            name: 'dhcpcomments',
                            label: 'Comments'
                        }
                    ]
                }
            };
        };
        exp.dhcphost_entity_spec = make_dhcphost_spec('dhcphost', '');
        exp.dhcpgrouphost_entity_spec = make_dhcphost_spec('dhcpgrouphost', 'dhcpgroup');
        exp.dhcpsubnethost_entity_spec = make_dhcphost_spec('dhcpsubnethost', 'dhcpsubnet');
        exp.dhcpsubnetgrouphost_entity_spec = make_dhcphost_spec('dhcpsubnetgrouphost', 'dhcpsubnetgroup');
        exp.dhcppoolhost_entity_spec = make_dhcphost_spec('dhcppoolhost', 'dhcppool');

//// dhcpserver ///////////////////////////////////////////////////////////////


        var make_dhcpserver_spec = function() {
            return {
                name: 'dhcpserver',
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
        exp.dhcpserver_entity_spec = make_dhcpserver_spec();

//// dhcpfailoverpeer ///////////////////////////////////////////////////////////////


        var make_dhcpfailoverpeer_spec = function() {
            return {
                name: 'dhcpfailoverpeer',
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
        exp.dhcpfailoverpeer_entity_spec = make_dhcpfailoverpeer_spec();


//// exp.register /////////////////////////////////////////////////////////////


        exp.register = function() {
            var v = reg.validator;
            v.register('dhcprange', IPA.dhcprange_validator);
            v.register('dhcprange_subnet', IPA.dhcprange_subnet_validator);

            var e = reg.entity;
            e.register({type: 'dhcpservice', spec: exp.dhcpservice_entity_spec});
            e.register({type: 'dhcpsubnet', spec: exp.dhcpsubnet_entity_spec});
            e.register({type: 'dhcppool', spec: exp.dhcppool_entity_spec});
            e.register({type: 'dhcpgroup', spec: exp.dhcpgroup_entity_spec});
            e.register({type: 'dhcpsubnetgroup', spec: exp.dhcpsubnetgroup_entity_spec});
            e.register({type: 'dhcpgrouproup', spec: exp.dhcpgroupgroup_entity_spec});
            e.register({type: 'dhcpsharednetwork', spec: exp.dhcpsharednetwork_entity_spec});
            e.register({type: 'dhcphost', spec: exp.dhcphost_entity_spec});
            e.register({type: 'dhcpgrouphost', spec: exp.dhcpgrouphost_entity_spec});
            e.register({type: 'dhcpsubnethost', spec: exp.dhcpsubnethost_entity_spec});
            e.register({type: 'dhcpsubnetgrouphost', spec: exp.dhcpsubnetgrouphost_entity_spec});
            e.register({type: 'dhcppoolhost', spec: exp.dhcppoolhost_entity_spec});
            e.register({type: 'dhcpserver', spec: exp.dhcpserver_entity_spec});
            e.register({type: 'dhcpfailoverpeer', spec: exp.dhcpfailoverpeer_entity_spec});
        }


//// menu spec ////////////////////////////////////////////////////////////////


        var make_dhcp_menu_spec = function(menu_name, menu_lable, menu_entity) {
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
        exp.dhcp_v4_menu_spec = make_dhcp_menu_spec('dhcpv4','DHCP IPv4', 'dhcp' );

        exp.add_menu_items = function() {
            network_services_item = menu.query({name: 'network_services'});
            if (network_services_item.length > 0) {
                menu.add_item( exp.dhcp_v4_menu_spec, 'network_services' );
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


        phases.on('customization', exp.customize_host_ui);
        phases.on('registration', exp.register);
        phases.on('profile', exp.add_menu_items, 20);

        return exp;

    }
);
