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
existing_types = []
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT type FROM expenses"))
    existing_types = [row[0] for row in result]
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
        typ = st.text_input("Enter new type") if choice == "➕ Add new type…" else choice
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
periods = ["Current month", "Last month", "Past 3 months", "Year to date", "Past year", "Custom range"]
cols = st.columns(len(periods))
selected = None
for idx, p in enumerate(periods):
    if cols[idx].button(p):
        selected = p
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
    first_of_month = today.replace(day=1)
    end_date = first_of_month - relativedelta(days=1)
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
else:
    start_date = st.date_input("Start date", today.replace(day=1))
    end_date = st.date_input("End date", today)
    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

st.markdown(f"**Showing entries from {start_date} to {end_date}**")

# Filter toggle: Only normal entries
only_normal = st.checkbox("Only show normal entries", value=False)

# 7) Summary by category
# Load raw data for grouping
raw = pd.read_sql(
    text(
        '''
        SELECT category, normal, amount
        FROM expenses
        WHERE date BETWEEN :start AND :end
        '''
    ),
    engine,
    params={"start": start_date, "end": end_date}
)
if only_normal:
    raw = raw[raw.normal]

df = (
    raw.groupby('category', as_index=False)
       .amount.sum()
       .rename(columns={'amount': 'total'})
)

if df.empty:
    st.info("No entries in this period.")
else:
    total_sum = df['total'].sum()
    df['percent'] = df['total'] / total_sum * 100

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X('category:N', title=None),
            y=alt.Y('total:Q', title='Amount', axis=alt.Axis(format='$,.2f'), scale=alt.Scale(zero=False)),
            color=alt.Color('category:N', legend=None)
        )
        .properties(width=600, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    summary_df = pd.DataFrame({
        'Category': df['category'],
        'Amount': df['total'].map('${:,.2f}'.format),
        '% of Total': df['percent'].map('{:.1f}%'.format)
    })
    st.table(summary_df)

# 8) Detailed entries
entries = pd.read_sql(
    text(
        '''
        SELECT date, description, type, category, normal, amount
        FROM expenses
        WHERE date BETWEEN :start AND :end
        ORDER BY date DESC
        '''
    ),
    engine,
    params={"start": start_date, "end": end_date}
)
if only_normal:
    entries = entries[entries.normal]

entries['Amount'] = entries['amount'].map('${:,.2f}'.format)
entries['Normal'] = entries['normal'].map({True: 'Yes', False: 'No'})
entries = entries.drop(columns=['amount', 'normal'])

st.subheader('All Entries')
st.dataframe(entries.sort_values(by='date', ascending=False))
