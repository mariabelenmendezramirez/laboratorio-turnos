"""API local para gestionar turnos diarios de un laboratorio."""
from datetime import date
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

HOST, PORT = "127.0.0.1", 8000
DB = Path(__file__).with_name("turnos.sqlite3")


def connect():
    conn = sqlite3.connect(DB, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, last_number INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets (
            day TEXT NOT NULL, number INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('waiting','serving','done')),
            window INTEGER, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(day, number), UNIQUE(day, window)
        );
    """)
    return conn


def today(conn):
    day = date.today().isoformat()
    conn.execute("INSERT OR IGNORE INTO daily(day,last_number) VALUES (?,0)", (day,))
    return day


def snapshot(conn):
    day = today(conn)
    windows = []
    for number in range(1, 5):
        row = conn.execute("SELECT number FROM tickets WHERE day=? AND status='serving' AND window=?", (day, number)).fetchone()
        windows.append({"window": number, "ticket": f"A{row['number']:02d}" if row else None})
    waiting = conn.execute("SELECT number FROM tickets WHERE day=? AND status='waiting' ORDER BY number", (day,)).fetchall()
    last = conn.execute("SELECT last_number FROM daily WHERE day=?", (day,)).fetchone()[0]
    return {"date": day, "lastNumber": last, "windows": windows,
            "waiting": [f"A{r['number']:02d}" for r in waiting],
            "nextTicket": f"A{last+1:02d}"}


def assign(conn, day, window):
    row = conn.execute("SELECT number FROM tickets WHERE day=? AND status='waiting' ORDER BY number LIMIT 1", (day,)).fetchone()
    if row:
        conn.execute("UPDATE tickets SET status='serving',window=? WHERE day=? AND number=?", (window, day, row['number']))


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self): self.send_json(200, {})

    def do_GET(self):
        if urlparse(self.path).path != '/api/state':
            return self.send_json(404, {"error": "Ruta no encontrada"})
        with closing(connect()) as conn: self.send_json(200, snapshot(conn))

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"error": "JSON inválido"})
        with closing(connect()) as conn:
            day = today(conn)
            if path == '/api/tickets':
                conn.execute('BEGIN IMMEDIATE')
                conn.execute('UPDATE daily SET last_number=last_number+1 WHERE day=?', (day,))
                number = conn.execute('SELECT last_number FROM daily WHERE day=?', (day,)).fetchone()[0]
                free = conn.execute("SELECT window FROM (SELECT 1 AS window UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) WHERE window NOT IN (SELECT window FROM tickets WHERE day=? AND status='serving') ORDER BY window LIMIT 1", (day,)).fetchone()
                window = free['window'] if free else None
                conn.execute('INSERT INTO tickets(day,number,status,window) VALUES (?,?,?,?)', (day, number, 'serving' if window else 'waiting', window))
                conn.commit()
                return self.send_json(201, {"ticket": f"A{number:02d}", "window": window, "state": snapshot(conn)})
            if path == '/api/finish':
                try: window = int(body.get('window'))
                except (TypeError, ValueError): return self.send_json(400, {"error": "Ventanilla inválida"})
                if window not in range(1, 5): return self.send_json(400, {"error": "Ventanilla inválida"})
                conn.execute('BEGIN IMMEDIATE')
                current = conn.execute("SELECT number FROM tickets WHERE day=? AND status='serving' AND window=?", (day, window)).fetchone()
                if current:
                    conn.execute("UPDATE tickets SET status='done',window=NULL WHERE day=? AND number=?", (day, current['number']))
                assign(conn, day, window)
                conn.commit()
                return self.send_json(200, {"state": snapshot(conn)})
            return self.send_json(404, {"error": "Ruta no encontrada"})

    def log_message(self, fmt, *args): print(f"{self.log_date_time_string()} {fmt % args}")


if __name__ == '__main__':
    with closing(connect()) as db: today(db)
    print(f"API de turnos en http://localhost:{PORT} (SQLite: {DB})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()




