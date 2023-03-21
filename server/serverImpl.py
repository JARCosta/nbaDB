#!/usr/bin/python3
from urllib.robotparser import RequestRate
from wsgiref.handlers import CGIHandler
from flask import Flask, session, request, render_template

import requests
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import numpy as np
from difflib import SequenceMatcher, get_close_matches

import hashlib
import time

import domain

import psycopg2
import psycopg2.extras
from time import sleep

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


def root():
    return domain.root.get_main_page()


def teams():
    return domain.teams.teams.get_list()


def get_soup(url:str):  # sourcery skip: raise-specific-error
    r_html = requests.get(url).text
    soup =  BeautifulSoup(r_html,'html.parser')
    if soup.find('p').text == 'The owner of this website (www.basketball-reference.com) has banned you temporarily from accessing this website.':
        raise Exception(soup.find('p').text)
    return soup

def update_teams():
    return domain.teams.update()

def players():
    return domain.players.get_list()

def games():
    return domain.games.get_list()

def update_games():
    return domain.games.update()


def show_games():
    return domain.games.show()


def clear():
    return domain.root.clear()


