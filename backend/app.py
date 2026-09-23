from flask import Flask, request, jsonify, redirect
import secrets
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://shortener:shortener_pass@postgres:5432/shortener_db",
)

def get_db():
    """Открывает новое соединение с PostgreSQL."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Создаёт таблицу urls, если её ещё нет."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    code      VARCHAR(16) PRIMARY KEY,
                    original  TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "url is required"}), 400

    original = data["url"]
    code = secrets.token_urlsafe(6)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (code, original) VALUES (%s, %s)",
                (code, original),
            )
        conn.commit()

    return jsonify({"short": code, "original": original}), 201

@app.route("/<code>", methods=["GET"])
def follow(code):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT original FROM urls WHERE code = %s", (code,))
            row = cur.fetchone()

    if not row:
        return jsonify({"error": "not found"}), 404

    return redirect(row["original"])

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
