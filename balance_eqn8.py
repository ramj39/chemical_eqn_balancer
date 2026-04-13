import streamlit as st
import re
import numpy as np
import pandas as pd
import sqlite3
import os
from collections import defaultdict
from datetime import datetime

db_file = "balanced_equations.db"

# --- Database setup ---
def init_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input TEXT,
        balanced TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_equation(input_eq, balanced_eq):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO equations (input, balanced, timestamp) VALUES (?, ?, ?)",
                   (input_eq, balanced_eq, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_equations():
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM equations", conn)
    conn.close()
    return df

def reset_db():
    if os.path.exists(db_file):
        os.remove(db_file)
    init_db()

# --- Formula parser ---
def parse_formula(formula):
    def expand(match):
        group, count = match.groups()
        count = int(count)
        expanded = ""
        for atom, num in re.findall(r'([A-Z][a-z]?)(\d*)', group):
            num = int(num) if num else 1
            expanded += atom + str(num * count)
        return expanded

    while '(' in formula:
        formula = re.sub(r'\(([^)]+)\)(\d+)', expand, formula)

    counts = defaultdict(int)
    for atom, num in re.findall(r'([A-Z][a-z]?)(\d*)', formula):
        counts[atom] += int(num) if num else 1
    return dict(counts)

# --- Balancing function ---
def balance_equation(equation: str) -> str:
    try:
        left_side, right_side = equation.split("->")
        left_compounds = [c.strip() for c in left_side.split("+")]
        right_compounds = [c.strip() for c in right_side.split("+")]
        compounds = left_compounds + right_compounds

        atom_list = []
        compound_dicts = []
        for comp in compounds:
            d = parse_formula(comp)
            compound_dicts.append(d)
            for atom in d:
                if atom not in atom_list:
                    atom_list.append(atom)

        matrix = []
        for atom in atom_list:
            row = []
            for i, comp in enumerate(compounds):
                count = compound_dicts[i].get(atom, 0)
                if i < len(left_compounds):
                    row.append(count)
                else:
                    row.append(-count)
            matrix.append(row)

        mat = np.array(matrix, dtype=float)
        u, s, vh = np.linalg.svd(mat)
        vec = vh.T[:, -1]
        coeffs = np.round(vec / np.min(vec[vec > 0])).astype(int)

        balanced = []
        for i, comp in enumerate(compounds):
            coeff = coeffs[i]
            if coeff != 1:
                balanced.append(f"{coeff}{comp}")
            else:
                balanced.append(comp)
        return " + ".join(balanced[:len(left_compounds)]) + " → " + " + ".join(balanced[len(left_compounds):])
    except Exception as e:
        return f"Could not balance this equation. Error: {e}"

# --- Initialize DB ---
init_db()

# --- Streamlit UI ---
st.title("⚗️ Chemical Equation Balancer (SQLite Persistent Log)")

user_input = st.text_input("Enter a chemical equation (e.g., KI + Pb(NO3)2 -> KNO3 + PbI2)", key="equation_input")

if st.button("Balance Equation", key="balance_button"):
    result = balance_equation(user_input)
    st.write("### Result:")
    st.write(result)

    if "Could not balance" not in result:
        insert_equation(user_input, result)
        st.success("Equation saved to database.")

# --- Reset button ---
if st.button("Reset Log", key="reset_button"):
    reset_db()
    st.warning("Database log has been cleared. A new one will be created on the next save.")

# --- Show current DB contents + counter + search ---
df = get_equations()
if not df.empty:
    st.write("### Current Database Log")
    st.write(f"**Total equations stored:** {len(df)}")

    # Search/filter box
    search_query = st.text_input("Search equations (by input or balanced form):", key="search_box")
    if search_query:
        mask = df["input"].str.contains(search_query, case=False, na=False) | \
               df["balanced"].str.contains(search_query, case=False, na=False)
        filtered_df = df[mask]
        if len(filtered_df) > 0:
            st.dataframe(filtered_df)
            st.write(f"**Matches found:** {len(filtered_df)}")
        else:
            st.warning("No matches found.")
    else:
        st.dataframe(df)

    # Download as CSV
    st.download_button(
        label="Download Full Log (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="balanced_equations.csv",
        mime="text/csv",
        key="download_csv"
    )
