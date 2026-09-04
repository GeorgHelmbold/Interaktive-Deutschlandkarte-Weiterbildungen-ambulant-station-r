# Interaktive Deutschlandkarte

Webanwendung zur Darstellung von weiterbildungsermächtigten Einrichtungen für
Nephrologie in Deutschland. Die Anwendung stellt die Daten als Karte, als
Gesamttabelle und nach Bundesland gefiltert bereit.

## Voraussetzungen

- Python 3.10 oder neuer
- PostgreSQL
- ein LocationIQ API-Key für die Adress-Geocodierung
- genau eine Excel-Datei mit der Endung `.xlsx` im Projektordner

Die Anwendung erwartet eine `.env`-Datei im Projektordner. Sie wird nicht ins
Repository eingecheckt.

## Konfiguration

Beispiel für `.env`:

```dotenv
host=localhost
port=5432
database=aerzte
db_username=defuser
password=DEIN_PASSWORT
LOCATIONIQ_API_KEY=DEIN_LOCATIONIQ_API_KEY
```

Die Namen der Variablen entsprechen den Einstellungen in `entities.py`. Der
PostgreSQL-Benutzer muss die Datenbanktabellen und die materialisierte Ansicht
erstellen bzw. löschen dürfen.

## Installation und Start

Für den vollständigen Standard-Setup im Projektordner genügt:

```bash
./start.sh
```

Dieser Start ist der "Neuanfang": Er erstellt die virtuelle Umgebung neu, lädt
Abhängigkeiten, konvertiert die `.xlsx`-Datei in CSV-Dateien, baut die
Datenbanktabellen neu auf und startet danach den Server.

Wenn du nur die bereits vorbereitete Umgebung starten willst, ohne die Datenbank
und CSV-Dateien erneut neu aufzubauen, kannst du direkt dieses Skript ausführen:

```bash
./run.sh
```

`run.sh` ist der "Schnellstart": Es aktiviert die vorhandene `.venv`, setzt
bei Bedarf die Ausführungserlaubnis für sich selbst und startet nur die
FastAPI-Anwendung. Es führt keine Datenkonvertierung und keinen Neuaufbau der
Datenbank durch.

`start.sh` ist für einen vollständigen Datenimport gedacht. Bei jedem Aufruf
wird die einzige Excel-Datei im Projektordner erneut in CSV-Dateien umgewandelt
und die Datenbank anschließend vollständig neu aufgebaut. Gibt es keine oder
mehr als eine `.xlsx`-Datei, wird der Start mit einer Fehlermeldung abgebrochen.

`start.sh` führt diese Schritte aus:

1. Es erstellt `.venv` und aktiviert die virtuelle Umgebung.
2. Es installiert bzw. aktualisiert die Pakete aus `requirements.txt`.
3. Es führt `convert.py` aus und erzeugt die CSV-Dateien der Bundesländer.
4. Es führt `createtables.py` aus und baut die PostgreSQL-Daten neu auf.
5. Es startet die FastAPI-Anwendung mit Uvicorn.

Die Anwendung ist anschließend unter http://127.0.0.1:8000/karte erreichbar.
Die interaktive API-Dokumentation befindet sich unter
http://127.0.0.1:8000/docs.

Zum Beenden des Servers `Ctrl+C` drücken. Die venv wird beim nächsten Start
wiederverwendet. Manuell verlassen lässt sie sich mit:

```bash
deactivate
```

### Manueller Start

Falls die Schritte einzeln ausgeführt werden sollen:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python convert.py
python createtables.py
uvicorn main:app --reload
```

## Datenverarbeitung

### Excel in CSV-Dateien umwandeln

`convert.py` sucht genau eine `.xlsx`-Datei im Projektordner. Der Dateiname ist
beliebig. Die Arbeitsblätter werden eingelesen und als CSV-Dateien gespeichert:

```bash
source .venv/bin/activate
python convert.py
```

Die erzeugten CSV-Dateien werden im Projektordner abgelegt und sind wegen ihrer
Größe vom Repository ausgeschlossen. Die Excel-Datei ist nicht Bestandteil des
Repositories und muss separat bereitgestellt werden. Im Projektordner darf für
den automatischen Start genau eine `.xlsx`-Datei liegen.

### PostgreSQL-Tabellen erstellen

```bash
source .venv/bin/activate
python createtables.py
```

Das Skript verarbeitet alle Bundesländer-CSV-Dateien, erstellt für jedes
Bundesland eine Tabelle und ergänzt die Spalten `lat` und `lng`. Für die
Adresskoordinaten wird LocationIQ verwendet. Danach wird die materialisierte
Ansicht `alle_bundesländer` neu erstellt.

**Achtung:** Die Tabellen und die Ansicht werden bei jedem Lauf gelöscht und
vollständig neu aufgebaut. Das Skript benötigt eine aktive PostgreSQL-Verbindung
und kann wegen der externen Geocoding-Anfragen einige Zeit laufen. Auch
`start.sh` führt diesen vollständigen Neuaufbau bei jedem Start aus.

## Wichtige Routen

| Route | Zweck |
| --- | --- |
| `/karte` | Interaktive Deutschlandkarte |
| `/data` | Tabelle aller Bundesländer |
| `/data/{bundesland}` | Tabelle eines Bundeslandes |
| `/suche` | Suche innerhalb eines Bundeslandes |
| `/suche-alle` | Suche über alle Bundesländer |
| `/api/standorte` | Standortdaten als JSON |
| `/docs` | Automatische FastAPI-Dokumentation |

## Projektstruktur

```text
main.py                 FastAPI-Anwendung und Routen
entities.py             Konfiguration für Datenbank und LocationIQ
convert.py              Excel-zu-CSV-Konvertierung
createtables.py         Tabellen, Geocoding und materialisierte Ansicht
start.sh                Einrichtung der venv und Anwendungsstart
requirements.txt        Python-Abhängigkeiten
templates/              HTML-Templates
static/                 CSS und JavaScript
```

## Fehlerbehebung

- **Fehlende Einstellungen:** `.env` prüfen; alle sechs Konfigurationswerte
	müssen vorhanden sein.
- **Datenbankfehler:** Prüfen, ob PostgreSQL läuft, die Zugangsdaten stimmen
	und der Benutzer Tabellen anlegen darf.
- **Fehlende oder mehrere Excel-Dateien:** Genau eine `.xlsx`-Datei in den
	Projektordner legen. Ihr Dateiname ist beliebig.
- **Kein Geocoding:** LocationIQ-Key, Internetverbindung und API-Limit prüfen.
