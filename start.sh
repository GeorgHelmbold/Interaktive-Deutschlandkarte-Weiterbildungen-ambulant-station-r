#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

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
exec uvicorn main:app --reload