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

    url = "https://eu1.locationiq.com/v1/search"
    params = {
        "key": geo_config.locationiq_api_key,
        "q": query,                  # String unberührt lassen!
        "countrycodes": "de",        # Beschränkt die Suche strikt auf Deutschland (ISO 3166-1 alpha-2)
        "format": "json",
        "limit": 1
    }

    wait = 0.3
    for versuch in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"⏳ Netzwerkfehler bei '{query}': {e} — warte {wait}s (Versuch {versuch + 1}/{max_retries})")
            time.sleep(wait)
            wait *= 2
            continue

        if resp.status_code == 429:
            print(f"⏳ Rate-Limit erreicht bei '{query}', warte {wait}s (Versuch {versuch + 1}/{max_retries})")
            time.sleep(wait)
            wait *= 2
            continue

        if resp.status_code != 200 or not resp.json():
            geo_cache[query] = None
            return None

        data = resp.json()[0]
        result = (float(data["lat"]), float(data["lon"]))
        geo_cache[query] = result
        time.sleep(0.8)
        return result

    geo_cache[query] = None
    return None


FALLBACK_LAT, FALLBACK_LNG = 50.970097, 9.687096  # Bad Hersfeld – bekannter LocationIQ-Fallback

def geocode(kreis: str, bundesland: str, einrichtung: str):
    adresse = extract_adresse(einrichtung)
    kreis_query = f"{kreis}, {bundesland}"

    koordinaten = None
    if len(adresse) >= 6:
        koordinaten = geocode_query(adresse)

    if koordinaten == (FALLBACK_LAT, FALLBACK_LNG):
        print(f"⚠️  LocationIQ-Ersatzkoordinate für '{adresse}' erhalten — versuche den Kreis.")
        koordinaten = None

    if koordinaten is None:
        print(f"⚠️  Adress-Geocoding fehlgeschlagen für '{adresse}' — Fallback auf Kreis: {kreis_query}")
        koordinaten = geocode_query(kreis_query)

    if koordinaten == (FALLBACK_LAT, FALLBACK_LNG):
        print(f"⚠️  LocationIQ-Ersatzkoordinate auch für den Kreis erhalten: {kreis_query}")

    if koordinaten is None:
        print(f"❌ Auch Kreis-Fallback fehlgeschlagen: {kreis}, {bundesland}")

    return koordinaten

def maketables(bundesland):
    with open(f'{bundesland}.csv', encoding="utf-8") as csvdatei:
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
            if zeilennr == 0:
                if set(row) != set(spaltennamen):
                    raise ValueError(
                        f"{bundesland}.csv hat unerwartete Spaltennamen: {row}"
                    )
                spalten_indizes = [row.index(name) for name in spaltennamen]
                drop_table = f'''
                DROP TABLE IF EXISTS "{bundesland}";
                '''
                cur.execute(drop_table)
                spalten_sql = ", ".join(f'"{name}" text' for name in spaltennamen)
                pk_spalten = ", ".join(f'"{name}"' for name in spaltennamen[-4:])
                querie = f'CREATE TABLE "{bundesland}" ({spalten_sql}, "lat" DOUBLE PRECISION, "lng" DOUBLE PRECISION, PRIMARY KEY ({pk_spalten}))'
                cur.execute(querie)
            else:
                attribut1, attribut2, attribut3, attribut4, attribut5, attribut6, attribut7 = (
                    row[index] for index in spalten_indizes
                )
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


def pruefe_duplikate():
    schluessel_spalten = [
        "Weiterbildungsermächtigung für Nephrologie",
        "Befugnis",
        "Angaben zur Person",
        "Einrichtung",
    ]

    for bundesland in bundesländer:
        with open(f'{bundesland}.csv', encoding="utf-8") as csvdatei:
            reader = csv.reader(csvdatei)
            kopfzeile = next(reader)
            indizes = [kopfzeile.index(spalte) for spalte in schluessel_spalten]
            gesehen = {}

            for zeilennr, row in enumerate(reader, start=2):
                if row == kopfzeile:
                    continue
                schluessel = tuple(row[index] for index in indizes)
                if schluessel in gesehen:
                    raise ValueError(
                        f"Doppelter Primärschlüssel in {bundesland}.csv, "
                        f"Zeilen {gesehen[schluessel]} und {zeilennr}."
                    )
                gesehen[schluessel] = zeilennr


pruefe_duplikate()

drop_view = '''
    DROP MATERIALIZED VIEW IF EXISTS alle_bundesländer;
'''
cur.execute(drop_view)


cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

for bundesland in bundesländer:
    maketables(bundesland)

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