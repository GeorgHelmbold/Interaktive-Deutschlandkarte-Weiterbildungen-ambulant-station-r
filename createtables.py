import csv
import time
import requests
import psycopg2
import sys
import re
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

geo_cache = {}  # query-String -> (lat, lng) oder None
http_session = requests.Session()

def extract_adresse(einrichtung: str) -> str:
    if ',' not in einrichtung:
        return ""

    ohne_klammern = re.sub(r'\([^()]*\)', '', einrichtung)
    ohne_klammern = re.sub(r'\s+', ' ', ohne_klammern).strip()
    teile = [t.strip() for t in ohne_klammern.split(',')]
    letzte_zwei = teile[-2:]

    if not re.match(r'^\d{5}\s', letzte_zwei[-1]):
        print(
            "WARNUNG: Adressextraktion auffällig – letztes Segment beginnt nicht mit PLZ: "
            f"einrichtung={einrichtung!r} -> extrahiert={letzte_zwei!r}"
        )

    adresse = ', '.join(letzte_zwei)
    return adresse

def geocode_query(query: str, max_retries: int = 5):
    if query in geo_cache:
        return geo_cache[query]
    if max_retries < 1:
        raise ValueError("max_retries muss mindestens 1 sein")

    url = "https://gateway.mapmetrics-atlas.net/osm-geocode/"
    params = {
        "token": geo_config.mapatlas_api_key,
        "q": query,
        "limit": 1,
    }

    wait = 0.3
    for versuch in range(max_retries):
        try:
            resp = http_session.get(url, params=params, timeout=(3.0, 10.0))
        except requests.exceptions.RequestException as e:
            print(
                f"⏳ Netzwerkfehler bei '{query}' ({type(e).__name__}) — "
                f"warte {wait}s (Versuch {versuch + 1}/{max_retries})"
            )
            time.sleep(wait)
            wait *= 2
            continue

        # GEÄNDERT: Auch bei HTTP 5xx (Server-Aussetzer von MapMetrics) automatisch wiederholen
        if resp.status_code in (429, 500, 502, 503, 504):
            print(f"⏳ HTTP {resp.status_code} bei '{query}', warte {wait}s (Versuch {versuch + 1}/{max_retries})")
            time.sleep(wait)
            wait *= 2
            continue

        if resp.status_code in (401, 403):
            raise RuntimeError(
                f"Geocoding für '{query}' wegen HTTP {resp.status_code} abgelehnt. "
                "Prüfe MAPATLAS_API_KEY in .env und verwende einen gültigen API-Token "
                "aus dem MapAtlas/MapMetrics-Portal."
            ) from None

        # GEÄNDERT: Bei sonstigen Fehlern nicht crashen, sondern None zurückgeben (aktiviert den Kreis-Fallback)
        if resp.status_code != 200:
            print(f"⚠️ Geocoding für '{query}' wegen HTTP {resp.status_code} fehlgeschlagen.")
            geo_cache[query] = None
            return None
            
        data = resp.json()
        
        # GeoJSON auf leere Ergebnisse prüfen
        if not data.get("features"):
            geo_cache[query] = None
            return None

        # GeoJSON liefert die Koordinaten als [Längengrad, Breitengrad]
        lon, lat = data["features"][0]["geometry"]["coordinates"]
        result = (float(lat), float(lon))
        
        geo_cache[query] = result
        time.sleep(0.2)
        return result

    geo_cache[query] = None
    return None


FALLBACK_LAT, FALLBACK_LNG = 50.970097, 9.687096  # Bad Hersfeld – bekannter Fallback

def geocode(kreis: str, bundesland: str, einrichtung: str):
    adresse = extract_adresse(einrichtung)

    koordinaten = None
    if len(adresse) >= 6:
        koordinaten = geocode_query(adresse)

    if koordinaten is None:
        print(f"⚠️  Adress-Geocoding fehlgeschlagen für '{adresse}' — Fallback auf Kreis: {kreis}, {bundesland}")
        koordinaten = geocode_query(f"{kreis}, {bundesland}")

    if koordinaten is None:
        print(f"❌ Auch Kreis-Fallback fehlgeschlagen: {kreis}, {bundesland}")
    elif koordinaten == (FALLBACK_LAT, FALLBACK_LNG):
        print(f"⚠️  Fallback-Koordinate (Bad Hersfeld) erhalten für '{adresse or kreis}' — vermutlich fehlgeschlagenes Geocoding")

    return koordinaten

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
                pk_spalten = ", ".join(f'"{name}"' for name in spaltennamen[-2:])
                querie = f'CREATE TABLE "{bundesland}" ({spalten_sql}, "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, PRIMARY KEY ({pk_spalten}))'
                cur.execute(querie)
            else:
                if attribut6 == "Angaben zur Person":
                    continue
                kreis = attribut2
                einrichtung = attribut7
                koordinaten = geocode(kreis, bundesland, einrichtung)
                lat, lng = koordinaten if koordinaten else (None, None)

                insert_query = f'''
                INSERT INTO "{bundesland}" ({spalten_sql_names}, "lat", "lng")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                '''
                cur.execute(insert_query, (attribut1, attribut2, attribut3, attribut4, attribut5, attribut6, attribut7, lat, lng))
            zeilennr += 1


drop_view = '''
    DROP MATERIALIZED VIEW IF EXISTS alle_bundesländer;
'''
cur.execute(drop_view)

cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
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

# Trigram-Indizes für schnelle Teilwortsuche (ILIKE '%wort%')
cur.execute('CREATE INDEX idx_view_person_trgm ON alle_bundesländer USING gin ("Angaben zur Person" gin_trgm_ops);')
cur.execute('CREATE INDEX idx_view_einrichtung_trgm ON alle_bundesländer USING gin ("Einrichtung" gin_trgm_ops);')
cur.execute('CREATE INDEX idx_view_kreis_trgm ON alle_bundesländer USING gin ("Kreis" gin_trgm_ops);')
# B-Tree für exakte Filterung (Radio-Button ambulant/stationär)
cur.execute('CREATE INDEX idx_view_typ ON alle_bundesländer USING gin ("ambulant/stationär/niedergelassen" gin_trgm_ops);')
conn.commit()

cur.close()
conn.close()