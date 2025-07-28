import streamlit as st
import pandas as pd

st.set_page_config(page_title="myapp", layout="centered")

st.title("Flash")

import pandas as pd




import streamlit as st
import pandas as pd

# --- Load original deck once ---
if "original_deck" not in st.session_state:
    st.session_state["original_deck"] = pd.read_csv(r"C:\Users\ralmarez\Downloads\flash.csv") # columns: front, back, Tense, Person
# --- Manual shuffle function ---
def reshuffle_deck():
    st.session_state["shuffled_deck"] = st.session_state["original_deck"].sample(frac=1).reset_index(drop=True)
    st.session_state["index"] = 0
    st.session_state["show_back"] = False

# --- Initialize shuffled deck ---
if "shuffled_deck" not in st.session_state:
    reshuffle_deck()

df = st.session_state["shuffled_deck"]

# --- Sidebar: Multi-Select Filters with Select/Deselect All ---
st.sidebar.header("🧠 Filter Deck")

tense_options = sorted(df["Tense"].dropna().unique())
person_options = sorted(df["Person"].dropna().unique())

# --- Buttons for Tense ---
st.sidebar.subheader("Tense")
if st.sidebar.button("Select All Tenses"):
    selected_tenses = tense_options
elif st.sidebar.button("Deselect All Tenses"):
    selected_tenses = []
else:
    selected_tenses = st.sidebar.multiselect("Select Tense(s)", options=tense_options, default=tense_options)

# --- Buttons for Person ---
st.sidebar.subheader("Person")
if st.sidebar.button("Select All Persons"):
    selected_persons = person_options
elif st.sidebar.button("Deselect All Persons"):
    selected_persons = []
else:
    selected_persons = st.sidebar.multiselect("Select Person(s)", options=person_options, default=person_options)
# --- Apply filters ---
filtered_df = df[df["Tense"].isin(selected_tenses) & df["Person"].isin(selected_persons)]

# --- Reset index if needed ---
st.session_state.setdefault("index", 0)
st.session_state.setdefault("show_back", False)
if st.session_state["index"] >= len(filtered_df):
    st.session_state["index"] = 0
    st.session_state["show_back"] = False

# --- Navigation + Flip ---
col1, flip_col, col2 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Prev") and st.session_state["index"] > 0:
        st.session_state["index"] -= 1
        st.session_state["show_back"] = False
with col2:
    if st.button("Next ➡️") and st.session_state["index"] < len(filtered_df) - 1:
        st.session_state["index"] += 1
        st.session_state["show_back"] = False
with flip_col:
    if st.button("🔄 Flip Card"):
        st.session_state["show_back"] = not st.session_state["show_back"]

# --- Shuffle Again Button ---
if st.button("🔀 Shuffle Again"):
    reshuffle_deck()

# --- Styling ---
st.markdown("""
    <style>
    .card {
        background-color: #fff;
        padding: 2rem;
        text-align: center;
        font-size: 1.4rem;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Card Display ---
if not filtered_df.empty:
    card = filtered_df.iloc[st.session_state["index"]]
    content = card["back"] if st.session_state["show_back"] else card["front"]
    st.markdown(f"<div class='card'>{content}</div>", unsafe_allow_html=True)
else:
    st.warning("No cards match your selected filters. Try adjusting Tense and Person.")


with st.expander("📘 Show Verb Endings Cheat Sheet"):
    st.markdown("""
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 0.5rem;
        text-align: center;
    }
    th {
        background-color: #f4f4f4;
    }
    </style>

    <table>
        <tr>
            <th>Tense</th><th>yo</th><th>tú</th><th>él/ella/usted</th><th>nosotros/as</th><th>vosotros/as</th><th>ellos/ellas/ustedes</th>
        </tr>
        <tr>
            <td>Present</td><td>o/o/o</td><td>as/es/es</td><td>a/e/e</td><td>amos/emos/imos</td><td>áis/éis/ís</td><td>an/en/en</td>
        </tr>
        <tr>
            <td>Preterite</td><td>é/í/í</td><td>aste/iste/iste</td><td>ó/ió/ió</td><td>amos/imos/imos</td><td>asteis/isteis/isteis</td><td>aron/ieron/ieron</td>
        </tr>
        <tr>
            <td>Imperfect</td><td>aba/ía/ía</td><td>abas/ías/ías</td><td>aba/ía/ía</td><td>ábamos/íamos/íamos</td><td>abais/íais/íais</td><td>aban/ían/ían</td>
        </tr>
        <tr>
            <td>Future</td><td>aré/eré/iré</td><td>arás/erás/irás</td><td>ará/erá/irá</td><td>aremos/eremos/iremos</td><td>aréis/eréis/iréis</td><td>arán/erán/irán</td>
        </tr>
        <tr>
            <td>Conditional</td><td>aría/ería/iría</td><td>arías/erías/irías</td><td>aría/ería/iría</td><td>aríamos/eríamos/iríamos</td><td>aríais/eríais/iríais</td><td>arían/erían/irían</td>
        </tr>
        <tr>
            <td>Progressive</td><td>estoy -ando/-iendo/-iendo</td><td>estás -ando/-iendo/-iendo</td><td>está -ando/-iendo/-iendo</td><td>estamos -ando/-iendo/-iendo</td><td>estáis -ando/-iendo/-iendo</td><td>están -ando/-iendo/-iendo</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)