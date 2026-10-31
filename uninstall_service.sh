#!/usr/bin/env bash

set -Eeuo pipefail

SERVICE_FILE="/etc/systemd/system/fastapi.service"

if sudo test -f "$SERVICE_FILE"; then
    sudo systemctl disable --now fastapi.service
    sudo rm "$SERVICE_FILE"
    sudo systemctl daemon-reload
    echo "Systemd-Dienst entfernt. Projektdateien und Datenbank bleiben erhalten."
else
    echo "Systemd-Dienst ist nicht installiert."
fi
