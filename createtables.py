import csv
import time
import requests
import psycopg2
import sys
from entities import ConnectionConfig, GeocodingConfig

config = ConnectionConfig()
geo_config = GeocodingConfig()

conn = psycopg2.connect(
    host=config.host,
    port=config.port,
    dbname=config.database,
    user=config.db_username,
    password=config.password
)
cur = conn.cursor()

bundesländer = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]

geo_cache = {}  # (bundesland, kreis) -> (lat, lng) oder None

def geocode(kreis: str, bundesland: str, max_retries: int = 5):
    key = (bundesland, kreis)
    if key in geo_cache:
        return geo_cache[key]

    url = "https://us1.locationiq.com/v1/search"
    params = {
        "key": geo_config.locationiq_api_key,
        "q": f"{kreis}, {bundesland}, Germany",
        "format": "json",
        "limit": 1
    }

    wait = 0.5  # Basis-Wartezeit
    for versuch in range(max_retries):
        resp = requests.get(url, params=params)

        if resp.status_code == 429:
            print(f"⏳ Rate-Limit erreicht bei '{kreis}, {bundesland}', warte {wait}s (Versuch {versuch + 1}/{max_retries})")
            time.sleep(wait)
            wait *= 2  # exponentielles Backoff: 0.5 → 1.0 → 2.0 → 4.0 → 8.0
            continue

        if resp.status_code != 200 or not resp.json():
            print(f"⚠️  Kein Geocoding-Treffer für: {kreis}, {bundesland} — Status {resp.status_code}: {resp.text}")
            geo_cache[key] = None
            return None

        data = resp.json()[0]
        result = (float(data["lat"]), float(data["lon"]))
        geo_cache[key] = result
        time.sleep(0.5)  # normale Pause zwischen erfolgreichen Requests
        return result

    print(f"❌ Geocoding endgültig fehlgeschlagen nach {max_retries} Versuchen: {kreis}, {bundesland}")
    geo_cache[key] = None
    return None


def maketables(bundesland):
    with open(f'{bundesland}.csv') as csvdatei:
        csv_reader_object = csv.reader(csvdatei, delimiter=',')
        zeilennr = 0
        spaltennamen = ["Landesärztekammer", "Kreis", "ambulant/stationär/niedergelassen", "Weiterbildungsermächtigung für Nephrologie", "Befugnis", "Angaben zur Person", "Einrichtung"]
        spalten_sql_names = ", ".join(f'"{name}"' for name in spaltennamen)
        for row in csv_reader_object:
            if len(row) < 7:
                print("Tabelle hat unerwartet zu wenig Spalten")
                cur.close()
                conn.close()
                sys.exit()
            if len(row) > 7:
                print("Tabelle hat unerwartet zu viele Spalten")
                cur.close()
                conn.close()
                sys.exit()
            attribut1 = row[0]
            attribut2 = row[1]
            attribut3 = row[2]
            attribut4 = row[3]
            attribut5 = row[4]
            attribut6 = row[5]
            attribut7 = row[6]
            if zeilennr == 0:
                drop_table = f'''
                DROP TABLE IF EXISTS "{bundesland}";
                '''
                cur.execute(drop_table)
                spalten_sql = ", ".join(f'"{name}" text' for name in spaltennamen)
                pk_spalten = ", ".join(f'"{name}"' for name in spaltennamen[-5:])
                querie = f'CREATE TABLE "{bundesland}" ({spalten_sql}, "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, PRIMARY KEY ({pk_spalten}))'
                cur.execute(querie)
            else:
                kreis = attribut2
                koordinaten = geocode(kreis, bundesland)
                lat, lng = koordinaten if koordinaten else (None, None)

                insert_query = f'''
                INSERT INTO "{bundesland}" ({spalten_sql_names}, "lat", "lng")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                '''
                cur.execute(insert_query, (attribut1, attribut2, attribut3, attribut4, attribut5, attribut6, attribut7, lat, lng))
            zeilennr += 1


print(f"DEBUG: verwendeter Key = {geo_config.locationiq_api_key!r}")

drop_view = '''
    DROP MATERIALIZED VIEW IF EXISTS alle_bundesländer;
'''
cur.execute(drop_view)
conn.commit()

for bundesland in bundesländer:
    maketables(bundesland)
conn.commit()

union_parts = [
    f'SELECT *, \'{bundesland}\' AS bundesland FROM "{bundesland}"'
    for bundesland in bundesländer
]
view_query = "CREATE MATERIALIZED VIEW alle_bundesländer AS\n" + "\nUNION ALL\n".join(union_parts) + ";"
cur.execute(view_query)
conn.commit()

cur.close()
conn.close()