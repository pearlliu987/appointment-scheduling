from flask import Flask, render_template, redirect, request, session, url_for
from flask_session import Session
import sqlite3

# Connect to database
connection = sqlite3.connect("appointments.db", check_same_thread=False, isolation_level=None)
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS appointments (name TEXT, date TEXT, time TEXT, timestamp TEXT)")

# Configure app
app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app) 

@app.route("/")
def index():
    session.pop("appt", None)
    
    cursor.execute("SELECT DISTINCT date FROM appointments WHERE name IS null AND date >= DATE('now', 'localtime') AND date <= DATE('now', 'localtime', '+2 day') ORDER BY date")
    dates = cursor.fetchall()
    cursor.execute("SELECT DISTINCT time FROM appointments WHERE name IS null AND date IN (SELECT DISTINCT date FROM appointments WHERE name IS null AND date >= DATE('now', 'localtime') AND date <= DATE('now', 'localtime', '+2 day') ORDER BY date LIMIT 1) ORDER BY time")
    earliest_date_times = cursor.fetchall()
    return render_template("index.html", dates=dates, earliest_date_times=earliest_date_times)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        n = request.form.get("name")
        d = request.form.get("date")
        t = request.form.get("time")

        if len(n) > 0:
            cursor.execute("SELECT rowid FROM appointments WHERE name IS null AND date=? AND time=?", (d, t))
            appt = cursor.fetchone()
            if (appt):
                cursor.execute("UPDATE appointments SET name=?, timestamp=DATETIME('now', 'localtime') WHERE rowid=?", (n, appt[0]))
                session["appt"] = appt[0]
                return render_template("scheduled.html", name=n, date=d, time=t)
        
        return render_template("failure.html")

    return redirect(url_for("index"))

@app.route("/cancel", methods=["GET", "POST"])
def cancel():
    if request.method == "POST":
        appt = str(session["appt"])
        cursor.execute("SELECT name, date, time FROM appointments WHERE rowid=?", (appt,))
        deleted = cursor.fetchone()
        cursor.execute("UPDATE appointments SET name=null, timestamp=null WHERE rowid=?", (appt,))
        session.pop("appt", None)
        return render_template("cancelled.html", name=deleted[0], date=deleted[1], time=deleted[2])
    
    return redirect(url_for("index"))

@app.route("/upcoming")
def upcoming(): 
    cursor.execute("SELECT name, date, time FROM appointments WHERE date >= DATE('now', 'localtime') AND name IS NOT null ORDER BY date")
    upcoming_appts = cursor.fetchall()
    return render_template("upcoming.html", upcoming_appts=upcoming_appts)

@app.route("/times")
def times():
    selected_date = request.args.get("date")
    if selected_date:  
        cursor.execute("SELECT DISTINCT time FROM appointments WHERE name IS null AND date=? ORDER BY time", (selected_date,))
        times = cursor.fetchall()
    else: 
        times = []
    return render_template("times.html", times=times)