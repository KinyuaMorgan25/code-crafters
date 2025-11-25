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
pages/
utils/
.streamlit/
```

## Local Setup

1. Create and seed the MySQL database using the provided schema.
2. Create a virtual environment and install dependencies:

```
pip install -r requirements.txt
```

3. Provide DB credentials via environment variables (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`) or Streamlit secrets.
4. Run the app:

```
streamlit run app.py
```

Use the default admin email `kinyuamorgan90@gmail.com` to access the admin portal.

