#!/bin/bash
# NordVPN Proxy Gateway Setup Script

# Update system
apt-get update
apt-get install -y curl tinyproxy

# Configure tinyproxy to allow external connections
cat > /etc/tinyproxy/tinyproxy.conf << 'EOF'
User tinyproxy
Group tinyproxy
Port 8888
Timeout 600
DefaultErrorFile "/usr/share/tinyproxy/default.html"
StatFile "/usr/share/tinyproxy/stats.html"
LogFile "/var/log/tinyproxy/tinyproxy.log"
LogLevel Info
PidFile "/run/tinyproxy/tinyproxy.pid"
MaxClients 100
MinSpareServers 5
MaxSpareServers 20
StartServers 10
MaxRequestsPerChild 0
# Allow all IPs (Cloud Run IPs are dynamic)
Allow 0.0.0.0/0
ViaProxyName "tinyproxy"
EOF

# Start tinyproxy
systemctl enable tinyproxy
systemctl start tinyproxy

# Install NordVPN
sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh) -n

# NordVPN will need manual login via: nordvpn login --token <TOKEN>
# After login: nordvpn connect

echo "Setup complete. Run: nordvpn login --token YOUR_TOKEN && nordvpn connect"
