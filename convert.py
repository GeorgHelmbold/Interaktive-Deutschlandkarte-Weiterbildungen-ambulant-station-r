import pandas as pd

xlsx = pd.ExcelFile('Weiterbildungsbefugnisse Stand 72025_Tariq.xlsx')

for blatt in xlsx.sheet_names:
    df = pd.read_excel(xlsx, sheet_name=blatt)
    df.to_csv(f'{blatt}.csv', index=False)