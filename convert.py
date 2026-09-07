from pathlib import Path
import sys
import pandas as pd

projektordner = Path(__file__).resolve().parent
excel_dateien = sorted(projektordner.glob('*.xlsx'))

if len(excel_dateien) != 1:
    print(
        f"Fehler: Es muss genau eine Excel-Datei (*.xlsx) im Projektordner "
        f"liegen, gefunden wurden {len(excel_dateien)}.",
        file=sys.stderr,
    )
    sys.exit(1)

xlsx = pd.ExcelFile(excel_dateien[0])

for blatt in xlsx.sheet_names:
    df = pd.read_excel(xlsx, sheet_name=blatt)
    df.to_csv(f'{blatt}.csv', index=False)