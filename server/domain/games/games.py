






from asyncio import sleep
from bs4 import BeautifulSoup
from flask import render_template, request
import psycopg2
import requests
from utils import get_db_connection_string as DB_CONNECTION_STRING

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
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        arg = list(request.args)
        # return str(request.args[arg[0]])
        # for arg in args:
        if arg == []:
                                                                                                                                    # , home.ref, visitor.ref
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name JOIN team visitor ON visitor = visitor.name ORDER BY date DESC;"""
            data = []
            result = ('All games',)
        elif arg[0] == "team":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name
                    JOIN team visitor on visitor = visitor.name
                    WHERE home.name = %s OR visitor.name = %s;"""
            data = [request.args[arg[0]],request.args[arg[0]]]
            result = ('Games from '+request.args[arg[0]],)
        elif arg[0] == "short":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.logo, visitor.logo, game.loaded
                    FROM game JOIN team home ON home = home.name
                    JOIN team visitor on visitor = visitor.name
                    WHERE home.short = %s OR visitor.short = %s;"""
            data = [request.args[arg[0]],request.args[arg[0]]]
            result = ('Games from '+request.args[arg[0]],)
        elif arg[0] == "player":
            query = """SELECT date::date, home.short, home_score, visitor.short, visitor_score, game.href, home.color, visitor.color, home.logo, visitor.logo, game.loaded
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
        return render_template("games/games.html", cursor=cursor, result=result)
    except Exception as e:
        raise e  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()


def update():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING())
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
        return render_template("domain/../templates/redirect_to_root.html")
        return "Success loading months: " + str(months)
    except Exception as e:
        raise e  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()

def show():
    dbConn = None
    cursor = None
    try:
        dbConn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = dbConn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        href = request.args["href"]
        query = "select * from plays join player on player = player.name where plays.href =%s"
        cursor.execute(query, (href,))
        return render_template("games/show_game.html", cursor=cursor)
    except Exception as e:
        raise e  # Renders a page with the error.
    finally:
        cursor.close()
        dbConn.close()
