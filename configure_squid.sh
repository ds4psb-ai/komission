#!/bin/bash
set -euo pipefail

PROXY_USER="proxyuser"
PROXY_PASS="pPxM318ad3gYI0J3dtiBbg"

cat >/etc/squid/squid.conf <<'CONF'
http_port 3128
auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic realm proxy
acl authenticated proxy_auth REQUIRED
http_access allow authenticated
http_access deny all
access_log stdio:/var/log/squid/access.log
cache deny all
CONF

htpasswd -b -c /etc/squid/passwd "$PROXY_USER" "$PROXY_PASS"
chown proxy:proxy /etc/squid/passwd
chmod 640 /etc/squid/passwd
systemctl restart squid

cat >/var/log/proxy-creds <<CREDS
PROXY_USER=$PROXY_USER
PROXY_PASS=$PROXY_PASS
CREDS
