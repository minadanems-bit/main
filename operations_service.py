# =====================================================
# DAILY OPERATIONS MODULE (FULL UPDATED VERSION)
# =====================================================

import streamlit as st
from datetime import date
import urllib.parse

from printer_service import calculate_printer_difference, get_printers
from database import save_db, get_manager_phone


def daily_operations_ui(db):

    if "user" not in st.session_state:
        return

    st.title("📊 NMS ERP - Daily Operations")

    branches = db.get("branches", []) or ["No Branch"]

    current_branch = st.session_state.get("branch", branches[0])
    if current_branch not in branches:
        current_branch = branches[0]

    st.session_state["branch"] = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(current_branch)
    )

    shifts = ["Morning", "Between", "Night"]
    current_shift = st.session_state.get("shift", "Morning")

    st.session_state["shift"] = st.selectbox(
        "🕒 Shift",
        shifts,
        index=shifts.index(current_shift)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📅 {date.today()}")
    with col2:
        st.info(f"👤 {st.session_state.get('user')}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    # =====================================================
    # TAB 1 — OPENING
    # =====================================================

    with tab1:

        st.subheader("🌅 Opening Tasks")
        for task in db["tasks"].get("opening", []):
            st.checkbox(task, key=f"open_task_{task}")

        st.divider()
        st.subheader("💰 Opening Cash")

        t_open = 0.0
        for d in [200, 100, 50, 20, 10, 5]:
            v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"open_{d}")
            t_open += v * d

        coins = st.number_input("Coins", step=0.5, key="open_coins")
        t_open += coins
        st.session_state["t_open"] = t_open

        # ===== Digital Opening =====

        for key in ["opay_open", "debit_open", "enbd_open"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

        opay_open = st.number_input("💳 Opay Opening", min_value=0.0, step=1.0,
                                    value=float(st.session_state["opay_open"]))
        debit_open = st.number_input("💳 Debit Opening", min_value=0.0, step=1.0,
                                     value=float(st.session_state["debit_open"]))
        enbd_open = st.number_input("🏦 ENBD Wallet Opening", min_value=0.0, step=1.0,
                                    value=float(st.session_state["enbd_open"]))

        st.session_state["opay_open"] = float(opay_open)
        st.session_state["debit_open"] = float(debit_open)
        st.session_state["enbd_open"] = float(enbd_open)

    # =====================================================
    # TAB 2 — CLOSING
    # =====================================================

    with tab2:

        st.subheader("🌇 Closing Tasks")
        for task in db["tasks"].get("closing", []):
            st.checkbox(task, key=f"close_task_{task}")

        st.divider()
        st.subheader("💰 Closing Cash")

        sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales")

        insta = st.number_input("Instapay", step=1.0, key="c_insta")
        wallet = st.number_input("Wallet", step=1.0, key="c_wallet")
        visa = st.number_input("Visa", step=1.0, key="c_visa")

        for key in ["opay_close", "debit_close", "enbd_close"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

        opay_close = st.number_input("💳 Opay Closing", min_value=0.0, step=1.0,
                                     value=float(st.session_state["opay_close"]))
        debit_close = st.number_input("💳 Debit Closing", min_value=0.0, step=1.0,
                                      value=float(st.session_state["debit_close"]))
        enbd_close = st.number_input("🏦 ENBD Wallet Closing", min_value=0.0, step=1.0,
                                     value=float(st.session_state["enbd_close"]))

        st.session_state["opay_close"] = float(opay_close)
        st.session_state["debit_close"] = float(debit_close)
        st.session_state["enbd_close"] = float(enbd_close)

        # ===== Expenses List =====

        st.subheader("🧾 Expenses")

        expense_items = db.get("expenses", [])
        selected_expenses = st.multiselect("Select Expenses", expense_items)

        total_expenses = 0.0
        expense_details = {}

        for item in selected_expenses:
            amount = st.number_input(f"{item} Amount", step=1.0, key=f"exp_{item}")
            total_expenses += amount
            expense_details[item] = amount

        st.session_state["expense_details"] = expense_details
        st.session_state["expenses_total"] = total_expenses

        # ===== Calculations =====

        t_digital = insta + wallet + visa
        t_open = st.session_state.get("t_open", 0)

        expected = t_open + sys_sales - total_expenses - t_digital
        st.metric("Expected Cash", f"{expected:,.2f}")

        # ===== Cash Count =====

        t_close = 0
        for d in [200, 100, 50, 20, 10, 5]:
            v = st.number_input(f"{d} LE ", min_value=0, step=1, key=f"close_{d}")
            t_close += v * d

        coins = st.number_input("Closing Coins", step=0.5, key="close_coins")
        t_close += coins

        diff = t_close - expected

        st.metric("Difference", f"{diff:,.2f}")

        st.session_state["cash_diff"] = diff
        st.session_state["t_close"] = t_close

    # =====================================================
    # ARCHIVE + WHATSAPP
    # =====================================================

    st.divider()

    branch = st.session_state.get("branch")
    shift = st.session_state.get("shift")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Archive Shift", use_container_width=True):

            db["history"] = db.get("history", [])

            db["history"].append({
                "date": str(date.today()),
                "branch": branch,
                "shift": shift,
                "staff": st.session_state.get("user"),
                "sales": st.session_state.get("c_sys_sales", 0),
                "cash_diff": st.session_state.get("cash_diff", 0),
                "expenses": st.session_state.get("expense_details", {}),
                "opay_open": st.session_state.get("opay_open", 0),
                "opay_close": st.session_state.get("opay_close", 0),
                "debit_open": st.session_state.get("debit_open", 0),
                "debit_close": st.session_state.get("debit_close", 0),
                "enbd_open": st.session_state.get("enbd_open", 0),
                "enbd_close": st.session_state.get("enbd_close", 0),
            })

            save_db(db)
            st.success("Archived Successfully ✅")

    with col2:

        report = f"""
📊 SHIFT REPORT
Date: {date.today()}
Branch: {branch}
Shift: {shift}
Staff: {st.session_state.get("user")}

💰 Sales: {st.session_state.get("c_sys_sales", 0)}
💵 Cash Difference: {st.session_state.get("cash_diff", 0)}

💳 Digital:
Opay: {st.session_state.get("opay_open", 0)} ➜ {st.session_state.get("opay_close", 0)}
Debit: {st.session_state.get("debit_open", 0)} ➜ {st.session_state.get("debit_close", 0)}
ENBD: {st.session_state.get("enbd_open", 0)} ➜ {st.session_state.get("enbd_close", 0)}

🧾 Expenses:
{st.session_state.get("expense_details", {})}
"""

        url = f"https://wa.me/{get_manager_phone()}?text={urllib.parse.quote(report)}"

        st.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="width:100%;background:#25D366;color:white;padding:12px;border:none;border-radius:8px;font-weight:bold;">'
            f'📱 Send To WhatsApp'
            f'</button></a>',
            unsafe_allow_html=True
        )
