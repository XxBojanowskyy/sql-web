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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS balances (
            username TEXT PRIMARY KEY,
            balance REAL
        )
    """)

    # Dodaj użytkowników
    cur.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123')")
    cur.execute("INSERT OR IGNORE INTO users VALUES ('user1', 'test')")

    # Dodaj balansy
    cur.execute("INSERT OR IGNORE INTO balances VALUES ('admin', 100000)")
    cur.execute("INSERT OR IGNORE INTO balances VALUES ('user1', 10)")

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
    # --- najpierw normalizacja inputu ---
    from_user = request.form.get("from_user", "").strip().lower()
    to_user = request.form.get("to_user", "").strip().lower()

    amount = float(request.form.get("amount"))

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # --- sprawdzenie odbiorcy ---
    cur.execute("SELECT balance FROM balances WHERE username=?", (to_user,))
    to_row = cur.fetchone()
    if not to_row:
        conn.close()
        return {"success": False, "error": "Odbiorca nie istnieje"}

    # --- sprawdzenie nadawcy ---
    cur.execute("SELECT balance FROM balances WHERE username=?", (from_user,))
    from_row = cur.fetchone()
    if not from_row:
        conn.close()
        return {"success": False, "error": "Nadawca nie istnieje"}

    from_balance = from_row[0]

    # --- admin ma nieskończoną kasę ---
    if from_user == "admin":
        from_balance = float("inf")

    # --- za mało środków ---
    if from_balance < amount:
        conn.close()
        return {"success": False, "error": "Brak środków"}

    # --- odejmij środki zwykłym użytkownikom ---
    if from_user != "admin":
        cur.execute("UPDATE balances SET balance = balance - ? WHERE username=?", (amount, from_user))

    # --- dodaj środki odbiorcy ---
    cur.execute("UPDATE balances SET balance = balance + ? WHERE username=?", (amount, to_user))

    conn.commit()

    # --- pobierz balans odbiorcy ---
    cur.execute("SELECT balance FROM balances WHERE username=?", (to_user,))
    after_balance = cur.fetchone()[0]
    conn.close()

    # --- CSRF flaga ---
    if from_user == "admin" and to_user == "user1":
        return {
            "success": True,
            "flag": "CTF{To_Jest_CSRF}",
            "new_balance": after_balance
        }

    return {
        "success": True,
        "new_balance": after_balance
    }

@app.route("/api/balance", methods=["GET"])
def balance():
    user = "user1"
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM balances WHERE username=?", (user,))
    row = cur.fetchone()
    conn.close()
    return {"balance": row[0]}
