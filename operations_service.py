# =====================================================
# DAILY OPERATIONS MODULE (FULL SAFE VERSION)
# =====================================================

import streamlit as st
from datetime import date
import urllib.parse

from printer_service import calculate_printer_difference, get_printers
from database import save_db, get_manager_phone


# =====================================================
# MAIN UI
# =====================================================

def daily_operations_ui(db):

    if "user" not in st.session_state:
        return

    st.title("📊 NMS ERP - Daily Operations")

    # =====================================================
    # SAFE BRANCH SELECT
    # =====================================================

    branches = db.get("branches", [])

    if not branches:
        branches = ["No Branch"]

    current_branch = st.session_state.get("branch", branches[0])

    if current_branch not in branches:
        current_branch = branches[0]

    st.session_state["branch"] = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(current_branch)
    )

    # =====================================================
    # SAFE SHIFT SELECT
    # =====================================================

    shifts = ["Morning", "Between", "Night"]

    current_shift = st.session_state.get("shift", "Morning")

    if current_shift not in shifts:
        current_shift = "Morning"

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


        # ========================
        # Opay & Debit Opening
        # ========================
        
        if "opay_open" not in st.session_state:
            st.session_state["opay_open"] = 0.0
        
        if "debit_open" not in st.session_state:
            st.session_state["debit_open"] = 0.0
        
        opay_open = st.number_input(
            "💳 Opay Opening",
            min_value=0.0,
            step=1.0,
            value=float(st.session_state["opay_open"]),
            key="opay_open_input"
        )
        
        debit_open = st.number_input(
            "💳 Debit Opening",
            min_value=0.0,
            step=1.0,
            value=float(st.session_state["debit_open"]),
            key="debit_open_input"
        )
        
        st.session_state["opay_open"] = float(opay_open)
        st.session_state["debit_open"] = float(debit_open)

        st.divider()
        st.subheader("🖨 Printer Start Counters")

        printer_start = {}
        printers = get_printers() or {}
        for printer in printers.keys():
            st.markdown(f"##### 📠 {printer}")

            total = st.number_input(
                f"{printer} ✔ Total",
                min_value=0,
                key=f"{printer}_start_total"
            )

            one = st.number_input(
                f"{printer} ✔ 1 Side",
                min_value=0,
                key=f"{printer}_start_one"
            )

            two = st.number_input(
                f"{printer} ✔ 2 Side",
                min_value=0,
                key=f"{printer}_start_two"
            )

            err = st.number_input(
                f"{printer} ❌ Errors",
                min_value=0,
                key=f"{printer}_start_err"
            )

            jam = st.number_input(
                f"{printer} ⚠ Jam",
                min_value=0,
                key=f"{printer}_start_jam"
            )

            printer_start[printer] = {
                "Total": total,
                "One Side": one,
                "Two Side": two,
                "Errors": err,
                "Jam": jam
            }

            st.divider()

        st.session_state["printer_start"] = printer_start

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
        

        st.divider()
        st.subheader("🧮 Cash Count")

        t_close = 0

        for d in [200, 100, 50, 20, 10, 5]:
            v = st.number_input(
                f"{d} LE ",
                min_value=0,
                step=1,
                key=f"close_{d}"
            )
            t_close += v * d

        coins = st.number_input(
            "Closing Coins",
            step=0.5,
            key="close_coins"
        )

        t_close += coins

        diff = t_close - expected

        st.metric("Expected Cash", f"{expected:,.2f}")
        st.metric("Difference", f"{diff:,.2f}")

        st.session_state["cash_diff"] = diff
        st.session_state["t_close"] = t_close

        st.divider()
        st.subheader("🖨 Printer End Counters")

        printer_end = {}
        printers = get_printers() or {}

        for printer in printers:

            st.markdown(f"##### 📠 {printer}")

            total_end = st.number_input(
                f"{printer} ✔ End Total",
                min_value=0,
                key=f"{printer}_end_total"
            )

            one_end = st.number_input(
                f"{printer} ✔ End 1 Side",
                min_value=0,
                key=f"{printer}_end_one"
            )

            two_end = st.number_input(
                f"{printer} ✔ End 2 Side",
                min_value=0,
                key=f"{printer}_end_two"
            )

            err_end = st.number_input(
                f"{printer} ❌ End Errors",
                min_value=0,
                key=f"{printer}_end_err"
            )

            jam_end = st.number_input(
                f"{printer} ⚠ End Jam",
                min_value=0,
                key=f"{printer}_end_jam"
            )

            printer_end[printer] = {
                "Total": total_end,
                "One Side": one_end,
                "Two Side": two_end,
                "Errors": err_end,
                "Jam": jam_end
            }

            st.divider()

        st.session_state["printer_end"] = printer_end

        if st.button("📊 Calculate Printer Usage"):

            diff_p = calculate_printer_difference(
                st.session_state.get("printer_start", {}),
                st.session_state.get("printer_end", {})
            )

            st.session_state["printer_diff"] = diff_p

            st.success("Printer Usage Calculated ✅")
            st.json(diff_p)

    # =====================================================
    # TAB 3 — SOCIAL
    # =====================================================

    with tab3:

        st.subheader("📱 Social Tasks")

        for task in db["tasks"].get("social", []):
            st.checkbox(task, key=f"social_{task}")

    # =====================================================
    # ARCHIVE + WHATSAPP
    # =====================================================

    st.divider()

    sys_sales = st.session_state.get("c_sys_sales", 0)
    branch = st.session_state.get("branch")
    shift = st.session_state.get("shift")

    col1, col2 = st.columns(2)

    with col1:
        
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

    with col2:

        sys_sales = st.session_state.get("c_sys_sales", 0)

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
