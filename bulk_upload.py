# bulk_upload.py
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1) Load .env and connect
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# 2) Read CSV
csv_path = r"C:\Users\ralmarez\Downloads\temp_exp.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"No CSV found at {csv_path}")

df = pd.read_csv(csv_path, parse_dates=["date"])

# 3) Debug print before cleaning
print("Columns before cleaning:", df.columns.tolist())

# 4) Strip whitespace from column names
df.columns = df.columns.str.strip()

# 5) Debug print after cleaning
print("Columns after cleaning:", df.columns.tolist())

# 6) Lowercase (optional)
df.columns = df.columns.str.lower()

# 7) Ensure correct column names
expected = {"date","description","type","category","normal","amount"}
if not expected.issubset(set(df.columns)):
    missing = expected - set(df.columns)
    raise ValueError(f"Missing columns in DataFrame after cleanup: {missing}")

# 8) Clean amount and normal types
df["amount"] = df["amount"].astype(str).str.replace(r"[\$,]", "", regex=True).astype(float)
df["normal"] = df["normal"].astype(str).str.lower().map({"true": True, "false": False})

# 9) Bulk insert
df.to_sql(
    "expenses",
    con=engine,
    if_exists="append",
    index=False,
    method="multi"
)

print(f"✅ Inserted {len(df)} rows into expenses")
