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

# class dhcpcommon(object):
dhcp_version = 4

    # def __init__(self, dhcp_version):
         # self.dhcp_version = dhcp_version


def dhcp_set_version( version ):
    dhcp_version = version

def dhcp_get_version( version ):
    return dhcp_version


def dhcp_modify_domainserver( dhcp_version, options, dhcpOptions):
    if dhcp_version == 4 :
        start_with_options = 'domain-name-servers '
    elif dhcp_version == 6 :
        start_with_options = 'dhcp6.name-servers '
    
    option_item = 'domainnameservers'
    
    dhcp_modify_options_ip_address( options, option_item, dhcpOptions, start_with_options )

def dhcp_modify_domainsearch( dhcp_version, options, dhcpOptions ):
    if dhcp_version == 4 :
        start_with_options = 'domain-search '
    elif dhcp_version == 6 :
        start_with_options = 'dhcp6.domain-search '

    option_item = 'domainsearch'
    if option_item in options:
        option_value = start_with_options + ', '.join('"' + s + '"' for s in options[option_item])
        dhcp_modify_options( option_value, dhcpOptions, start_with_options )

def dhcp_modify_router( dhcp_version, options, dhcpOptions):
    start_with_options = 'routers '
    option_item = 'router'

    dhcp_modify_options_ip_address( options, option_item, dhcpOptions, start_with_options )

def dhcp_modify_maxleasetime( dhcp_version, options, dhcpStatements ):
    start_with_options = 'max-lease-time '
    option_item = 'maxleasetime'

    dhcp_modify_statements_value( options, option_item, dhcpStatements, start_with_options )

def dhcp_modify_defaultleasetime( dhcp_version, options, dhcpStatements ):
    start_with_options = 'default-lease-time '
    option_item = 'defaultleasetime'

    dhcp_modify_statements_value( options, option_item, dhcpStatements, start_with_options )

def dhcp_modify_permitknownclients( dhcp_version, options, dhcpPermitList ):
    end_with_options = ' known-clients'
    option_item = 'permitknownclients'
    return dhcp_modify_permit( options, option_item, dhcpPermitList, end_with_options )


def dhcp_modify_permitunknownclients( dhcp_version, options, dhcpPermitList) :
    end_with_options = ' unknown-clients'
    option_item = 'permitunknownclients'

    return dhcp_modify_permit( options, option_item, dhcpPermitList, end_with_options )

def dhcp_modify_domainname( dhcp_version, options, dhcpOptions, dhcpStatements ):
    if dhcp_version == 4 :
        start_with_options = 'domain-name '
        start_with_statements = 'dddns-domainname '
    elif dhcp_version == 6 :
        start_with_options = 'domain-name '
        start_with_statements = 'dddns-domainname '

    option_item = 'domainname'
    if option_item in options:
        option_value = '{0}"{1}"'.format(start_with_options, options[option_item])
        statement_value = '{0}"{1}"'.format(start_with_statements, options[option_item])
        dhcp_modify_options_statements( option_value, statement_value, dhcpOptions, dhcpStatements, start_with_options, start_with_statements )

def dhcp_modify_hostname( dhcp_version, options, dhcpOptions, dhcpStatements ):
    if dhcp_version == 4 :
        start_with_options = 'host-name '
        start_with_statements = 'ddns-hostname '
    elif dhcp_version == 6 :
        start_with_options = 'host-name '
        start_with_statements = 'ddns-hostname '

    option_item = 'domainname'
    if option_item in options:
        option_value = '{0}"{1}"'.format(start_with_options, options[option_item])
        statement_value = '{0}"{1}"'.format(start_with_statements, options[option_item])
        dhcp_modify_options_statements( option_value, statement_value, dhcpOptions, dhcpStatements, start_with_options, start_with_statements )

#######################################################################################################
##                                general
#######################################################################################################
def dhcp_modify_options_ip_address( options, option_item, dhcpOptions, start_with_options ):
    if option_item in options:
        # if isinstance(options[option_item], list) or isinstance(options[option_item], tuple):
        if isinstance(options[option_item], list) or isinstance(options[option_item], tuple):
            option_value = start_with_options + ', '.join( s for s in options[option_item])
            dhcp_modify_options( option_value, dhcpOptions, start_with_options )
        elif len(options[option_item]) > 0 :
            option_value = '{0}{1}'.format(start_with_options, options[option_item])
            dhcp_modify_options( option_value, dhcpOptions, start_with_options )

def dhcp_modify_options( option_value, dhcpOptions, start_with_options ):
    foundOption = False
    for i, s in enumerate(dhcpOptions):
        if s.startswith(start_with_options):
            foundOption = True
            dhcpOptions[i] = option_value
            break
    if not foundOption:
        dhcpOptions.append(option_value)

def dhcp_modify_options_value( options, option_item, dhcpOptions, start_with_options ):
    if option_item in options:
        option_value = '{0}{1}'.format(start_with_options, options[option_item])
        dhcp_modify_options( option_value, dhcpOptions, start_with_options )

def dhcp_modify_statements( statement_value, dhcpStatements, start_with_statements ):
    foundOption = False
    for i, s in enumerate(dhcpStatements):
        if s.startswith(start_with_statements):
            foundOption = True
            dhcpStatements[i] = statement_value
            break
    if not foundOption:
        dhcpStatements.append(statement_value)

def dhcp_modify_statements_value( options, option_item, dhcpStatements, start_with_options ):
    if option_item in options:
        option_value = '{0}{1}'.format(start_with_options, options[option_item])
        dhcp_modify_statements( option_value, dhcpStatements, start_with_options )

def dhcp_modify_permit( options, option_item, dhcpPermitList, end_with_options ):
    if option_item in options:
        option_value = '{0}{1}'.format('allow' if options[option_item] else 'deny', end_with_options)
        newPermitList = [p for p in dhcpPermitList if not p.endswith(end_with_options)]
        newPermitList.append(option_value)
        dhcpPermitList = newPermitList
    return dhcpPermitList

def dhcp_modify_options_statements( option_value, statement_value, dhcpOptions, dhcpStatements, start_with_options, start_with_statements ):

    dhcp_modify_options( option_value, dhcpOptions, start_with_options )
    dhcp_modify_statements( statement_value, dhcpStatements, start_with_statements )


def dhcp_remove_options( dhcpOptions, start_with_options ):
    for i, s in enumerate(dhcpOptions):
        if s.startswith(start_with_options):
            dhcpOptions.pop(i)
            break
