import os
import string
import random
from tempfile import mkdtemp
from datetime import datetime
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import login_required, approval_list, date_maker, find_id, update_connections, connection_parent, \
    connection_child, connection_spouse, connection_sibling, generations, profile_back, \
    filename_check, genetic, couples, extract_name, removable, born_check

# Configure application
app = Flask(__name__)

# Setting a secret key
key = os.urandom(50)
app.secret_key = key

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Choose uploading folder
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///family_tree.db")


# Opens index page
@app.route("/")
def index():
    return render_template("index.html")


# Go to the tree page
@app.route("/my_tree")
@login_required
def my_tree():
    user_id = session["user_id"]
    table_name = str(user_id)
    user_couples = couples(table_name, user_id)
    user_genetic = genetic(table_name, user_id)
    user_generations = generations(table_name, user_id, user_couples, user_genetic)

    return render_template("my_tree.html", couples=user_couples, genetic=user_genetic,

                           generations=user_generations)


# Page for the specific person from the tree
@app.route("/profile/<person>", methods=["GET", "POST"])
@login_required
def profile(person):

    # Basic information on a person: birth, death, id
    person_name = extract_name(person)
    person_id = find_id(person_name)
    user = session["user_id"]
    person_birth = date_maker(db.execute("SELECT birth FROM people WHERE id = ? AND related_to = ?",
                                         person_id, user)[0]["birth"])
    if db.execute("SELECT death FROM people WHERE id = ? AND related_to = ?", person_id, user)[0]["death"] is not None:
        person_death = date_maker(db.execute("SELECT death FROM people WHERE id = ? AND related_to = ?",
                                             person_id, user)[0]["death"])
    else:
        person_death = None

    # An empty array for person's photos
    photos = []

    # Collect all the photos of the person
    if db.execute("SELECT photo FROM people_photos WHERE person_id = ?", person_id):
        rows = db.execute("SELECT photo FROM people_photos WHERE person_id = ?", person_id)
        for row in rows:
            if row["photo"] not in photos:
                photos.append(row["photo"])

    # Get the person's description from the data base
    if db.execute("SELECT story FROM people_stories WHERE person_id = ?", person_id):
        text = db.execute("SELECT story FROM people_stories WHERE person_id = ?", person_id)[0]["story"]
    else:
        text = None

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # If user sent a text
        if request.form.get("text"):
            text = request.form.get("text")
            if db.execute("SELECT story FROM people_stories WHERE person_id = ?", person_id):
                db.execute("UPDATE people_stories SET story = ? WHERE person_id = ?", text, person_id)
            else:
                db.execute("INSERT INTO people_stories (story, person_id) VALUES (?, ?)", text, person_id)

        # If user wants to delete the photo
        elif request.form.get("yes"):
            photo = request.form.get("yes")
            path = "static/files/" + photo
            os.remove(path)
            db.execute("DELETE FROM people_photos WHERE photo = ? AND person_id = ?", photo, person_id)
            photos.remove(photo)

        # If user sent a photo
        elif "image" in request.files:
            if request.files["image"]:
                file = request.files['image']
                filename = secure_filename(file.filename)

                # In case we already have a file with this name in our folder we need to slightly change it,
                # until the name is unique

                letters = string.ascii_letters
                while filename_check(filename):
                    new = ''.join(random.choice(letters) for i in range(1))
                    filename = new + filename

               # Save file into the uploading folder and the name of the file - to our data base
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                db.execute("INSERT INTO people_photos (photo, person_id) VALUES (?, ?)", filename, person_id)
                photos.append(filename)
            else:
                if person_name.find(" add") != -1 and person_name.count("add") == 2:
                    person_name = person_name[:person_name.find(" add")]
                return profile_back(person_name, person_birth, person_death, text, photos)

    if person_name.find(" add") != -1 and person_name.count("add") == 2:
        person_name = person_name[:person_name.find(" add")]

    # Before returning the template, we need to check several variables -
    # for this we have profile_back function in helpers.py
    return profile_back(person_name, person_birth, person_death, text, photos)


# Add a person to the tree
@app.route("/add")
@login_required
def add():
    return render_template("add.html")


# Opens a page, where user can put information on a new person in the tree
@app.route("/information", methods=["GET", "POST"])
@login_required
def information():

    # Clear global variables, that was storing information on a new person, if any
    for element in dir():
        if element[0:2] != "__":
            del globals()[element]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure name was submitted
        if not request.form.get("first_name") or not request.form.get("last_name"):
            return render_template("information.html", message1="Please type the name")

        # Ensure date of birth was submitted
        elif not request.form.get("birth"):
            return render_template("information.html", message2="Please choose the date of birth")

        # If everything is ok, proceed to remembering the information
        else:
            name = request.form.get("first_name").strip() + " " + request.form.get("last_name").strip()

            # Check if name contains only letters and apostrophe, no additional characters
            check_name = name.replace(" ", "")
            check_name = check_name.replace("'", "")
            if not check_name.isalpha():
                return render_template("information.html", message1="Please provide correct nickname")

            # Get the date of birth: YYYY-MM-DD
            birth = request.form.get("birth")
            related_to = session["user_id"]

            if db.execute("SELECT * FROM people WHERE name = ? AND birth = ? AND related_to = ?",
                          name, birth, related_to):
                # We can't add person with the same name and same date of birth
                return render_template("information.html", message2="It seems like this person is already in the tree")

            global person_data
            person_data = {"name": name, "birth": birth, "related_to": related_to}
            if request.form.get("death"):
                if request.form.get("death") < request.form.get("birth"):
                    return render_template("information.html",
                                           message2="Date of death can't be earlier than date of birth")
                else:
                    death = request.form.get("death")
                    person_data["death"] = death

            # Redirect to the next step in adding the person to the tree - choice of relative
            return redirect("/relatives")
    else:
        return render_template("information.html")


# Choice of relatives for the new person in the tree
@app.route("/relatives", methods=["GET", "POST"])
@login_required
def relatives():

    # Getting all the relatives
    user_id = session["user_id"]
    people_dict = db.execute("SELECT name FROM people WHERE related_to = ?", user_id)
    people = []
    for i in people_dict:
        if i["name"].find(" add") != -1:
            name = i["name"][:i["name"].find(" add")] + " born " + \
                   db.execute("SELECT birth FROM people WHERE name = ? AND related_to = ?",
                              i["name"], user_id)[0]["birth"]
        else:
            name = i["name"]
        people.append(name)

    person_name = person_data["name"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("relative"):
            return render_template("relatives.html", people=people, name=person_name,
                                   message1="Please choose someone")
        else:
            relative = request.form.get("relative")

            # Storing information on a relative in global variable "connection"
            global connection
            connection = {"name": relative}
            # Next step - choice of connection
            return redirect("/connection")
    else:
        return render_template("relatives.html", people=people, name=person_name)


# Choice of connection type with a relative
@app.route("/connection", methods=["GET", "POST"])
@login_required
def connection():

    # Basic data
    user_id = session["user_id"]
    table_name = str(user_id)
    relative_name = connection["name"]
    relative_name = born_check(relative_name)
    relative_id = db.execute("SELECT id FROM people WHERE name = ? AND related_to = ?", relative_name, user_id)[0]["id"]

    person_name = person_data["name"]

    # Creates an array of possible relationships. For now we can only be sure in sibling connection
    relationships = ["sibling"]

    # Ensure that the new person can be related to the relative in one of any possible way:
    # as a parent, as a child, as a spouse or as a sibling.

    # Checking, if a person can be relative's parent. To be one, relative has to pass two conditions:
    # 1) Person birthday must be earlier than relative's birthday
    # 2) Relative has 1 or less parents in the data base already

    # Check for birthday dates
    relative_birth = db.execute("SELECT birth FROM people WHERE id = ?", relative_id)[0]["birth"]
    if person_data["birth"] < relative_birth:
        # Check for relative's parents
        relative_parents = set()
        if db.execute("SELECT parent_1, parent_2 FROM ? WHERE child = ?", table_name, relative_id):
            parent_1 = db.execute("SELECT parent_1 FROM ? WHERE child = ?", table_name, relative_id)[0]["parent_1"]
            parent_2 = db.execute("SELECT parent_2 FROM ? WHERE child = ?", table_name, relative_id)[0]["parent_2"]
            relative_parents.add(parent_1)
            relative_parents.add(parent_2)
            relative_parents.discard(1)
            # If a relative has only one parent or less, new person can be their parent
            if len(relative_parents) <= 1:
                relationships.append("parent")
        else:
            relationships.append("parent")
    else:
        relationships.append("child")

    # Checking for a spouse relationship
    # Compare birth and death dates - two people must exist at the same time to be a couple
    if db.execute("SELECT death FROM people WHERE id = ?", relative_id)[0]["death"] is not None:
        relative_death = db.execute("SELECT death FROM people WHERE id = ?", relative_id)[0]["death"]
    else:
        relative_death = datetime.today().strftime('%Y-%m-%d')
    if "death" in person_data:
        death = person_data["death"]
    else:
        death = datetime.today().strftime('%Y-%m-%d')
    if death == relative_death or person_data["birth"] < relative_death or relative_birth < death:

        # Checking for possible relative's spouse in the table:
        if not db.execute("SELECT parent_1 FROM ? WHERE parent_2 = ?", table_name, relative_id) \
                or db.execute("SELECT parent_1 FROM ? WHERE parent_2 = ?", table_name, relative_id)[0]["parent_1"] == 1:
            if not db.execute("SELECT parent_2 FROM ? WHERE parent_1 = ?", table_name, relative_id) \
                    or db.execute("SELECT parent_2 FROM ? WHERE parent_1 = ?",
                                  table_name, relative_id)[0]["parent_2"] == 1:
                relationships.append("spouse/partner")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("connection"):
            return render_template("connection.html", name=person_name, relative=connection["name"],
                                   relationships=relationships, message1="Choose something")
        else:
            connection["type"] = request.form.get("connection")
            return redirect("/approval")
    else:
        return render_template("connection.html", name=person_name, relative=connection["name"],
                               relationships=relationships)


# Final step in adding a new person to the tree
@app.route("/approval", methods=["GET", "POST"])
@login_required
def approval():
    # Basic information on a new person: name, date of birth and death if relevant
    name = person_data["name"]

    birth = person_data["birth"]
    birth = date_maker(birth)

    if "death" in person_data:
        death = person_data["death"]
        death = date_maker(death)
    else:
        death = None

    # Empty variables for other possible relatives
    children = []
    parents = []
    siblings = []
    partner = None

    table_name = str(session["user_id"])
    relative_name = born_check(connection["name"])
    relative_id = find_id(relative_name)

    # Information on all possible connections in the tree judging on the information about the relative
    # If a new person is a parent to existing relative in the tree
    if connection["type"] == 'parent':
        children.append(connection["name"])
        results = connection_parent(children, partner, table_name, relative_id)
        children = results["children"]
        partner = results["partner"]

    # If a new person is a child to the existing relative in the tree
    elif connection["type"] == "child":
        parents.append(connection["name"])
        results = connection_child(parents, siblings, table_name, relative_id)
        parents = results["parents"]
        siblings = results["siblings"]

    # If a new person is a spouse of the existing member of the tree
    elif connection["type"] == "spouse/partner":
        partner = connection["name"]
        results = connection_spouse(partner, children, table_name, relative_id)
        partner = results["spouse"]
        children = results["children"]

    # If a new person is a sibling to already existing member of the tree
    else:
        siblings.append(connection["name"])
        results = connection_sibling(siblings, parents, table_name, relative_id)
        siblings = results["siblings"]
        parents = results["parents"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        person_name = person_data["name"]

        # If there is already a person in the tree with the same name, we have to alter the name before saving it to the db
        if db.execute("SELECT * FROM people WHERE name = ? AND related_to = ? AND birth != ? ",
                person_data["name"], session["user_id"], person_data["birth"]):
            person_name += " " + "add" + person_data["birth"].replace("-", "") + "add"

        if death is not None:
            db.execute("INSERT INTO people (name, birth, death, related_to) VALUES (?, ?, ?, ?)",
                       person_name, person_data["birth"], person_data["death"], session["user_id"])
        else:
            db.execute("INSERT INTO people (name, birth, related_to) VALUES (?, ?, ?)",
                       person_name, person_data["birth"], session["user_id"])

        # Update table with connections
        person_id = find_id(person_name)
        update_connections(connection, person_id, children, parents, siblings, partner, table_name)
        # Redirect to approval message
        return render_template("all_set.html")
    else:
        return approval_list(name, birth, death, children, parents, siblings, partner, connection)


# Signing in
@app.route("/sign_in", methods=["GET", "POST"])
def signing():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("first_name") or not request.form.get("last_name"):
            return render_template("sign_in.html", message1="Invalid name")

        name = request.form.get("first_name") + " " + request.form.get("last_name")

        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("sign_in.html", message2="Please, provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("sign_in.html", message2="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to their tree
        return redirect("/my_tree")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sign_in.html")


# Sign out
@app.route("/sign_out")
@login_required
def sign_out():
    # Forget any user_id
    session.clear()
    # Redirect to login form
    return redirect("/sign_in")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure the username was submitted
        if not request.form.get("first_name") or not request.form.get("last_name"):
            return render_template("register.html", message1="Please, type first and last name")

        name = request.form.get("first_name").strip() + " " + request.form.get("last_name").strip()

        # Check if name contains only letters and apostrophe, no additional characters
        check_name = name.replace(" ", "")
        check_name = check_name.replace("'", "")
        if not check_name.isalpha():
            return render_template("register.html", message1="Please provide correct nickname")

        # Ensure the username is not taken
        if db.execute("SELECT * FROM users WHERE username = ?", name):
            return render_template("register.html", message1="This username is already taken")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html", message2="Please, choose a password")

        # Ensure repeated password is correct
        elif request.form.get("confirmation") != request.form.get("password"):
            return render_template("register.html", message2="Passwords are not equal")

        # Ensure the birth date was selected
        elif not request.form.get("birth"):
            return render_template("register.html", message3="Please, choose your date of birth")

        # Hash the password
        password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Add user to the people table
        db.execute("INSERT INTO people (name, birth) VALUES (?, ?)",
                   name, request.form.get("birth"))

        user_id = db.execute("SELECT id FROM people WHERE name = ? AND related_to is NULL", name)[0]['id']

        # Insert name, password and date of birth into the users table
        db.execute("INSERT INTO users (id, username, hash, birth) VALUES (?, ?, ?, ?)",
                   user_id, name, password, request.form.get("birth"))

        db.execute("UPDATE people SET related_to = ? WHERE id = ?", user_id, user_id)

        # Create a table of connections for this user. There will be 5 columns: child_generation, parent_1, parent_2,
        # child, sib_group. In parent_1, parent_2 and child columns will be stored people's ids. If one person
        # in this family node is missing (for example, couple doesn't have any children), their id == 1
        # (id of an undefined person). Child_generation will be useful later for drawing the tree and placing
        # the relatives. By default user's generation == 100. Their parents = 100 + 1. Their children = 100 - 1.
        # If a couple has several children, there will be several rows for each child. In addition all children
        # from one couple will share the same sib_group (child_generation + first known child id). Table name == user_id

        table_name = str(db.execute("SELECT id FROM users WHERE username = ?", name)[0]["id"])
        db.execute(
            "CREATE TABLE ? ( child_generation INTEGER NOT NULL, parent_1 INTEGER, parent_2 INTEGER, child INTEGER, sib_group INTEGER, FOREIGN KEY (parent_1) REFERENCES people (id), FOREIGN KEY (parent_2) REFERENCES people (id), FOREIGN KEY (child) REFERENCES people (id))",
            table_name)

        # Now insert into this table user: he/she will be registered as a child with undefined parents for now.
        db.execute("INSERT INTO ? (child_generation, parent_1, parent_2, child, sib_group) VALUES (100, 1, 1, ?, ?)",
                   table_name, user_id, user_id)

        # Remember which user has logged in
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", name)[0]["id"]

        # Redirect to the user's tree
        return redirect("/my_tree")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# Deletes user's account
@app.route("/clear", methods=["GET", "POST"])
@login_required
def delete():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        id = session["user_id"]
        table_name = str(id)

        # Clear the session
        # Forget any user_id
        session.clear()

        # Delete the user's connection table first
        # Then his row in the users' table and then - all his relatives
        db.execute("DROP TABLE ?", table_name)

        relatives = []
        rows = db.execute("SELECT id FROM people WHERE related_to = ?", id)
        for row in rows:
            relatives.append(row["id"])

        for i in relatives:
            photos = []
            if db.execute("SELECT photo FROM people_photos WHERE person_id = ?", i):
                rows = db.execute("SELECT photo FROM people_photos WHERE person_id = ?", i)
                for row in rows:
                    photos.append(row["photo"])
            if len(photos) != 0:
                for photo in photos:
                    path = "static/files/" + photo
                    os.remove(path)
                    db.execute("DELETE FROM people_photos WHERE photo = ? AND person_id = ?", photo, i)

            db.execute("DELETE FROM people_stories WHERE person_id = ?", i)

        db.execute("DELETE FROM people WHERE related_to = ?", id)
        db.execute("DELETE FROM users WHERE id = ?", id)

        # Redirect to index page
        return redirect("/")
    else:
        return render_template("clear.html")


# Page for the specific person from the tree
@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete_person():

    # Not every person can be deleted from the tree. User cannot delete only those, who:
    # 1) is the user
    # 2) has parents in the tree AND partner or child
    # So first step is to make a list of people, who can be deleted - removable

    user_id = session["user_id"]
    relatives = removable(user_id)

    if request.method == "POST":
        if not request.form.get("removable"):
            return render_template("delete.html", relatives=relatives)
        person = request.form.get("removable")
        person = born_check(person)

        person_id = db.execute("SELECT id FROM people WHERE name = ? AND related_to = ?", person, user_id)[0]["id"]

        while db.execute("SELECT * FROM ? WHERE parent_1 = ? ", str(user_id), person_id):
            db.execute("UPDATE ? SET parent_1 = ? WHERE parent_1 = ?", str(user_id), 1, person_id)
        while db.execute("SELECT * FROM ? WHERE parent_2 = ? ", str(user_id), person_id):
            db.execute("UPDATE ? SET parent_2 = ? WHERE parent_2 = ?", str(user_id), 1, person_id)
        while db.execute("SELECT * FROM ? WHERE child = ? ", str(user_id), person_id):
            db.execute("UPDATE ? SET child = ? WHERE child = ?", str(user_id), 1, person_id)

        if db.execute("SELECT photo FROM people_photos WHERE person_id = ?", person_id):
            photos = []
            rows = db.execute("SELECT photo FROM people_photos WHERE person_id = ?", person_id)
            for row in rows:
                photos.append(row["photo"])
            if len(photos) != 0:
                for photo in photos:
                    path = "static/files/" + photo
                    os.remove(path)
                    db.execute("DELETE FROM people_photos WHERE photo = ? AND person_id = ?", photo, person_id)

        db.execute("DELETE FROM people_stories WHERE person_id = ?", person_id)

        db.execute("DELETE FROM people WHERE related_to = ? AND id = ?", user_id, person_id)

        return redirect("/my_tree")

    return render_template("delete.html", relatives=relatives)
