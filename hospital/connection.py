import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def connect():
    client = MongoClient(os.getenv('MONGO_URI'))
    return client