from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
# import sqlalchemy as sa
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
            uPassword VARCHAR(255) NOT NULL
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
            cur.execute("""Insert into user_table (email, username, uPassword) values
                        (%s, %s, %s);""",
                        (email, username, hashed_pw))

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
            """Select username, uPassword from user_table where username = %s;""", (username))

        user = cur.fetchone()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
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

    cur.execute("""Select u.user_id, u.username, u.password, s.reminders, s.darkMode, s.pinUrgantTask, s.autoHideTask 
                    from users u
                    join settings_table s ON users.user_id = settings_table.user_id
                    where username = 'Bob'
                """)

    result = cur.fetchone()
    return render_template("account.html", username=result.username, email=result.email, reminders=result.reminders, darkMode=result.darkMode, pinUrgantTask=result.pinUrgantTask, autoHideTask=result.autoHideTask)


# ALLOWED_KEYS_ACCOUNT = {"reminders",
#                         "darkMode", "pinUrgantTask", "autoHideTask"}


# @app.route("/account/toggle", methods=["PATCH"])
# def toggle_setting_account():
#     if "user_id" not in session:
#         return jsonify({"error": "Not logged in"}), 401

#     data = request.get_json()
#     key = data.get("key")
#     value = data.get("value")

#     # Block anything not in the allowed list
#     if key not in ALLOWED_KEYS_ACCOUNT:
#         return jsonify({"error": "Invalid setting"}), 400

#     user_id = session["user_id"]

#     with engine.connect() as conn:
#         conn.execute(
#             settings_table.update()
#             .where(settings_table.c.user_id == user_id)
#             .values(**{key: value})
#         )
#         conn.commit()

#     return jsonify({"key": key, "value": value})


# ALLOWED_KEYS_SETTINGS = {"reminders", "alerts",
#                          "darkMode", "pinUrgantTask", "autoHideTask"}


# @app.route("/settings")
# def settings():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     user_id = session["user_id"]

#     with engine.connect() as conn:
#         query = (
#             sa.select(settings_table.c.reminders,
#                       settings_table.c.alerts, settings_table.c.darkMode, settings_table.c.textSize, settings_table.c.language, settings_table.c.pinUrgantTask, settings_table.c.autoHideTask, settings_table.c.sortBy)
#             .join(settings_table, user_table.c.id == settings_table.c.user_id)
#             .where(user_table.c.id == user_id)
#         )

#         result = conn.execute(query).fetchone()
#     return render_template("settings.html", reminders=result.reminders, alerts=result.alerts, darkMode=result.darkMode, textSize=result.textSize, language=result.language, pinUrgantTask=result.pinUrgantTask, autoHideTask=result.autoHideTask, sortBy=result.sortBy)


# @app.route("/settings/toggle", methods=["PATCH"])
# def toggle_setting():
#     if "user_id" not in session:
#         return jsonify({"error": "Not logged in"})

#     data = request.get_json()
#     key = data.get("key")
#     value = data.get("value")

#     # Block anything not in the allowed list
#     if key not in ALLOWED_KEYS_SETTINGS:
#         return jsonify({"error": "Invalid setting"})

#     user_id = session["user_id"]

#     with engine.connect() as conn:
#         conn.execute(
#             settings_table.update()
#             .where(settings_table.c.user_id == user_id)
#             .values(**{key: value})
#         )
#         conn.commit()

#     return jsonify({"key": key, "value": value})


# @app.route("/account/edit", methods=["PATCH"])
# def saveAcc():
#     if "user_id" not in session:
#         return jsonify({"error": "Not logged in"})

#     user_id = session.get("user_id")

#     data = request.json
#     email = data.get("newEmail")
#     username = data.get("newUsername")

#     with engine.connect() as conn:
#         conn.execute(
#             user_table.update()
#             .where(user_table.c.id == user_id)
#             .values(email=email, username=username)
#         )
#         conn.commit()

#     return jsonify({'status': 'success'})


# @app.route("/deleteAcc")
# def deleteAcc():
#     if "user_id" not in session:
#         return jsonify({"error": "Not logged in"})

#     user_id = session.get("user_id")

#     with engine.connect() as conn:
#         conn.execute(
#             user_table.delete()
#             .where(user_table.c.id == user_id)
#         )
#         conn.commit()

#     with engine.connect() as conn:
#         conn.execute(
#             settings_table.delete()
#             .where(settings_table.c.user_id == user_id)
#         )
#         conn.commit()

#     return redirect(url_for("login"))


app.run(debug=True)
