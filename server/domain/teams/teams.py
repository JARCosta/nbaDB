#!/usr/bin/python3

from flask import render_template
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


def get_list():
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

def update():
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
        update_colors()
        return render_template("teams.html")
        return str(teams)
    except Exception:
        return str(Exception)  # Renders a page with the error.
    finally:
        dbConn.commit()
        cursor.close()
        dbConn.close()

def update_colors():
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