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

def root():
    return domain.root.get_main_page()


def teams():
    return domain.teams.get_list()

def update_teams():
    return domain.teams.update()


def players():
    return domain.players.get_list()

def update_players():
    return domain.players.update()

def games():
    return domain.games.get_list()

def update_games():
    return domain.games.update()

def show_games():
    return domain.games.show()


def clear():
    return domain.root.clear()
