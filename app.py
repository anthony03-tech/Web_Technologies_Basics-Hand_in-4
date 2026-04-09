from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

app = Flask(__name__)
app.secret_key = "super-secret-key"

# Database
conn = psycopg2.connect(host="localhost", dbname="postgres",
                        user="postgres", password="admin", port="5432")
cur = conn.cursor()

# User table
cur.execute("""CREATE TABLE IF NOT EXISTS user_table (
            user_id SMALLSERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
            );
""")

# Settings table
cur.execute("""CREATE TABLE IF NOT EXISTS settings_table (
            settings_id SMALLSERIAL PRIMARY KEY,
            user_id INT,
            reminders BOOLEAN NOT NULL,
            alerts BOOLEAN NOT NULL,
            darkMode BOOLEAN NOT NULL,
            textSize CHAR (1) NOT NULL,
            language VARCHAR(255) NOT NULL,
            pinUrgantTask BOOLEAN NOT NULL,
            autoHideTask BOOLEAN NOT NULL,
            sortBy VARCHAR(255) NOT NULL,
            CONSTRAINT fk_user_table
                FOREIGN KEY(user_id)
                    REFERENCES user_table(user_id)
            );
""")

conn.commit()


@app.route("/")
def homePage():
    return redirect(url_for("login"))


@app.route("/createAccount", methods=["GET", "POST"])
def createAccount():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        hashed_pw = generate_password_hash(password)

        try:
            cur.execute("""Insert into user_table (email, username, password) values
                        (%s, %s, %s) RETURNING user_id;""", (email, username, hashed_pw))

            user_id = cur.fetchone()[0]

            cur.execute("""Insert into settings_table (user_id, reminders, alerts, darkMode, textSize, language, pinUrgantTask, autoHideTask, sortBy) values
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (user_id, True, True, False, "M", "English", True, False, "ByDate"))

            conn.commit()

            return redirect(url_for("login"))

        except Exception:
            error = "User already exists"

    return render_template("createAccount.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur.execute(
            "Select user_id, username, password from user_table where username = %s;", (username,))

        user = cur.fetchone()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect(url_for("toDoList"))
        else:
            error = "Invalide username or password"

    return render_template("login.html", error=error)


@app.route("/to-do-list")
def toDoList():
    return render_template("to-do-list.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/forgotPassword")
def forgotPassword():
    return render_template("forgotPassword.html")


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cur.execute("""Select u.user_id, u.username, u.email, s.reminders, s.darkMode, s.pinUrgantTask, s.autoHideTask
                    from user_table u
                    join settings_table s ON u.user_id = s.user_id
                    where u.user_id = %s""",
                (user_id,))

    result = cur.fetchone()
    return render_template("account.html", username=result[1], email=result[2], reminders=result[3], darkMode=result[4], pinUrgantTask=result[5], autoHideTask=result[6])


ALLOWED_KEYS_ACCOUNT = {"reminders",
                        "darkMode", "pinUrgantTask", "autoHideTask"}


@app.route("/account/toggle", methods=["PATCH"])
def toggle_setting_account():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    # Block anything not in the allowed list
    if key not in ALLOWED_KEYS_ACCOUNT:
        return jsonify({"error": "Invalid setting"}), 400

    user_id = session["user_id"]

    cur.execute(f"Update settings_table set {key} = %s where user_id = %s",
                (value, user_id,))

    conn.commit()

    return jsonify({"key": key, "value": value})


@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cur.execute("""Select u.user_id, s.reminders, s.alerts, s.darkMode, s.textSize, s.language, s.pinUrgantTask, s.autoHideTask, s.sortBy
                    from user_table u
                    join settings_table s ON u.user_id = s.user_id
                    where u.user_id = %s""",
                (user_id,))

    result = cur.fetchone()
    return render_template("settings.html", reminders=result[1], alerts=result[2], darkMode=result[3], textSize=result[4], language=result[5], pinUrgantTask=result[6], autoHideTask=result[7], sortBy=result[8])


ALLOWED_KEYS_SETTINGS = {"reminders", "alerts",
                         "darkMode", "pinUrgantTask", "autoHideTask"}


@app.route("/settings/toggle", methods=["PATCH"])
def toggle_setting():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    # Block anything not in the allowed list
    if key not in ALLOWED_KEYS_SETTINGS:
        return jsonify({"error": "Invalid setting"})

    user_id = session["user_id"]

    cur.execute(
        f"Update settings_table set {key} = %s where user_id = %s", (value, user_id,))

    conn.commit()

    return jsonify({"key": key, "value": value})


@app.route("/account/edit", methods=["PATCH"])
def saveAcc():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})

    user_id = session.get("user_id")

    data = request.json
    email = data.get("newEmail")
    username = data.get("newUsername")

    cur.execute("""Update user_table set username = %s, email = %s
                    where user_id = %s;""",
                (username, email, user_id))

    conn.commit()

    return jsonify({'status': 'success'})


@app.route("/deleteAcc")
def deleteAcc():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session.get("user_id")

    cur.execute("""Delete from user_table where user_id = %s""", (user_id,))
    conn.commit()

    cur.execute("""Delete from settings_table where user_id = %s""", (user_id,))
    conn.commit()

    return redirect(url_for("login"))


app.run(debug=True)
