#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

chmod +x "$PROJECT_DIR/run.sh"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

shopt -s nullglob
excel_dateien=("$PROJECT_DIR"/*.xlsx)
if (( ${#excel_dateien[@]} != 1 )); then
	printf 'Fehler: Es muss genau eine Excel-Datei (*.xlsx) im Projektordner liegen, gefunden wurden %d.\n' "${#excel_dateien[@]}" >&2
	exit 1
fi

python convert.py
python createtables.py

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
rm -- "${bundesland_csv_dateien[@]}"

uvicorn main:app --host 0.0.0.0 --port 8000