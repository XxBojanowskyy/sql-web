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

    cur.execute("CREATE TABLE IF NOT EXISTS balances (username TEXT PRIMARY KEY, balance REAL)")
    cur.execute("INSERT OR IGNORE INTO balances VALUES ('admin', 1000)")
    cur.execute("INSERT OR IGNORE INTO balances VALUES ('User1', 10)")
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

@app.route("/csrf")
def csrf_page():
    return send_from_directory(".", "CSRF.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cur.execute(query)
    user = cur.fetchone()
    conn.close()

    if user:
        return "Zalogowano poprawnie! Flaga to: CTF{SQL_Injection}"
    else:
        return "Błędne dane logowania"


@app.route("/api/transfer", methods=["POST"])
def transfer():
    from_user = request.form.get("from_user")
    to_user   = request.form.get("to_user")
    amount    = float(request.form.get("amount", 0))

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT balance FROM balances WHERE username=?", (from_user,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "User not found"}

    saldo = row[0]

    if amount <= 0 or amount > saldo:
        conn.close()
        return {"success": False, "error": "Invalid amount"}

    cur.execute("UPDATE balances SET balance = balance - ? WHERE username=?", (amount, from_user))
    cur.execute("UPDATE balances SET balance = balance + ? WHERE username=?", (amount, to_user))
    conn.commit()
    conn.close()

    return {"success": True, "from_user": from_user, "to_user": to_user, "amount": amount}


@app.route("/api/get_balance")
def get_balance():
    user = request.args.get("user")
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM balances WHERE username=?", (user,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {"balance": row[0]}
    return {"balance": None}
