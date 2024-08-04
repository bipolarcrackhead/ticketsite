from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from decouple import config

try:
    MONGO_URL = config("MONGO_URL")
except:
    print("Please set the SECRET_KEY and MONGO_URL in your .env")
    exit(1)

client = MongoClient(MONGO_URL)
db = client["crud_db"]
users_collection = db["users"]

username = input("Enter username: ")
password = input("Enter password: ")

new_user = {
    "username": username,
    "password": generate_password_hash(password),
}

users_collection.insert_one(new_user)
print("User created successfully.\nUsername:", username, "\nPassword: ", password)
