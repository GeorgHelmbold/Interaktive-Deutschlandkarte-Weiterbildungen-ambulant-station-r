import csv
import psycopg2
import sys

conn = psycopg2.connect(
    host="100.84.119.113",
    dbname="aerzte",
    user="defuser",
    password="nephro2026"
)
cur = conn.cursor()

bundesländer = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]

def maketables(bundesland):
    with open(f'{bundesland}.csv') as csvdatei:
        csv_reader_object = csv.reader(csvdatei, delimiter=',')
        zeilennr=0
        spaltennamen = ["Landesärztekammer", "Kreis", "ambulant/stationär/niedergelassen", "Weiterbildungsermächtigung für Nephrologie", "Befugnis", "Angaben zur Person", "Einrichtung"]
        spalten_sql_names = ", ".join(f'"{name}"' for name in spaltennamen)
        for row in csv_reader_object:
            if len(row)<7:
                print("Tabelle hat unerwartet zu wenig Spalten")
                cur.close()
                conn.close()
                sys.exit()
            if len(row)>7:
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
                querie = f'CREATE TABLE "{bundesland}" ({spalten_sql}, PRIMARY KEY ({pk_spalten}))'
                cur.execute(querie)
            else:
                insert_query = f'''
                INSERT INTO "{bundesland}" ({spalten_sql_names})
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                '''
                cur.execute(insert_query, (attribut1, attribut2, attribut3, attribut4, attribut5, attribut6, attribut7))
            zeilennr += 1
        

for bundesland in bundesländer:
    maketables(bundesland)
conn.commit()

union_parts = [
    f'SELECT *, \'{bundesland}\' AS bundesland FROM "{bundesland}"'
    for bundesland in bundesländer
]
view_query = "CREATE MATERIALIZED VIEW alle_bundesländer AS\n" + "\nUNION ALL\n".join(union_parts) + ";"
drop_view = f'''
    DROP MATERIALIZED VIEW IF EXISTS alle_bundesländer;
'''
cur.execute(drop_view)
cur.execute(view_query)
conn.commit()

cur.close()
conn.close()
