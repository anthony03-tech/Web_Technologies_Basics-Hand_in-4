from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa
import psycopg2

app = Flask(__name__)
app.secret_key = "super-secret-key"

# users = {
#     1:  {"name": "Alex Martin",    "email": "alex.martin@email.com"},
#     2: {"name": "Bob Nakamura",  "email": "bob@example.com"},
#     3: {"name": "Clara Osei",    "email": "clara@example.com"},
# }

# python -m sqlite3 users.db
# Database
engine = sa.create_engine("sqlite:///users.db", echo=True)
metadata = sa.MetaData()

# User table
user_table = sa.Table(
    "user",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("email", sa.String(255), unique=True, nullable=False),
    sa.Column("username", sa.String(255), unique=True, nullable=False),
    sa.Column("password", sa.String(255), nullable=False),
)

settings_table = sa.Table(
    "settings",
    metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey(
        "user.id"), primary_key=True),
    sa.Column("reminders", sa.Boolean, nullable=False),
    sa.Column("alerts", sa.Boolean, nullable=False),
    sa.Column("darkMode", sa.Boolean, nullable=False),
    sa.Column("textSize", sa.CHAR(1), nullable=False),
    sa.Column("language", sa.String(255), nullable=False),
    sa.Column("pinUrgantTask", sa.Boolean, nullable=False),
    sa.Column("autoHideTask", sa.Boolean, nullable=False),
    sa.Column("sortBy", sa.String(255), nullable=False),
)

metadata.create_all(engine)


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
            with engine.connect() as conn:
                result = conn.execute(
                    user_table.insert().values(
                        username=username,
                        password=hashed_pw,
                        email=email
                    )
                )

                user_id = result.inserted_primary_key[0]

                conn.execute(
                    settings_table.insert().values(
                        user_id=user_id,
                        reminders=True,
                        alerts=True,
                        darkMode=False,
                        textSize="M",
                        language="English",
                        pinUrgantTask=True,
                        autoHideTask=False,
                        sortBy="By Date"
                    )
                )

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

        with engine.connect() as conn:
            query = sa.select(user_table).where(
                user_table.c.username == username
            )
            user = conn.execute(query).fetchone()

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

    with engine.connect() as conn:
        query = (
            sa.select(user_table.c.username, user_table.c.email, settings_table.c.reminders, settings_table.c.darkMode,
                      settings_table.c.pinUrgantTask, settings_table.c.autoHideTask)
            .join(settings_table, user_table.c.id == settings_table.c.user_id)
            .where(user_table.c.id == user_id)
        )

        result = conn.execute(query).fetchone()
    return render_template("account.html", username=result.username, email=result.email, reminders=result.reminders, darkMode=result.darkMode, pinUrgantTask=result.pinUrgantTask, autoHideTask=result.autoHideTask)


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

    with engine.connect() as conn:
        conn.execute(
            settings_table.update()
            .where(settings_table.c.user_id == user_id)
            .values(**{key: value})
        )
        conn.commit()

    return jsonify({"key": key, "value": value})

# @app.route("/account/<int:user_id>")
# def get_user(user_id):
#     user = users.get(user_id)
#     return jsonify({"id": user_id, **user})


ALLOWED_KEYS_SETTINGS = {"reminders", "alerts",
                         "darkMode", "pinUrgantTask", "autoHideTask"}


@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    with engine.connect() as conn:
        query = (
            sa.select(settings_table.c.reminders,
                      settings_table.c.alerts, settings_table.c.darkMode, settings_table.c.textSize, settings_table.c.language, settings_table.c.pinUrgantTask, settings_table.c.autoHideTask, settings_table.c.sortBy)
            .join(settings_table, user_table.c.id == settings_table.c.user_id)
            .where(user_table.c.id == user_id)
        )

        result = conn.execute(query).fetchone()
    return render_template("settings.html", reminders=result.reminders, alerts=result.alerts, darkMode=result.darkMode, textSize=result.textSize, language=result.language, pinUrgantTask=result.pinUrgantTask, autoHideTask=result.autoHideTask, sortBy=result.sortBy)


@app.route("/settings/toggle", methods=["PATCH"])
def toggle_setting():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    # Block anything not in the allowed list
    if key not in ALLOWED_KEYS_SETTINGS:
        return jsonify({"error": "Invalid setting"})

    user_id = session["user_id"]

    with engine.connect() as conn:
        conn.execute(
            settings_table.update()
            .where(settings_table.c.user_id == user_id)
            .values(**{key: value})
        )
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

    with engine.connect() as conn:
        conn.execute(
            user_table.update()
            .where(user_table.c.id == user_id)
            .values(email=email, username=username)
        )
        conn.commit()

    return jsonify({'status': 'success'})


@app.route("/deleteAcc")
def deleteAcc():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})

    user_id = session.get("user_id")

    with engine.connect() as conn:
        conn.execute(
            user_table.delete()
            .where(user_table.c.id == user_id)
        )
        conn.commit()

    with engine.connect() as conn:
        conn.execute(
            settings_table.delete()
            .where(settings_table.c.user_id == user_id)
        )
        conn.commit()

    return redirect(url_for("login"))


app.run(debug=True)
