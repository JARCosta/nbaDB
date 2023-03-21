#!/usr/bin/python3

from flask import render_template, session
import psycopg2

DB_HOST = "db.tecnico.ulisboa.pt"
DB_USER = "ist199088"
DB_DATABASE = DB_USER
DB_PASSWORD = "jackers"
DB_CONNECTION_STRING = "host=%s dbname=%s user=%s password=%s" % (
    DB_HOST,
    DB_DATABASE,
    DB_USER,
    DB_PASSWORD,
)


def get_main_page():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        data = []
        cursor.execute("SELECT * FROM team;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM game;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM player;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM game WHERE loaded = 0")
        data.append(len(list(cursor)))
        
        file1 = open("../log.log", "a")
        file1.write(f'session login: {session["user_id"]}\n')
        
        #return str([len(teams), len(games), len(players)])
        return render_template("index.html", result=data, title="Hellow")
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        # cursor2.close()
        # cursor3.close()
        dbConn.close()
        # dbConn2.close()
        # dbConn3.close()

def clear():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
            DELETE FROM plays WHERE 1=1;
            DELETE FROM player WHERE 1=1;
            DELETE FROM game WHERE 1=1;
            DELETE FROM team WHERE 1=1;
        """
        cursor.execute(query)
        return query
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()
