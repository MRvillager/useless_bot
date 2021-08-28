#!/bin/python3
import sqlite3


def run():
    connection = sqlite3.connect("data/data.sqlite", isolation_level=None)

    cursor = connection.cursor()

    sql_file = open("data/init.sql", "r")
    sql_as_string = sql_file.read()
    cursor.executescript(sql_as_string)


if __name__ == "__main__":
    run()
