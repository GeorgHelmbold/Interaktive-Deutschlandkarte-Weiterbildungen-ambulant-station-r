# Interaktive Deutschlandkarte

## Voraussetzungen

- Python 3.10 oder neuer
- PostgreSQL
- ein LocationIQ API-Key für den Datenimport und die damit verbundene Adress-Geocodierung
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

## Installation und Start (Systemd)

Die Anwendung ist so konfiguriert, dass sie als permanenter Hintergrunddienst (Systemd-Service) auf einem Linux-Server läuft. Die Einrichtung erfolgt in drei Schritten.

### 1. Erstmalige Einrichtung (Setup)

Wenn der Server komplett neu aufgesetzt wird, gehe in dieser Reihenfolge vor:

1. **Daten bereitstellen:** Lege genau eine `.xlsx`-Datei in den Projektordner.
2. **Datenbank konfigurieren:** Erstelle die PostgreSQL-Datenbank und die `.env`-Datei wie oben beschrieben.
3. **Datenbank aufbauen:** Führe das Start-Skript aus. Dies erstellt die virtuelle Umgebung, installiert alle Abhängigkeiten, konvertiert die Excel-Datei, baut die PostgreSQL-Tabellen auf und löscht temporäre Dateien:
   ```bash
   ./start.sh
   ```
4. **Dienst installieren (Einmalig):** Richte den Systemd-Service ein, der den FastAPI-Server ab sofort steuert und im Hintergrund am Laufen hält:
   ```bash
   ./install_service.sh
   ```

Der Server ist nun unter http://127.0.0.1:8000/ erreichbar. Die interaktive Karte mit Suche findest du unter `/chart`. Die API-Dokumentation unter `/docs` und das OpenAPI-Schema unter `/openapi.json` sind deaktiviert.
Antworten enthalten `X-Content-Type-Options: nosniff` und die
`Referrer-Policy: strict-origin-when-cross-origin`.

Leaflet und Markerbilder werden lokal ausgeliefert. Die Kartenkacheln kommen
weiterhin von `tile.openstreetmap.org`. Beim Kartenaufruf erhält OpenStreetMap
die IP-Adresse und die angefragten Kartenausschnitte. Die Datenschutzerklärung
unter `/datenschutz` ist derzeit ein Platzhalter und muss vor einer
Veröffentlichung mit den tatsächlichen Betreiber-, Hosting- und
Speicherangaben vervollständigt werden.

`run.sh` bindet den Webserver nur an `127.0.0.1`. Für den Zugriff über eine
öffentliche Domain ist ein entsprechend abgesicherter Reverse Proxy oder Tunnel erforderlich.

### 2. Daten aktualisieren (Alltäglicher Workflow)

Wenn es neue Daten gibt, übernimmt `start.sh` das Stoppen und Neustarten des Dienstes.

1. Tausche einfach die `.xlsx`-Datei im Projektordner aus.
2. Führe `./start.sh` aus. 

Das Skript stoppt den Dienst für den Neuaufbau und startet ihn anschließend mit den neuen Daten neu. Schlägt das Update fehl, versucht das Skript ebenfalls, den Dienst wieder zu starten.

Der Dienst läuft unter dem Benutzer, der `install_service.sh` ausführt. Die
Systemd-Unit enthält zusätzliche Schutzoptionen; der Projektordner muss für
diesen Benutzer lesbar sein.

### 3. Server-Steuerung & Logs

Da der Server im Hintergrund läuft (gesteuert durch `run.sh`), nutzt du zur Steuerung nun die systemeigenen Befehle:

- **Status prüfen:** `sudo systemctl status fastapi.service`
- **Server stoppen:** `sudo systemctl stop fastapi.service`
- **Server starten:** `sudo systemctl start fastapi.service`

`stop.sh` stoppt den Systemd-Dienst; `resume.sh` startet ihn wieder. `run.sh`
wird von systemd zum Starten des Servers verwendet. Für einen manuellen Start
kannst du `./run.sh` direkt ausführen; Uvicorn läuft dann im Vordergrund und
lässt sich mit `Ctrl+C` beenden. Starte es nicht manuell, während der
Systemd-Dienst bereits läuft.

**Live-Logs ansehen:**
Fehlermeldungen und Konsolenausgaben von Uvicorn werden von Systemd gesammelt. Du kannst sie dir in Echtzeit ansehen mit:
```bash
sudo journalctl -u fastapi.service -f
```
*(Beenden der Ansicht mit `Ctrl+C`)*

Den Systemd-Dienst entfernen, ohne Projektdateien oder Datenbank zu löschen:

```bash
./uninstall_service.sh
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
den automatischen Start genau eine `.xlsx`-Datei liegen. Die Arbeitsblätter
müssen nach den Bundesländern benannt sein, damit der Tabellenimport die
erzeugten CSV-Dateien findet.

### PostgreSQL-Tabellen erstellen

```bash
source .venv/bin/activate
python createtables.py
```

Das Skript verarbeitet alle Bundesländer-CSV-Dateien, erstellt für jedes
Bundesland eine Tabelle und ergänzt die Spalten `lat` und `lng`. Für die
Adresskoordinaten wird der LocationIQ-EU-Endpunkt verwendet. Die Adresse wird
anhand der Postleitzahl extrahiert; wenn die Adresssuche fehlschlägt oder die
bekannte Ersatzkoordinate liefert, wird der Kreis als Fallback abgefragt.
Erfolgreiche Geocoding-Abfragen werden in `geocode_cache.json` gespeichert und
bei späteren Importen wiederverwendet. Danach wird die materialisierte Ansicht
`alle_bundesländer` neu erstellt.

**Achtung:** Die Tabellen und die Ansicht werden bei jedem Lauf gelöscht und
vollständig neu aufgebaut. Das Skript benötigt eine aktive PostgreSQL-Verbindung
und kann wegen der externen Geocoding-Anfragen einige Zeit laufen. Auch
`start.sh` führt diesen vollständigen Neuaufbau bei jedem Start aus.
Vor dem Neuaufbau prüft das Skript doppelte Primärschlüssel. Die CSV-Spalten
werden anhand ihrer Namen zugeordnet; ihre Reihenfolge darf abweichen. CSV-Dateien
werden als UTF-8 gelesen.

## Wichtige Routen

| Route | Zweck |
| --- | --- |
| `/` | Startseite |
| `/chart` | Karte und gefilterte Ergebnistabelle |
| `/datenschutz` | Datenschutzhinweise |

## Projektstruktur

```text
main.py                 FastAPI-Anwendung und Routen
entities.py             Konfiguration für Datenbank und LocationIQ
convert.py              Excel-zu-CSV-Konvertierung
createtables.py         Tabellen, Geocoding und materialisierte Ansicht
install_service.sh      (Einmalig) Erstellt den Systemd-Hintergrunddienst
start.sh                Daten-Update: VENV laden, Tabellen neu bauen, Service neustarten
run.sh                  Wird von Systemd genutzt, um den reinen Webserver zu starten
stop.sh                 Stoppt den Systemd-Dienst
resume.sh               Startet den Systemd-Dienst
uninstall_service.sh    Entfernt den Systemd-Dienst
requirements.txt        Python-Abhängigkeiten
templates/              HTML-Templates
static/                 Datenschutzseite, CSS, JavaScript und lokale Kartenressourcen
```

## Fehlerbehebung

- **`Permission denied` beim Ausführen eines Skripts:** Ausführungsrechte setzen, z. B. mit `chmod +x ./*.sh`.
- **Fehlende Einstellungen:** `.env` prüfen; alle sechs Konfigurationswerte müssen vorhanden sein.
- **Datenbankfehler:** Prüfen, ob PostgreSQL läuft, die Zugangsdaten stimmen und der Benutzer Tabellen anlegen darf.
- **Fehlende oder mehrere Excel-Dateien:** Genau eine `.xlsx`-Datei in den Projektordner legen. Ihr Dateiname ist beliebig.
- **Kein Geocoding:** LocationIQ-Key, Internetverbindung und API-Limit prüfen.
- **Server startet nicht (Systemd):** Nutze `sudo journalctl -u fastapi.service -n 50`, um dir die letzten 50 Zeilen der Server-Fehlermeldungen anzeigen zu lassen.
