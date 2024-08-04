from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from decouple import config

try:
    SECRET_KEY = config("SECRET_KEY")
    MONGO_URL = config("MONGO_URL")
except:
    print("Please set the SECRET_KEY and MONGO_URL in your .env")
    exit(1)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client["crud_db"]
users_collection = db["users"]
items_collection = db["items"]

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.password = user_data["password"]


@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None


@app.route("/")
@login_required
def index():
    items = items_collection.find({"user_id": current_user.id})
    return render_template("index.html", items=items)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_data = users_collection.find_one({"username": username})
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = users_collection.find_one({"username": username})
        if existing_user is None:
            hashed_password = generate_password_hash(password)
            users_collection.insert_one(
                {"username": username, "password": hashed_password}
            )
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        flash("Username already exists. Please choose a different one.")
    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        new_item = {
            "name": name,
            "description": description,
            "user_id": current_user.id,
        }
        items_collection.insert_one(new_item)
        return redirect(url_for("index"))
    return render_template("add_item.html")


@app.route("/edit/<item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = items_collection.find_one(
        {"_id": ObjectId(item_id), "user_id": current_user.id}
    )
    if not item:
        return redirect(url_for("index"))
    if request.method == "POST":
        updated_item = {
            "name": request.form["name"],
            "description": request.form["description"],
            "user_id": current_user.id,
        }
        items_collection.update_one({"_id": ObjectId(item_id)}, {"$set": updated_item})
        return redirect(url_for("index"))
    return render_template("edit_item.html", item=item)


@app.route("/delete/<item_id>")
@login_required
def delete_item(item_id):
    items_collection.delete_one({"_id": ObjectId(item_id), "user_id": current_user.id})
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
