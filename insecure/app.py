"""
INSECURE LOGIN SYSTEM - FOR EDUCATIONAL PURPOSES ONLY
Demonstrates: plain-text password storage, no session protection
Attack: if DB is stolen, all passwords are immediately visible
"""

from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "hardcoded_secret_123"  # INSECURE: hardcoded secret key

DB_PATH = "insecure_users.db"

# --- HTML Templates ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Insecure Login</title>
<style>
  body { font-family: monospace; background: #1a1a1a; color: #ff4444; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #2a2a2a; padding: 2rem; border: 1px solid #ff4444; width: 300px; }
  h2 { margin-top: 0; }
  input { width: 100%; padding: 8px; margin: 6px 0 12px; background: #111; border: 1px solid #555; color: #eee; box-sizing: border-box; }
  button { width: 100%; padding: 10px; background: #ff4444; border: none; color: white; cursor: pointer; font-size: 1rem; }
  .warning { background: #3a1a1a; border: 1px solid #ff4444; padding: 8px; font-size: 0.75rem; margin-bottom: 1rem; }
  a { color: #ff8888; }
  .msg { color: #ff8888; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="box">
  <h2>⚠ INSECURE LOGIN</h2>
  <div class="warning">WARNING: Passwords stored in plain text. This is a security demo.</div>
  {% if msg %}<p class="msg">{{ msg }}</p>{% endif %}
  <form method="POST" action="/login">
    <label>Username</label>
    <input type="text" name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <button type="submit">Log In</button>
  </form>
  <p><a href="/register">Register</a> | <a href="/dump_db">View DB (attack demo)</a></p>
</div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head><title>Register</title>
<style>
  body { font-family: monospace; background: #1a1a1a; color: #ff4444; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #2a2a2a; padding: 2rem; border: 1px solid #ff4444; width: 300px; }
  h2 { margin-top: 0; }
  input { width: 100%; padding: 8px; margin: 6px 0 12px; background: #111; border: 1px solid #555; color: #eee; box-sizing: border-box; }
  button { width: 100%; padding: 10px; background: #ff4444; border: none; color: white; cursor: pointer; font-size: 1rem; }
  a { color: #ff8888; }
  .msg { color: #ff8888; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="box">
  <h2>Register (Insecure)</h2>
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
  body { font-family: monospace; background: #1a1a1a; color: #ff4444; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
  .box { background: #2a2a2a; padding: 2rem; border: 1px solid #ff4444; width: 400px; }
  a { color: #ff8888; }
</style>
</head>
<body>
<div class="box">
  <h2>Welcome, {{ username }}!</h2>
  <p>You are logged into the <strong>insecure</strong> system.</p>
  <p><a href="/logout">Logout</a> | <a href="/dump_db">View DB (attack demo)</a></p>
</div>
</body>
</html>
"""

DUMP_HTML = """
<!DOCTYPE html>
<html>
<head><title>DB Dump - Attack Demo</title>
<style>
  body { font-family: monospace; background: #1a1a1a; color: #eee; padding: 2rem; }
  h2 { color: #ff4444; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #444; padding: 8px 16px; text-align: left; }
  th { background: #ff4444; color: white; }
  tr:nth-child(even) { background: #2a2a2a; }
  .warning { background: #3a1a1a; border: 1px solid #ff4444; padding: 12px; margin-bottom: 1rem; }
  a { color: #ff8888; }
</style>
</head>
<body>
  <h2>⚠ Database Dump (Attack Simulation)</h2>
  <div class="warning">
    An attacker who gains access to this database can see ALL passwords in plain text immediately.
    No cracking required.
  </div>
  <table>
    <tr><th>ID</th><th>Username</th><th>Password (PLAIN TEXT)</th></tr>
    {% for row in rows %}
    <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td style="color:#ff4444;font-weight:bold">{{ row[2] }}</td></tr>
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
            password TEXT NOT NULL
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
        password = request.form["password"]  # INSECURE: stored as plain text
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_HTML, msg="Username already exists.")
    return render_template_string(REGISTER_HTML, msg=None)


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    conn = get_db()
    # INSECURE: comparing plain text passwords
    row = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    conn.close()
    if row:
        session["username"] = username
        return redirect(url_for("index"))
    return render_template_string(LOGIN_HTML, msg="Invalid credentials.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dump_db")
def dump_db():
    """Attack demo: shows all passwords in plain text"""
    conn = get_db()
    rows = conn.execute("SELECT id, username, password FROM users").fetchall()
    conn.close()
    return render_template_string(DUMP_HTML, rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
