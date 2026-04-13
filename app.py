from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from datetime import date
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"

# Database
load_dotenv()


def get_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    return conn

# cur.execute("""Drop table if exists settings_table""")
# cur.execute("""Drop table if exists task_table""")
# cur.execute("""Drop table if exists user_table""")

# conn.commit()


conn = get_db()
cur = conn.cursor()

# User table
cur.execute("""Create table if not exists user_table (
            user_id SMALLSERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
            );
""")

# Settings table
cur.execute("""Create table if not exists settings_table (
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
            CONSTRAINT fk_settings_user
                FOREIGN KEY(user_id)
                    REFERENCES user_table(user_id)
            );
""")

# Task table
cur.execute("""Create table if not exists task_table (
            task_id SERIAL PRIMARY KEY,
            user_id INT,
            task_name VARCHAR(255) NOT NULL,
            type VARCHAR(255) NOT NULL,
            deadline DATE NOT NULL,
            status BOOLEAN NOT NULL,
            CONSTRAINT fk_task_user
                FOREIGN KEY(user_id)
                    REFERENCES user_table(user_id)
            );
""")

conn.commit()


def getUserId():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})

    user_id = session.get("user_id")

    return user_id


@app.route("/")
def homePage():
    return redirect(url_for("login"))


@app.route("/updatePw", methods=["PATCH"])
def updatePw():
    data = request.get_json()
    email = data.get("email")
    newPw = data.get("newPw")

    if not email or not newPw:
        return jsonify({"error": "All fields are required"}), 400

    hashed_pw = generate_password_hash(newPw)

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """Select email from user_table where email = %s""", (email,))
        user = cur.fetchone()

        if not user:
            return jsonify({"error": "Email does not exist"}), 404

        cur.execute(
            """Update user_table set password = %s where email = %s""", (hashed_pw, email))
        conn.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to save changes"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/createAccount", methods=["GET", "POST"])
def createAccount():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        if not username or not password or not email:
            return render_template("createAccount.html", error="All fields are required")

        hashed_pw = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                """SELECT email FROM user_table WHERE email = %s""", (email,))
            existing_user = cur.fetchone()

            if existing_user:
                return render_template("createAccount.html", error="Email already exists")

            cur.execute("""Insert into user_table (email, username, password) values
                        (%s, %s, %s) RETURNING user_id;""", (email, username, hashed_pw))

            user_id = cur.fetchone()[0]

            cur.execute("""Insert into settings_table (user_id, reminders, alerts, darkMode, textSize, language, pinUrgantTask, autoHideTask, sortBy) values
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (user_id, True, True, False, "M", "English", True, False, "ByDate"))

            conn.commit()

            return redirect(url_for("login"))

        except Exception as e:
            conn.rollback()
            error = "User already exists"
        finally:
            cur.close()
            conn.close()

    return render_template("createAccount.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            return render_template("login.html", error="All fields are required")

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "Select user_id, username, password from user_table where username = %s;", (username,))
            user = cur.fetchone()
        except Exception as e:
            conn.rollback()
            return render_template("login.html", error="Something went wrong, please try again")
        finally:
            cur.close()
            conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect(url_for("toDoList"))
        else:
            error = "Invalide username or password"

    return render_template("login.html", error=error)


@app.route("/to-do-list")
def toDoList():
    user_id = getUserId()

    today = date.today()
    tasks_today = []
    tasks_week = []
    tasks_overdue = []

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """Select task_name, type, deadline, status from task_table where user_id = %s""", (user_id,))
        rows = cur.fetchall()
    except Exception as e:
        conn.rollback()
        rows = []
    finally:
        cur.close()
        conn.close()

    for row in rows:
        tasks = {"taskName": row[0], "taskType": row[1],
                 "deadline": row[2], "status": row[3]
                 }
        if row[2] == today:
            tasks_today.append(tasks)
        elif row[2] < today:
            tasks_overdue.append(tasks)
        else:
            tasks_week.append(tasks)

    return render_template("to-do-list.html", tasks_today=tasks_today, tasks_overdue=tasks_overdue, tasks_week=tasks_week)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/forgotPassword", methods=["GET", "POST"])
def forgotPassword():
    return render_template("forgotPassword.html")


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""Select u.user_id, u.username, u.email, s.reminders, s.darkMode, s.pinUrgantTask, s.autoHideTask
                        from user_table u
                        join settings_table s ON u.user_id = s.user_id
                        where u.user_id = %s""",
                    (user_id,))

        result = cur.fetchone()
    except Exception as e:
        conn.rollback()
        return redirect(url_for("login"))
    finally:
        cur.close()
        conn.close()

    return render_template("account.html", username=result[1], email=result[2], reminders=result[3],
                           darkMode=result[4], pinUrgantTask=result[5], autoHideTask=result[6])


ALLOWED_KEYS_ACCOUNT = {"reminders",
                        "darkMode", "pinUrgantTask", "autoHideTask"}


@app.route("/account/toggle", methods=["PATCH"])
def toggle_setting_account():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_db()
    cur = conn.cursor()

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    # Block anything not in the allowed list
    if key not in ALLOWED_KEYS_ACCOUNT:
        return jsonify({"error": "Invalid setting"}), 400

    if value is None:
        return jsonify({"error": "Missing value"}), 400

    user_id = session["user_id"]

    try:
        cur.execute(f"Update settings_table set {key} = %s where user_id = %s",
                    (value, user_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to update setting"}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"key": key, "value": value})


@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""Select u.user_id, s.reminders, s.alerts, s.darkMode, s.textSize, s.language, s.pinUrgantTask, s.autoHideTask, s.sortBy
                        from user_table u
                        join settings_table s ON u.user_id = s.user_id
                        where u.user_id = %s""",
                    (user_id,))

        result = cur.fetchone()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return render_template("settings.html", reminders=result[1], alerts=result[2], darkMode=result[3],
                           textSize=result[4], language=result[5], pinUrgantTask=result[6], autoHideTask=result[7], sortBy=result[8])


ALLOWED_KEYS_SETTINGS = {"reminders", "alerts",
                         "darkMode", "pinUrgantTask", "autoHideTask"}


@app.route("/settings/toggle", methods=["PATCH"])
def toggle_setting():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_db()
    cur = conn.cursor()

    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    # Block anything not in the allowed list
    if key not in ALLOWED_KEYS_SETTINGS:
        return jsonify({"error": "Invalid setting"})

    user_id = session["user_id"]

    try:
        cur.execute(
            f"Update settings_table set {key} = %s where user_id = %s", (value, user_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return jsonify({"key": key, "value": value})


@app.route("/account/edit", methods=["PATCH"])
def saveAcc():
    user_id = getUserId()

    conn = get_db()
    cur = conn.cursor()

    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    email = data.get("newEmail")
    username = data.get("newUsername")

    if not email or not username:
        return jsonify({"error": "All fields are required"}), 400

    try:
        cur.execute("""Update user_table set username = %s, email = %s
                        where user_id = %s;""",
                    (username, email, user_id))

        conn.commit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to save changes"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/deleteAcc")
def deleteAcc():
    user_id = getUserId()

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """Delete from settings_table where user_id = %s""", (user_id,))
        cur.execute("""Delete from task_table where user_id = %s""", (user_id,))
        cur.execute("""Delete from user_table where user_id = %s""", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return redirect(url_for("account"))
    finally:
        cur.close()
        conn.close()

    session.clear()
    return redirect(url_for("login"))


@app.route("/addTask", methods=["PATCH"])
def addTask():
    user_id = getUserId()

    conn = get_db()
    cur = conn.cursor()

    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    taskName = data.get("taskName")
    taskDate = data.get("taskDate")
    taskType = data.get("type")

    if not taskName or not taskDate or not taskType:
        return jsonify({"error": "All fields are required"}), 400

    try:
        cur.execute(
            """Select task_name from task_table where user_id = %s AND task_name = %s""", (user_id, taskName))
        result = cur.fetchone()

        if result:
            return jsonify({"error": "Task name already exists!"}), 409

        cur.execute("""Insert into task_table (user_id, task_name, type, deadline, status) values
                    (%s, %s, %s, %s, %s)""",
                    (user_id, taskName, taskType, taskDate, False))
        conn.commit()
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Failed to add task"}), 500
    finally:
        cur.close()
        conn.close()


@app.route("/deleteTask", methods=["DELETE"])
def deleteTask():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db()
    cur = conn.cursor()

    taskName = data.get("taskName")

    try:
        cur.execute(
            """Delete from task_table where task_name = %s""", (taskName,))

        conn.commit()

        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
