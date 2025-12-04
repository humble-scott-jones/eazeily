#!/usr/bin/env python3
"""List Postgres tables and row counts using the app's DATABASE_URL.

This script tries to use psycopg (v3) if available, falls back to psycopg2.
It prints tables in the public schema and sample row counts for each table.
Run this inside Railway (or an environment that can reach the DB):
  railway run python scripts/list_tables.py
"""
import os
import sys
from urllib.parse import urlparse

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    print("DATABASE_URL not set in environment", file=sys.stderr)
    sys.exit(2)

def connect_psycopg(db_url):
    try:
        import psycopg
        conn = psycopg.connect(db_url)
        cur = conn.cursor()
        return conn, cur
    except Exception:
        return None, None

def connect_psycopg2(db_url):
    try:
        import psycopg2
        conn = psycopg2.connect(dsn=db_url)
        cur = conn.cursor()
        return conn, cur
    except Exception:
        return None, None

conn = cur = None
conn, cur = connect_psycopg(DB_URL)
if conn is None:
    conn, cur = connect_psycopg2(DB_URL)

if conn is None:
    print("Could not import psycopg or psycopg2 or connect to DB.", file=sys.stderr)
    sys.exit(3)

try:
    print("Connected to DB. Listing tables in public schema...\n")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
    tables = [r[0] for r in cur.fetchall()]
    if not tables:
        print("No tables found in public schema.")
    else:
        for t in tables:
            # safe row count
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"{t}\";")
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = "?"
            print(f"{t}: {cnt}")
finally:
    try:
        cur.close()
    except Exception:
        pass
    try:
        conn.close()
    except Exception:
        pass
