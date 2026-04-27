"""
SECURE LOGIN SYSTEM
Demonstrates: bcrypt password hashing with per-user salt, secure sessions
Defense: even if DB is stolen, passwords cannot be recovered without cracking each hash
"""

from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
import bcrypt
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # SECURE: randomly generated secret key

DB_PATH = "secure_users.db"

# --- HTML Templates ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Secure Login</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #58d68d; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #161b22; padding: 2rem; border: 1px solid #58d68d; width: 300px; }
  h2 { margin-top: 0; }
  input { width: 100%; padding: 8px; margin: 6px 0 12px; background: #0d1117; border: 1px solid #444; color: #eee; box-sizing: border-box; }
  button { width: 100%; padding: 10px; background: #58d68d; border: none; color: #0d1117; cursor: pointer; font-size: 1rem; font-weight: bold; }
  .info { background: #0a2a1a; border: 1px solid #58d68d; padding: 8px; font-size: 0.75rem; margin-bottom: 1rem; }
  a { color: #82e9a8; }
  .msg { color: #ff8888; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="box">
  <h2>🔒 SECURE LOGIN</h2>
  <div class="info">Passwords protected with bcrypt + salt. DB theft reveals nothing useful.</div>
  {% if msg %}<p class="msg">{{ msg }}</p>{% endif %}
  <form method="POST" action="/login">
    <label>Username</label>
    <input type="text" name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <button type="submit">Log In</button>
  </form>
  <p><a href="/register">Register</a> | <a href="/dump_db">View DB (defense demo)</a></p>
</div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head><title>Register</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #58d68d; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #161b22; padding: 2rem; border: 1px solid #58d68d; width: 300px; }
  h2 { margin-top: 0; }
  input { width: 100%; padding: 8px; margin: 6px 0 12px; background: #0d1117; border: 1px solid #444; color: #eee; box-sizing: border-box; }
  button { width: 100%; padding: 10px; background: #58d68d; border: none; color: #0d1117; cursor: pointer; font-size: 1rem; font-weight: bold; }
  a { color: #82e9a8; }
  .msg { color: #ff8888; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="box">
  <h2>Register (Secure)</h2>
  {% if msg %}<p class="msg">{{ msg }}</p>{% endif %}
  <form method="POST" action="/register">
    <label>Username</label>
    <input type="text" name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <button type="submit">Register</button>
  </form>
  <p><a href="/">Back to Login</a></p>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #58d68d; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #161b22; padding: 2rem; border: 1px solid #58d68d; width: 400px; }
  a { color: #82e9a8; }
</style>
</head>
<body>
<div class="box">
  <h2>Welcome, {{ username }}!</h2>
  <p>You are logged into the <strong>secure</strong> system.</p>
  <p><a href="/logout">Logout</a> | <a href="/dump_db">View DB (defense demo)</a></p>
</div>
</body>
</html>
"""

DUMP_HTML = """
<!DOCTYPE html>
<html>
<head><title>DB Dump - Defense Demo</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #eee; padding: 2rem; }
  h2 { color: #58d68d; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #444; padding: 8px 16px; text-align: left; font-size: 0.85rem; }
  th { background: #58d68d; color: #0d1117; }
  tr:nth-child(even) { background: #161b22; }
  .info { background: #0a2a1a; border: 1px solid #58d68d; padding: 12px; margin-bottom: 1rem; }
  a { color: #82e9a8; }
  .hash { color: #aaa; font-size: 0.75rem; word-break: break-all; }
</style>
</head>
<body>
  <h2>🔒 Database Dump (Defense Demo)</h2>
  <div class="info">
    Even with full database access, an attacker only sees bcrypt hashes.
    Each hash includes its own salt. Cracking requires brute-forcing each hash individually — computationally expensive by design.
  </div>
  <table>
    <tr><th>ID</th><th>Username</th><th>Password Hash (bcrypt)</th></tr>
    {% for row in rows %}
    <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td class="hash">{{ row[2] }}</td></tr>
    {% endfor %}
  </table>
  <p><a href="/">Back to Login</a></p>
</body>
</html>
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    if "username" in session:
        return render_template_string(DASHBOARD_HTML, username=session["username"])
    return render_template_string(LOGIN_HTML, msg=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        # SECURE: bcrypt automatically generates and embeds a unique salt
        # work factor 12 = 2^12 iterations, making brute force slow
        password_hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash.decode("utf-8"))
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_HTML, msg="Username already exists.")
    return render_template_string(REGISTER_HTML, msg=None)


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"].encode("utf-8")

    conn = get_db()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()

    if row:
        stored_hash = row[0].encode("utf-8")
        # SECURE: bcrypt.checkpw re-hashes with the embedded salt and compares
        if bcrypt.checkpw(password, stored_hash):
            session["username"] = username
            return redirect(url_for("index"))

    return render_template_string(LOGIN_HTML, msg="Invalid credentials.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dump_db")
def dump_db():
    """Defense demo: shows bcrypt hashes — useless to attacker without cracking"""
    conn = get_db()
    rows = conn.execute("SELECT id, username, password_hash FROM users").fetchall()
    conn.close()
    return render_template_string(DUMP_HTML, rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
