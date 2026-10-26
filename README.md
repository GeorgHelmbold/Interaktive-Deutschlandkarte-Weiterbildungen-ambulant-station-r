# Interaktive Deutschlandkarte

## Voraussetzungen

- Python 3.10 oder neuer
- PostgreSQL
- ein API-Key für die Adress-Geocodierung
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
MAPATLAS_API_KEY=DEIN_API_KEY
```

Die Namen der Variablen entsprechen den Einstellungen in `entities.py`. Der
PostgreSQL-Benutzer muss die Datenbanktabellen und die materialisierte Ansicht
erstellen bzw. löschen dürfen.

## Installation und Start (Systemd)

Die Anwendung ist so konfiguriert, dass sie als permanenter Hintergrunddienst (Systemd-Service) auf einem Linux-Server läuft. Die Einrichtung erfolgt in drei Schritten.

### 1. Erstmalige Einrichtung (Setup)

Wenn der Server komplett neu aufgesetzt wird, gehe in dieser Reihenfolge vor:

1. **Daten bereitstellen:** Lege genau eine `.xlsx`-Datei in den Projektordner.
2. **Datenbank erstellen** Erstelle die PostgreSQL Datenbank und erstelle die .env, wie erklärt.
2. **Datenbank aufbauen:** Führe das Start-Skript aus. Dies erstellt die virtuelle Umgebung, installiert alle Abhängigkeiten, konvertiert die Excel-Datei, baut die PostgreSQL-Tabellen auf und löscht temporäre Dateien:
   ```bash
   ./start.sh
   ```
3. **Dienst installieren (Einmalig):** Richte den Systemd-Service ein, der den FastAPI-Server ab sofort steuert und im Hintergrund am Laufen hält:
   ```bash
   ./install_service.sh
   ```

Der Server ist nun unter http://127.0.0.1:8000/karte erreichbar. Die interaktive API-Dokumentation befindet sich unter http://127.0.0.1:8000/docs.

### 2. Daten aktualisieren (Alltäglicher Workflow)

Wenn es neue Daten gibt, musst du den Service nicht manuell stoppen. 

1. Tausche einfach die `.xlsx`-Datei im Projektordner aus.
2. Führe `./start.sh` aus. 

Das Skript bereitet die neue Datenbank vor und teilt Systemd am Ende automatisch mit, dass der Server mit den neuen Daten neu gestartet werden soll.

### 3. Server-Steuerung & Logs

Da der Server im Hintergrund läuft (gesteuert durch `run.sh`), nutzt du zur Steuerung nun die systemeigenen Befehle:

- **Status prüfen:** `sudo systemctl status fastapi.service`
- **Server stoppen:** `sudo systemctl stop fastapi.service`
- **Server starten:** `sudo systemctl start fastapi.service`

**Live-Logs ansehen:**
Fehlermeldungen und Konsolenausgaben von Uvicorn werden von Systemd gesammelt. Du kannst sie dir in Echtzeit ansehen mit:
```bash
sudo journalctl -u fastapi.service -f
```
*(Beenden der Ansicht mit `Ctrl+C`)*

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
Adresskoordinaten wird die MapAtlas-Geocoding-API verwendet. Deren Gateway-URL,
Pfad und Authentifizierungsparameter müssen der aktuellen
[MapAtlas-OpenAPI-Spezifikation](https://mapatlas.eu/openapi.json) entsprechen.
Danach wird die materialisierte Ansicht `alle_bundesländer` neu erstellt.

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
entities.py             Konfiguration für Datenbank und Geolocation
convert.py              Excel-zu-CSV-Konvertierung
createtables.py         Tabellen, Geocoding und materialisierte Ansicht
install_service.sh      (Einmalig) Erstellt den Systemd-Hintergrunddienst
start.sh                Daten-Update: VENV laden, Tabellen neu bauen, Service neustarten
run.sh                  Wird von Systemd genutzt, um den reinen Webserver zu starten
requirements.txt        Python-Abhängigkeiten
templates/              HTML-Templates
static/                 CSS und JavaScript
```

## Fehlerbehebung

- **Fehlende Einstellungen:** `.env` prüfen; alle sechs Konfigurationswerte müssen vorhanden sein.
- **Datenbankfehler:** Prüfen, ob PostgreSQL läuft, die Zugangsdaten stimmen und der Benutzer Tabellen anlegen darf.
- **Fehlende oder mehrere Excel-Dateien:** Genau eine `.xlsx`-Datei in den Projektordner legen. Ihr Dateiname ist beliebig.
- **Kein Geocoding:** API-Key, Internetverbindung, DNS-Auflösung des Geocoding-Hosts und API-Limit prüfen. Wenn die Verbindung nach mehreren Versuchen weiterhin fehlschlägt oder die API dauerhaft einen HTTP-Fehler meldet, wird der Tabellenaufbau vor dem Commit abgebrochen statt unvollständige Koordinaten zu speichern; bestehende Tabellen und die materialisierte Ansicht bleiben erhalten. Behebe die Ursache und starte `./start.sh` erneut.
- **Server startet nicht (Systemd):** Nutze `sudo journalctl -u fastapi.service -n 50`, um dir die letzten 50 Zeilen der Server-Fehlermeldungen anzeigen zu lassen.
