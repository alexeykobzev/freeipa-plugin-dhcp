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

from dhcpv4 import *


#### Constants ################################################################

#dhcpv6_dn = 'cn=dhcp,{0}'.format(api.env.basedn)
dhcpv6_dn = '{0}'.format(api.env.basedn)
service_dhcpv6_dn = 'cn=v6'
container_dhcpv6_dn = DN(('cn', 'v6'), 'cn=dhcp')
register = Registry()

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

@register()
class dhcpv6subnet_add(dhcpsubnet_add):
    __doc__ = _('Create a new DHCP IPv6 subnet.')
    msg_summary = _('Created DHCP IPv6 subnet "%(value)s"')


    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        ip = IPNetwork('{0}/{1}'.format(keys[-1], options['dhcpv6netmask']))
        dhcpOptions = []
        dhcpOptions.append('subnet-mask {0}'.format(ip.netmask))
        dhcpOptions.append('broadcast-address {0}'.format(ip.broadcast))
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
        cn = unicode(ip.network)
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

@register()
class dhcpv6subnet_mod(dhcpsubnet_mod):
    __doc__ = _('Modify a DHCP IPv6 subnet.')
    msg_summary = _('Modified a DHCP IPv6 subnet.')

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

@register()
class dhcpv6host_add(dhcphost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6host_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')


@register()
class dhcpv6host_del(dhcphost_del):
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')

#### dhcphost_group ###############################################################
@register()
class dhcpv6grouphost(dhcpgrouphost):
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
class dhcpv6grouphost_find(dhcpgrouphost_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6grouphost_show(dhcpgrouphost_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6grouphost_add(dhcpgrouphost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6grouphost_mod(dhcpgrouphost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6grouphost_del(dhcpgrouphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


#### dhcphost_group ###############################################################
@register()
class dhcpv6subnetgrouphost(dhcpsubnetgrouphost):
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
class dhcpv6subnetgrouphost_find(dhcpsubnetgrouphost_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6subnetgrouphost_show(dhcpsubnetgrouphost_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6subnetgrouphost_add(dhcpsubnetgrouphost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6subnetgrouphost_mod(dhcpsubnetgrouphost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6subnetgrouphost_del(dhcpsubnetgrouphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')

#### dhcphost_subnet ###############################################################

@register()
class dhcpv6subnethost(dhcpsubnethost):
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
class dhcpv6subnethost_find(dhcpsubnethost_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6subnethost_show(dhcpsubnethost_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6subnethost_add(dhcpsubnethost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')

@register()
class dhcpv6subnethost_mod(dhcpsubnethost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6subnethost_del(dhcpsubnethost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


#### dhcphost_pool ###############################################################

@register()
class dhcpv6poolhost(dhcppoolhost):
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
class dhcpv6poolhost_find(dhcppoolhost_find):
    __doc__ = _('Search for a DHCP IPv6 server.')
    msg_summary = ngettext(
        '%(count)d DHCP IPv6 server matched',
        '%(count)d DHCP IPv6 servers matched', 0
    )

@register()
class dhcpv6poolhost_show(dhcppoolhost_show):
    __doc__ = _('Display a DHCP IPv6 host.')

@register()
class dhcpv6poolhost_add(dhcppoolhost_add):
    __doc__ = _('Create a new DHCP IPv6 host.')
    msg_summary = _('Created DHCP IPv6 host "%(value)s"')


@register()
class dhcpv6poolhost_mod(dhcppoolhost_mod):
    __doc__ = _('Modify a DHCP IPv6 host.')
    msg_summary = _('Modified a DHCP IPv6 host.')

@register()
class dhcpv6poolhost_del(dhcppoolhost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP IPv6 host.')
    msg_summary = _('Deleted DHCP IPv6 host "%(value)s"')


###############################################################################

