import streamlit as st
import requests
import pandas as pd
import datetime
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import asyncio
# from backend.app.db.models import SessionLocal, User

st.set_page_config(page_title="Analytics Dashboard", layout="wide")
st.title("Kyra Analytics Dashboard")

try:
    API_URL = st.secrets.get("API_URL", "http://localhost:8000/api/v1/admin/analytics")
except:
    API_URL = "http://localhost:8000/api/v1/admin/analytics"

# --- Authentication ---
def login_form():
    st.sidebar.header("Admin Login")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")
    if login_btn:
        resp = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            # Check if user is admin
            me = requests.get(
                "http://localhost:8000/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if me.status_code == 200 and me.json().get("is_admin"):
                st.session_state["token"] = token
                st.session_state["is_admin"] = True
                st.success("Logged in as admin!")
                st.rerun()
            else:
                st.session_state["token"] = None
                st.session_state["is_admin"] = False
                st.error("You are not an admin.")
        else:
            st.session_state["token"] = None
            st.session_state["is_admin"] = False
            st.error("Login failed.")

if "token" not in st.session_state or not st.session_state.get("is_admin"):
    login_form()
    st.stop()

# --- Logout ---
if st.sidebar.button("Logout"):
    st.session_state["token"] = None
    st.session_state["is_admin"] = False
    st.rerun()

# --- Selection: Answered or Unanswered ---
answered = st.sidebar.radio("Show", ["Answered", "Unanswered"]) == "Answered"

# --- Filters ---
st.sidebar.header("Filters")
ethnic_group = st.sidebar.text_input("Ethnic Group")
gender = st.sidebar.text_input("Gender")
country = st.sidebar.text_input("Country")
long_term_conditions = st.sidebar.text_input("Long Term Conditions")
medications = st.sidebar.text_input("Medications")
min_age = st.sidebar.number_input("Min Age", min_value=0, max_value=120, value=0)
max_age = st.sidebar.number_input("Max Age", min_value=0, max_value=120, value=0)
rag_score_min = st.sidebar.number_input("Min RAG Score", value=0.0)
rag_score_max = st.sidebar.number_input("Max RAG Score", value=0.0)
reason = st.sidebar.text_input("Reason (for unanswered)")
category = st.sidebar.selectbox("Category", ["All"] + ["Symptoms & Diagnosis", "Treatment & Medication", "Prevention & Lifestyle"])

params = {"answered": answered}
if ethnic_group:
    params["ethnic_group"] = ethnic_group
if gender:
    params["gender"] = gender
if country:
    params["country"] = country
if long_term_conditions:
    params["long_term_conditions"] = long_term_conditions
if medications:
    params["medications"] = medications
if min_age:
    params["min_age"] = min_age
if max_age:
    params["max_age"] = max_age
if rag_score_min:
    params["rag_score_min"] = rag_score_min
if rag_score_max:
    params["rag_score_max"] = rag_score_max
if not answered and reason:
    params["reason"] = reason
if category != "All":
    params["category"] = category

# --- Fetch Data ---
with st.spinner("Fetching data..."):
    resp = requests.get(API_URL, headers={"Authorization": f"Bearer {st.session_state['token']}"}, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if not data:
            st.info("No data found for the selected filters.")
            st.stop()
        df = pd.DataFrame(data)
    else:
        st.error(f"Failed to fetch data: {resp.status_code} {resp.text}")
        st.stop()

# --- Data Processing ---
if "date_of_birth" in df.columns:
    today = datetime.date.today()
    def calc_age(dob):
        try:
            return today.year - int(dob[:4])
        except:
            return None
    df["age"] = df["date_of_birth"].apply(calc_age)

# --- Normalize sources column for Arrow compatibility ---
if "sources" in df.columns:
    def normalize_sources(val):
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [val]
        return []
    df["sources"] = df["sources"].apply(normalize_sources)

# --- Display Table ---
st.subheader("Results Table")
st.dataframe(df)

# --- Plots ---
st.subheader("Demographic Plots")
col1, col2 = st.columns(2)
with col1:
    if "ethnic_group" in df.columns:
        st.bar_chart(df["ethnic_group"].value_counts())
    if "gender" in df.columns:
        st.bar_chart(df["gender"].value_counts())
    if "country" in df.columns:
        st.bar_chart(df["country"].value_counts())
with col2:
    if "age" in df.columns:
        st.bar_chart(df["age"].dropna().astype(int).value_counts().sort_index())
    if "rag_score" in df.columns:
        st.bar_chart(df["rag_score"].dropna().astype(float))

if not answered and "reason" in df.columns:
    st.subheader("Unanswered Reasons Distribution")
    st.bar_chart(df["reason"].value_counts())

# --- Category Analytics ---
if "category" in df.columns:
    st.subheader("Question Categories")
    col1, col2 = st.columns(2)
    with col1:
        category_counts = df["category"].value_counts()
        st.bar_chart(category_counts)
    with col2:
        if len(category_counts) > 0:
            st.write("Category Breakdown:")
            for cat, count in category_counts.items():
                if pd.notna(cat):  # Only show non-null categories
                    percentage = (count / len(df)) * 100
                    st.write(f"• {cat}: {count} ({percentage:.1f}%)")

st.caption("Data is filtered by the selected criteria. Only admin users can access this dashboard.") 