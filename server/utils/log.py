#!/usr/bin/python3

def log_join(sessionId):
    logFile = open("log.log", "a")
    logFile.write(f'session login: {sessionId}\n')