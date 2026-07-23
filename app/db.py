import os
import sqlite3

DB_PATH = os.environ.get(
    'DATABASE_PATH',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gestao_ti.db')
)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn
