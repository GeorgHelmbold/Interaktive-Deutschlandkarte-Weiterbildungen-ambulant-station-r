#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

# VENV nur neu erstellen, wenn es nicht existiert (spart Zeit beim Neustart)
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Erstelle virtuelle Umgebung und installiere Abhängigkeiten ..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo "Virtuelle Umgebung bereit."
else
    echo "[1/4] Verwende vorhandene virtuelle Umgebung."
    source "$VENV_DIR/bin/activate"
fi

# Prüfen auf genau eine Excel-Datei
shopt -s nullglob
excel_dateien=("$PROJECT_DIR"/*.xlsx)
if (( ${#excel_dateien[@]} != 1 )); then
    printf 'Fehler: Es muss genau eine Excel-Datei (*.xlsx) im Projektordner liegen, gefunden wurden %d.\n' "${#excel_dateien[@]}" >&2
    exit 1
fi

service_installed() {
    [[ -f /etc/systemd/system/fastapi.service ]]
}

restart_service_on_error() {
    local status=$?
    trap - EXIT
    if (( status != 0 )) && service_installed; then
        echo "Update fehlgeschlagen; starte den Dienst wieder." >&2
        sudo systemctl start fastapi.service || echo "Fehler: Dienst konnte nicht gestartet werden." >&2
    fi
    exit "$status"
}

trap restart_service_on_error EXIT

if service_installed; then
    echo "Stoppe Systemd-Dienst ..."
    sudo systemctl stop fastapi.service
fi

# Daten konvertieren und Tabellen erstellen
echo "[2/4] Konvertiere Excel-Arbeitsblätter ..."
python convert.py
echo "Konvertierung abgeschlossen."
echo "[3/4] Importiere Daten und geocodiere Adressen ..."
python createtables.py
echo "Datenbankimport abgeschlossen."

# Temporäre CSVs löschen (-f verhindert Absturz bei fehlenden Dateien)
bundesland_csv_dateien=(
    "Baden-Württemberg.csv"
    "Bayern.csv"
    "Berlin.csv"
    "Brandenburg.csv"
    "Bremen.csv"
    "Hamburg.csv"
    "Hessen.csv"
    "Mecklenburg-Vorpommern.csv"
    "Niedersachsen.csv"
    "Nordrhein-Westfalen.csv"
    "Rheinland-Pfalz.csv"
    "Saarland.csv"
    "Sachsen.csv"
    "Sachsen-Anhalt.csv"
    "Schleswig-Holstein.csv"
    "Thüringen.csv"
)
rm -f "${bundesland_csv_dateien[@]}"

if service_installed; then
    echo "[4/4] Starte Systemd-Dienst neu ..."
    sudo systemctl restart fastapi.service
    echo "Daten initialisiert und Server neu gestartet!"
else
    echo "Datenbank initialisiert. Systemd-Neustart übersprungen."
fi