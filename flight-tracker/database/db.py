"""Funções de acesso ao banco SQLite (schema + CRUD)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Optional

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS flight_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    return_date TEXT NOT NULL,
    price REAL NOT NULL,
    airline TEXT,
    departure_time TEXT,
    arrival_time TEXT,
    duration_minutes INTEGER,
    direct INTEGER DEFAULT 0,
    link TEXT,
    source TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    recipient TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    sent INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS price_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    return_date TEXT NOT NULL,
    min_price REAL,
    max_price REAL,
    avg_price REAL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_flight_prices_route_dates
    ON flight_prices (origin, destination, departure_date, return_date);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


init_db()  # schema é idempotente (CREATE TABLE IF NOT EXISTS) — garante tabelas em qualquer entry point


def insert_flight_price(flight: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO flight_prices
                (origin, destination, departure_date, return_date, price, airline,
                 departure_time, arrival_time, duration_minutes, direct, link, source, timestamp)
            VALUES (:origin, :destination, :departure_date, :return_date, :price, :airline,
                    :departure_time, :arrival_time, :duration_minutes, :direct, :link, :source, :timestamp)
            """,
            flight,
        )
        return cur.lastrowid


def get_latest_prices(limit: int = 200) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM flight_prices ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_best_combinations(limit: int = 10) -> list:
    """Melhor preço já visto para cada combinação origem/destino/ida/volta."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT origin, destination, departure_date, return_date, airline,
                   MIN(price) AS price, departure_time, arrival_time, direct, link, timestamp
            FROM flight_prices
            GROUP BY origin, destination, departure_date, return_date
            ORDER BY price ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_price_history(origin: str, destination: str, departure_date: str, return_date: str) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM flight_prices
            WHERE origin = ? AND destination = ? AND departure_date = ? AND return_date = ?
            ORDER BY timestamp ASC
            """,
            (origin, destination, departure_date, return_date),
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total, MIN(price) AS min_price,
                   MAX(price) AS max_price, AVG(price) AS avg_price
            FROM flight_prices
            """
        ).fetchone()
        return dict(row) if row else {}


def insert_alert(alert_type: str, message: str, recipient: str, sent: bool = True) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts (alert_type, message, recipient, sent_at, sent)
            VALUES (?, ?, ?, ?, ?)
            """,
            (alert_type, message, recipient, datetime.now().isoformat(), int(sent)),
        )
        return cur.lastrowid


def insert_price_trend(trend: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO price_trends
                (origin, destination, departure_date, return_date, min_price, max_price, avg_price, timestamp)
            VALUES (:origin, :destination, :departure_date, :return_date, :min_price, :max_price, :avg_price, :timestamp)
            """,
            trend,
        )
        return cur.lastrowid
