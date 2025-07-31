# pages/1_Expenses.py
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from datetime import date
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
        """
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
    ))

# 4) Page config
st.set_page_config(page_title="Expenses", page_icon="🧾")
st.title("🧾 Expense Tracker")

# 5) Prepare dropdown choices
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT type FROM expenses"))
    existing_types = [row[0] for row in result]
if not existing_types:
    existing_types = ["Income", "Expense", "Transfer"]
type_options = existing_types + ["➕ Add new type…"]

category_list = ["Saving", "Want", "Need"]

# 6) Collapsible entry form inside an expander
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
                    """
                    INSERT INTO expenses (date, description, type, category, normal, amount)
                    VALUES (:d, :desc, :typ, :cat, :normal, :amt)
                    """
                )
                with engine.begin() as conn:
                    conn.execute(
                        insert_sql,
                        {"d": d, "desc": desc, "typ": typ, "cat": cat, "normal": normal, "amt": amt}
                    )
                st.success(f"Logged {typ.lower()} of ${amt:.2f} on {d}")

# 7) Monthly summary
first_of_month = date.today().replace(day=1)
df = pd.read_sql(
    text(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE date >= :start
        GROUP BY category
        """
    ),
    engine,
    params={"start": first_of_month}
)

st.subheader(f"Spending since {first_of_month}")
if df.empty:
    st.info("No entries yet.")
else:
    # Calculate percentages
    total_sum = df["total"].sum()
    df["percent"] = df["total"] / total_sum * 100

    # Bar chart with Altair
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("category:N", title=None),
            y=alt.Y(
                "total:Q",
                title="Amount",
                axis=alt.Axis(format="$,.2f"),
                scale=alt.Scale(zero=False)
            ),
            color=alt.Color("category:N", legend=None)
        )
        .properties(width=600, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    # Prepare summary table
    summary_df = pd.DataFrame({
        "Category": df["category"],
        "Amount": df["total"].map("${:,.2f}".format),
        "% of Total": df["percent"].map("{:.1f}%".format)
    })
    st.table(summary_df)

# 8) Detailed table of all entries this month
entries_df = pd.read_sql(
    text(
        """
        SELECT date, description, type, category, normal, amount
        FROM expenses
        WHERE date >= :start
        ORDER BY date DESC
        """
    ),
    engine,
    params={"start": first_of_month}
)
entries_df["Amount"] = entries_df["amount"].map("${:,.2f}".format)
entries_df["Normal"] = entries_df["normal"].map({True: "Yes", False: "No"})
entries_df = entries_df.drop(columns=["amount", "normal"])

st.subheader("All Entries This Month")
st.dataframe(entries_df.sort_values(by="date", ascending=False))
