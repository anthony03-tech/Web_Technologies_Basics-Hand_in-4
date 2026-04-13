## 📌 What is the project?

A personal to-do list web app where users can:
- Create an account and log in securely
- Add, view, and delete tasks categorized as Normal, Important, or Urgent
- See tasks grouped into Overdue, Today, and Coming Up sections
- Manage profile info and toggle preferences (dark mode, reminders, auto-hide, etc.)
- Reset their password via the forgot password flow

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | PostgreSQL (via psycopg2) |
| Frontend | HTML, CSS, JavaScript |
| Auth | Werkzeug password hashing, Flask sessions |
| Config | python-dotenv |
| Testing | pytest |
| Production server | Gunicorn |

## ⚙️ How do I set it up locally?

### 1. Prerequisites
- Python 3.8+
- PostgreSQL running locally

### 2. Clone the repository
```bash
git clone <your-repo-url>
cd <project-folder>
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:
```env
DB_HOST=localhost
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

### 5. Set up the database

Make sure PostgreSQL is running. The app will automatically create the required tables (`user_table`, `settings_table`, `task_table`) on first run.

### 6. Run the app
```bash
python app.py
```

The app will be available at http://localhost:5000

## 🧪 Testing

The project uses pytest for automated testing. Tests are located in `test_app.py` and use Flask's built-in test client alongside `unittest.mock` to test route behaviour without requiring a live database.

### Run the tests

```bash
pytest test_app.py -v
```

### What's covered

| Test | What it checks |
|---|---|
| `test_update_pw_missing_fields` | `/updatePw` returns `400` when email or password is missing |
| `test_add_task_not_logged_in` | `/addTask` returns `401` with "Not logged in" when there's no session |
| `test_settings_toggle_not_logged_in` | `/settings/toggle` returns `401` for unauthenticated requests |
| `test_settings_toggle_invalid_key` | `/settings/toggle` rejects unknown/injected field names |
| `test_delete_task_missing_body` | `/deleteTask` returns `400` when the request body is empty |

### Manual testing

For flows that involve the database (e.g. creating a task, toggling settings), you can test manually through the browser:

| Feature | How to test |
|---|---|
| Add a task | Click "Add new Task", fill in name, date, and type |
| Delete a task | Click "Delete Task", then the Delete button next to a task |
| Edit profile | Go to Account → Edit |
| Toggle settings | Go to Settings or Account and flip any toggle |
| Change password | Go to Settings → Update, or use Forgot Password on login |
| Delete account | Account page → Delete account |

## 🚀 How do I deploy it?

### Simple VPS / cloud server

1. Push your code to GitHub.
2. Set the environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`) in your hosting platform's dashboard.
3. Set the start command to:
```bash
gunicorn app:app
```

## 📁 Project Structure

```
LU-Hand-in_4-4_Final-Deployment
│   │   .env                       # Environment variables (not committed)
│   │   .gitignore
│   │   app.py                     # Main Flask application & all routes
│   │   conftest.py                # Pytest path configuration
│   │   README.md
│   │   requirements.txt           # Python dependencies
│   │
│   ├───static
│   │       css-createAcc.css
│   │       css-FirstPage.css
│   │       css-forgotPw.css
│   │       css-login.css
│   │       css-SecondPage.css
│   │       css-ThirdPage.css
│   │
│   ├───templates
│   │       account.html
│   │       createAccount.html
│   │       forgotPassword.html
│   │       login.html
│   │       settings.html
│   │       to-do-list.html
│   │
│   └───tests
│           test_app.py             # Automated pytest tests
```