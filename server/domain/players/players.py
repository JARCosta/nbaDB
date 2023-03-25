#!/usr/bin/python3

from asyncio import sleep
from bs4 import BeautifulSoup
from flask import render_template
import psycopg2
from psycopg2.extras import DictCursor
import requests
from utils.dbConnection import get_db_connection_string as DB_CONNECTION_STRING

def get_soup(url:str):  # sourcery skip: raise-specific-error
    r_html = requests.get(url).text
    soup =  BeautifulSoup(r_html,'html.parser')
    if soup.find('p').text == 'The owner of this website (www.basketball-reference.com) has banned you temporarily from accessing this website.':
        raise Exception(soup.find('p').text)
    return soup


def get_list():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING())
        cursor = dbConn.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT player.name, player.href, team.name, team.href, team.color, team.logo FROM player join team on team = team.name ORDER BY player.name;")
        return render_template("players/players.html", cursor=cursor)
    except Exception as e:
        raise e  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()


def update_players_aux(cursor, game):
    soup = get_soup(game[5])
    tables = soup.find_all("table")
    tables = [tables[0], tables[8]]

    for table in tables: # for each table create players
        team = str(str(table.find("caption").text).split("Basic and Advanced Stats Table")[0][:-1])
        table = table.find("tbody").find_all("tr", class_=False)
        
        players = [i.find("th", {"data-stat" : "player"}).text for i in table]
        hrefs = ["https://www.basketball-reference.com"+i.find("th", {"data-stat" : "player"}).find("a")["href"] for i in table]
        query, data = "START TRANSACTION;", []
        for i in range(len(players)): # iniciatize player
            query += """
                insert into player (name, team, href)
                    Select %s,%s,%s Where not exists(select * from player where name=%s);
            """
            data.extend([players[i], team, hrefs[i], players[i]])
        cursor.execute(query+"COMMIT;", data)

    query, data = "", []
    for table in tables: # for each table, add game to each player
        table = table.find("tbody").find_all("tr", class_=False)
        
        players = [i.find("th", {"data-stat" : "player"}).text for i in table]
        MP  = [str(i.find("td", {"data-stat" : "mp" }).text) for i in table if i.find("td", {"data-stat" : "mp" }) != None]
        PTS = [int(i.find("td", {"data-stat" : "pts"}).text) for i in table if i.find("td", {"data-stat" : "pts"}) != None]
        TRB = [int(i.find("td", {"data-stat" : "trb"}).text) for i in table if i.find("td", {"data-stat" : "trb"}) != None]
        AST = [int(i.find("td", {"data-stat" : "ast"}).text) for i in table if i.find("td", {"data-stat" : "ast"}) != None]
        BLK = [int(i.find("td", {"data-stat" : "blk"}).text) for i in table if i.find("td", {"data-stat" : "blk"}) != None]
        STL = [int(i.find("td", {"data-stat" : "stl"}).text) for i in table if i.find("td", {"data-stat" : "stl"}) != None]
        TOV = [int(i.find("td", {"data-stat" : "tov"}).text) for i in table if i.find("td", {"data-stat" : "tov"}) != None]
        FG3 = [int(i.find("td", {"data-stat" : "fg3"}).text) for i in table if i.find("td", {"data-stat" : "fg3"}) != None]
        stats = [PTS,TRB,AST,BLK,STL,TOV,FG3]

        multipliers = [1,1.2,1.5,3,3,-2,1]
        fantasy_points = [sum([int(str(stats[j][i])) * multipliers[j] for j in range(len(stats))]) for i in range(len(PTS)) ]

        for i in range(len(players)):                   # add player to game
            if i < len(PTS):                            # if played
                query += """
                    INSERT INTO plays (player, href, minutes_played, points, rebounds, assists, blocks, steal, turnover, triples, "fantasy points")
                        Select %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s Where not exists(select * from plays where player=%s AND href =%s);
                """
                data.extend([players[i], game[5], MP[i], stats[0][i], stats[1][i], stats[2][i], stats[3][i], stats[4][i], stats[5][i], stats[6][i], fantasy_points[i], players[i], game[5]])
            else:                                       # if benched
                query += """
                    INSERT INTO plays (player, href)
                        Select %s,%s Where not exists(select * from plays where player=%s AND href =%s);
                """
                data.extend([players[i], game[5], players[i], game[5]])
    query += """ UPDATE game
    SET loaded = 1
    WHERE href = %s;
    """
    data.append(game[5])
    file1 = open("log.log", "a")
    file1.write(str(game) + "\n")
    return query, data, [str(i.find("caption").text).split("Basic and Advanced Stats Table")[0][:-1] for i in tables]


def update():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING())
        cursor = dbConn.cursor(cursor_factory=DictCursor)
        cursor.execute('SELECT * FROM game WHERE loaded=0 ORDER BY date DESC;')
        curs = list(cursor)
        n_its = 20
        # sleep(120)
        # curs = [list(i) for i in np.array_split(curs, n_its)]
        for chunk in range(0, len(curs), n_its):
            x = chunk
            query, data = "START TRANSACTION;", []
            for game in curs[x:x+n_its]:
                temp = update_players_aux(cursor, game)
                query += temp[0]
                data.extend(temp[1])
            cursor.execute(query + "COMMIT;", data)
            sleep(120)
        return render_template("domain/../templates/redirect_to_root.html")
        return str([curs, query, data])
    except Exception as e:
        if str(e) == 'The owner of this website (www.basketball-reference.com) has banned you temporarily from accessing this website.':
            file1 = open("log.log", "w")
            file1.write("ban while updating players")
        raise e  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()
    