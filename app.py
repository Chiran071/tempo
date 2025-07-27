from flask import Flask, render_template, request, redirect, session
from api import search_movies
import sqlite3

app = Flask(__name__)
app.secret_key = "hello world"

@app.route("/")
def index():
    watchlist = []

    if 'email' in session:
        try:
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM loginInfo WHERE email = ?", (session['email'],))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row[0]
                cursor.execute("""
                    SELECT movie.id, movie.title, movie.poster 
                    FROM movie
                    JOIN watchlist ON movie.id = watchlist.movie_id
                    WHERE watchlist.user_id = ?
                """, (user_id,))
                watchlist = cursor.fetchall()
        except Exception as e:
            return render_template("error.html", error="Failed to load watchlist: " + str(e))
        finally:
            conn.close()

    return render_template("home.html", watchlist=watchlist)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()
            Email = request.form.get('email')
            Password = request.form.get("password")

            cursor.execute("SELECT email, password FROM loginInfo WHERE email=? AND password=?", (Email, Password))
            user = cursor.fetchone()

            if user:
                session['email'] = Email
                return redirect("/")
            else:
                return render_template("login.html", error="Incorrect id or password", action="/login")
        except Exception as e:
            return render_template("error.html", error="Something went wrong: " + str(e))
        finally:
            conn.close()
    else:
        return render_template("login.html", action="/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()
            Email = request.form.get('email')
            Password = request.form.get("password")

            if not Email or not Password:
                return render_template("register.html", action="/register", error="Need to enter both email and password")
            if not Email.endswith("@gmail.com"):
                return render_template("register.html", action="/register", error="Email must end with @gmail.com")

            cursor.execute("INSERT INTO loginInfo(email, password) VALUES(?, ?)", (Email, Password))
            conn.commit()
            return redirect("/login")
        except Exception as e:
            return render_template("error.html", error="Something went wrong: " + str(e))
        finally:
            conn.close()
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect("/")

@app.route("/search")
def search():
    title = request.args.get("query")
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    results = []

    # Search in local DB
    cursor.execute("SELECT * FROM movie WHERE title LIKE ?", ('%' + title + '%',))
    local_results = cursor.fetchall()

    if local_results:
        for movie in local_results:
            results.append({"title": movie[2], "poster": movie[1], "id": movie[0]})
    else:
        # Fetch from API and insert into DB
        api_results = search_movies(title)
        for movie in api_results:
            cursor.execute("SELECT id FROM movie WHERE title = ? AND poster = ?", (movie["title"], movie["poster"]))
            existing = cursor.fetchone()
            if existing:
                movie_id = existing[0]
            else:
                cursor.execute("INSERT INTO movie (poster, title) VALUES (?, ?)", (movie["poster"], movie["title"]))
                conn.commit()
                movie_id = cursor.lastrowid

            results.append({"title": movie["title"], "poster": movie["poster"], "id": movie_id})

    # Get user's watchlist movie IDs if logged in
    watchlist_ids = []
    if 'email' in session:
        cursor.execute("SELECT id FROM loginInfo WHERE email = ?", (session['email'],))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            cursor.execute("SELECT movie_id FROM watchlist WHERE user_id = ?", (user_id,))
            watchlist_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template("search.html", results=results, watchlist_ids=watchlist_ids)

@app.route("/addtowatchlist", methods=["POST"])
def addtowatchlist():
    if 'email' not in session:
        return redirect("/login")

    movie_id = request.form.get("movie_id")

    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM loginInfo WHERE email = ?", (session['email'],))
        user = cursor.fetchone()
        if not user:
            return redirect("/login")

        user_id = user[0]
        cursor.execute("INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id))
        conn.commit()
        return redirect("/")
    except Exception as e:
        return render_template("error.html", error="Failed to add to watchlist: " + str(e))
    finally:
        conn.close()

@app.route("/removefromwatchlist", methods=["POST"])
def removefromwatchlist():
    if 'email' not in session:
        return redirect("/login")

    movie_id = request.form.get("movie_id")

    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM loginInfo WHERE email = ?", (session['email'],))
        user = cursor.fetchone()
        if not user:
            return redirect("/login")

        user_id = user[0]
        cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
        conn.commit()
        return redirect("/")
    except Exception as e:
        return render_template("error.html", error="Failed to remove from watchlist: " + str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
