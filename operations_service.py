# =====================================================
# DAILY OPERATIONS MODULE (ULTRA FULL VERSION)
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

    # =====================================================
    # BRANCH
    # =====================================================

    branches = db.get("branches", []) or ["No Branch"]

    current_branch = st.session_state.get("branch", branches[0])
    if current_branch not in branches:
        current_branch = branches[0]

    st.session_state["branch"] = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(current_branch)
    )

    # =====================================================
    # SHIFT
    # =====================================================

    shifts = ["Morning", "Between", "Night"]
    current_shift = st.session_state.get("shift", "Morning")

    st.session_state["shift"] = st.selectbox(
        "🕒 Shift",
        shifts,
        index=shifts.index(current_shift)
    )

    st.info(f"📅 {date.today()} | 👤 {st.session_state.get('user')}")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    # =====================================================
    # TAB 1 — OPENING
    # =====================================================

    with tab1:

        st.subheader("💰 Opening Cash")

        t_open = 0.0
        for d in [200, 100, 50, 20, 10, 5]:
            v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"open_{d}")
            t_open += v * d

        coins = st.number_input("Coins", step=0.5, key="open_coins")
        t_open += coins

        # Digital Opening
        for key in ["opay_open", "debit_open", "nbe_open"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

        st.session_state["opay_open"] = st.number_input(
            "💳 Opay Opening", min_value=0.0, step=1.0,
            value=float(st.session_state["opay_open"])
        )

        st.session_state["debit_open"] = st.number_input(
            "💳 Debit Opening", min_value=0.0, step=1.0,
            value=float(st.session_state["debit_open"])
        )

        st.session_state["nbe_open"] = st.number_input(
            "🏦 NBE Wallet Opening", min_value=0.0, step=1.0,
            value=float(st.session_state["nbe_open"])
        )

        st.success(f"Total Opening Cash: {t_open:,.2f} LE")
        st.session_state["t_open"] = t_open

    # =====================================================
    # TAB 2 — CLOSING
    # =====================================================

    with tab2:

        st.subheader("💰 Closing Section")

        sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales")
        insta = st.number_input("Instapay", step=1.0)
        wallet = st.number_input("Wallet", step=1.0)
        visa = st.number_input("Visa", step=1.0)

        for key in ["opay_close", "debit_close", "nbe_close"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

        st.session_state["opay_close"] = st.number_input(
            "💳 Opay Closing", min_value=0.0, step=1.0,
            value=float(st.session_state["opay_close"])
        )

        st.session_state["debit_close"] = st.number_input(
            "💳 Debit Closing", min_value=0.0, step=1.0,
            value=float(st.session_state["debit_close"])
        )

        st.session_state["nbe_close"] = st.number_input(
            "🏦 NBE Wallet Closing", min_value=0.0, step=1.0,
            value=float(st.session_state["nbe_close"])
        )

        # ========================
        # EXPENSES (SELECT LIST)
        # ========================

        st.divider()
        st.subheader("💸 Expenses")

        expense_categories = db.get("expense_categories", [])

        if "shift_expenses" not in st.session_state:
            st.session_state["shift_expenses"] = []

        col1, col2 = st.columns(2)

        with col1:
            selected_expense = st.selectbox("Expense Type", expense_categories)

        with col2:
            expense_value = st.number_input("Amount", min_value=0.0, step=1.0)

        if st.button("➕ Add Expense"):
            st.session_state["shift_expenses"].append({
                "type": selected_expense,
                "amount": expense_value
            })

        total_expenses = sum(e["amount"] for e in st.session_state["shift_expenses"])

        st.write("### Added Expenses")
        st.json(st.session_state["shift_expenses"])
        st.warning(f"Total Expenses: {total_expenses:,.2f} LE")

        # ========================
        # CASH CALCULATION
        # ========================

        t_digital = insta + wallet + visa
        expected = (
            st.session_state["t_open"]
            + sys_sales
            - total_expenses
            - t_digital
        )

        st.metric("Expected Cash", f"{expected:,.2f}")

    # =====================================================
    # ARCHIVE + WHATSAPP
    # =====================================================

    st.divider()

    if st.button("💾 Archive Shift"):

        db["history"].append({
            "date": str(date.today()),
            "branch": st.session_state["branch"],
            "shift": st.session_state["shift"],
            "staff": st.session_state["user"],
            "sales": sys_sales,
            "expenses": st.session_state["shift_expenses"],
            "opay_open": st.session_state["opay_open"],
            "opay_close": st.session_state["opay_close"],
            "debit_open": st.session_state["debit_open"],
            "debit_close": st.session_state["debit_close"],
            "nbe_open": st.session_state["nbe_open"],
            "nbe_close": st.session_state["nbe_close"],
        })

        save_db(db)
        st.success("Archived Successfully ✅")

    # ========================
    # WHATSAPP REPORT (FULL)
    # ========================

    wa_text = f"""
📊 SHIFT REPORT
Date: {date.today()}
Branch: {st.session_state["branch"]}
Shift: {st.session_state["shift"]}
Staff: {st.session_state["user"]}

💰 Sales: {sys_sales}

💳 Digital:
Opay: {st.session_state["opay_open"]} ➜ {st.session_state["opay_close"]}
Debit: {st.session_state["debit_open"]} ➜ {st.session_state["debit_close"]}
NBE: {st.session_state["nbe_open"]} ➜ {st.session_state["nbe_close"]}

💸 Expenses: {total_expenses}
"""

    url = f"https://wa.me/{get_manager_phone()}?text={urllib.parse.quote(wa_text)}"

    st.markdown(
        f'<a href="{url}" target="_blank">'
        f'<button style="width:100%;background:#25D366;color:white;padding:12px;border:none;border-radius:8px;font-weight:bold;">'
        f'📱 Send Full Report To WhatsApp'
        f'</button></a>',
        unsafe_allow_html=True
    )
