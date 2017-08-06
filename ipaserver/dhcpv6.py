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
    object_name = _('DHCP configuration')
    object_name_plural = _('DHCP configuration')
    object_class = ['dhcpservice', 'top']
    default_attributes = ['cn']
    label = _('DHCP Configuration')
    label_singular = _('DHCP Configuration')

@register()
class dhcpv6service_show(dhcpservice_show):
    __doc__ = _('Display the DHCP configuration.')

@register()
class dhcpv6service_mod(dhcpservice_mod):
    __doc__ = _('Modify the DHCP configuration.')
    msg_summary = _('Modified the DHCP configuration.')

#### dhcpsubnet ###############################################################


@register()
class dhcpv6subnet(dhcpsubnet):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP subnet')
    object_name_plural = _('DHCP subnets')
    object_class = ['dhcpsubnet', 'top']
    default_attributes = ['cn']
    label = _('DHCP Subnets')
    label_singular = _('DHCP Subnet')

@register()
class dhcpv6subnet_add(dhcpsubnet_add):
    __doc__ = _('Create a new DHCP subnet.')
    msg_summary = _('Created DHCP subnet "%(value)s"')

@register()
class dhcpv6subnet_find(dhcpsubnet_find):
    __doc__ = _('Search for a DHCP subnet.')
    msg_summary = ngettext(
        '%(count)d DHCP subnet matched',
        '%(count)d DHCP subnets matched', 0
    )

@register()
class dhcpv6subnet_show(dhcpsubnet_show):
    __doc__ = _('Display a DHCP subnet.')

@register()
class dhcpv6subnet_mod(dhcpsubnet_mod):
    __doc__ = _('Modify a DHCP subnet.')
    msg_summary = _('Modified a DHCP subnet.')

@register()
class dhcpv6subnet_del(dhcpsubnet_del):
    __doc__ = _('Delete a DHCP subnet.')
    msg_summary = _('Deleted DHCP subnet "%(value)s"')


#### dhcpfailoverpeer ###############################################################

@register()
class dhcpv6failoverpeer(dhcpfailoverpeer):
    container_dn = container_dhcpv6_dn
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


@register()
class dhcpv6failoverpeer_add(dhcpfailoverpeer_add):
    __doc__ = _('Create a new DHCP fail over peer.')
    msg_summary = _('Created DHCP fail over peer "%(value)s"')

@register()
class dhcpv6failoverpeer_find(dhcpfailoverpeer_find):
    __doc__ = _('Search for a DHCP fail over peer.')
    msg_summary = ngettext(
        '%(count)d DHCP fail over peer matched',
        '%(count)d DHCP fail over peers matched', 0
    )


@register()
class dhcpv6failoverpeer_show(dhcpfailoverpeer_show):
    __doc__ = _('Display a DHCP fail over peer.')


@register()
class dhcpv6failoverpeer_mod(dhcpfailoverpeer_mod):
    __doc__ = _('Modify a DHCP fail over peer.')
    msg_summary = _('Modified a DHCP fail over peer.')


@register()
class dhcpv6failoverpeer_del(dhcpfailoverpeer_del):
    __doc__ = _('Delete a DHCP fail over peer.')
    msg_summary = _('Deleted DHCP fail over peer "%(value)s"')


#### dhcpsharednetwork ###############################################################

@register()
class dhcpv6sharednetwork(dhcpsharednetwork):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP Shared Network')
    object_name_plural = _('DHCP Shared Networks')
    object_class = ['dhcpSharedNetwork', 'top']
    default_attributes = ['cn']
    #uuid_attribute
    #rdn_attribute
    #attributer_members
    label = _('DHCP Shared Networks')
    label_singular = _('DHCP Shared Network')

@register()
class dhcpv6sharednetwork_add(dhcpsharednetwork_add):
    __doc__ = _('Create a new DHCP shared network.')
    msg_summary = _('Created DHCP shared network "%(value)s"')

@register()
class dhcpv6sharednetwork_find(dhcpsharednetwork_find):
    __doc__ = _('Search for a DHCP shared network.')
    msg_summary = ngettext(
        '%(count)d DHCP shared network matched',
        '%(count)d DHCP shared networks matched', 0
    )


@register()
class dhcpv6sharednetwork_show(dhcpsharednetwork_show):
    __doc__ = _('Display a DHCP shared network.')


@register()
class dhcpv6sharednetwork_mod(dhcpsharednetwork_mod):
    __doc__ = _('Modify a DHCP shared network.')
    msg_summary = _('Modified a DHCP shared network.')


@register()
class dhcpv6sharednetwork_del(dhcpsharednetwork_del):
    __doc__ = _('Delete a DHCP shared network.')
    msg_summary = _('Deleted DHCP shared network "%(value)s"')


#### dhcppool #################################################################


@register()
class dhcpv6pool(dhcppool):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP pool')
    object_name_plural = _('DHCP pools')
    object_class = ['dhcppool', 'top']
    default_attributes = ['cn']
    label = _('DHCP Pools')
    label_singular = _('DHCP Pool')

@register()
class dhcpv6pool_add(dhcppool_add):
    __doc__ = _('Create a new DHCP pool.')
    msg_summary = _('Created DHCP pool "%(value)s"')

@register()
class dhcpv6pool_find(dhcppool_find):
    __doc__ = _('Search for a DHCP pool.')
    msg_summary = ngettext(
        '%(count)d DHCP pool matched',
        '%(count)d DHCP pools matched', 0
    )

@register()
class dhcpv6pool_show(dhcppool_show):
    __doc__ = _('Display a DHCP pool.')

@register()
class dhcpv6pool_mod(dhcppool_mod):
    __doc__ = _('Modify a DHCP pool.')
    msg_summary = _('Modified a DHCP pool.')


@register()
class dhcpv6pool_del(dhcppool_del):
    __doc__ = _('Delete a DHCP pool.')
    msg_summary = _('Deleted DHCP pool "%(value)s"')


#### dhcpgroup #################################################################

@register()
class dhcpv6group(dhcpgroup):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpv6group_add(dhcpgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpv6group_find(dhcpgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpv6group_show(dhcpgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpv6group_mod(dhcpgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpv6group_del(dhcpgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpsubnetgroup #################################################################

@register()
class dhcpv6subnetgroup(dhcpsubnetgroup):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpv6subnetgroup_find(dhcpsubnetgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpv6subnetgroup_show(dhcpsubnetgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpv6subnetgroup_add(dhcpsubnetgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpv6subnetgroup_mod(dhcpsubnetgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpv6subnetgroup_del(dhcpsubnetgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpgroupgroup #################################################################

@register()
class dhcpv6groupgroup(dhcpgroupgroup):
    parent_object = 'dhcpgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpv6groupgroup_find(dhcpgroupgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpv6groupgroup_show(dhcpgroupgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpv6groupgroup_add(dhcpgroupgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpv6groupgroup_mod(dhcpgroupgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpv6groupgroup_del(dhcpgroupgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcppoolgroup #################################################################

@register()
class dhcpv6poolgroup(dhcppoolgroup):
    parent_object = 'dhcppool'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP group')
    object_name_plural = _('DHCP groups')
    object_class = ['dhcpgroup', 'top']
    default_attributes = ['cn']
    label = _('DHCP Groups')
    label_singular = _('DHCP Group')

@register()
class dhcpv6poolgroup_find(dhcppoolgroup_find):
    __doc__ = _('Search for a DHCP group.')
    msg_summary = ngettext(
        '%(count)d DHCP group matched',
        '%(count)d DHCP groups matched', 0
    )

@register()
class dhcpv6poolgroup_show(dhcppoolgroup_show):
    __doc__ = _('Display a DHCP group.')

@register()
class dhcpv6poolgroup_add(dhcppoolgroup_add):
    __doc__ = _('Create a new DHCP group.')
    msg_summary = _('Created DHCP group "%(value)s"')

@register()
class dhcpv6poolgroup_mod(dhcppoolgroup_mod):
    __doc__ = _('Modify a DHCP group.')
    msg_summary = _('Modified a DHCP group.')

@register()
class dhcpv6poolgroup_del(dhcppoolgroup_del):
    __doc__ = _('Delete a DHCP group.')
    msg_summary = _('Deleted DHCP group "%(value)s"')


#### dhcpserver ###############################################################


@register()
class dhcpv6server(dhcpserver):
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP server')
    object_name_plural = _('DHCP servers')
    object_class = ['dhcpserver', 'top']
    default_attributes = ['cn']
    label = _('DHCP Servers')
    label_singular = _('DHCP Server')

@register()
class dhcpv6server_add(dhcpserver_add):
    __doc__ = _('Create a new DHCP server.')
    msg_summary = _('Created DHCP server "%(value)s"')

@register()
class dhcpv6server_find(dhcpserver_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpv6server_show(dhcpserver_show):
    __doc__ = _('Display a DHCP server.')

@register()
class dhcpv6server_mod(dhcpserver_mod):
    __doc__ = _('Modify a DHCP server.')
    msg_summary = _('Modified a DHCP server.')

@register()
class dhcpv6server_del(dhcpserver_del):
    __doc__ = _('Delete a DHCP server.')
    msg_summary = _('Deleted DHCP server "%(value)s"')

#### dhcphost ###############################################################

@register()
class dhcpv6host(dhcphost):
#    parent_object = 'dhcpgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

@register()
class dhcpv6host_find(dhcphost_find):
    __doc__ = _('Search for a DHCP host.')
    msg_summary = ngettext(
        '%(count)d DHCP host matched',
        '%(count)d DHCP hosts matched', 0
    )

@register()
class dhcpv6host_show(dhcphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpv6host_add(dhcphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpv6host_mod(dhcphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')


@register()
class dhcpv6host_del(dhcphost_del):
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')

#### dhcphost_group ###############################################################
@register()
class dhcpv6grouphost(dhcpgrouphost):
    parent_object = 'dhcpsubnetgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6grouphost_find(dhcpgrouphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpv6grouphost_show(dhcpgrouphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpv6grouphost_add(dhcpgrouphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpv6grouphost_mod(dhcpgrouphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpv6grouphost_del(dhcpgrouphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


#### dhcphost_group ###############################################################
@register()
class dhcpv6subnetgrouphost(dhcpsubnetgrouphost):
    parent_object = 'dhcpsubnetgroup'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6subnetgrouphost_find(dhcpsubnetgrouphost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpv6subnetgrouphost_show(dhcpsubnetgrouphost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpv6subnetgrouphost_add(dhcpsubnetgrouphost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpv6subnetgrouphost_mod(dhcpsubnetgrouphost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpv6subnetgrouphost_del(dhcpsubnetgrouphost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')

#### dhcphost_subnet ###############################################################

@register()
class dhcpv6subnethost(dhcpsubnethost):
    parent_object = 'dhcpsubnet'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6subnethost_find(dhcpsubnethost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpv6subnethost_show(dhcpsubnethost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpv6subnethost_add(dhcpsubnethost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')

@register()
class dhcpv6subnethost_mod(dhcpsubnethost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpv6subnethost_del(dhcpsubnethost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


#### dhcphost_pool ###############################################################

@register()
class dhcpv6poolhost(dhcppoolhost):
    parent_object = 'dhcppool'
    container_dn = container_dhcpv6_dn
    object_name = _('DHCP host')
    object_name_plural = _('DHCP hosts')
    object_class = ['dhcphost', 'top']
    default_attributes = ['cn']
    label = _('DHCP Hosts')
    label_singular = _('DHCP Host')

    search_attributes = [ 'cn', 'dhcphwaddress' ]

@register()
class dhcpv6poolhost_find(dhcppoolhost_find):
    __doc__ = _('Search for a DHCP server.')
    msg_summary = ngettext(
        '%(count)d DHCP server matched',
        '%(count)d DHCP servers matched', 0
    )

@register()
class dhcpv6poolhost_show(dhcppoolhost_show):
    __doc__ = _('Display a DHCP host.')

@register()
class dhcpv6poolhost_add(dhcppoolhost_add):
    __doc__ = _('Create a new DHCP host.')
    msg_summary = _('Created DHCP host "%(value)s"')


@register()
class dhcpv6poolhost_mod(dhcppoolhost_mod):
    __doc__ = _('Modify a DHCP host.')
    msg_summary = _('Modified a DHCP host.')

@register()
class dhcpv6poolhost_del(dhcppoolhost_del):
    NO_CLI = True
    __doc__ = _('Delete a DHCP host.')
    msg_summary = _('Deleted DHCP host "%(value)s"')


###############################################################################

