#!/usr/bin/python3
from urllib.robotparser import RequestRate
from wsgiref.handlers import CGIHandler
from flask import Flask
from flask import render_template, request

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from difflib import get_close_matches
from time import sleep
import time
from difflib import SequenceMatcher


import psycopg2
import psycopg2.extras
from time import sleep
#from sklearn.tree import DecisionTreeClassifier
#from sklearn.model_selection import train_test_split
## SGBD configs
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

app = Flask(__name__)


def get_soup(url:str):  # sourcery skip: raise-specific-error
    r_html = requests.get(url).text
    soup =  BeautifulSoup(r_html,'html.parser')
    if soup.find('p').text == 'The owner of this website (www.basketball-reference.com) has banned you temporarily from accessing this website.':
        raise Exception(soup.find('p').text)
    return soup


@app.route("/")
def root():
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
        
        file1 = open("log.log", "a")
        file1.write("oi\n")
        #return str([len(teams), len(games), len(players)])
        return render_template("index.html", result=data, title="Helo")
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        # cursor2.close()
        # cursor3.close()
        dbConn.close()
        # dbConn2.close()
        # dbConn3.close()

@app.route("/teams")
def teams():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM team ORDER BY name;")
        return render_template("teams.html", cursor=cursor)
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()

@app.route("/update_teams")
def update_teams():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        years = range(2022,2024)
        query,data = "START TRANSACTION;", []
        for season in years:
            query += """insert into season (year)
                    Select %s Where not exists(select * from season where year=%s);
            """
            data.extend([season,season])
            url =  'https://www.basketball-reference.com/leagues/NBA_'+str(season)+'.html'
            soup = get_soup(url).find("table", {"id" : "per_game-team"}).find("tbody")
            teams = soup.find_all('td', {"data-stat" : "team"})
            for team in teams:
                href = 'https://www.basketball-reference.com' + team.find('a')['href']
                short = team.find('a')['href'].split('/')[2]
                name = team.text
                query += """
                    insert into team (name, short, , season)
                        Select %s,%s,%s Where not exists(select * from team where name=%s and season=%s);
                """
                data.extend([name, short, season, name, season])
        cursor.execute(query+"COMMIT;", tuple(data))
        update_team_colors()
        return render_template("teams.html")
        return str(teams)
    except Exception:
        return str(Exception)  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()

def update_team_colors():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        url =  'https://usteamcolors.com/nba-colors/'
        soup = get_soup(url).find_all('li', {'class' : 'card'})
        teams = [' '.join(i.find('a').text.replace('\n', '').split(' ')[:-1]) for i in soup]
        colors = [i.find('a')['style'].split(' ')[1] for i in soup]
        logos = [i.find('a').find('img')['src'] for i in soup]
        # return str(colors)
        query = "START TRANSACTION;"
        data = []
        for i in range(len(teams)):
            query += """
                UPDATE team 
                    SET color = %s, logo = %s
                    WHERE team.name = %s;
            """
            data.extend(iter([colors[i], logos[i], teams[i]]))
        cursor.execute(query+"COMMIT;", tuple(data))
        return render_template("redirect_to_root.html")
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()


@app.route("/players")
def players():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT player.name, player.href, team.name, team.href, team.color, team.logo FROM player join team on team = team.name ORDER BY player.name;")
        return render_template("players.html", cursor=cursor)
    except Exception as e:
        return str(e)  # Renders a page with the error.
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

def update_loaded_games():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('UPDATE game SET loaded = 1 FROM plays WHERE plays.href = game.href')
        return len(list(cursor))
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()


@app.route("/update_players")
def update_players():
    dbConn = None
    cursor = None
    try:
        # update_loaded_games()
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
        return render_template("redirect_to_root.html")
        return str([curs, query, data])
    except Exception as e:
        if str(e) == 'The owner of this website (www.basketball-reference.com) has banned you temporarily from accessing this website.':
            file1 = open("log.log", "w")
            file1.write("ban while updating players")
        return str([e, game])  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()

@app.route("/games")
def games():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        arg = list(request.args)
        # return str(request.args[arg[0]])
        # for arg in args:
        if arg == []:
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.href, visitor.href, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name JOIN team visitor ON visitor = visitor.name ORDER BY date DESC;"""
            data = []
            result = ('All games',)
        elif arg[0] == "team":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.href, visitor.href, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name
                    JOIN team visitor on visitor = visitor.name
                    WHERE home.name = %s OR visitor.name = %s;"""
            data = [request.args[arg[0]],request.args[arg[0]]]
            result = ('Games from '+request.args[arg[0]],)
        elif arg[0] == "short":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.href, visitor.href, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name
                    JOIN team visitor on visitor = visitor.name
                    WHERE home.short = %s OR visitor.short = %s;"""
            data = [request.args[arg[0]],request.args[arg[0]]]
            result = ('Games from '+request.args[arg[0]],)
        elif arg[0] == "player":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.href, visitor.href, home.logo, visitor.logo, game.loaded
                    FROM plays
                    JOIN game on plays.href = game.href
                    join team visitor on visitor = visitor.name
                    join team home on home = home.name
                    WHERE player = %s"""
            # query = """SELECT player.name, plays.href, minutes_played, points, rebounds, assists, blocks, steal, turnover, triples, "fantasy points", opponent.name, opponent.logo, opponent.color
            #         FROM plays JOIN player ON player = player.name JOIN game ON plays.href = game.href JOIN team as opponent ON CASE WHEN team = home then visitor ELSE home END = opponent.name WHERE player.name = %s"""
            data = [request.args[arg[0]],]
            result = ('Games from '+request.args[arg[0]],)
        #TODO games_from_player_vs_team
        # query = """select *
        #         from plays
        #         join game on plays.href = game.href

        #         join team home on home = home.name
        #         join team visitor on visitor = visitor.name
        #         --join team opponent on visitor = opponent.name or home = opponent.name
        #         --join team own on not(visitor = own.name or home = own.name)
        #         where player = 'Kevin Durant' and (home.name = 'Orlando Magic' or visitor.name = 'Orlando Magic')"""

        cursor.execute(query, data)
        return render_template("games.html", cursor=cursor, result=result)
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()


@app.route("/update_games")
def update_games():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # if curs == []:
        #     years = range(2020,2024)
        # else:
        #     last_game_date = [int(i) for i in str(curs[0][0]).split(" ")[0].split("-")[::-1]]
        #     years = [last_game_date[1],]
        #     if last_game_date[1] > 4:
        #         years.append(last_game_date[1]+1)
        years = range(2022,2024)
        for year in years:
            url = 'https://www.basketball-reference.com/leagues/NBA_'+str(year)+'_games.html'
            soup = get_soup(url)
            rest_months_href = ["https://www.basketball-reference.com"+i.find("a")["href"] for i in soup.find("div", {"class" : "filter"}).find_all("div")[1:]]
            soups = [soup,]
            soups.extend([get_soup(i) for i in rest_months_href])
            query, data = "START TRANSACTION;", []
            for soup in soups: # for each month
                for row in soup.find('tbody').find_all('tr', class_ = False):
                    if len(row.find('td', {'data-stat':'home_pts'}))==0:
                        break
                    date = row.find('th', {'data-stat':'date_game'}).text
                    home = row.find('td', {'data-stat':'home_team_name'}).text
                    h_points = row.find('td', {'data-stat':'home_pts'}).text
                    h_href = row.find('td', {'data-stat':'home_team_name'}).find('a')['href']
                    visitor = row.find('td', {'data-stat':'visitor_team_name'}).text
                    v_points = row.find('td', {'data-stat':'visitor_pts'}).text
                    v_href = row.find('td', {'data-stat':'visitor_team_name'}).find('a')['href']
                    href = 'https://www.basketball-reference.com' + row.find('td', {'data-stat':'box_score_text'}).find('a')['href']
                    query += """
                        INSERT INTO game (date, home, home_score, visitor, visitor_score, href, loaded, season)
                            SELECT %s,%s,%s,%s,%s,%s,0,%s WHERE NOT EXISTS(SELECT * FROM game WHERE date=%s AND home=%s AND visitor=%s);
                    """
                    data.extend([date, home, h_points, visitor, v_points, href, year, date, home, visitor])
            cursor.execute(query+"COMMIT;", data)
            sleep(60)
        return render_template("redirect_to_root.html")
        return "Success loading months: " + str(months)
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()


@app.route("/show_games")
def show_games():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        href = request.args["href"]
        query = "select * from plays join player on player = player.name where plays.href =%s"
        cursor.execute(query, (href,))
        return render_template("show_game.html", cursor=cursor)
    except Exception as e:
        return str(e)  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()

@app.route("/clear")
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


CGIHandler().run(app)
