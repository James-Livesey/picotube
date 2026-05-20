import sqlite3

connection = sqlite3.connect("picotube.db", check_same_thread=False)
cursor = connection.cursor()

def run_script(path):
    file = open(path, "r")

    cursor.executescript(file.read())

    file.close()

def init():
    run_script("sql/init.sql")