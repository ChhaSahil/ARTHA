import streamlit as st
st.set_page_config(page_title="Personal Finance Chatbot", page_icon="💰")
st.title("💬 Personal Finance Assistant - ARTHA")
from agent import callArtha
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from chat_logger import log_chat

IST = timezone(timedelta(hours = 5, minutes=30))


uri = "mongodb+srv://sahil45:Sahil21145073@cluster0.yh0nggp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print('Pinged your deployment')
except Exception as e:
    print(e)
db = client["personal_finance"]

def get_chat_history():
    return list(db.chat_logs.find().sort("timestamp",-1).limit(5))

user_input = st.text_input("Enter your message:", key="input")
if st.button("Send"):
    if user_input:
        log_chat("user",user_input)
        callArtha(user_input=user_input)

st.markdown("### 🕒 Last 5 Messages")
chats = get_chat_history()[::-1]  # reverse for chronological order
for chat in chats:
    role = "🧑 User" if chat['role'] == 'user' else "🤖 Assistant"
    timestamp = chat['timestamp'].strftime("%Y-%m-%d %H:%M")
    st.markdown(f"**{role} ({timestamp})**: {chat['content']}")
