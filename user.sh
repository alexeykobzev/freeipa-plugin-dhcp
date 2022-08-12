#!/bin/bash

### add the user to LDAP DIT
ldapmodify -D "cn=Directory Manager" -W -p 389 -h ipaserver.vigo.internal -a -f dhcpdaccount.ldif

### set a decent password for the newly created system account
ldappasswd -x -S -W -D "cn=Directory Manager" uid=dhcp,cn=sysaccounts,cn=etc,dc=vigo,dc=internal
