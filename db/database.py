#   """
#   NSAC Competition Management System - Database Module

#   This module provides database connectivity and query utilities using PyMySQL.
#   It includes functions for executing queries, fetching results, and managing connections.
#   """

import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

def get_conn():
#   """
#   Create and return a new database connection.

#   Returns:
#       pymysql.Connection: Database connection object.
#   """
    cfg = dict(DB_CONFIG)
    cfg["cursorclass"] = DictCursor
    return pymysql.connect(**cfg)

def query_one(sql, params=None):
#   """
#   Execute a query and return the first result row.

#   Args:
#       sql (str): SQL query string.
#       params (tuple or list, optional): Query parameters.
   
#   Returns:
#       dict or None: First result row as dictionary, or None if no results.
#   """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()
    finally:
        conn.close()

def query_all(sql, params=None):
#   """
#   Execute a query and return all result rows.

#   Args:
#       sql (str): SQL query string.
#       params (tuple or list, optional): Query parameters.

#   Returns:
#       list: List of result rows as dictionaries.
#   """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

def execute(sql, params=None):
#   """
#   Execute a query that modifies data (INSERT, UPDATE, DELETE).

#   Args:
#       sql (str): SQL query string.
#       params (tuple or list, optional): Query parameters.

#   Returns:
#       int: Last inserted row ID for INSERT queries.
#   """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.lastrowid
    finally:
        conn.close()
