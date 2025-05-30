import streamlit as st
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from pymongo import MongoClient
from datetime import datetime, timezone,timedelta

# 🔮 LLM with tool support
llm = ChatOllama(model="llama3.2:latest")
uri = "mongodb+srv://sahil45:Sahil21145073@cluster0.yh0nggp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print('Pinged your deployment')
except Exception as e:
    print(e)

IST = timezone(timedelta(hours = 5, minutes=30))
db = client["personal_finance"]

def get_time_range(period: str):
    """
    Returns the start and end datetime for a given period relative to Indian timezone.
    Period can be one of: 'day', 'week', 'month', 'year'
    """
    now = datetime.now(IST)
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Invalid period. Choose from: day, week, month, year.")
    end = now
    return start, end

# ✅ Category-based tools
@tool
def log_expense(amount: float, description: str) -> str:
    """Log an expense entry."""
    entry = {
        "amount": amount,
        "description": description,
        "timestamp": datetime.now(IST)
    }
    db.expenses.insert_one(entry)
    return f"Logged ₹{amount} as expense: {description}"

@tool
def log_income(amount: float, description: str) -> str:
    """Log an income entry."""
    entry = {
        "amount": amount,
        "description": description,
        "timestamp": datetime.now(IST)
    }
    db.income.insert_one(entry)
    return f"Logged ₹{amount} as income: {description}"

@tool
def log_savings(amount: float, description: str) -> str:
    """
    Log a savings entry into the database.

    Parameters:
    - amount (float): The amount saved, in INR.
    - description (str): A brief description of the savings.

    The function cleans the input (removing currency symbols or commas), converts the amount to float,
    adds the current Indian timestamp, and stores the data in the 'savings' MongoDB collection.
    """
    try:
        # Clean and normalize amount and description
        amount = float(str(amount).replace("₹", "").replace(",", "").strip())
        description = description.replace("₹", "").strip()

        # Insert into the MongoDB collection
        entry = {
            "amount": amount,
            "description": description,
            "timestamp": datetime.now(IST)
        }
        db.savings.insert_one(entry)

        return f"Logged ₹{amount} as savings: {description}"
    except Exception as e:
        return f"❌ Failed to log savings: {str(e)}"

@tool
def log_investment(amount: float, description: str) -> str:
    """Log an investment entry."""
    entry = {
        "amount": amount,
        "description": description,
        "timestamp": datetime.now(IST)
    }
    db.investments.insert_one(entry)
    return f"Logged ₹{amount} as investment: {description}"

@tool
def get_total_expenses(period: str = "month") -> str:
    """Get the total expenses logged during a given period.
    Period can be one of 'day', 'week', 'month', 'year'
    """
    try:
        start, end = get_time_range(period)
        total = db.expenses.aggregate([
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        result = next(total, {"total": 0})
        return f"Total expenses this {period}: ₹{result['total']}"
    except Exception as e:
        return f"❌ Failed to retrieve expenses: {str(e)}"
@tool
def get_total_income(period: str = "month") -> str:
    """Get the total income logged during a given period.
    Period can be one of 'day', 'week', 'month', 'year'
    """
    try:
        start, end = get_time_range(period)
        total = db.income.aggregate([
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        result = next(total, {"total": 0})
        return f"Total income this {period}: ₹{result['total']}"
    except Exception as e:
        return f"❌ Failed to retrieve income: {str(e)}"

@tool
def get_total_savings(period: str = "month") -> str:
    """Get the total savings logged during a given period.
    Period can be one of 'day', 'week', 'month', 'year'
    """
    try:
        start, end = get_time_range(period)
        total = db.savings.aggregate([
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        result = next(total, {"total": 0})
        return f"Total savings this {period}: ₹{result['total']}"
    except Exception as e:
        return f"❌ Failed to retrieve savings: {str(e)}"

@tool
def get_total_investment(period: str = "month") -> str:
    """Get the total investment logged during a given period.
    Period can be one of 'day', 'week', 'month', 'year'
    """
    try:
        start, end = get_time_range(period)
        total = db.investment.aggregate([
            {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        result = next(total, {"total": 0})
        return f"Total investment this {period}: ₹{result['total']}"
    except Exception as e:
        return f"❌ Failed to retrieve investment: {str(e)}"


@tool
def who_am_I(query: str) -> str:
    """Who am I?"""
    return "I am your personal finance assistant."

# 🛠️ Register tools
tools = [
    log_expense,
    log_income,
    log_savings,
    log_investment,
    get_total_expenses,
    get_total_investment,
    get_total_savings,
    get_total_income,
    who_am_I
]
llm_with_tools = llm.bind_tools(tools)

# 💬 LangGraph state schema
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 🤖 Main chatbot logic
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 🧠 LangGraph construction
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile()

# 🚀 Streaming response
def stream_graph_updates(user_input: str):
    from chat_logger import log_chat
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        artha_response = []
        for value in event.values():
            if value["messages"][-1].content=='':
                continue
            
            response = value["messages"][-1].content
            st.markdown(f"**Assistant:** {response}")
            artha_response.append(response)
        log_chat("Artha",' '.join(artha_response))

# ✅ Test examples
# if __name__ == "__main__":
#     # print("\n🧾 Expense Example:")
#     # stream_graph_updates("I spent ₹500 on groceries")

#     # print("\n💰 Income Example:")
#     # stream_graph_updates("Got credited ₹50,000 as salary")

    
#     stream_graph_updates("How much I saved this month my assistant?")

#     # print("\n📈 Investment Example:")
#     # stream_graph_updates("Invested ₹10,000 in mutual funds")

#     # print("\n💬 General Chat:")
#     # stream_graph_updates("Who are you?")
def callArtha(user_input:str):
    stream_graph_updates(user_input)