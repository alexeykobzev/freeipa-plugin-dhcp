# -*- coding: utf-8 -*-

# Copyright © 2016 Jeffery Harrell <jefferyharrell@gmail.com>
# See file 'LICENSE' for use and warranty information.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#### Imports ##################################################################


from ipalib import _, ngettext
from ipalib import api, errors, output, Command
from ipalib.output import Output, Entry, ListOfEntries
from .baseldap import (
    LDAPObject,
    LDAPCreate,
    LDAPUpdate,
    LDAPSearch,
    LDAPDelete,
    LDAPRetrieve)
from ipalib.parameters import *
from ipalib.plugable import Registry
from ipapython.dn import DN
from ipapython.dnsutil import DNSName
from netaddr import *

from ipaserver.plugins.dhcpcommon import *

#### Constants ################################################################

#dhcp_dn = 'cn=dhcp,{0}'.format(api.env.basedn)
dhcp_dn = '{0}'.format(api.env.basedn)
container_dhcp_dn = DN(('cn', 'v4'), 'cn=dhcp')
register = Registry()

dhcp_version = 4
dhcp_set_version( dhcp_version )

#### dhcpservice ##############################################################


@register()
class dhcpservice(LDAPObject):
    object_name = _('DHCP configuration')
    object_name_plural = _('DHCP configuration')
    object_class = ['dhcpservice', 'top']
    default_attributes = ['cn']
    label = _('DHCP Configuration')
    label_singular = _('DHCP Configuration')

    managed_permissions = {
        'System: Read DHCP Configuration': {
            'non_object': True,
            'ipapermlocation': dhcp_dn,
            'ipapermtarget': container_dhcp_dn,
            'ipapermbindruletype': 'anonymous',
            'replaces_global_anonymous_aci': True,
            'ipapermright': {'read', 'search', 'compare'},
            'ipapermtargetfilter': ['(objectclass=dhcpservice)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpOption', 'dhcpPrimaryDN',
                'dhcpSecondaryDN', 'dhcpClassesDN',
                'dhcpComments', 'dhcpServerDN',
                'dhcpFailOverPeerDN', 'dhcpGroupDN',
                'dhcpHostDN', 'dhcpKeyDN',
                'dhcpOptionsDN', 'dhcpServerDN',
                'dhcpSharedNetworkDN', 'dhcpSubnetDN',
                'dhcpZoneDN'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Write DHCP Configuration': {
            'non_object': True,
            'ipapermright': {'write'},
            'ipapermlocation': dhcp_dn,
            'ipapermtarget': container_dhcp_dn,
            'ipapermtargetfilter': ['(objectclass=dhcpservice)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpOption', 'dhcpPrimaryDN',
                'dhcpSecondaryDN', 'dhcpClassesDN',
                'dhcpComments', 'dhcpServerDN',
                'dhcpFailOverPeerDN', 'dhcpGroupDN',
                'dhcpHostDN', 'dhcpKeyDN',
                'dhcpOptionsDN', 'dhcpServerDN',
                'dhcpSharedNetworkDN', 'dhcpSubnetDN',
                'dhcpZoneDN'
            },
            'default_privileges': {'DHCP Administrators'},
        },
    }

    takes_params = (
        DNParam(
            'dhcpprimarydn?',
            cli_name='primarydn',
            label=_('Primary Server'),
            doc=_('Primary server DN.')
        ),
        DNParam(
            'dhcpsecondarydn*',
            cli_name='secondarydn',
            label=_('Secondary Servers'),
            doc=_('Secondary server DN.')
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainname?',
            cli_name='domainname',
            label=_('Domain Name'),
            doc=_('DNS domain name'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainnameservers*',
            cli_name='domainnameservers',
            label=_('Domain Name Servers'),
            doc=_('DNS domain name servers'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainsearch*',
            cli_name='domainsearch',
            label=_('Domain Search'),
            doc=_('DNS domain search'),
            flags=['virtual_attribute']
        ),
    )


    def get_dhcpservice(self, ldap):
        entry = ldap.get_entry(self.get_dn(), None)
        return entry


    def get_dn(self, *keys, **kwargs):
        if not dhcpservice.dhcpservice_exists(self.api.Backend.ldap2):
            raise errors.NotFound(reason=_('DHCP is not configured'))
        return DN(container_dhcp_dn, dhcp_dn)


    @staticmethod
    def dhcpservice_exists(ldap):
        try:
            ldap.get_entry(DN(container_dhcp_dn, dhcp_dn), [])
        except errors.NotFound:
            return False
        return True


    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):
        dhcpStatements = entry_attrs.get('dhcpstatements', [])

        for statement in dhcpStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('domain-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainname'] = v.replace('"', '')
            if option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            if option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')

        return entry_attrs


@register()
class dhcpservice_show(LDAPRetrieve):
    __doc__ = _('Display the DHCP configuration.')


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpservice.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpservice_mod(LDAPUpdate):
    __doc__ = _('Modify the DHCP configuration.')
    msg_summary = _('Modified the DHCP configuration.')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        if 'dhcpstatements' in entry_attrs:
            dhcpStatements = entry_attrs.get('dhcpstatements', [])
        else:
            entry = ldap.get_entry(dn)
            dhcpStatements = entry.get('dhcpstatements', [])

        if 'dhcpoption' in entry_attrs:
            dhcpOptions = entry_attrs.get('dhcpoption', [])
        else:
            entry = ldap.get_entry(dn)
            dhcpOptions = entry.get('dhcpoption', [])

        dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements )
        dhcp_modify_domainserver( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions )
        dhcp_modify_defaultleasetime( dhcp_version, options, dhcpStatements )
        dhcp_modify_maxleasetime( dhcp_version, options, dhcpStatements )

        entry_attrs['dhcpstatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpservice.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


#### dhcpsubnet ###############################################################


@register()
class dhcpsubnet(LDAPObject):
    container_dn = container_dhcp_dn
    object_name = _('DHCP subnet')
    object_name_plural = _('DHCP subnets')
    object_class = ['dhcpsubnet', 'top']
    default_attributes = ['cn']
    label = _('DHCP Subnets')
    label_singular = _('DHCP Subnet')

    search_attributes = [ 'cn' ]

    managed_permissions = {
        'System: Add DHCP Subnets': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcpsubnet)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpNetMask', 'dhcpRange',
                'dhcpPoolDN', 'dhcpGroupDN',
                'dhcpHostDN', 'dhcpClassesDN',
                'dhcpLeasesDN', 'dhcpOptionsDN',
                'dhcpZoneDN', 'dhcpKeyDN',
                'dhcpFailOverPeerDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Subnets': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcpsubnet)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpNetMask', 'dhcpRange',
                'dhcpPoolDN', 'dhcpGroupDN',
                'dhcpHostDN', 'dhcpClassesDN',
                'dhcpLeasesDN', 'dhcpOptionsDN',
                'dhcpZoneDN', 'dhcpKeyDN',
                'dhcpFailOverPeerDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Subnets': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcpsubnet)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpNetMask', 'dhcpRange',
                'dhcpPoolDN', 'dhcpGroupDN',
                'dhcpHostDN', 'dhcpClassesDN',
                'dhcpLeasesDN', 'dhcpOptionsDN',
                'dhcpZoneDN', 'dhcpKeyDN',
                'dhcpFailOverPeerDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption', 'dhcpPermitList'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='subnet',
            label=_('Subnet'),
            doc=_('DHCP subnet.'),
            primary_key = True
        ),
        Int(
            'dhcpnetmask',
            cli_name='netmask',
            label=_('Netmask'),
            doc=_('DHCP netmask.'),
            minvalue=0,
            maxvalue=32,
            default=24
        ),
        Str(
            'dhcprange?',
            cli_name='range',
            label=_('Range'),
            doc=_('DHCP range.')
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcppermitlist*',
            cli_name='dhcppermitlist',
            label=_('DHCP permit list'),
            doc=_('DHCP permit list.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP comments.')
        ),
        Str(
            'router?',
            cli_name='router',
            label=_('Router'),
            doc=_('Router.'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainnameservers*',
            cli_name='domainnameservers',
            label=_('Domain Name Server'),
            doc=_('Domain Name Servers.'),
            flags=['virtual_attribute']
        )
    )


    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('routers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['router'] = v

            elif option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')

        return entry_attrs


@register()
class dhcpsubnet_add(LDAPCreate):
    __doc__ = _('Create a new DHCP subnet.')
    msg_summary = _('Created DHCP subnet "%(value)s"')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        ip = IPNetwork('{0}/{1}'.format(keys[-1], options['dhcpnetmask']))
        dhcpOptions = []
        dhcpOptions.append('subnet-mask {0}'.format(ip.netmask))
        dhcpOptions.append('broadcast-address {0}'.format(ip.broadcast))
        entry_attrs['dhcpoption'] = dhcpOptions
        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        return dn


@register()
class dhcpsubnet_add_cidr(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new DHCP subnet by network address in CIDR format.')
    msg_summary = _('Created DHCP subnet "%(value)s"')

    takes_args = (
        Str(
            'networkaddr',
            cli_name='networkaddr',
            label=_('Network Address'),
            doc=_("Network address in CIDR notation.")
        ),
        Str(
            'dhcprange?',
            cli_name='range',
            label=_('Range'),
            doc=_('DHCP range.')
        )
    )

    def execute(self, *args, **kw):
        ip = IPNetwork(args[0])
        cn = unicode(ip.network)
        dhcpnetmask = ip.prefixlen
        if len(args) > 1:
          dhcprange = args[1]
          result = api.Command['dhcpsubnet_add'](cn, dhcpnetmask=dhcpnetmask, dhcprange=dhcprange)
        else:
          result = api.Command['dhcpsubnet_add'](cn, dhcpnetmask=dhcpnetmask)
        return dict(result=result['result'], value=cn)


@register()
class dhcpsubnet_find(LDAPSearch):
    __doc__ = _('Search for a DHCP subnet.')
    msg_summary = ngettext(
        '%(count)d DHCP subnet matched',
        '%(count)d DHCP subnets matched', 0
    )


@register()
class dhcpsubnet_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP subnet.')


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpsubnet.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpsubnet_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP subnet.')
    msg_summary = _('Modified a DHCP subnet.')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        entry = ldap.get_entry(dn)

        if 'dhcpstatements' in entry_attrs:
            dhcpStatements = entry_attrs.get('dhcpstatements', [])
        else:
            dhcpStatements = entry.get('dhcpstatements', [])

        if 'dhcpoption' in entry_attrs:
            dhcpOptions = entry_attrs.get('dhcpoption', [])
        else:
            dhcpOptions = entry.get('dhcpoption', [])

        if 'router' in options:
            option = 'routers {0}'.format(options['router'])
            foundOption = False
            for i, s in enumerate(dhcpOptions):
                if s.startswith('routers '):
                    foundOption = True
                    dhcpOptions[i] = option
                    break
            if not foundOption:
                dhcpOptions.append(option)

        dhcp_modify_router( dhcp_version, options, dhcpOptions )      
        dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements )
        dhcp_modify_domainserver( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions )

        entry_attrs['dhcpstatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpsubnet.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpsubnet_del(LDAPDelete):
    __doc__ = _('Delete a DHCP subnet.')
    msg_summary = _('Deleted DHCP subnet "%(value)s"')


#### dhcpfailoverpeer ###############################################################

@register()
class dhcpfailoverpeer(LDAPObject):
    container_dn = container_dhcp_dn
    object_name = _('DHCP Fail Over Peer')
    object_name_plural = _('DHCP Fail Over Peers')
    object_class = ['dhcpFailOverPeer', 'top']
    default_attributes = ['cn', 
                         'dhcpFailOverPrimaryServer', 
                         'dhcpFailOverSecondaryServer',
                         'dhcpFailOverPrimaryPort',
                         'dhcpFailOvreSecondaryPort']
    #uuid_attribute
    #rdn_attribute
    #attributer_members
    label = _('DHCP Fail Over Peers')
    label_singular = _('DHCP Fail Over Peer')

    managed_permissions = {
        'System: Add DHCP Fail Over': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcpFailOverPeer)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpFailOverPrimaryServer', 'dhcpFailOverSecondaryServer',
                'dhcpFailoverPrimaryPort', 'dhcpFailOverSecondaryPort',
                'dhcpFailOverResponseDelay', 'dhcpFailOverUnackedUpdates',
                'dhcpMaxClientLeadTime', 'dhcpFailOverSplit',
                'dhcpHashBucketAssignment', 'dhcpFailOverLoadBalanceTime',
                'dhcpComments'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Fail Over': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcpFailOverPeer)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpFailOverPrimaryServer', 'dhcpFailOverSecondaryServer',
                'dhcpFailoverPrimaryPort', 'dhcpFailOverSecondaryPort',
                'dhcpFailOverResponseDelay', 'dhcpFailOverUnackedUpdates',
                'dhcpMaxClientLeadTime', 'dhcpFailOverSplit',
                'dhcpHashBucketAssignment', 'dhcpFailOverLoadBalanceTime',
                'dhcpComments'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Fail Over': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcpFailOverPeer)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpFailOverPrimaryServer', 'dhcpFailOverSecondaryServer',
                'dhcpFailoverPrimaryPort', 'dhcpFailOverSecondaryPort',
                'dhcpFailOverResponseDelay', 'dhcpFailOverUnackedUpdates',
                'dhcpMaxClientLeadTime', 'dhcpFailOverSplit',
                'dhcpHashBucketAssignment', 'dhcpFailOverLoadBalanceTime',
                'dhcpComments'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='fail_over_peer_name',
            label=_('DHCP Fail Over Peer Name'),
            primary_key=True,
        ),
        Str(
            'dhcpfailoverprimaryserver',
            cli_name='fail_over_primary_server',
            label=_('DHCP Fail Over Primary Server'),
        ),
        Str(
            'dhcpfailoversecondaryserver',
            cli_name='fail_over_secondary_server',
            label=_('DHCP Fail Over Secondary Server'),
        ),
        Str(
            'dhcpfailoverprimaryport',
            cli_name='fail_over_primary_port',
            label=_('DHCP Fail Over Primary Port'),
        ),
        Str(
            'dhcpfailoversecondaryport',
            cli_name='fail_over_secondary_port',
            label=_('DHCP Fail Over Secondary Port'),
        ),
        Str(
            'dhcpfailoverresponsedelay?',
            cli_name='fail_over_response_delay',
            label=_('DHCP Fail Over Response Delay'),
        ),
        Str(
            'dhcpfailoverunackedupdates?',
            cli_name='fail_over_unacked_updates',
            label=_('DHCP Fail Over Unacked Updates'),
        ),
        Str(
            'dhcpmaxclientleadtime?',
            cli_name='fail_over_max_client_lead_time',
            label=_('DHCP Fail Over Max Client Lead Time'),
        ),
        Str(
            'dhcpfailoversplit?',
            cli_name='fail_over_split',
            label=_('DHCP Fail Over Split'),
        ),
        Str(
            'dhcphashbucketassignment?',
            cli_name='fail_over_hash_bucket_assignment',
            label=_('DHCP Fail Over Hash Bucket Assignment'),
        ),
        Str(
            'dhcpfailoverloadbalancetime?',
            cli_name='fail_over_load_balance_time',
            label=_('DHCP Fail Over Load Balance Time'),
        ),
        Str(
            'dhcpcomments?',
            cli_name='fail_over_comments',
            label=_('DHCP Fail Over Comments'),
        ),

    )

@register()
class dhcpfailoverpeer_add(LDAPCreate):
    __doc__ = _('Create a new DHCP fail over peer.')
    msg_summary = _('Created DHCP fail over peer "%(value)s"')

@register()
class dhcpfailoverpeer_find(LDAPSearch):
    __doc__ = _('Search for a DHCP fail over peer.')
    msg_summary = ngettext(
        '%(count)d DHCP fail over peer matched',
        '%(count)d DHCP fail over peers matched', 0
    )


@register()
class dhcpfailoverpeer_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP fail over peer.')


@register()
class dhcpfailoverpeer_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP fail over peer.')
    msg_summary = _('Modified a DHCP fail over peer.')


@register()
class dhcpfailoverpeer_del(LDAPDelete):
    __doc__ = _('Delete a DHCP fail over peer.')
    msg_summary = _('Deleted DHCP fail over peer "%(value)s"')


#### dhcpsharednetwork ###############################################################

@register()
class dhcpsharednetwork(LDAPObject):
    container_dn = container_dhcp_dn
    object_name = _('DHCP Shared Network')
    object_name_plural = _('DHCP Shared Networks')
    object_class = ['dhcpSharedNetwork', 'top']
    default_attributes = ['cn']
    #uuid_attribute
    #rdn_attribute
    #attributer_members
    label = _('DHCP Shared Networks')
    label_singular = _('DHCP Shared Network')

    managed_permissions = {
        'System: Add DHCP Shared Networks': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcpSharedNetwork)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpSubnetDN', 'dhcpPoolDN',
                'dhcpOptionsDN', 'dhcpZoneDN', 
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Shared Networks': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcpSharedNetwork)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpSubnetDN', 'dhcpPoolDN',
                'dhcpOptionsDN', 'dhcpZoneDN', 
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Shared Networks': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcpSharedNetwork)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpSubnetDN', 'dhcpPoolDN',
                'dhcpOptionsDN', 'dhcpZoneDN', 
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='shared_network_name',
            label=_('DHCP Shared Network Name'),
            primary_key=True,
        ),
        Str(
            'dhcpsubnetdn',
            cli_name='shared_network_subnet_dn',
            label=_('DHCP Shared Network Subnet DN'),
        ),
        Str(
            'dhcppooldn',
            cli_name='shared_network_pool_dn',
            label=_('DHCP Shared Network Pool DN'),
        ),
        Str(
            'dhcpoptionsdn',
            cli_name='shared_network_options_dn',
            label=_('DHCP Shared Network Options DN'),
        ),
        Str(
            'dhcpzonedn',
            cli_name='shared_network_zone_dn',
            label=_('DHCP Shared Network Zone DN'),
        ),
        Str(
            'dhcpstatements',
            cli_name='shared_network_statements',
            label=_('DHCP Shared Network Statements'),
        ),
        Str(
            'dhcpcomments',
            cli_name='shared_network_comments',
            label=_('DHCP Shared Network Comments'),
        ),
        Str(
            'dhcpoption',
            cli_name='shared_network_option',
            label=_('DHCP Shared Network Option'),
        ),

    )

@register()
class dhcpsharednetwork_add(LDAPCreate):
    __doc__ = _('Create a new DHCP shared network.')
    msg_summary = _('Created DHCP shared network "%(value)s"')

@register()
class dhcpsharednetwork_find(LDAPSearch):
    __doc__ = _('Search for a DHCP shared network.')
    msg_summary = ngettext(
        '%(count)d DHCP shared network matched',
        '%(count)d DHCP shared networks matched', 0
    )


@register()
class dhcpsharednetwork_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP shared network.')


@register()
class dhcpsharednetwork_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP shared network.')
    msg_summary = _('Modified a DHCP shared network.')


@register()
class dhcpsharednetwork_del(LDAPDelete):
    __doc__ = _('Delete a DHCP shared network.')
    msg_summary = _('Deleted DHCP shared network "%(value)s"')


#### dhcppool #################################################################


@register()
class dhcppool(LDAPObject):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcp_dn
    object_name = _('DHCP pool')
    object_name_plural = _('DHCP pools')
    object_class = ['dhcppool', 'top']
    default_attributes = ['cn']
    label = _('DHCP Pools')
    label_singular = _('DHCP Pool')

    search_attributes = [ 'cn', 'dhcprange' ]

    managed_permissions = {
        'System: Add DHCP Pools': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcppool)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpRange', 'dhcpClassesDN',
                'dhcpPermitList', 'dhcpLeasesDN',
                'dhcpOptionsDN', 'dhcpZoneDN',
                'dhcpKeyDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Pools': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcppool)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpRange', 'dhcpClassesDN',
                'dhcpPermitList', 'dhcpLeasesDN',
                'dhcpOptionsDN', 'dhcpZoneDN',
                'dhcpKeyDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Pools': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcppool)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpRange', 'dhcpClassesDN',
                'dhcpPermitList', 'dhcpLeasesDN',
                'dhcpOptionsDN', 'dhcpZoneDN',
                'dhcpKeyDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='name',
            label=_('Name'),
            doc=_('DHCP pool name.'),
            primary_key=True
        ),
        Str(
            'dhcprange',
            cli_name='range',
            label=_('Range'),
            doc=_('DHCP range.')
        ),
        Str(
            'dhcppermitlist*',
            cli_name='permitlist',
            label=_('Permit List'),
            doc=_('DHCP permit list.')
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitknownclients?',
            cli_name='permitknownclients',
            label=_('Permit Known Clients'),
            doc=_('Permit known clients.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitunknownclients?',
            cli_name='permitunknownclients',
            label=_('Permit Unknown Clients'),
            doc=_('Permit unknown clients.'),
            flags=['virtual_attribute']
        ),
    )


    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        dhcpPermitList = entry_attrs.get('dhcppermitlist', [])

        for item in dhcpPermitList:
            if item.endswith(' known-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitknownclients'] = False
            if item.endswith(' unknown-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitunknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitunknownclients'] = False

        dhcpStatements = entry_attrs.get('dhcpstatements', [])

        for statement in dhcpStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('domain-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainname'] = v.replace('"', '')
            if option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            if option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')

        return entry_attrs


@register()
class dhcppool_add(LDAPCreate):
    __doc__ = _('Create a new DHCP pool.')
    msg_summary = _('Created DHCP pool "%(value)s"')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        # Allow known and unknown clients by default.

        entry_attrs['dhcppermitlist'] = ['allow unknown-clients', 'allow known-clients']

        # If the dhcpService entry has dhcpstatements attributes that start with
        # "default-lease-time" or "max-lease-time", grab them and copy their
        # values into the new pool. This code could probably be a lot more
        # efficient, but it works. The blame REALLY lies with the author of the
        # DHCP LDAP schema for being so lazy.

        hasDefaultLeaseTime = False
        hasMaxLeaseTime = False

        if 'dhcpstatements' in entry_attrs:
            for statement in entry_attrs['dhcpstatements']:
                if statement.startswith('default-lease-time'):
                    hasDefaultLeaseTime = True
                if statement.startswith('max-lease-time'):
                    hasMaxLeaseTime = True

        if hasDefaultLeaseTime and hasMaxLeaseTime:
            return dn

        config = ldap.get_entry(DN(container_dhcp_dn, dhcp_dn))

        if 'dhcpStatements' in config:
            configDHCPStatements = config['dhcpStatements']
        else:
            configDHCPStatements = []

        defaultLeaseTime = None
        maxLeaseTime = None

        for statement in configDHCPStatements:
            if statement.startswith('default-lease-time'):
                (s, v) = statement.split(" ")
                defaultLeaseTime = v
            if statement.startswith('max-lease-time'):
                (s, v) = statement.split(" ")
                maxLeaseTime = v

        if 'dhcpstatements' in entry_attrs:
            entryDHCPStatements = entry_attrs['dhcpstatements']
        else:
            entryDHCPStatements = []

        if defaultLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryDHCPStatements):
                if s.startswith('default-lease-time'):
                    foundStatement = True
                    entryDHCPStatements[i] = 'default-lease-time {0}'.format(defaultLeaseTime)
                    break
            if foundStatement is False:
                entryDHCPStatements.append('default-lease-time {0}'.format(defaultLeaseTime))

        if maxLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryDHCPStatements):
                if s.startswith('max-lease-time'):
                    foundStatement = True
                    entryDHCPStatements[i] = 'max-lease-time {0}'.format(maxLeaseTime)
                    break
            if foundStatement is False:
                entryDHCPStatements.append('max-lease-time {0}'.format(maxLeaseTime))

        entry_attrs['dhcpstatements'] = entryDHCPStatements

        return dn


@register()
class dhcppool_find(LDAPSearch):
    __doc__ = _('Search for a DHCP pool.')
    msg_summary = ngettext(
        '%(count)d DHCP pool matched',
        '%(count)d DHCP pools matched', 0
    )


@register()
class dhcppool_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP pool.')


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcppool.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcppool_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP pool.')
    msg_summary = _('Modified a DHCP pool.')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        entry = ldap.get_entry(dn)


        if 'dhcppermitlist' in entry_attrs:
            dhcpPermitList = entry_attrs.get('dhcppermitlist', [])
        else:
            dhcpPermitList = entry.get('dhcppermitlist', [])

        dhcpPermitList = dhcp_modify_permitknownclients( dhcp_version, options, dhcpPermitList )
        dhcpPermitList = dhcp_modify_permitunknownclients( dhcp_version, options, dhcpPermitList )
        
        entry_attrs['dhcppermitlist'] = dhcpPermitList

        if 'dhcpstatements' in entry_attrs:
            dhcpStatements = entry_attrs.get('dhcpstatements', [])
        else:
            dhcpStatements = entry.get('dhcpstatements', [])

        if 'dhcpoption' in entry_attrs:
            dhcpOptions = entry_attrs.get('dhcpoption', [])
        else:
            dhcpOptions = entry.get('dhcpoption', [])

        dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements )
        dhcp_modify_domainserver( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions )
        dhcp_modify_defaultleasetime( dhcp_version, options, dhcpStatements )
        dhcp_modify_maxleasetime( dhcp_version, options, dhcpStatements )


        entry_attrs['dhcpstatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcppool.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcppool_del(LDAPDelete):
    __doc__ = _('Delete a DHCP pool.')
    msg_summary = _('Deleted DHCP pool "%(value)s"')


@register()
class dhcppool_is_valid(Command):
    NO_CLI = True
    has_output = output.standard_boolean
    msg_summary = _('"%(value)s"')

    takes_args = (
        Str(
            'dhcpsubnetcn',
            cli_name='subnet',
            label=_('Subnet'),
            doc=_('DHCP subnet.')
        ),
        Str(
            'dhcprange+',
            cli_name='range',
            label=_('Range'),
            doc=_('DHCP range.')
        )
    )

    def execute(self, *args, **kw):

        # Run some basic sanity checks on a DHCP pool IP range to make sure it
        # fits into its parent DHCP subnet. This method looks up the parent
        # subnet given the necessary LDAP keys because that's what works best
        # with the GUI.

        dhcpsubnetcn = args[0]
        dhcprange = args[1][0]

        ldap = self.api.Backend.ldap2
        dn = DN(
            ('cn', dhcpsubnetcn),
            container_dhcp_dn,
            dhcp_dn
        )
        try:
            entry = ldap.get_entry(dn)
        except:
            return dict(result=False, value=u'No such subnet.')

        subnetIP = IPNetwork("{0}/{1}".format(entry['cn'][0], int(entry['dhcpNetMask'][0])))

        (rangeStart, rangeEnd) = dhcprange.split(" ")
        rangeStartIP = IPNetwork("{0}/32".format(rangeStart))
        rangeEndIP = IPNetwork("{0}/32".format(rangeEnd))

        if rangeStartIP > rangeEndIP:
            return dict(result=False, value=u'First IP must come before last IP!')

        if rangeStartIP < subnetIP[0] or rangeStartIP > subnetIP[-1]:
            return dict(result=False, value=u'{0} is outside parent subnet {1}. Addresses in this pool must come from the range {2}-{3}.'.format(rangeStartIP.ip, subnetIP.cidr, subnetIP[0], subnetIP[-1]))

        if rangeEndIP < subnetIP[0] or rangeEndIP > subnetIP[-1]:
            return dict(result=False, value=u'{0} is outside parent subnet {1}. Addresses in this pool must come from the range {2}-{3}.'.format(rangeEndIP.ip, subnetIP.cidr, subnetIP[0], subnetIP[-1]))

        return dict(result=True, value=u'Valid IP range.')


#### dhcpgroup #################################################################


@register()
class dhcpgroup(LDAPObject):
    container_dn = container_dhcp_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

    search_attributes = [ 'cn', 'dhcprange' ]

    managed_permissions = {
        'System: Add DHCP Groups': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcpgroup)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpHostDN', 'dhcpOptionsDN',
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Groups': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcpgroup)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpHostDN', 'dhcpOptionsDN',
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Groups': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcpgroup)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpHostDN', 'dhcpOptionsDN',
                'dhcpStatements', 'dhcpComments',
                'dhcpOption'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='name',
            label=_('Name'),
            doc=_('DHCP group name.'),
            primary_key=True
        ),
        Str(
            'dhcprange?',
            cli_name='range',
            label=_('Range'),
            doc=_('DHCP range.')
        ),
        Str(
            'dhcppermitlist*',
            cli_name='permitlist',
            label=_('Permit List'),
            doc=_('DHCP permit list.')
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitknownclients?',
            cli_name='permitknownclients',
            label=_('Permit Known Clients'),
            doc=_('Permit known clients.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitunknownclients?',
            cli_name='permitunknownclients',
            label=_('Permit Unknown Clients'),
            doc=_('Permit unknown clients.'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainname?',
            cli_name='domainname',
            label=_('Domain Name'),
            doc=_('DNS domain name'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainnameservers*',
            cli_name='domainnameservers',
            label=_('Domain Name Servers'),
            doc=_('DNS domain name servers'),
            flags=['virtual_attribute']
        ),
        Str(
            'domainsearch*',
            cli_name='domainsearch',
            label=_('Domain Search'),
            doc=_('DNS domain search'),
            flags=['virtual_attribute']
        ),
        Str(
            'router?',
            cli_name='router',
            label=_('Router'),
            doc=_('Router.'),
            flags=['virtual_attribute']
        )

    )


    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        dhcpPermitList = entry_attrs.get('dhcppermitlist', [])

        for item in dhcpPermitList:
            if item.endswith(' known-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitknownclients'] = False
            if item.endswith(' unknown-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitunknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitunknownclients'] = False

        dhcpStatements = entry_attrs.get('dhcpstatements', [])

        for statement in dhcpStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('domain-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainname'] = v.replace('"', '')
            if option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            if option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')
            if option.startswith('routers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['router'] = v

        return entry_attrs


@register()
class dhcpgroup_add(LDAPCreate):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        # Allow known and unknown clients by default.

        entry_attrs['dhcppermitlist'] = ['allow unknown-clients', 'allow known-clients']

        # If the dhcpService entry has dhcpstatements attributes that start with
        # "default-lease-time" or "max-lease-time", grab them and copy their
        # values into the new group. This code could probably be a lot more
        # efficient, but it works. The blame REALLY lies with the author of the
        # DHCP LDAP schema for being so lazy.

        hasDefaultLeaseTime = False
        hasMaxLeaseTime = False

        if 'dhcpstatements' in entry_attrs:
            for statement in entry_attrs['dhcpstatements']:
                if statement.startswith('default-lease-time'):
                    hasDefaultLeaseTime = True
                if statement.startswith('max-lease-time'):
                    hasMaxLeaseTime = True

        if hasDefaultLeaseTime and hasMaxLeaseTime:
            return dn

        config = ldap.get_entry(DN(container_dhcp_dn, dhcp_dn))

        if 'dhcpStatements' in config:
            configDHCPStatements = config['dhcpStatements']
        else:
            configDHCPStatements = []

        defaultLeaseTime = None
        maxLeaseTime = None

        for statement in configDHCPStatements:
            if statement.startswith('default-lease-time'):
                (s, v) = statement.split(" ")
                defaultLeaseTime = v
            if statement.startswith('max-lease-time'):
                (s, v) = statement.split(" ")
                maxLeaseTime = v

        if 'dhcpstatements' in entry_attrs:
            entryDHCPStatements = entry_attrs['dhcpstatements']
        else:
            entryDHCPStatements = []

        if defaultLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryDHCPStatements):
                if s.startswith('default-lease-time'):
                    foundStatement = True
                    entryDHCPStatements[i] = 'default-lease-time {0}'.format(defaultLeaseTime)
                    break
            if foundStatement is False:
                entryDHCPStatements.append('default-lease-time {0}'.format(defaultLeaseTime))

        if maxLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryDHCPStatements):
                if s.startswith('max-lease-time'):
                    foundStatement = True
                    entryDHCPStatements[i] = 'max-lease-time {0}'.format(maxLeaseTime)
                    break
            if foundStatement is False:
                entryDHCPStatements.append('max-lease-time {0}'.format(maxLeaseTime))

        entry_attrs['dhcpstatements'] = entryDHCPStatements


        if 'dhcpoption' in entry_attrs:
            dhcpOptions = entry_attrs.get('dhcpoption', [])
        else:
            dhcpOptions = []

        if 'domainname' in options:
            option = 'domain-name "{0}"'.format(options['domainname'])
            foundOption = False
            for i, s in enumerate(dhcpOptions):
                if s.startswith('domain-name '):
                    foundOption = True
                    dhcpOptions[i] = option
                    break
            if not foundOption:
                dhcpOptions.append(option)
                
        if 'domainsearch' in options:
            option = 'domain-search ' + ', '.join('"' + s + '"' for s in options['domainsearch'])
            foundOption = False
            for i, s in enumerate(dhcpOptions):
                if s.startswith('domain-search '):
                    foundOption = True
                    dhcpOptions[i] = option
                    break
            if not foundOption:
                dhcpOptions.append(option)

        if 'router' in options:
            option = 'routers {0}'.format(options['router'])
            foundOption = False
            for i, s in enumerate(dhcpOptions):
                if s.startswith('routers '):
                    foundOption = True
                    dhcpOptions[i] = option
                    break
            if not foundOption:
                dhcpOptions.append(option)
                
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


@register()
class dhcpgroup_find(LDAPSearch):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )


@register()
class dhcpgroup_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP group.')


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpgroup.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpgroup_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        entry = ldap.get_entry(dn)

        if 'dhcppermitlist' in entry_attrs:
            dhcpPermitList = entry_attrs.get('dhcppermitlist', [])
        else:
            dhcpPermitList = entry.get('dhcppermitlist', [])
        
        dhcp_modify_permitknownclients( dhcp_version, options, dhcpPermitList )
        dhcp_modify_permitunknownclients( dhcp_version, options, dhcpPermitList )
        entry_attrs['dhcppermitlist'] = dhcpPermitList

        if 'dhcpstatements' in entry_attrs:
            dhcpStatements = entry_attrs.get('dhcpstatements', [])
        else:
            dhcpStatements = entry.get('dhcpstatements', [])

        if 'dhcpoption' in entry_attrs:
            dhcpOptions = entry_attrs.get('dhcpoption', [])
        else:
            dhcpOptions = entry.get('dhcpoption', [])

        dhcp_modify_router( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements )
        dhcp_modify_domainserver( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions )
        dhcp_modify_defaultleasetime( dhcp_version, options, dhcpStatements )
        dhcp_modify_maxleasetime( dhcp_version, options, dhcpStatements )

        entry_attrs['dhcpStatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpgroup.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpgroup_del(LDAPDelete):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpsubnetgroup #################################################################

@register()
class dhcpsubnetgroup(dhcpgroup):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcp_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpsubnetgroup_find(dhcpgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpsubnetgroup_show(dhcpgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpsubnetgroup_add(dhcpgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpsubnetgroup_mod(dhcpgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpsubnetgroup_del(dhcpgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpgroupgroup #################################################################

@register()
class dhcpgroupgroup(dhcpgroup):
    parent_object = 'dhcpgroup'
    container_dn = container_dhcp_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpgroupgroup_find(dhcpgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpgroupgroup_show(dhcpgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpgroupgroup_add(dhcpgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpgroupgroup_mod(dhcpgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpgroupgroup_del(dhcpgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcppoolgroup #################################################################

@register()
class dhcppoolgroup(dhcpgroup):
    parent_object = 'dhcppool'
    container_dn = container_dhcp_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcppoolgroup_find(dhcpgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcppoolgroup_show(dhcpgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcppoolgroup_add(dhcpgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcppoolgroup_mod(dhcpgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcppoolgroup_del(dhcpgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpserver ###############################################################


@register()
class dhcpserver(LDAPObject):
    container_dn = container_dhcp_dn
    object_name = _('DHCP server')
    object_name_plural = _('DHCP servers')
    object_class = ['dhcpserver', 'top']
    default_attributes = ['cn']
    label = _('DHCP Servers')
    label_singular = _('DHCP Server')

    search_attributes = [ 'cn', 'dhcpservicedn' ]

    managed_permissions = {
        'System: Add DHCP Servers': {
            'ipapermright': {'add'},
            'ipapermdefaultattr': { 'cn' },
            'ipapermtargetfilter': ['(objectclass=dhcpserver)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpServiceDN', 'dhcpComments',
                'dhcpDelayedServiceParameter', 'dhcpFailOverEndpointState',
                'dhcpHashBucketAssignment', 'dhcpImplementation',
                'dhcpLocatorDN', 'dhcpMaxClientLeadTime',
                'dhcpOption', 'dhcpStatements',
                'dhcpVersion'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Modify DHCP Servers': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcpserver)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpServiceDN', 'dhcpComments',
                'dhcpDelayedServiceParameter', 'dhcpFailOverEndpointState',
                'dhcpHashBucketAssignment', 'dhcpImplementation',
                'dhcpLocatorDN', 'dhcpMaxClientLeadTime',
                'dhcpOption', 'dhcpStatements',
                'dhcpVersion'
            },
            'default_privileges': {'DHCP Administrators'},
        },
        'System: Remove DHCP Servers': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcpserver)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpServiceDN', 'dhcpComments',
                'dhcpDelayedServiceParameter', 'dhcpFailOverEndpointState',
                'dhcpHashBucketAssignment', 'dhcpImplementation',
                'dhcpLocatorDN', 'dhcpMaxClientLeadTime',
                'dhcpOption', 'dhcpStatements',
                'dhcpVersion'
            },
            'default_privileges': {'DHCP Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='hostname',
            label=_('Hostname'),
            doc=_('Hostname.'),
            primary_key=True
        ),
        DNParam(
            'dhcpservicedn',
            cli_name='dhcpservicedn',
            label=_('Service Instance'),
            doc=_('DHCP service instance DN'),
            default_from=lambda: DN(container_dhcp_dn, dhcp_dn),
            autofill=True
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP comments.')
        ),
        Str('dhcplocatordn?',
            cli_name='server_locator_dn',
            label=_('DHCP Server Locator DN'),
            default_from=lambda: DN(container_dhcp_dn, dhcp_dn),
        ),
        Str('dhcpversion?',
            cli_name='server_version',
            label=_('DHCP Server Version'),
        ),
        Str('dhcpimplementation?',
            cli_name='server_implementation',
            label=_('DHCP Server implementation'),
        ),
        Str('dhcphashbucketassignment?',
            cli_name='server_hash_bucket_assignment',
            label=_('DHCP Server Hash bucket assignment'),
        ),
        Str('dhcpdelayedserviceparameter?',
            cli_name='server_delayed_service_parameter',
            label=_('DHCP Server Delayed Service Parameter'),
        ),
        Str('dhcpmaxclientleadtime?',
            cli_name='server_max_client_lead_time',
            label=_('DHCP Server Max Client Lead Time'),
        ),
        Str('dhcpfailoverendpointstate?',
            cli_name='server_fail_over_endpoint_state',
            label=_('DHCP Server Fail Over Endpoint State'),
        )
    )


@register()
class dhcpserver_add(LDAPCreate):
    __doc__ = _('Create a new DHCP server.')
    msg_summary = _('Created DHCP server "%(value)s"')


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)

        dhcpservice = ldap.get_entry(DN(container_dhcp_dn, dhcp_dn))
        dhcpsecondarydns = dhcpservice.get('dhcpsecondarydn', [])

        if dn not in dhcpsecondarydns:
            dhcpsecondarydns.append(dn)

        dhcpservice['dhcpsecondarydn'] = dhcpsecondarydns

        try:
            ldap.update_entry(dhcpservice)
        except errors.EmptyModlist:
            pass

        return dn


@register()
class dhcpserver_find(LDAPSearch):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )


@register()
class dhcpserver_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP server.')


@register()
class dhcpserver_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP server.')
    msg_summary = _('Modified a DHCP server.')


@register()
class dhcpserver_del(LDAPDelete):
    __doc__ = _('Delete a DHCP server.')
    msg_summary = _('Deleted DHCP server "%(value)s"')


    def pre_callback(self, ldap, dn, *keys, **options):
        assert isinstance(dn, DN)

        dhcpservice = ldap.get_entry(DN(container_dhcp_dn, dhcp_dn))
        dhcpsecondarydns = dhcpservice.get('dhcpsecondarydn', [])

        try:
            dhcpsecondarydns.remove(dn)
        except AttributeError as ValueError:
            pass

        dhcpservice['dhcpsecondarydn'] = dhcpsecondarydns

        try:
            ldap.update_entry(dhcpservice)
        except errors.EmptyModlist:
            pass

        return dn

#### dhcphost ###############################################################

@register()
class dhcphost(LDAPObject):
#    parent_object = 'dhcpgroup'
    container_dn = container_dhcp_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

    managed_permissions = {
        'System: Add DHCP Hosts': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=dhcphost)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpComments', 'dhcpHWAddress',
                'dhcpOptionsDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption',
                'dhcpClientId'
            },
            'default_privileges': {'DHCP Administrators', 'Host Administrators'},
        },
        'System: Modify DHCP Hosts': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=dhcphost)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpComments', 'dhcpHWAddress',
                'dhcpOptionsDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption',
                'dhcpClientId'
            },
            'default_privileges': {'DHCP Administrators', 'Host Administrators'},
        },
        'System: Remove DHCP Hosts': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=dhcphost)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'dhcpComments', 'dhcpHWAddress',
                'dhcpOptionsDN', 'dhcpStatements',
                'dhcpComments', 'dhcpOption',
                'dhcpClientId'
            },
            'default_privileges': {'DHCP Administrators', 'Host Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn?',
            cli_name='cn',
            label=_('Canonical Name'),
            doc=_('Canonical name.'),
            primary_key=True
        ),
        Str(
            'fqdn',
            cli_name='fqdn',
            label=_('Host Name'),
            doc=_('Host name.'),
            flags=['virtual_attribute']
        ),
        Str('macaddress*',
            normalizer=lambda value: value.upper(),
            pattern='^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$',
            pattern_errmsg=('Must be of the form HH:HH:HH:HH:HH:HH, where '
                            'each H is a hexadecimal character.'),
            label=_('MAC address'),
            doc=_('Hardware MAC address(es) on this host'),
            flags=['virtual_attribute']
        ),
        Str(
            'ipaddress?',
            cli_name='ipaddress',
            label=_('Host IP Address'),
            doc=_('Host IP Address.'),
            flags=['virtual_attribute']
        ),
        Str(
            'hostname?',
            cli_name='hostname',
            label=_('Host name'),
            doc=_('Host name.'),
            flags=['virtual_attribute']
        ),
        Str(
            'dhcpclientid?',
            cli_name='dhcpclientid',
            label=_('Client Identifier'),
            doc=_('Client Identifier.')
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP Statements'),
            doc=_('DHCP statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP Options'),
            doc=_('DHCP options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP Comments.')
        ),
    )

    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        dhcpStatements = entry_attrs.get('dhcpstatements', [])

        for statements in dhcpStatements:
            if statements.startswith('fixed-address '):
                (o, v) = statements.split(' ', 1)
                entry_attrs['ipaddress'] = v
            elif statements.startswith('ddns-hostname '):
                (o, v) = statements.split(' ', 1)
                entry_attrs['hostname'] = v.replace('"', '')

        dhcpHWaddress = entry_attrs.get('dhcphwaddress', [])

        for hwaddress in dhcpHWaddress:
            if hwaddress.startswith('ethernet '):
                (o, v) = hwaddress.split(' ', 1)
                entry_attrs['macaddress'] = v.replace('"', '')

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('host-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['hostname'] = v.replace('"', '')

        return entry_attrs


@register()
class dhcphost_add_dhcpschema(LDAPCreate):
    NO_CLI = True
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcphost_find(LDAPSearch):
    __doc__ = _('Search for a DHCP host.')
    msg_summary = ngettext(
        '%(count)d DHCP host matched',
        '%(count)d DHCP hosts matched', 0
    )


@register()
class dhcphost_show(LDAPRetrieve):
    __doc__ = _('Display a DHCP host.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcphost.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn
    
@register()
class dhcphost_del_dhcpschema(LDAPDelete):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


@register()
class dhcphost_mod(LDAPUpdate):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcphost.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcphost_add(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')

    takes_args = (
        Str(
            'hostname',
            cli_name='hostname',
            label=_('Hostname'),
            doc=_("Hostname.")
        ),
        Str(
            'macaddress',
            normalizer=lambda value: value.upper(),
            pattern='^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$',
            pattern_errmsg=('Must be of the form HH:HH:HH:HH:HH:HH, where '
                            'each H is a hexadecimal character.'),
            cli_name='macaddress',
            label=_('MAC Address'),
            doc=_("MAC address.")
        ),
        Str(
            'ipaddress?',
            cli_name='ipaddress',
            label=_('IP Address'),
            doc=_("Host IP Address.")
        )
    )

    def execute(self, *args, **kw):
        hostname = args[0]
        macaddress = args[1]
        # if ipaddress is present
        dhcpstatements = [u'ddnshostname "{0}"'.format(hostname)]
        if (len(args) > 2):
            dhcpstatements = [u'fixed-address {0}'.format(args[2]), u'ddnshostname "{0}"'.format(hostname)]            
        cn = u'{hostname}-{macaddress}'.format(
            hostname=hostname,
            macaddress=macaddress.replace(':', '')
        )
        result = api.Command['dhcphost_add_dhcpschema'](
            cn,
            dhcpstatements,
            dhcphwaddress=u'ethernet {0}'.format(macaddress),
            dhcpoption=[u'host-name "{0}"'.format(hostname)]
        )
        return dict(result=result['result'], value=cn)

@register()
class dhcphost_del(Command):
    has_output = output.standard_entry
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')

    takes_args = (
        Str(
            'hostname',
            cli_name='hostname',
            label=_('Hostname'),
            doc=_("Hostname.")
        ),
        Str(
            'macaddress',
            normalizer=lambda value: value.upper(),
            pattern='^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$',
            pattern_errmsg=('Must be of the form HH:HH:HH:HH:HH:HH, where '
                            'each H is a hexadecimal character.'),
            cli_name='macaddress',
            label=_('MAC Address'),
            doc=_("MAC address.")
        )
    )

    def execute(self, *args, **kw):
        hostname = args[0]
        macaddress = args[1]
        cn = u'{hostname}-{macaddress}'.format(
            hostname=hostname,
            macaddress=macaddress.replace(':', '')
        )
        result = api.Command['dhcphost_del_dhcpschema'](cn)
        return dict(result=result['result'], value=cn)

#### dhcphost_group ###############################################################
@register()
class dhcpgrouphost(dhcphost):
    parent_object = 'dhcpsubnetgroup'
    container_dn = container_dhcp_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpgrouphost_find(dhcphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpgrouphost_show(dhcphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpgrouphost_add(dhcphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpgrouphost_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpgrouphost_del(dhcphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


#### dhcphost_group ###############################################################
@register()
class dhcpsubnetgrouphost(dhcphost):
    parent_object = 'dhcpsubnetgroup'
    container_dn = container_dhcp_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpsubnetgrouphost_find(dhcphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpsubnetgrouphost_show(dhcphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpsubnetgrouphost_add(dhcphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpsubnetgrouphost_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpsubnetgrouphost_del(dhcphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')

#### dhcphost_subnet ###############################################################

@register()
class dhcpsubnethost(dhcphost):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcp_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpsubnethost_find(dhcphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpsubnethost_show(dhcphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpsubnethost_add(dhcphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')

@register()
class dhcpsubnethost_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpsubnethost_del(dhcphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


#### dhcphost_pool ###############################################################

@register()
class dhcppoolhost(dhcphost):
    parent_object = 'dhcppool'
    container_dn = container_dhcp_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcppoolhost_find(dhcphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcppoolhost_show(dhcphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcppoolhost_add(dhcphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcppoolhost_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcppoolhost_del(dhcphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


###############################################################################


from . import host


def host_add_dhcphost(self, ldap, dn, entry_attrs, *keys, **options):
    if 'macaddress' in entry_attrs:
        for addr in entry_attrs['macaddress']:
            if 'ipaddress' in entry_attrs:
                api.Command['dhcphost_add'](entry_attrs['fqdn'][0], addr, entry_attrs['ipaddress'][0])
            else:
                api.Command['dhcphost_add'](entry_attrs['fqdn'][0], addr)
    return dn

host.host_add.register_post_callback(host_add_dhcphost)


def host_mod_dhcphost(self, ldap, dn, entry_attrs, *keys, **options):
    if 'macaddress' not in options:
        return dn

    if options['macaddress'] is None:
        macaddresses = []
    else:
        macaddresses = list(options['macaddress'])

    filter = ldap.make_filter(
        {
            'cn': entry_attrs['fqdn'][0]
        },
        exact=False,
        leading_wildcard=False,
        trailing_wildcard=True
    )

    entries = []
    try:
        entries = ldap.get_entries(
            DN(container_dhcp_dn, dhcp_dn),
            ldap.SCOPE_SUBTREE,
            filter
        )
    except errors.NotFound:
        pass

    for entry in entries:
        entry_macaddr = entry['dhcpHWAddress'][0].replace('ethernet ', '')
        if entry_macaddr not in macaddresses:
            api.Command['dhcphost_del'](entry_attrs['fqdn'][0], entry_macaddr)
        if entry_macaddr in macaddresses:
            macaddresses.remove(entry_macaddr)

    for new_macaddr in macaddresses:
        api.Command['dhcphost_add'](entry_attrs['fqdn'][0], new_macaddr)

    return dn

host.host_mod.register_post_callback(host_mod_dhcphost)


def host_del_dhcphost(self, ldap, dn, *keys, **options):

    entry = ldap.get_entry(dn)

    if 'macaddress' in entry:
        for addr in entry['macaddress']:
            try:
                api.Command['dhcphost_del'](entry['fqdn'][0], addr)
            except:
                pass

    return dn

host.host_del.register_pre_callback(host_del_dhcphost)