from pymongo import MongoClient

MONGO_URI = "mongodb+srv://syncsphere:qwer1234@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)

db = client["syncsphere"]