#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

# VENV nur neu erstellen, wenn es nicht existiert (spart Zeit beim Neustart)
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

# Prüfen auf genau eine Excel-Datei
shopt -s nullglob
excel_dateien=("$PROJECT_DIR"/*.xlsx)
if (( ${#excel_dateien[@]} != 1 )); then
    printf 'Fehler: Es muss genau eine Excel-Datei (*.xlsx) im Projektordner liegen, gefunden wurden %d.\n' "${#excel_dateien[@]}" >&2
    exit 1
fi

sudo systemctl stop fastapi.service || true

trap 'status=$?; if (( status != 0 )); then echo "Update fehlgeschlagen; starte den Dienst wieder." >&2; sudo systemctl start fastapi.service || echo "Fehler: Dienst konnte nicht gestartet werden." >&2; fi; exit "$status"' EXIT

# Daten konvertieren und Tabellen erstellen
python convert.py
python createtables.py

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

sudo systemctl restart fastapi.service || true
echo "Daten initialisiert und Server (falls aktiv) neu gestartet!"