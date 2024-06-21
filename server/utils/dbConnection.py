#!/usr/bin/python3

import json

def get_db_connection_string():
    DB_FILE = open("server/utils/config.json")

    DB_INFO = json.load(DB_FILE)
    DB_FILE.close()

    DB_CONNECTION_STRING = "host=%s dbname=%s user=%s password=%s" % (
        DB_INFO["DB_HOST"],
        DB_INFO["DB_DATABASE"],
        DB_INFO["DB_USER"],
        DB_INFO["DB_PASSWORD"],
    )
    return DB_CONNECTION_STRING