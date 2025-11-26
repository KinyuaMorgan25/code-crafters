# Library Management System

Full-stack Library Management System built with Streamlit and MySQL. The app delivers role-based access, CRUD operations for books, users, transactions, and reservations, and a self-service catalog for members.

## Features

- Secure authentication backed by Werkzeug's scrypt hashing.
- Role-aware navigation (member vs admin/librarian).
- Book catalog with search, pagination, borrow, and reservation flows.
- User dashboard showing active loans, fines, and history.
- Admin panel for inventory, users, transactions, and KPI reports.
- Business rules: 14-day loan period, max 5 concurrent loans, and fine thresholds.

## Project Structure

```
app.py
config.py
requirements.txt
auth/
database/
views/
utils/
.streamlit/
```

## Local Setup

1. Create a virtual environment and install dependencies:

```
pip install -r requirements.txt
```

2. Choose your database backend:
   - **MySQL (production parity)**: create and seed the schema manually, then provide credentials via env vars (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, optional `MYSQL_PORT`) or Streamlit secrets.
   - **SQLite (zero-config local dev)**: set `DB_ENGINE=sqlite` (and optionally `SQLITE_PATH=/custom/path/library.db`). The first launch will auto-create tables, 10+ categories, 15+ books, and sample copies you can borrow immediately.

3. Run the app:

```
streamlit run app.py
```

### Default credentials & roles

- Admin: `kinyuamorgan90@gmail.com` / `admin123` (also available via the **Admin Portal** tab on the landing page)
- Patron: `patron@example.com` / `patron123`

Use the Admin Portal tab to log in directly to the management experience; successful admin sign-in jumps straight into the Admin panel sidebar section.

