#!/usr/bin/env bash

set -Eeuo pipefail

sudo systemctl stop fastapi.service
echo "Systemd-Dienst fastapi.service wurde gestoppt."
