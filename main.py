from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator
from entities import ConnectionConfig

app = FastAPI(
    docs_url=None,      # Deaktiviert /docs (Swagger UI)
    redoc_url=None,     # Deaktiviert /redoc
    openapi_url=None    # Deaktiviert /openapi.json (wichtig, sonst ist das Schema noch lesbar!)
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

config = ConnectionConfig()

def escape_like_literal(value: str) -> str:
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")

@contextmanager
def create_connection(
    config: ConnectionConfig,
) -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.database,
        user=config.db_username,
        password=config.password
    )
    try:
        yield conn
    finally:
        conn.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )

@app.get("/datenschutz", response_class=HTMLResponse)
def datenschutz():
    return FileResponse("static/datenschutz.html", media_type="text/html")

@app.get("/chart", response_class=HTMLResponse)
def chart(request: Request, ort_begriff: str = "", person_begriff: str = "", typ: str = "alle"):
    bedingungen = []
    werte = []

    if ort_begriff:
        bedingungen.append('("Kreis" ILIKE %s ESCAPE \'!\' OR "Einrichtung" ILIKE %s ESCAPE \'!\')')
        wert = f"%{escape_like_literal(ort_begriff)}%"
        werte.extend([wert, wert])

    if person_begriff:
        bedingungen.append('("Angaben zur Person" ILIKE %s ESCAPE \'!\' OR "Einrichtung" ILIKE %s ESCAPE \'!\')')
        wert = f"%{escape_like_literal(person_begriff)}%"
        werte.extend([wert, wert])

    if typ != "alle":
        bedingungen.append('"ambulant/stationär/niedergelassen" LIKE %s ESCAPE \'!\'')
        werte.append(f"%{escape_like_literal(typ)}%")

    where_klausel = " AND ".join(bedingungen) if bedingungen else "TRUE"

    query = '''
        SELECT *
        FROM alle_bundesländer
        WHERE {}
    '''.format(where_klausel)

    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, tuple(werte))
        rows = cur.fetchall()
        cur.close()

    rows_dicts = [dict(row) for row in rows]
    standorte_json = json.dumps(rows_dicts, ensure_ascii=False).replace("</", "<\\/")

    # Für die Tabellenanzeige: lat/lng (und bundesland) rausfiltern
    ausgeschlossene_spalten = {"lat", "lng", "bundesland"}
    tabellen_rows = [
        {k: v for k, v in row.items() if k not in ausgeschlossene_spalten}
        for row in rows_dicts
    ]

    return templates.TemplateResponse(
        request,
        "chart.html",
        {"rows": tabellen_rows, "typ": typ, "ort_begriff": ort_begriff, "person_begriff": person_begriff, "standorte_json": standorte_json}
    )