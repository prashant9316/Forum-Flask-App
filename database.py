from flask import g
# import sqlite3
import psycopg2
from psycopg2.extras import DictCursor as Cursor

uri = 'postgres://pkxaltivphests:e197a4f05ad81678b8a59b3809b0ca4a77446118dc321ddddb9841ecb730a482@ec2-54-147-54-83.compute-1.amazonaws.com:5432/d9m3k5ase7h1u'


# def connect_db():
#     sql = sqlite3.connect('data.db')
#     sql.row_factory = sqlite3.Row
#     return sql


# def get_db():
#     if not hasattr(g, 'sqlite_db'):
#         g.sqlite_db = connect_db()
#     return g.sqlite_db

def connect_db():
    conn = psycopg2.connect(uri, cursor_factory = Cursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql

def get_db():
    db = connect_db()

    if not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn = db[0]

    if not hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur

def init_db():
    db = connect_db()

    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()

    db[0].close()

def init_admin():
    db = connect_db()

    db[1].execute('update users set admin = True where name = %s', ('coding@mishra', ))

    db[1].close()
    db[0].close()