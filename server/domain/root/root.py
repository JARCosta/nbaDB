#!/usr/bin/python3

from flask import render_template, session
import psycopg2
from psycopg2.extras import DictCursor

from utils.dbConnection import get_db_connection_string
from utils.log import log_join


def get_main_page():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(get_db_connection_string())
        cursor = dbConn.cursor(cursor_factory=DictCursor)
        data = []
        cursor.execute("SELECT * FROM team;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM game;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM player;")
        data.append(len(list(cursor)))

        cursor.execute("SELECT * FROM game WHERE loaded = 0")
        data.append(len(list(cursor)))
        
        log_join(session["user_id"])
        
        #return str([len(teams), len(games), len(players)])
        return render_template("root/index.html", result=data, title="Hellow")
    # except Exception as e:
    #     raise e  # Renders a page with the error.
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
        dbConn = psycopg2.connect(get_db_connection_string())
        cursor = dbConn.cursor(cursor_factory=DictCursor)
        query = """
            DELETE FROM plays WHERE 1=1;
            DELETE FROM player WHERE 1=1;
            DELETE FROM game WHERE 1=1;
            DELETE FROM team WHERE 1=1;
            DELETE FROM contract WHERE 1=1;
        """
        cursor.execute(query)
        return query
    except Exception as e:
        raise e  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()
