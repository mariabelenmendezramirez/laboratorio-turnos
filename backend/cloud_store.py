"""Persistencia Postgres para las funciones serverless de Vercel."""

from datetime import datetime
from os import environ
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row


def connection():
    database_url = environ.get("DATABASE_URL") or environ.get("POSTGRES_URL")
    if not database_url:
        raise RuntimeError("Falta configurar DATABASE_URL en Vercel.")
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=8)


def clinic_day():
    timezone = ZoneInfo(environ.get("QUEUE_TIMEZONE", "America/Mexico_City"))
    return datetime.now(timezone).date()


def ensure_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily (
            day DATE PRIMARY KEY,
            last_number INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            day DATE NOT NULL,
            number INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('waiting', 'serving', 'done')),
            "window" INTEGER CHECK ("window" BETWEEN 1 AND 4),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (day, number),
            UNIQUE (day, "window")
        )
    """)


def ensure_day(conn, day):
    conn.execute(
        "INSERT INTO daily(day, last_number) VALUES (%s, 0) ON CONFLICT(day) DO NOTHING",
        (day,),
    )


def snapshot(conn):
    day = clinic_day()
    ensure_day(conn, day)
    serving = {
        row["window"]: row["number"]
        for row in conn.execute(
            'SELECT "window", number FROM tickets WHERE day=%s AND status=\'serving\'',
            (day,),
        ).fetchall()
    }
    waiting = conn.execute(
        "SELECT number FROM tickets WHERE day=%s AND status='waiting' ORDER BY number",
        (day,),
    ).fetchall()
    last_number = conn.execute(
        "SELECT last_number FROM daily WHERE day=%s", (day,)
    ).fetchone()["last_number"]
    return {
        "date": day.isoformat(),
        "lastNumber": last_number,
        "windows": [
            {"window": number, "ticket": f"A{serving[number]:02d}" if number in serving else None}
            for number in range(1, 5)
        ],
        "waiting": [f"A{row['number']:02d}" for row in waiting],
        "nextTicket": f"A{last_number + 1:02d}",
    }


def take_ticket():
    with connection() as conn:
        ensure_schema(conn)
        day = clinic_day()
        ensure_day(conn, day)
        # Serialize issuance and completion for this date to avoid duplicate calls.
        last_number = conn.execute(
            "SELECT last_number FROM daily WHERE day=%s FOR UPDATE", (day,)
        ).fetchone()["last_number"]
        number = last_number + 1
        busy = {
            row["window"]
            for row in conn.execute(
                'SELECT "window" FROM tickets WHERE day=%s AND status=\'serving\'',
                (day,),
            ).fetchall()
        }
        window = next((candidate for candidate in range(1, 5) if candidate not in busy), None)
        conn.execute("UPDATE daily SET last_number=%s WHERE day=%s", (number, day))
        conn.execute(
            'INSERT INTO tickets(day, number, status, "window") VALUES (%s, %s, %s, %s)',
            (day, number, "serving" if window else "waiting", window),
        )
        return {"ticket": f"A{number:02d}", "window": window, "state": snapshot(conn)}


def finish_window(window):
    if window not in range(1, 5):
        raise ValueError("Ventanilla inválida")
    with connection() as conn:
        ensure_schema(conn)
        day = clinic_day()
        ensure_day(conn, day)
        conn.execute("SELECT last_number FROM daily WHERE day=%s FOR UPDATE", (day,)).fetchone()
        current = conn.execute(
            'SELECT number FROM tickets WHERE day=%s AND status=\'serving\' AND "window"=%s',
            (day, window),
        ).fetchone()
        if current:
            conn.execute(
                'UPDATE tickets SET status=\'done\', "window"=NULL WHERE day=%s AND number=%s',
                (day, current["number"]),
            )
        next_ticket = conn.execute(
            "SELECT number FROM tickets WHERE day=%s AND status='waiting' ORDER BY number LIMIT 1",
            (day,),
        ).fetchone()
        if next_ticket:
            conn.execute(
                'UPDATE tickets SET status=\'serving\', "window"=%s WHERE day=%s AND number=%s',
                (window, day, next_ticket["number"]),
            )
        return {"state": snapshot(conn)}


def get_state():
    with connection() as conn:
        ensure_schema(conn)
        return snapshot(conn)
