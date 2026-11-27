"""
app.py - Backend of the Library Management System (Flask).

Each function below is a "route": it runs when the browser opens a URL.
The route talks to MySQL (through db.py) and sends back an HTML page.
"""
from datetime import date, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error

import db

app = Flask(__name__)
app.secret_key = "dbms-mini-project"   # needed for flash() messages

LOAN_DAYS = 14                          # a book is issued for 14 days


# ---------------------------------------------------------------- Dashboard
@app.route("/")
def dashboard():
    stats = {
        "books":   db.fetch_one("SELECT COUNT(*) AS n FROM books")["n"],
        "copies":  db.fetch_one("SELECT COALESCE(SUM(quantity), 0) AS n FROM books")["n"],
        "members": db.fetch_one("SELECT COUNT(*) AS n FROM members")["n"],
        "issued":  db.fetch_one("SELECT COUNT(*) AS n FROM issues WHERE return_date IS NULL")["n"],
        "overdue": db.fetch_one(
            "SELECT COUNT(*) AS n FROM issues "
            "WHERE return_date IS NULL AND due_date < CURDATE()")["n"],
    }
    # Aggregate query with GROUP BY: number of titles per category
    categories = db.fetch_all(
        "SELECT category, COUNT(*) AS titles, SUM(quantity) AS copies "
        "FROM books GROUP BY category ORDER BY titles DESC")
    return render_template("dashboard.html", stats=stats, categories=categories)


# ---------------------------------------------------------------- Books
@app.route("/books")
def books():
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        rows = db.fetch_all(
            "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s OR category LIKE %s "
            "ORDER BY title", (like, like, like))
    else:
        rows = db.fetch_all("SELECT * FROM books ORDER BY title")
    return render_template("books.html", books=rows, search=search)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        f = request.form
        qty = int(f["quantity"])
        db.execute(
            "INSERT INTO books (title, author, category, quantity, available) "
            "VALUES (%s, %s, %s, %s, %s)",
            (f["title"], f["author"], f["category"], qty, qty))
        flash("Book added successfully.", "success")
        return redirect(url_for("books"))
    return render_template("book_form.html", book=None)


@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books"))

    if request.method == "POST":
        f = request.form
        new_qty = int(f["quantity"])
        issued_now = book["quantity"] - book["available"]   # copies currently with members
        if new_qty < issued_now:
            flash(f"{issued_now} copies are issued right now; quantity cannot be less than that.", "error")
            return render_template("book_form.html", book=book)
        db.execute(
            "UPDATE books SET title=%s, author=%s, category=%s, quantity=%s, available=%s "
            "WHERE book_id=%s",
            (f["title"], f["author"], f["category"], new_qty, new_qty - issued_now, book_id))
        flash("Book updated.", "success")
        return redirect(url_for("books"))
    return render_template("book_form.html", book=book)


@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    db.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    flash("Book deleted.", "success")
    return redirect(url_for("books"))


# ---------------------------------------------------------------- Members
@app.route("/members")
def members():
    # LEFT JOIN + GROUP BY: show how many books each member has right now
    rows = db.fetch_all(
        "SELECT m.*, COUNT(i.issue_id) AS books_held "
        "FROM members m "
        "LEFT JOIN issues i ON m.member_id = i.member_id AND i.return_date IS NULL "
        "GROUP BY m.member_id ORDER BY m.name")
    return render_template("members.html", members=rows)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                "INSERT INTO members (name, email, phone, joined_on) VALUES (%s, %s, %s, %s)",
                (f["name"], f["email"], f["phone"], date.today()))
            flash("Member added successfully.", "success")
            return redirect(url_for("members"))
        except Error:
            # email column is UNIQUE, so a duplicate email raises an error
            flash("A member with this email already exists.", "error")
    return render_template("member_form.html", member=None)


@app.route("/members/edit/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id):
    member = db.fetch_one("SELECT * FROM members WHERE member_id = %s", (member_id,))
    if member is None:
        flash("Member not found.", "error")
        return redirect(url_for("members"))

    if request.method == "POST":
        f = request.form
        try:
            db.execute(
                "UPDATE members SET name=%s, email=%s, phone=%s WHERE member_id=%s",
                (f["name"], f["email"], f["phone"], member_id))
            flash("Member updated.", "success")
            return redirect(url_for("members"))
        except Error:
            flash("A member with this email already exists.", "error")
    return render_template("member_form.html", member=member)


@app.route("/members/delete/<int:member_id>", methods=["POST"])
def delete_member(member_id):
    held = db.fetch_one(
        "SELECT COUNT(*) AS n FROM issues WHERE member_id = %s AND return_date IS NULL",
        (member_id,))["n"]
    if held:
        flash("This member still has books. Return them before deleting.", "error")
    else:
        db.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
        flash("Member deleted.", "success")
    return redirect(url_for("members"))


# ---------------------------------------------------------------- Issue / Return
@app.route("/issues")
def issues():
    # INNER JOIN of three tables to show readable names instead of ids
    rows = db.fetch_all(
        "SELECT i.issue_id, b.title, m.name, i.issue_date, i.due_date, i.return_date, "
        "       (i.return_date IS NULL AND i.due_date < CURDATE()) AS overdue "
        "FROM issues i "
        "JOIN books b   ON i.book_id = b.book_id "
        "JOIN members m ON i.member_id = m.member_id "
        "ORDER BY i.return_date IS NOT NULL, i.issue_date DESC")
    return render_template("issues.html", issues=rows)


@app.route("/issues/new", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        member_id = int(request.form["member_id"])
        today = date.today()

        # TRANSACTION: both statements must succeed together, or neither does.
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            cursor.execute("SELECT available FROM books WHERE book_id = %s FOR UPDATE", (book_id,))
            book = cursor.fetchone()
            if book is None or book["available"] < 1:
                conn.rollback()
                flash("No copies of this book are available.", "error")
                return redirect(url_for("issue_book"))

            cursor.execute(
                "INSERT INTO issues (book_id, member_id, issue_date, due_date) "
                "VALUES (%s, %s, %s, %s)",
                (book_id, member_id, today, today + timedelta(days=LOAN_DAYS)))
            cursor.execute(
                "UPDATE books SET available = available - 1 WHERE book_id = %s", (book_id,))
            conn.commit()
            flash("Book issued successfully.", "success")
        except Error as e:
            conn.rollback()
            flash(f"Could not issue book: {e}", "error")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for("issues"))

    books = db.fetch_all("SELECT book_id, title, available FROM books WHERE available > 0 ORDER BY title")
    members = db.fetch_all("SELECT member_id, name FROM members ORDER BY name")
    return render_template("issue_form.html", books=books, members=members)


@app.route("/issues/return/<int:issue_id>", methods=["POST"])
def return_book(issue_id):
    issue = db.fetch_one(
        "SELECT * FROM issues WHERE issue_id = %s AND return_date IS NULL", (issue_id,))
    if issue is None:
        flash("This book is already returned.", "error")
        return redirect(url_for("issues"))

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute("UPDATE issues SET return_date = %s WHERE issue_id = %s",
                       (date.today(), issue_id))
        cursor.execute("UPDATE books SET available = available + 1 WHERE book_id = %s",
                       (issue["book_id"],))
        conn.commit()
        flash("Book returned.", "success")
    except Error as e:
        conn.rollback()
        flash(f"Could not return book: {e}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("issues"))


if __name__ == "__main__":
    app.run(debug=True)
