from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

IST = timezone(timedelta(hours = 5, minutes=30))


uri = "mongodb+srv://sahil45:Sahil21145073@cluster0.yh0nggp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print('Pinged your deployment')
except Exception as e:
    print(e)
db = client["personal_finance"]
def log_chat(role,content):
    db.chat_logs.insert_one({
        "role":role,
        "content":content,
        "timestamp":datetime.now(IST)
    })