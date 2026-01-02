import os
import sqlite3
import requests
from flask import Flask, request, redirect, session
from openai import OpenAI

# ================== CONFIG ==================
APP_NAME = "CENTRO"
CREATOR = "Sahitya Kumar"

SERPAPI_KEY = os.getenv("68d4ac1688d682428f5847f007a511dab9fd1759970638d456e13f79b5210618")
OPENAI_API_KEY = os.getenv("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")

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ================== APP ==================
app = Flask(__name__)
app.secret_key = "centro_secret_key"

client = OpenAI(api_key=OPENAI_API_KEY)

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect("centro.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS searches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            ip TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def db():
    return sqlite3.connect("centro.db")

# ================== AI ANSWER ==================
def ai_answer(query):
    if not OPENAI_API_KEY:
        return None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Give a short, factual, neutral answer for: {query}"
                }
            ],
            max_tokens=120
        )
        return response.choices[0].message.content
    except:
        return None

# ================== UI ==================
def page(content):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{APP_NAME} – Professional Search</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {{
    --bg:#0b0f19;--card:rgba(255,255,255,0.06);
    --border:rgba(255,255,255,0.12);
    --text:#e8eaf0;--muted:#9aa4bf;--accent:#4f7cff;
}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;font-family:Inter,sans-serif;
background:radial-gradient(circle at top,#121a3a,#0b0f19);
color:var(--text);display:flex;flex-direction:column;align-items:center}}
header{{margin-top:60px;text-align:center}}
.logo{{font-size:44px;font-weight:700;letter-spacing:2px}}
.tagline{{color:var(--muted);font-size:14px;margin-top:6px}}
.search-box{{margin-top:40px;width:100%;display:flex;justify-content:center}}
form{{width:100%;max-width:680px;display:flex;background:var(--card);
border:1px solid var(--border);border-radius:50px;
backdrop-filter:blur(12px);padding:6px}}
input{{flex:1;background:transparent;border:none;outline:none;
padding:18px 20px;color:var(--text);font-size:16px}}
input::placeholder{{color:var(--muted)}}
button{{background:linear-gradient(135deg,#4f7cff,#6aa8ff);
border:none;border-radius:40px;padding:0 28px;color:white;
font-size:15px;font-weight:600;cursor:pointer}}
.results{{width:100%;max-width:900px;margin-top:40px}}
.result{{background:var(--card);border:1px solid var(--border);
border-radius:16px;padding:20px 22px;margin-bottom:18px;
backdrop-filter:blur(12px)}}
.result h3{{margin:0;font-size:18px;font-weight:600}}
.result a{{color:#8fb3ff;text-decoration:none}}
.result p{{margin-top:8px;color:var(--muted);font-size:14px;line-height:1.6}}
footer{{margin-top:auto;padding:30px 0;font-size:13px;color:var(--muted)}}
footer span{{color:var(--accent)}}
</style>
</head>
<body>
<header>
  <div class="logo">{APP_NAME}</div>
  <div class="tagline">Next-Generation Search • Created by {CREATOR}</div>
</header>
{content}
<footer>© 2026 <span>{APP_NAME}</span> • Created by {CREATOR}</footer>
</body>
</html>
"""

# ================== HOME ==================
@app.route("/")
def home():
    return page("""
<div class="search-box">
<form action="/search">
<input name="q" placeholder="Search the web with CENTRO">
<button>Search</button>
</form>
</div>
""")

# ================== SEARCH ==================
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect("/")

    conn = db()
    conn.execute(
        "INSERT INTO searches(query, ip) VALUES(?,?)",
        (q, request.remote_addr)
    )
    conn.commit()

    params = {
        "engine": "google",
        "q": q,
        "api_key": SERPAPI_KEY,
        "num": 8
    }

    res = requests.get("https://serpapi.com/search", params=params).json()

    results_html = ""
    for r in res.get("organic_results", []):
        results_html += f"""
        <div class="result">
            <a href="{r.get('link')}" target="_blank">
                <h3>{r.get('title')}</h3>
            </a>
            <p>{r.get('snippet','')}</p>
        </div>
        """

    answer = ai_answer(q)

    ai_block = f"""
    <div class="result">
        <h3>AI Answer</h3>
        <p>{answer}</p>
    </div>
    """ if answer else ""

    return page(f"""
<div class="search-box">
<form action="/search">
<input name="q" value="{q}" placeholder="Search the web with CENTRO">
<button>Search</button>
</form>
</div>

<div class="results">
{ai_block}
{results_html}
</div>
""")

# ================== ADMIN ==================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["user"] == ADMIN_USER and request.form["pass"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
    return page("""
<h2>Admin Login</h2>
<form method="post">
<input name="user" placeholder="Username"><br><br>
<input name="pass" type="password" placeholder="Password"><br><br>
<button>Login</button>
</form>
""")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    data = conn.execute(
        "SELECT query, time FROM searches ORDER BY time DESC LIMIT 50"
    ).fetchall()

    rows = "".join([f"<li>{d[0]} — {d[1]}</li>" for d in data])

    return page(f"""
<h2>Admin Dashboard</h2>
<ul style="text-align:left;width:50%;margin:auto">{rows}</ul>
<a href="/logout">Logout</a>
""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================== RUN ==================
if __name__ == "__main__":
    app.run(debug=True)
