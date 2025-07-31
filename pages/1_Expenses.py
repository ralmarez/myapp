# pages/1_Expenses.py
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text

# 1) Load .env
load_dotenv()

# 2) Create engine
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# 3) Ensure table exists
create_table_sql = """
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    normal BOOLEAN NOT NULL,
    amount NUMERIC NOT NULL
);
"""
with engine.begin() as conn:
    conn.execute(text(create_table_sql))

# 4) Page config
st.set_page_config(page_title="Expenses", page_icon="🧾")
st.title("🧾 Expense Tracker")

# 5) Entry form
with st.form("add_expense"):
    d = st.date_input("Date", value=date.today())
    desc = st.text_input("Description")
    typ = st.selectbox("Type", ["Income", "Expense"])
    cat = st.selectbox("Category", ["Food", "Rent", "Transport", "Utilities", "Entertainment", "Other"])
    normal = st.checkbox("Normal? (e.g. recurring)",value=True)
    amt = st.number_input("Amount", min_value=0.0, format="%.2f")
    if st.form_submit_button("Add Entry"):
        insert_sql = """
            INSERT INTO expenses (date, description, type, category, normal, amount)
            VALUES (:d, :desc, :typ, :cat, :normal, :amt)
        """
        with engine.begin() as conn:
            conn.execute(
                text(insert_sql),
                {"d": d, "desc": desc, "typ": typ, "cat": cat, "normal": normal, "amt": amt}
            )
        st.success(f"Logged {typ.lower()} of ${amt:.2f} on {d}")

# 6) Monthly summary
first_of_month = date.today().replace(day=1)
query = """
    SELECT category, SUM(amount) AS total
    FROM expenses
    WHERE date >= :start
    GROUP BY category
"""
df = pd.read_sql(text(query), engine, params={"start": first_of_month})

st.subheader(f"Spending since {first_of_month}")
if df.empty:
    st.info("No entries yet.")
else:
    st.bar_chart(df.set_index("category")["total"])
    st.table(df)
