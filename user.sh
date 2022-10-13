#!/bin/bash

### log in through Kerberos 
kinit admin@VIGO.INTERNAL

### add the user and set privileges to LDAP DIT
ldapmodify -X admin -D "cn=Directory Manager" -W -p 389 -h ipaserver.vigo.internal -a -f user/dhcpd_account.ldif
ldapmodify -X admin -D "cn=Directory Manager" -W -p 389 -h ipaserver.vigo.internal -a -f user/dhcpd_privileges.ldif

### set a decent password for the newly created system account
ldappasswd -X admin -S -W -D "cn=Directory Manager" uid=dhcp,cn=sysaccounts,cn=etc,dc=vigo,dc=internal
