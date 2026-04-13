# ⚗️ Chemical Equation Balancer (Streamlit App)

This app balances chemical equations automatically using Sympy’s matrix solver.  
It parses reactants and products, builds a stoichiometric matrix, and outputs integer coefficients.

---

## 🚀 Features
- Input any chemical equation in the format:  
  `Reactant1 + Reactant2 -> Product1 + Product2`
- Balances equations with integer coefficients.
- Suppresses "1" for single molecules (e.g., `O2` instead of `1O2`).
- Runs as a Streamlit web app.

---

## 📦 Requirements
See `requirements.txt`:
- `streamlit`
- `sympy`

Install with:
```bash
pip install -r requirements.txt
