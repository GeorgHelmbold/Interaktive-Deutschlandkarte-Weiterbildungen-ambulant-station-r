#!/usr/bin/env bash

set -Eeuo pipefail

# Aktuellen Ordner und Benutzer ermitteln
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$USER"

echo "Erstelle Systemd-Service für Benutzer: $CURRENT_USER im Pfad: $PROJECT_DIR"

# Service-Datei dynamisch generieren und mit sudo-Rechten in /etc/systemd/system/ schreiben
cat <<EOF | sudo tee /etc/systemd/system/fastapi.service > /dev/null
[Unit]
Description=FastAPI Server
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/bin/bash $PROJECT_DIR/run.sh
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
EOF

# Systemd aktualisieren und Service starten
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl start fastapi.service

echo "Service wurde erfolgreich eingerichtet und gestartet!"