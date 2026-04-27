# Secure Login System — ITIS 6200 Course Project

This project demonstrates the difference between a secure and insecure password storage system, focusing on the threat of database theft and the defense of bcrypt password hashing.

---

## Project Structure

```
secure_login/
├── secure/         # Secure version: bcrypt + salted hashing
│   ├── app.py
│   └── requirements.txt
├── insecure/       # Insecure version: plain-text password storage
│   ├── app.py
│   └── requirements.txt
└── README.md
```

---

## Running the Applications

### Prerequisites

- Python 3.8+
- pip

### Secure Version (Port 5000)

```bash
cd secure
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5000

### Insecure Version (Port 5001)

```bash
cd insecure
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5001

---

## Demonstrating the Attack vs. Defense

### Step 1 — Run the insecure version
1. Go to http://localhost:5001
2. Register a new user with any username/password (e.g., `alice` / `password123`)
3. Click **"View DB (attack demo)"**
4. You will see the password stored in **plain text** — an attacker with DB access immediately has full credentials

### Step 2 — Run the secure version
1. Go to http://localhost:5000
2. Register a new user with the same credentials
3. Click **"View DB (defense demo)"**
4. You will see only a **bcrypt hash** — an attacker with DB access sees something like:
   `$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36VdBbBqNH6WJ.../...`
5. Without the original password, this hash is computationally infeasible to reverse

---

## Security Mechanism Summary

| | Insecure Version | Secure Version |
|---|---|---|
| Password storage | Plain text | bcrypt hash |
| Salt | None | Per-user, auto-embedded by bcrypt |
| Work factor | N/A | 12 (2^12 iterations) |
| DB theft impact | All passwords exposed | Hashes only — must brute-force each |
| Secret key | Hardcoded string | `secrets.token_hex(32)` |

---

## Key Code Comparison

**Insecure registration (plain text):**
```python
conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
```

**Secure registration (bcrypt):**
```python
password_hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
```

**Secure login verification:**
```python
if bcrypt.checkpw(password, stored_hash):
    session["username"] = username
```

`bcrypt.checkpw` re-hashes the input with the salt embedded in `stored_hash` and compares — the original password never needs to be stored.
