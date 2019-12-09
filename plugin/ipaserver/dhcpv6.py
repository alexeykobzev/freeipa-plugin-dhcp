# -*- coding: utf-8 -*-

# Copyright © 2017 Edward Heuveling <cabeljunky@gmail.com>
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

from ipaserver.plugins.dhcpv4 import *
from ipaserver.plugins.dhcpcommon import *

#### Constants ################################################################

#dhcpv6_dn = 'cn=dhcp,{0}'.format(api.env.basedn)
dhcpv6_dn = '{0}'.format(api.env.basedn)
service_dhcpv6_dn = 'cn=v6'
container_dhcpv6_dn = DN(('cn', 'v6'), 'cn=dhcp')
register = Registry()

dhcp_version = 6
dhcp_set_version( dhcp_version )
#modify_dhcp = modify_dhcp( 6 )

@register()
class dhcpv6service(dhcpservice):
    object_name = _('DHCP IPv6 configuration')
    object_name_plural = _('DHCP IPv6 configuration')
    object_class = ['dhcpservice', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Configuration')
    label_singular = _('DHCP IPv6 Configuration')

@register()
class dhcpv6service_show(dhcpservice_show):
    __doc__ = _('Display the DHCP IPv6 configuration.')

@register()
class dhcpv6service_mod(dhcpservice_mod):
    __doc__ = _('Modify the DHCP IPv6 configuration.')
    msg_summary = _('Modified the DHCP IPv6 configuration.')

#### dhcpsubnet ###############################################################


@register()
class dhcpv6subnet(dhcpsubnet):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 subnet')
    object_name_plural = _('DHCP IPv6 subnets')
    object_class = ['dhcpsubnet6', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Subnets')
    label_singular = _('DHCP IPv6 Subnet')

    takes_params = (
        Str(
            'cn',
            cli_name='subnet',
            label=_('Subnet'),
            doc=_('DHCP IPv6 subnet.'),
            primary_key = True
        ),
        Int(
            'dhcpv6netmask',
            cli_name='netmask',
            label=_('Netmask'),
            doc=_('DHCP IPv6 netmask.'),
            minvalue=0,
            maxvalue=128,
            default=64,
            flags=['virtual_attribute']
        ),
        Str(
            'dhcprange6?',
            cli_name='dhcprange6',
            label=_('DHCP IPv6 Range'),
            doc=_('DHCP IPv6 range.')
        ),
        Str(
            'domainnameservers*',
            cli_name='domainnameservers',
            label=_('Domain Name Server'),
            doc=_('Domain Name Servers.'),
            flags=['virtual_attribute']
        ),
        Str(
            'dhcpstatements*',
            cli_name='dhcpstatements',
            label=_('DHCP IPv6 Statements'),
            doc=_('DHCP IPv6 statements.')
        ),
        Str(
            'dhcppermitlist*',
            cli_name='dhcppermitlist',
            label=_('DHCP IPv6 Statements'),
            doc=_('DHCP IPv6 statements.')
        ),
        Str(
            'dhcpoption*',
            cli_name='dhcpoptions',
            label=_('DHCP IPv6 Options'),
            doc=_('DHCP IPv6 options.')
        ),
        Str(
            'dhcpcomments?',
            cli_name='dhcpcomments',
            label=_('Comments'),
            doc=_('DHCP IPv6 comments.')
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

        dhcpOptions = entry_attrs.get('dhcpoption', [])

        for option in dhcpOptions:
            if option.startswith('routers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['router'] = v
            elif option.startswith('dhcp6.name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            elif option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')

        return entry_attrs


@register()
class dhcpv6subnet_add(dhcpsubnet_add):
    __doc__ = _('Create a new DHCP IPv6 subnet.')
    msg_summary = _('Created DHCP IPv6 subnet "%(value)s"')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        ip = IPNetwork('{0}'.format(keys[-1]))
        dhcpOptions = []
        #dhcpOptions.append('subnet-mask {0}'.format(ip.netmask))
        #dhcpOptions.append('broadcast-address {0}'.format(ip.broadcast))
        entry_attrs['dhcpoption'] = dhcpOptions
        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        return dn

@register()
class dhcpv6subnet_add_cidr(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new DHCP IPv6 subnet by network address in CIDR format.')
    msg_summary = _('Created DHCP IPv6 subnet "%(value)s"')

    takes_args = (
        Str(
            'networkaddr',
            cli_name='networkaddr',
            label=_('Network Address'),
            doc=_("Network address in CIDR notation.")
        )
    )

    def execute(self, *args, **kw):
        ip = IPNetwork(args[-1])
        cn = unicode( str(ip) )
        dhcpv6netmask = ip.prefixlen
        result = api.Command['dhcpv6subnet_add'](cn, dhcpv6netmask=dhcpv6netmask)
        return dict(result=result['result'], value=cn)


@register()
class dhcpv6subnet_find(dhcpsubnet_find):
    __doc__ = _('Search for a DHCP IPv6 subnet.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 subnet matched',
        '%(count)d DHCP IPv6 subnets matched', 0
    )

@register()
class dhcpv6subnet_show(dhcpsubnet_show):
    __doc__ = _('Display a DHCP IPv6 subnet.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpv6subnet.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn

@register()
class dhcpv6subnet_mod(dhcpsubnet_mod):
    __doc__ = _('Modify a DHCP IPv6 subnet.')
    msg_summary = _('Modified a DHCP IPv6 subnet.')


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

        dhcp_modify_router( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements )
        dhcp_modify_domainserver( dhcp_version, options, dhcpOptions )
        dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions )

        entry_attrs['dhcpstatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn


    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpv6subnet.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn

@register()
class dhcpv6subnet_del(dhcpsubnet_del):
    __doc__ = _('Delete a DHCP IPv6 subnet.')
    msg_summary = _('Deleted DHCP IPv6 subnet "%(value)s"')


#### dhcpfailoverpeer ###############################################################

@register()
class dhcpv6failoverpeer(dhcpfailoverpeer):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 Fail Over Peer')
    object_name_plural = _('DHCP IPv6 Fail Over Peers')
    object_class = ['dhcpFailOverPeer', 'top']
    default_attributes = ['cn', 
                         'dhcpFailOverPrimaryServer', 
                         'dhcpFailOverSecondaryServer',
                         'dhcpFailOverPrimaryPort',
                         'dhcpFailOvreSecondaryPort']
    #uuid_attribute
    #rdn_attribute
    #attributer_members
    label = _('DHCP IPv6 Fail Over Peers')
    label_singular = _('DHCP IPv6 Fail Over Peer')


@register()
class dhcpv6failoverpeer_add(dhcpfailoverpeer_add):
    __doc__ = _('Create a new DHCP IPv6 fail over peer.')
    msg_summary = _('Created DHCP IPv6 fail over peer "%(value)s"')

@register()
class dhcpv6failoverpeer_find(dhcpfailoverpeer_find):
    __doc__ = _('Search for a DHCP IPv6 fail over peer.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 fail over peer matched',
        '%(count)d DHCP IPv6 fail over peers matched', 0
    )


@register()
class dhcpv6failoverpeer_show(dhcpfailoverpeer_show):
    __doc__ = _('Display a DHCP IPv6 fail over peer.')


@register()
class dhcpv6failoverpeer_mod(dhcpfailoverpeer_mod):
    __doc__ = _('Modify a DHCP IPv6 fail over peer.')
    msg_summary = _('Modified a DHCP IPv6 fail over peer.')


@register()
class dhcpv6failoverpeer_del(dhcpfailoverpeer_del):
    __doc__ = _('Delete a DHCP IPv6 fail over peer.')
    msg_summary = _('Deleted DHCP IPv6 fail over peer "%(value)s"')


#### dhcpsharednetwork ###############################################################

@register()
class dhcpv6sharednetwork(dhcpsharednetwork):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 Shared Network')
    object_name_plural = _('DHCP IPv6 Shared Networks')
    object_class = ['dhcpSharedNetwork', 'top']
    default_attributes = ['cn']
    #uuid_attribute
    #rdn_attribute
    #attributer_members
    label = _('DHCP IPv6 Shared Networks')
    label_singular = _('DHCP IPv6 Shared Network')

@register()
class dhcpv6sharednetwork_add(dhcpsharednetwork_add):
    __doc__ = _('Create a new DHCP IPv6 shared network.')
    msg_summary = _('Created DHCP IPv6 shared network "%(value)s"')

@register()
class dhcpv6sharednetwork_find(dhcpsharednetwork_find):
    __doc__ = _('Search for a DHCP IPv6 shared network.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 shared network matched',
        '%(count)d DHCP IPv6 shared networks matched', 0
    )


@register()
class dhcpv6sharednetwork_show(dhcpsharednetwork_show):
    __doc__ = _('Display a DHCP IPv6 shared network.')


@register()
class dhcpv6sharednetwork_mod(dhcpsharednetwork_mod):
    __doc__ = _('Modify a DHCP IPv6 shared network.')
    msg_summary = _('Modified a DHCP IPv6 shared network.')


@register()
class dhcpv6sharednetwork_del(dhcpsharednetwork_del):
    __doc__ = _('Delete a DHCP IPv6 shared network.')
    msg_summary = _('Deleted DHCP IPv6 shared network "%(value)s"')


#### dhcppool #################################################################


@register()
class dhcpv6pool(dhcppool):
    parent_object = 'dhcpv6subnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 pool')
    object_name_plural = _('DHCP IPv6 pools')
    object_class = ['dhcppool6', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Pools')
    label_singular = _('DHCP IPv6 Pool')

    takes_params = (
        Str(
            'cn',
            cli_name='name',
            label=_('Name'),
            doc=_('DHCP pool name.'),
            primary_key=True
        ),
        Str(
            'dhcprange6+',
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

@register()
class dhcpv6pool_add(dhcppool_add):
    __doc__ = _('Create a new DHCP IPv6 pool.')
    msg_summary = _('Created DHCP IPv6 pool "%(value)s"')


@register()
class dhcpv6pool_find(dhcppool_find):
    __doc__ = _('Search for a DHCP IPv6 pool.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 pool matched',
        '%(count)d DHCP IPv6 pools matched', 0
    )

@register()
class dhcpv6pool_show(dhcppool_show):
    __doc__ = _('Display a DHCP IPv6 pool.')

@register()
class dhcpv6pool_mod(dhcppool_mod):
    __doc__ = _('Modify a DHCP IPv6 pool.')
    msg_summary = _('Modified a DHCP IPv6 pool.')


@register()
class dhcpv6pool_del(dhcppool_del):
    __doc__ = _('Delete a DHCP IPv6 pool.')
    msg_summary = _('Deleted DHCP IPv6 pool "%(value)s"')


@register()
class dhcpv6pool_is_valid(Command):
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
            'dhcprange6+',
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
            container_dhcpv6_dn,
            dhcpv6_dn
        )
        try:
            entry = ldap.get_entry(dn)
        except:
            return dict(result=False, value=u'No such subnet.')

        subnetIP = IPNetwork( entry['cn'][0] )

        (rangeStart, rangeEnd) = dhcprange.split(" ")
        rangeStartIP = IPNetwork("{0}/128".format(rangeStart))
        rangeEndIP = IPNetwork("{0}/128".format(rangeEnd))

        if rangeStartIP > rangeEndIP:
            return dict(result=False, value=u'First IPv6 must come before last IPv6!')

        if rangeStartIP < subnetIP[0] or rangeStartIP > subnetIP[-1]:
            return dict(result=False, value=u'{0} is outside parent subnet {1}. Addresses in this pool must come from the range {2}-{3}.'.format(rangeStartIP.ip, subnetIP.cidr, subnetIP[0], subnetIP[-1]))

        if rangeEndIP < subnetIP[0] or rangeEndIP > subnetIP[-1]:
            return dict(result=False, value=u'{0} is outside parent subnet {1}. Addresses in this pool must come from the range {2}-{3}.'.format(rangeEndIP.ip, subnetIP.cidr, subnetIP[0], subnetIP[-1]))

        return dict(result=True, value=u'Valid IPv6 range.')


#### dhcpgroup #################################################################

@register()
class dhcpv6group(dhcpgroup):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 group')
    object_name_plural = _('DHCP IPv6 groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Groups')
    label_singular = _('DHCP IPv6 Group')

@register()
class dhcpv6group_add(dhcpgroup_add):
    __doc__ = _('Create a new DHCP IPv6 group.')
    msg_summary = _('Created DHCP IPv6 group "%(value)s"')

@register()
class dhcpv6group_find(dhcpgroup_find):
    __doc__ = _('Search for a DHCP IPv6 group.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 group matched',
        '%(count)d DHCP IPv6 groups matched', 0
    )

@register()
class dhcpv6group_show(dhcpgroup_show):
    __doc__ = _('Display a DHCP IPv6 group.')

@register()
class dhcpv6group_mod(dhcpgroup_mod):
    __doc__ = _('Modify a DHCP IPv6 group.')
    msg_summary = _('Modified a DHCP IPv6 group.')

@register()
class dhcpv6group_del(dhcpgroup_del):
    __doc__ = _('Delete a DHCP IPv6 group.')
    msg_summary = _('Deleted DHCP IPv6 group "%(value)s"')


#### dhcpsubnetgroup #################################################################

@register()
class dhcpv6subnetgroup(dhcpsubnetgroup):
    parent_object = 'dhcpv6subnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 group')
    object_name_plural = _('DHCP IPv6 groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Groups')
    label_singular = _('DHCP IPv6 Group')

@register()
class dhcpv6subnetgroup_find(dhcpsubnetgroup_find):
    __doc__ = _('Search for a DHCP IPv6 group.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 group matched',
        '%(count)d DHCP IPv6 groups matched', 0
    )

@register()
class dhcpv6subnetgroup_show(dhcpsubnetgroup_show):
    __doc__ = _('Display a DHCP IPv6 group.')

@register()
class dhcpv6subnetgroup_add(dhcpsubnetgroup_add):
    __doc__ = _('Create a new DHCP IPv6 group.')
    msg_summary = _('Created DHCP IPv6 group "%(value)s"')

@register()
class dhcpv6subnetgroup_mod(dhcpsubnetgroup_mod):
    __doc__ = _('Modify a DHCP IPv6 group.')
    msg_summary = _('Modified a DHCP IPv6 group.')

@register()
class dhcpv6subnetgroup_del(dhcpsubnetgroup_del):
    __doc__ = _('Delete a DHCP IPv6 group.')
    msg_summary = _('Deleted DHCP IPv6 group "%(value)s"')


#### dhcpgroupgroup #################################################################

@register()
class dhcpv6groupgroup(dhcpgroupgroup):
    parent_object = 'dhcpv6group'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 group')
    object_name_plural = _('DHCP IPv6 groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Groups')
    label_singular = _('DHCP IPv6 Group')

@register()
class dhcpv6groupgroup_find(dhcpgroupgroup_find):
    __doc__ = _('Search for a DHCP IPv6 group.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 group matched',
        '%(count)d DHCP IPv6 groups matched', 0
    )

@register()
class dhcpv6groupgroup_show(dhcpgroupgroup_show):
    __doc__ = _('Display a DHCP IPv6 group.')

@register()
class dhcpv6groupgroup_add(dhcpgroupgroup_add):
    __doc__ = _('Create a new DHCP IPv6 group.')
    msg_summary = _('Created DHCP IPv6 group "%(value)s"')

@register()
class dhcpv6groupgroup_mod(dhcpgroupgroup_mod):
    __doc__ = _('Modify a DHCP IPv6 group.')
    msg_summary = _('Modified a DHCP IPv6 group.')

@register()
class dhcpv6groupgroup_del(dhcpgroupgroup_del):
    __doc__ = _('Delete a DHCP IPv6 group.')
    msg_summary = _('Deleted DHCP IPv6 group "%(value)s"')


#### dhcppoolgroup #################################################################

@register()
class dhcpv6poolgroup(dhcppoolgroup):
    parent_object = 'dhcpv6pool'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 group')
    object_name_plural = _('DHCP IPv6 groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Groups')
    label_singular = _('DHCP IPv6 Group')

@register()
class dhcpv6poolgroup_find(dhcppoolgroup_find):
    __doc__ = _('Search for a DHCP IPv6 group.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 group matched',
        '%(count)d DHCP IPv6 groups matched', 0
    )

@register()
class dhcpv6poolgroup_show(dhcppoolgroup_show):
    __doc__ = _('Display a DHCP IPv6 group.')

@register()
class dhcpv6poolgroup_add(dhcppoolgroup_add):
    __doc__ = _('Create a new DHCP IPv6 group.')
    msg_summary = _('Created DHCP IPv6 group "%(value)s"')

@register()
class dhcpv6poolgroup_mod(dhcppoolgroup_mod):
    __doc__ = _('Modify a DHCP IPv6 group.')
    msg_summary = _('Modified a DHCP IPv6 group.')

@register()
class dhcpv6poolgroup_del(dhcppoolgroup_del):
    __doc__ = _('Delete a DHCP IPv6 group.')
    msg_summary = _('Deleted DHCP IPv6 group "%(value)s"')


#### dhcpserver ###############################################################


@register()
class dhcpv6server(dhcpserver):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 server')
    object_name_plural = _('DHCP IPv6 servers')
    object_class = ['dhcpserver', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Servers')
    label_singular = _('DHCP IPv6 Server')

@register()
class dhcpv6server_add(dhcpserver_add):
    __doc__ = _('Create a new DHCP IPv6 server.')
    msg_summary = _('Created DHCP IPv6 server "%(value)s"')

@register()
class dhcpv6server_find(dhcpserver_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6server_show(dhcpserver_show):
    __doc__ = _('Display a DHCP IPv6 server.')

@register()
class dhcpv6server_mod(dhcpserver_mod):
    __doc__ = _('Modify a DHCP IPv6 server.')
    msg_summary = _('Modified a DHCP IPv6 server.')

@register()
class dhcpv6server_del(dhcpserver_del):
    __doc__ = _('Delete a DHCP IPv6 server.')
    msg_summary = _('Deleted DHCP IPv6 server "%(value)s"')

#### dhcphost ###############################################################

@register()
class dhcpv6host(dhcphost):
#    parent_object = 'dhcpgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 host')
    object_name_plural = _('DHCP IPv6 hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Hosts')
    label_singular = _('DHCP IPv6 Host')

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
            'ipaddress6?',
            cli_name='ipaddress6',
            label=_('Host IPv6 Address'),
            doc=_('Host IPv6 Address.'),
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
    )

    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        dhcpStatements = entry_attrs.get('dhcpstatements', [])

        for statements in dhcpStatements:
            if statements.startswith('fixed-address6 '):
                (o, v) = statements.split(' ', 1)
                entry_attrs['ipaddress6'] = v
                entry_attrs['ipaddress6'] = v
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
class dhcpv6host_find(dhcphost_find):
    __doc__ = _('Search for a DHCP IPv6 host.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 host matched',
        '%(count)d DHCP IPv6 hosts matched', 0
    )

@register()
class dhcpv6host_show(dhcphost_show):
    __doc__ = _('Display a DHCP IPv6 host.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpv6host.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn

@register()
class dhcpv6host_add_dhcpschema(LDAPCreate):
    NO_CLI = True
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpv6host_add(dhcphost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6host_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

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

        dhcp_modify_hostname( dhcp_version, options, dhcpOptions, dhcpStatements )

        entry_attrs['dhcpStatements'] = dhcpStatements
        entry_attrs['dhcpoption'] = dhcpOptions

        return dn

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = dhcpv6host.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class dhcpv6host_del(dhcphost_del):
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6host_add_cmd(Command):
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
            'ipaddress6',
            cli_name='ipaddress6',
            label=_('IPv6 Address'),
            doc=_("Hosts IPv6 Address.")
        )
    )

    def execute(self, *args, **kw):
        hostname = args[0]
        macaddress = args[1]
        cn = u'{hostname}-{macaddress}'.format(
            hostname=hostname,
            macaddress=macaddress.replace(':', '')
        )
        result = api.Command['dhcphost_add_dhcpschema'](
            cn,
            dhcphwaddress=u'ethernet {0}'.format(macaddress),
            dhcpstatements=[u'fixed-address6 {0}'.format(hostname), u'ddnshostname "{0}"'.format(hostname)],
            dhcpoption=[u'host-name "{0}"'.format(hostname)]
        )
        return dict(result=result['result'], value=cn)

#### dhcphost_group ###############################################################
@register()
class dhcpv6grouphost(dhcpv6host):
    parent_object = 'dhcpv6subnetgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 host')
    object_name_plural = _('DHCP IPv6 hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Hosts')
    label_singular = _('DHCP IPv6 Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]


@register()
class dhcpv6grouphost_find(dhcpv6host_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6grouphost_show(dhcpv6host_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6grouphost_add(dhcpv6host_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6grouphost_mod(dhcpv6host_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6grouphost_del(dhcpv6host_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


#### dhcphost_group ###############################################################
@register()
class dhcpv6subnetgrouphost(dhcpv6host):
    parent_object = 'dhcpv6subnetgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 host')
    object_name_plural = _('DHCP IPv6 hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Hosts')
    label_singular = _('DHCP IPv6 Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6subnetgrouphost_find(dhcpv6host_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6subnetgrouphost_show(dhcpv6host_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6subnetgrouphost_add(dhcpv6host_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6subnetgrouphost_mod(dhcpv6host_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6subnetgrouphost_del(dhcpv6host_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')

#### dhcphost_subnet ###############################################################

@register()
class dhcpv6subnethost(dhcpv6host):
    parent_object = 'dhcpv6subnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 host')
    object_name_plural = _('DHCP IPv6 hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Hosts')
    label_singular = _('DHCP IPv6 Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6subnethost_find(dhcpv6host_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6subnethost_show(dhcpv6host_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6subnethost_add(dhcpv6host_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')

@register()
class dhcpv6subnethost_mod(dhcpv6host_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6subnethost_del(dhcpv6host_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


#### dhcphost_pool ###############################################################

@register()
class dhcpv6poolhost(dhcpv6host):
    parent_object = 'dhcpv6pool'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP IPv6 host')
    object_name_plural = _('DHCP IPv6 hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP IPv6 Hosts')
    label_singular = _('DHCP IPv6 Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6poolhost_find(dhcpv6host_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6poolhost_show(dhcpv6host_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6poolhost_add(dhcpv6host_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6poolhost_mod(dhcpv6host_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6poolhost_del(dhcpv6host_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


###############################################################################

