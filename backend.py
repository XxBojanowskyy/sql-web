from flask import Flask, request, send_from_directory
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    conn.commit()

    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
        conn.commit()

    conn.close()

init_db()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/xss")
def xss_page():
    return send_from_directory(".", "XSS.html")

@app.route("/sql")
def sql_page():
    return send_from_directory(".", "SQL.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # CELOWA luka SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    print("SQL:", query)

    try:
        cur.execute(query)
        user = cur.fetchone()
    except Exception as e:
        return f"Błąd SQL: {e}"

    conn.close()

    if user:
        return "Zalogowano poprawnie! Flaga to: CTF{SQL_Injection}"
    else:
        return "Błędne dane logowania"
