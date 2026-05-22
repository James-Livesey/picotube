import sqlite3
import threading

connection = sqlite3.connect("picotube.db", check_same_thread=False)
cursor = connection.cursor()
lock = threading.Lock()

def run_script(path):
    file = open(path, "r")

    cursor.executescript(file.read())

    file.close()

def init():
    run_script("sql/init.sql")

    connection.commit()