import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
import altair as alt

# 1) Load .env
load_dotenv()

# 2) Create engine
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# 3) Ensure table exists
with engine.begin() as conn:
    conn.execute(text(
        '''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            description TEXT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            normal BOOLEAN NOT NULL,
            amount NUMERIC NOT NULL
        );
        '''
    ))

# 4) Page config
st.set_page_config(page_title="Expenses", page_icon="🧾")
st.title("🧾 Expense Tracker")

# 5) Prepare dropdown choices
def load_type_options():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT type FROM expenses"))
        return [row[0] for row in result]

existing_types = load_type_options()
if not existing_types:
    existing_types = ["Income", "Expense", "Transfer"]
type_options = existing_types + ["➕ Add new type…"]
category_list = ["Saving", "Want", "Need"]

# 6) Collapsible entry form
with st.expander("Add New Entry", expanded=False):
    with st.form("add_expense"):
        d = st.date_input("Date", value=date.today())
        desc = st.text_input("Description")
        choice = st.selectbox("Type", type_options)
        if choice == "➕ Add new type…":
            typ = st.text_input("Enter new type")
        else:
            typ = choice
        cat = st.selectbox("Category", category_list)
        normal = st.checkbox("Normal? (e.g. recurring)", value=True)
        amt = st.number_input("Amount", min_value=0.0, format="%.2f")
        if st.form_submit_button("Add Entry"):
            if not typ:
                st.error("Please enter a type.")
            else:
                insert_sql = text(
                    '''
                    INSERT INTO expenses (date, description, type, category, normal, amount)
                    VALUES (:d, :desc, :typ, :cat, :normal, :amt)
                    '''
                )
                with engine.begin() as conn:
                    conn.execute(insert_sql, {"d": d, "desc": desc, "typ": typ, "cat": cat, "normal": normal, "amt": amt})
                st.success(f"Logged {typ.lower()} of ${amt:.2f} on {d}")

# --- View Expenses with button row for date ranges ---
st.subheader("View Expenses")

# Define periods
periods = [
    "Current month",
    "Last month",
    "Past 3 months",
    "Year to date",
    "Past year",
    "Custom range"
]
cols = st.columns(len(periods))
selected = None
for idx, p in enumerate(periods):
    if cols[idx].button(p):
        selected = p

# Default to current month if none clicked yet
if 'selected_period' not in st.session_state:
    st.session_state.selected_period = "Current month"
if selected:
    st.session_state.selected_period = selected
period = st.session_state.selected_period
st.markdown(f"**Period:** {period}")

today = date.today()
if period == "Current month":
    start_date = today.replace(day=1)
    end_date = today
elif period == "Last month":
    first_this = today.replace(day=1)
    end_date = first_this - relativedelta(days=1)
    start_date = end_date.replace(day=1)
elif period == "Past 3 months":
    end_date = today
    start_date = (today.replace(day=1) - relativedelta(months=2)).replace(day=1)
elif period == "Year to date":
    start_date = today.replace(month=1, day=1)
    end_date = today
elif period == "Past year":
    end_date = today
    start_date = today - relativedelta(years=1)
else:  # Custom range
    start_date = st.date_input("Start date", today.replace(day=1))
    end_date = st.date_input("End date", today)
    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

st.markdown(f"**Showing entries from {start_date} to {end_date}**")

# 7) Summary by category
summary_sql = text(
    '''
    SELECT category, SUM(amount) AS total
    FROM expenses
    WHERE date BETWEEN :start AND :end
    GROUP BY category
    '''
)
df = pd.read_sql(summary_sql, engine, params={"start": start_date, "end": end_date})

if df.empty:
    st.info("No entries in this period.")
else:
    total_sum = df["total"].sum()
    df["percent"] = df["total"] / total_sum * 100
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("category:N", title=None),
            y=alt.Y("total:Q", title="Amount", axis=alt.Axis(format="$,.2f"), scale=alt.Scale(zero=False)),
            color=alt.Color("category:N", legend=None)
        )
        .properties(width=600, height=400)
    )
    st.altair_chart(chart, use_container_width=True)
    summary_df = pd.DataFrame({
        "Category": df["category"],
        "Amount": df["total"].map("${:,.2f}".format),
        "% of Total": df["percent"].map("{:.1f}%".format)
    })
    st.table(summary_df)

# 8) Detailed entries
entries_sql = text(
    '''
    SELECT date, description, type, category, normal, amount
    FROM expenses
    WHERE date BETWEEN :start AND :end
    ORDER BY date DESC
    '''
)
entries_df = pd.read_sql(entries_sql, engine, params={"start": start_date, "end": end_date})
entries_df["Amount"] = entries_df["amount"].map("${:,.2f}".format)
entries_df["Normal"] = entries_df["normal"].map({True: "Yes", False: "No"})
entries_df = entries_df.drop(columns=["amount", "normal"])
st.subheader("All Entries")
st.dataframe(entries_df.sort_values(by="date", ascending=False))
