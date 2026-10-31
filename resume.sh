#!/usr/bin/env bash

set -Eeuo pipefail

sudo systemctl start fastapi.service
echo "Systemd-Dienst fastapi.service wurde gestartet."
