# =====================================================
# DAILY OPERATIONS MODULE (CLEAN FULL VERSION)
# =====================================================

import streamlit as st
from datetime import date
import urllib.parse

from pdf_generator import create_downloadable_pdf
from printer_service import calculate_printer_difference, get_printers
from database import save_db, get_manager_phone


def daily_operations_ui(db):

    if "user" not in st.session_state:
        return

    st.title("📊 NMS ERP - Daily Operations")

    # =====================================================
    # BRANCH & SHIFT
    # =====================================================

    branches = db.get("branches", [])
    if not branches:
        branches = ["No Branch"]

    st.session_state["branch"] = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(
            st.session_state.get("branch", branches[0])
        ) if st.session_state.get("branch") in branches else 0
    )

    shifts = ["Morning", "Between", "Night"]
    st.session_state["shift"] = st.selectbox(
        "🕒 Shift",
        shifts,
        index=shifts.index(
            st.session_state.get("shift", "Morning")
        )
    )

    st.info(f"📅 {date.today()} | 👤 {st.session_state['user']}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    # =====================================================
    # TAB 1 — OPENING
    # =====================================================

    with tab1:

        st.subheader("🌅 Opening Cash")

        t_open = 0.0
        for d in [200, 100, 50, 20, 10, 5]:
            t_open += st.number_input(
                f"{d} LE",
                min_value=0,
                step=1,
                key=f"open_{d}"
            ) * d

        t_open += st.number_input("Coins", step=0.5, key="open_coins")

        # DIGITAL OPENING
        for key in ["opay_open", "debit_open", "nbe_open"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

            st.session_state[key] = st.number_input(
                f"{key.replace('_',' ').title()}",
                min_value=0.0,
                step=1.0,
                value=float(st.session_state[key])
            )

        st.session_state["t_open"] = t_open

        st.divider()

        # ======================
        # PRINTER START
        # ======================

        printer_start = {}
        printers = get_printers() or {}

        for printer in printers.keys():
            st.markdown(f"##### 📠 {printer}")

            printer_start[printer] = {
                "Total": st.number_input(f"{printer} Total", min_value=0, key=f"{printer}_start_total"),
                "One Side": st.number_input(f"{printer} One", min_value=0, key=f"{printer}_start_one"),
                "Two Side": st.number_input(f"{printer} Two", min_value=0, key=f"{printer}_start_two"),
                "Errors": st.number_input(f"{printer} Errors", min_value=0, key=f"{printer}_start_err"),
                "Jam": st.number_input(f"{printer} Jam", min_value=0, key=f"{printer}_start_jam"),
            }

            st.divider()

        st.session_state["printer_start"] = printer_start

    # =====================================================
    # TAB 2 — CLOSING
    # =====================================================

    with tab2:

        sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales")

        # ======================
        # DIGITAL CLOSE
        # ======================

        for key in ["opay_close", "debit_close", "nbe_close"]:
            if key not in st.session_state:
                st.session_state[key] = 0.0

            st.session_state[key] = st.number_input(
                f"{key.replace('_',' ').title()}",
                min_value=0.0,
                step=1.0,
                value=float(st.session_state[key])
            )

        # ======================
        # EXPENSES (SELECT LIST)
        # ======================

        st.subheader("💸 Expenses")

        expense_categories = db.get("expense_categories", [])

        if "shift_expenses" not in st.session_state:
            st.session_state["shift_expenses"] = []

        col1, col2 = st.columns(2)

        with col1:
            expense_type = st.selectbox("Expense Type", expense_categories)

        with col2:
            expense_value = st.number_input("Amount", min_value=0.0, step=1.0)

        if st.button("➕ Add Expense"):
            st.session_state["shift_expenses"].append(
                {"type": expense_type, "amount": expense_value}
            )

        total_expenses = sum(
            e["amount"] for e in st.session_state["shift_expenses"]
        )

        st.warning(f"Total Expenses: {total_expenses:,.2f}")

        # ======================
        # CASH CALC
        # ======================

        t_digital = (
            st.session_state["opay_open"]
            + st.session_state["debit_open"]
            + st.session_state["nbe_open"]
        )

        expected = (
            st.session_state["t_open"]
            + sys_sales
            - total_expenses
            - t_digital
        )

        st.metric("Expected Cash", f"{expected:,.2f}")

        t_close = 0
        for d in [200, 100, 50, 20, 10, 5]:
            t_close += st.number_input(
                f"{d} LE Close",
                min_value=0,
                step=1,
                key=f"close_{d}"
            ) * d

        t_close += st.number_input("Closing Coins", step=0.5)

        diff = t_close - expected

        st.metric("Difference", f"{diff:,.2f}")

        st.session_state["cash_diff"] = diff

        # ======================
        # PRINTER END
        # ======================

        printer_end = {}
        printers = get_printers() or {}

        for printer in printers.keys():
            st.markdown(f"##### 📠 {printer}")

            printer_end[printer] = {
                "Total": st.number_input(f"{printer} End Total", min_value=0),
                "One Side": st.number_input(f"{printer} End One", min_value=0),
                "Two Side": st.number_input(f"{printer} End Two", min_value=0),
                "Errors": st.number_input(f"{printer} End Errors", min_value=0),
                "Jam": st.number_input(f"{printer} End Jam", min_value=0),
            }

            st.divider()

        st.session_state["printer_end"] = printer_end

        if st.button("📊 Calculate Printer Usage"):
            st.session_state["printer_diff"] = calculate_printer_difference(
                st.session_state.get("printer_start", {}),
                st.session_state.get("printer_end", {})
            )
            st.success("Calculated ✅")

    # =====================================================
    # ARCHIVE + FULL REPORT
    # =====================================================

    st.divider()

    branch = st.session_state.get("branch", "-")
    shift = st.session_state.get("shift", "-")
    user = st.session_state.get("user", "-")
    sys_sales = st.session_state.get("c_sys_sales", 0.0)
    total_expenses = sum(
        e["amount"] for e in st.session_state.get("shift_expenses", [])
    )

    opay_open = st.session_state.get("opay_open", 0)
    opay_close = st.session_state.get("opay_close", 0)
    debit_open = st.session_state.get("debit_open", 0)
    debit_close = st.session_state.get("debit_close", 0)
    nbe_open = st.session_state.get("nbe_open", 0)
    nbe_close = st.session_state.get("nbe_close", 0)

    printer_diff = st.session_state.get("printer_diff", {})

    wa_text = f"""
📊 FULL SHIFT REPORT
Date: {date.today()}
Branch: {branch}
Shift: {shift}
Staff: {user}

💰 Sales: {sys_sales}

💸 Expenses:
{st.session_state.get("shift_expenses", [])}

💳 OPAY {opay_open} ➜ {opay_close}
💳 DEBIT {debit_open} ➜ {debit_close}
🏦 NBE {nbe_open} ➜ {nbe_close}

🖨 Printer Diff:
{printer_diff}

📉 Cash Difference:
{st.session_state.get("cash_diff", 0)}
"""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Archive Shift", use_container_width=True):
            db.setdefault("history", []).append({
                "date": str(date.today()),
                "branch": branch,
                "shift": shift,
                "staff": user,
                "sales": sys_sales,
                "expenses": st.session_state.get("shift_expenses", []),
                "opay_open": opay_open,
                "opay_close": opay_close,
                "debit_open": debit_open,
                "debit_close": debit_close,
                "nbe_open": nbe_open,
                "nbe_close": nbe_close,
            })

            save_db(db)
            st.success("Archived ✅")

    with col2:
        url = f"https://wa.me/{get_manager_phone()}?text={urllib.parse.quote(wa_text)}"

        st.markdown(
            f"""
            <a href="{url}" target="_blank">
            <button style="
            width:100%;
            background:#25D366;
            color:white;
            padding:15px;
            border:none;
            border-radius:10px;
            font-weight:bold;
            ">
            📱 SEND FULL REPORT TO WHATSAPP
            </button>
            </a>
            """,
            unsafe_allow_html=True
        )
