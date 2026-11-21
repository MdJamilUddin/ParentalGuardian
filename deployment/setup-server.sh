#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu 22.04/24.04 VPS. Run as root from the unzipped project:
#     bash /root/ParentalGuardian/deployment/setup-server.sh
# What it does: system updates, firewall (22/80/443), automatic security updates, fail2ban, Docker,
# a non-root "guardian" user, SSH hardening (only if your root login already uses an SSH key),
# and copies the project to /home/guardian/app.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Run as root."; exit 1; }
APP_USER="guardian"
SRC="$(cd "$(dirname "$0")/.." && pwd)"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y upgrade
apt-get install -y ufw fail2ban unattended-upgrades curl ca-certificates unzip git

# firewall: SSH, HTTP, HTTPS only
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# automatic security updates
dpkg-reconfigure -f noninteractive unattended-upgrades

# Docker (official convenience script)
if ! command -v docker >/dev/null; then curl -fsSL https://get.docker.com | sh; fi

# non-root user that can run Docker
id "$APP_USER" &>/dev/null || adduser --disabled-password --gecos "" "$APP_USER"
usermod -aG docker "$APP_USER"
if [ -s /root/.ssh/authorized_keys ]; then
  mkdir -p /home/$APP_USER/.ssh
  cp /root/.ssh/authorized_keys /home/$APP_USER/.ssh/authorized_keys
  chown -R $APP_USER:$APP_USER /home/$APP_USER/.ssh
  chmod 700 /home/$APP_USER/.ssh && chmod 600 /home/$APP_USER/.ssh/authorized_keys
  # key-only logins (root may still log in with a key, never with a password)
  cat > /etc/ssh/sshd_config.d/99-guardian.conf <<'CONF'
PasswordAuthentication no
PermitRootLogin prohibit-password
CONF
  sshd -t && systemctl restart ssh
else
  echo "NOTE: root has no SSH key, so password login was left enabled. Add an SSH key, then rerun this script."
fi

# project files
if [ ! -d /home/$APP_USER/app ]; then cp -a "$SRC" /home/$APP_USER/app; fi
chown -R $APP_USER:$APP_USER /home/$APP_USER/app

echo
echo "Done. Next:  ssh $APP_USER@<server-ip>   then   cd ~/app/deployment && cp .env.example .env"
