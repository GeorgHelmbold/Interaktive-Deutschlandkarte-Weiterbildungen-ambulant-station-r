from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host="100.84.119.113",
    dbname="aerzte",
    user="defuser",
    password="nephro2026"
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

bundesländer = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]

@app.get("/", response_class=HTMLResponse)
def home():
    return f'<h1>{"message"}</h1>'


@app.get("/data", response_class=HTMLResponse)
def all_bundeslaender(request: Request):
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

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    suchwert = f"%{begriff}%"

    if typ == "alle":
        query = f'''
            SELECT * FROM "{bundesland}"
            WHERE "Kreis" ILIKE %s
               OR "Einrichtung" ILIKE %s
               OR "Angaben zur Person" ILIKE %s
        '''
        cur.execute(query, (suchwert, suchwert, suchwert))
    else:
        typincludes = f"%{typ}%"
        query = f'''
            SELECT * FROM "{bundesland}"
            WHERE ("Kreis" ILIKE %s
               OR "Einrichtung" ILIKE %s
               OR "Angaben zur Person" ILIKE %s)
              AND "ambulant/stationär/niedergelassen" LIKE %s
        '''
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = '''
        SELECT * FROM alle_bundesländer
        WHERE "Kreis" ILIKE %s
           OR "Einrichtung" ILIKE %s
    '''
    suchwert = f"%{begriff}%"
    cur.execute(query, (suchwert, suchwert))
    
    rows = cur.fetchall()
    cur.close()

    return templates.TemplateResponse(
        request,
        "alle_bundeslaender.html",
        {"rows": rows}
    )