#!/bin/bash
# Deploy the Linux collector on ANY Debian-based host you want log
# visibility from - your Debian 13 server, Kali, or any future Linux box.
# Run as root (or with sudo) ON THAT HOST ITSELF, not on the KKSIEM box.
#
# Usage:
#   sudo HOST_NAME=debian-srv01 HOST_IP=192.168.30.20 HOST_SEGMENT=OPT2 \
#        HOST_SOURCE_TYPE=linux_server KAFKA_BROKERS=192.168.50.X:9092 \
#        ./deploy_linux_collector.sh
#
# Example for Kali used as an admin/maintenance box (not the attack range):
#   sudo HOST_NAME=kali-admin HOST_IP=192.168.30.30 HOST_SEGMENT=OPT2 \
#        HOST_SOURCE_TYPE=linux_server KAFKA_BROKERS=192.168.50.X:9092 \
#        ./deploy_linux_collector.sh
#
# All five env vars are required - the script refuses to proceed with
# defaults, since a wrong host/IP/segment silently mislabels every event
# from this machine (see schemas/canonical.py's source identity
# requirements). HOST_SOURCE_TYPE must be a value SourceType accepts -
# currently linux_server is the only Linux option (see
# kksiem/schemas/canonical.py); attacker-vs-admin distinction belongs in
# the Asset Registry's asset_type/criticality fields, not here.

set -euo pipefail

if [[ -z "${HOST_NAME:-}" || -z "${HOST_IP:-}" || -z "${HOST_SEGMENT:-}" || -z "${HOST_SOURCE_TYPE:-}" || -z "${KAFKA_BROKERS:-}" ]]; then
    echo "ERROR: HOST_NAME, HOST_IP, HOST_SEGMENT, HOST_SOURCE_TYPE, and KAFKA_BROKERS must all be set."
    echo "Example: sudo HOST_NAME=debian-srv01 HOST_IP=192.168.30.20 HOST_SEGMENT=OPT2 \\"
    echo "              HOST_SOURCE_TYPE=linux_server KAFKA_BROKERS=192.168.50.10:9092 $0"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: must run as root (needs to read /var/log/audit/audit.log and install packages)."
    exit 1
fi

echo "==> Installing auditd (provides /var/log/audit/audit.log)"
apt-get update -qq
apt-get install -y auditd audispd-plugins

echo "==> Ensuring auditd is enabled and running"
systemctl enable auditd
systemctl start auditd

echo "==> Adding baseline audit rules (auth events, sudo use)"
# -w watches a file/dir; -a always,exit tracks syscalls. These are a
# starting set aligned with what normalizer/parsers.py::parse_linux_auditd
# expects to see (USER_AUTH, SYSCALL with exe= field).
cat > /etc/audit/rules.d/kksiem.rules <<'EOF'
-w /etc/passwd -p wa -k kksiem_identity
-w /etc/shadow -p wa -k kksiem_identity
-w /etc/sudoers -p wa -k kksiem_privilege
-a always,exit -F arch=b64 -S execve -k kksiem_exec
EOF
augenrules --load || auditctl -R /etc/audit/rules.d/kksiem.rules

echo "==> Verifying audit.log is readable"
if [[ ! -r /var/log/audit/audit.log ]]; then
    echo "ERROR: /var/log/audit/audit.log not readable even as root. Check auditd started correctly:"
    systemctl status auditd --no-pager
    exit 1
fi

echo "==> Installing Fluent Bit"
if ! command -v fluent-bit &> /dev/null; then
    curl -sSL https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
fi

echo "==> Deploying KKSIEM Fluent Bit config"
mkdir -p /etc/fluent-bit /var/lib/fluent-bit
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/../kksiem/collectors/configs/fluent-bit-linux.conf" /etc/fluent-bit/kksiem-linux.conf

echo "==> Locating the fluent-bit binary installed by install.sh"
FLUENT_BIT_BIN="$(command -v fluent-bit || echo /opt/fluent-bit/bin/fluent-bit)"
if [[ ! -x "$FLUENT_BIT_BIN" ]]; then
    echo "ERROR: could not find fluent-bit binary. Check install.sh output above for the actual path,"
    echo "then set FLUENT_BIT_BIN manually before re-running this script."
    exit 1
fi
echo "    Found: $FLUENT_BIT_BIN"

if [[ ! -f /etc/systemd/system/fluent-bit.service && ! -f /lib/systemd/system/fluent-bit.service ]]; then
    echo "ERROR: no fluent-bit.service unit found - the package install may have used a"
    echo "different service name on this distro. Run 'systemctl list-units | grep fluent'"
    echo "to find it, then adjust this script's service name accordingly."
    exit 1
fi

echo "==> Writing systemd environment override (HOST_NAME/HOST_IP/HOST_SEGMENT/HOST_SOURCE_TYPE/KAFKA_BROKERS)"
mkdir -p /etc/systemd/system/fluent-bit.service.d
cat > /etc/systemd/system/fluent-bit.service.d/kksiem-env.conf <<EOF
[Service]
Environment="HOST_NAME=${HOST_NAME}"
Environment="HOST_IP=${HOST_IP}"
Environment="HOST_SEGMENT=${HOST_SEGMENT}"
Environment="HOST_SOURCE_TYPE=${HOST_SOURCE_TYPE}"
Environment="KAFKA_BROKERS=${KAFKA_BROKERS}"
ExecStart=
ExecStart=${FLUENT_BIT_BIN} -c /etc/fluent-bit/kksiem-linux.conf
EOF

echo "==> Starting Fluent Bit"
systemctl daemon-reload
systemctl enable fluent-bit
systemctl restart fluent-bit

sleep 2
if systemctl is-active --quiet fluent-bit; then
    echo "==> Fluent Bit is running. Tailing its log for 5s to confirm output:"
    timeout 5 journalctl -u fluent-bit -f --no-pager || true
else
    echo "ERROR: Fluent Bit failed to start. Check: journalctl -u fluent-bit -n 50 --no-pager"
    exit 1
fi

echo ""
echo "==> Done. Verify events are landing in Kafka from the KKSIEM box with:"
echo "    docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic raw.linux --from-beginning --max-messages 5"
