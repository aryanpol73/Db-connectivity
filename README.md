# Library Management System — DBMS Mini Project

A simple web app that connects an **HTML/CSS frontend** to a **MySQL database** through a **Python (Flask) backend**.

Features:
- Dashboard with counts (books, members, issued, overdue) and books per category
- Books: add, list, search, edit, delete
- Members: add, list, edit, delete (shows how many books each member holds)
- Issue a book (14-day loan) and return it, using SQL transactions

## Project structure

```
Db-connectivity/
├── app.py            # Flask backend: all routes (URLs) and SQL queries
├── db.py             # MySQL connection + helper functions
├── schema.sql        # Creates database, 3 tables and sample data
├── requirements.txt  # Python packages
├── templates/        # HTML pages (Jinja2)
└── static/style.css  # Styling
```

## Database (3 tables)

| Table   | Primary key | Foreign keys                     |
|---------|-------------|----------------------------------|
| books   | book_id     | –                                |
| members | member_id   | –                                |
| issues  | issue_id    | book_id → books, member_id → members |

## How to run

1. **Install** [Python 3.9+](https://www.python.org/downloads/) and [MySQL Server 8](https://dev.mysql.com/downloads/mysql/).

2. **Create the database** (enter your MySQL root password when asked):
   ```bash
   mysql -u root -p < schema.sql
   ```
   Or open `schema.sql` in MySQL Workbench and click ⚡ Execute.

3. **Set your MySQL password** — open `db.py` and change `"password"` to your own
   (default in the file is `root`). Or set environment variables `DB_USER`, `DB_PASSWORD`.

4. **Install Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the app:**
   ```bash
   python app.py
   ```
   Open **http://127.0.0.1:5000** in your browser.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Access denied for user 'root'` | Wrong password in `db.py` |
| `Unknown database 'library_db'` | Run `schema.sql` first (step 2) |
| `Can't connect to MySQL server` | Start the MySQL service |
| `ModuleNotFoundError: flask` | Run `pip install -r requirements.txt` |
