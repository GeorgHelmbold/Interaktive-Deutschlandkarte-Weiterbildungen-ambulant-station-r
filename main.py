from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator
from entities import ConnectionConfig, GeocodingConfig

geo_config = GeocodingConfig()
API_KEY = geo_config.locationiq_api_key

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

bundesländer = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
                "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
                "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
                "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]

config = ConnectionConfig()


@contextmanager
def create_connection(
    config: ConnectionConfig,
) -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.database,
        user=config.username,
        password=config.password
    )
    try:
        yield conn
    finally:
        conn.close()


@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>message</h1>"


@app.get("/karte", response_class=HTMLResponse)
def karte(request: Request):
    return templates.TemplateResponse(request, "karte.html", {})


@app.get("/api/standorte", response_class=JSONResponse)
def api_standorte():
    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM alle_bundesländer")
        rows = cur.fetchall()
        cur.close()
    return rows


@app.get("/data", response_class=HTMLResponse)
def all_bundeslaender(request: Request):
    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM alle_bundesländer")
        rows = cur.fetchall()
        cur.close()

    return templates.TemplateResponse(
        request,
        "alle_bundeslaender.html",
        {"rows": rows}
    )


@app.get("/data/{bundesland}", response_class=HTMLResponse)
def table_access(request: Request, bundesland: str):
    if bundesland not in bundesländer:
        return HTMLResponse(content="<h1>Unbekanntes Bundesland</h1>", status_code=404)

    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = f'SELECT * FROM "{bundesland}"'
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()

    return templates.TemplateResponse(
        request,
        "bundesland.html",
        {"bundesland": bundesland, "rows": rows}
    )


@app.get("/suche", response_class=HTMLResponse)
def suche(request: Request, bundesland: str, begriff: str = "", typ: str = "alle"):
    if bundesland not in bundesländer:
        return HTMLResponse(content="<h1>Unbekanntes Bundesland</h1>", status_code=404)

    suchwert = f"%{begriff}%"

    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if typ == "alle":
            query = '''
                SELECT * FROM "{}"
                WHERE "Kreis" ILIKE %s
                   OR "Einrichtung" ILIKE %s
                   OR "Angaben zur Person" ILIKE %s
            '''.format(bundesland)
            cur.execute(query, (suchwert, suchwert, suchwert))
        else:
            typincludes = f"%{typ}%"
            query = '''
                SELECT * FROM "{}"
                WHERE ("Kreis" ILIKE %s
                   OR "Einrichtung" ILIKE %s
                   OR "Angaben zur Person" ILIKE %s)
                  AND "ambulant/stationär/niedergelassen" LIKE %s
            '''.format(bundesland)
            cur.execute(query, (suchwert, suchwert, suchwert, typincludes))

        rows = cur.fetchall()
        cur.close()

    return templates.TemplateResponse(
        request,
        "bundesland.html",
        {"bundesland": bundesland, "rows": rows, "typ": typ, "begriff": begriff}
    )


@app.get("/suche-alle", response_class=HTMLResponse)
def suche_alle(request: Request, begriff: str = ""):
    suchwert = f"%{begriff}%"

    with create_connection(config) as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = '''
            SELECT * FROM alle_bundesländer
            WHERE "Kreis" ILIKE %s
               OR "Einrichtung" ILIKE %s
        '''
        cur.execute(query, (suchwert, suchwert))
        rows = cur.fetchall()
        cur.close()

    return templates.TemplateResponse(
        request,
        "alle_bundeslaender.html",
        {"rows": rows}
    )