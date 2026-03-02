# =====================================================
# DAILY OPERATIONS MODULE (FULL SAFE VERSION)
# =====================================================

import streamlit as st
from datetime import date
import urllib.parse
from pdf_generator import create_downloadable_pdf
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


            printer_start[printer] = {
                "Total": total
            }

            st.divider()

        st.session_state["printer_start"] = printer_start

    # =====================================================
    # TAB 2 — CLOSING
    # =====================================================

    with tab2:

        st.subheader("🌅 Closing Tasks")

        for task in db["tasks"].get("closing", []):
            st.checkbox(task, key=f"close_task_{task}")

        st.divider()

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
    # TAB 3 — SOCIAL + ARCHIVE + REPORT
    # =====================================================
    
    with tab3:
    
        st.subheader("📱 Social Tasks")
    
        for task in db["tasks"].get("social", []):
            st.checkbox(task, key=f"social_{task}")
    
        st.divider()
    
        # =====================================================
        # ARCHIVE
        # =====================================================
    
        sys_sales = st.session_state.get("c_sys_sales", 0)
    
        col1, col2 = st.columns(2)
    
        with col1:
    
            if st.button("💾 Archive Shift", use_container_width=True):
    
                db.setdefault("history", []).append({
                    "date": str(date.today()),
                    "branch": st.session_state.get("branch", "-"),
                    "shift": st.session_state.get("shift", "-"),
                    "staff": st.session_state.get("user", "-"),
                    "sales": sys_sales,
                    "expenses": st.session_state.get("shift_expenses", []),
                    "opay_open": st.session_state.get("opay_open", 0),
                    "opay_close": st.session_state.get("opay_close", 0),
                    "debit_open": st.session_state.get("debit_open", 0),
                    "debit_close": st.session_state.get("debit_close", 0),
                    "nbe_open": st.session_state.get("nbe_open", 0),
                    "nbe_close": st.session_state.get("nbe_close", 0),
                })
    
                save_db(db)
                st.success("Archived Successfully ✅")
    
        # =====================================================
        # WHATSAPP + PDF REPORT
        # =====================================================
    
        with col2:
    
            branch = st.session_state.get("branch", "-")
            user = st.session_state.get("user", "-")
            shift = st.session_state.get("shift", "-")
    
            sys_sales = st.session_state.get("c_sys_sales", 0.0)
    
            opay_open = st.session_state.get("opay_open", 0.0)
            opay_close = st.session_state.get("opay_close", 0.0)
            debit_open = st.session_state.get("debit_open", 0.0)
            debit_close = st.session_state.get("debit_close", 0.0)
            nbe_open = st.session_state.get("nbe_open", 0.0)
            nbe_close = st.session_state.get("nbe_close", 0.0)
    
            opay_diff = opay_close - opay_open
            debit_diff = debit_close - debit_open
            nbe_diff = nbe_close - nbe_open
    
            shift_expenses = st.session_state.get("shift_expenses", [])
            total_expenses = sum(e.get("amount", 0) for e in shift_expenses)
    
            expense_lines = "\n".join(
                f"• {e.get('type','Unknown')} : {e.get('amount',0):,.2f}"
                for e in shift_expenses
            )
    
            if not expense_lines:
                expense_lines = "No Expenses Recorded"
    
            # =====================================================
            # PRINTER SECTION (SAFE)
            # =====================================================
    
            printer_diff = st.session_state.get("printer_diff", {})
    
            printer_lines = ""
    
            if not printer_diff:
                printer_lines = "No Printer Data\n"
            else:
                for printer_name, values in printer_diff.items():
                    printer_lines += (
                        f"📠 {printer_name}\n"
                        f"Used: {values.get('used',0)}\n"
                        f"Jam: {values.get('jam',0)}\n"
                        f"1-Side: {values.get('1s',0)}\n"
                        f"2-Side: {values.get('2s',0)}\n"
                        "------------------------\n\n"
                    )
    
            cash_diff = st.session_state.get("cash_diff", 0.0)
    
            # =====================================================
            # BUILD WHATSAPP TEXT
            # =====================================================
    
            wa_text = f"""
    ■ NMS FULL SHIFT REPORT
    ■■■■■■■■■■■■■■■■■■■■■■
    
    📅 Date: {date.today()}
    🏢 Branch: {branch}
    🕒 Shift: {shift}
    👤 Staff: {user}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    💰 SALES
    Total System Sales: {sys_sales:,.2f}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    💳 DIGITAL PAYMENTS
    
    🟢 OPAY
    Open: {opay_open:,.2f}
    Close: {opay_close:,.2f}
    Diff: {opay_diff:,.2f}
    
    🔵 DEBIT
    Open: {debit_open:,.2f}
    Close: {debit_close:,.2f}
    Diff: {debit_diff:,.2f}
    
    🟡 NBE
    Open: {nbe_open:,.2f}
    Close: {nbe_close:,.2f}
    Diff: {nbe_diff:,.2f}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    💸 EXPENSES
    Total Expenses: {total_expenses:,.2f}
    
    {expense_lines}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    🖨 PRINTER DIFFERENCES
    
    {printer_lines}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    💵 CASH DIFFERENCE
    {cash_diff:,.2f}
    
    ■■■■■■■■■■■■■■■■■■■■■■
    Generated by NMS System
    """
    
            wa_text = wa_text.strip()[:3500]
    
            # =====================================================
            # BUTTONS
            # =====================================================
    
            if st.button("📄 Generate PDF", use_container_width=True):
    
                from pdf_generator import create_downloadable_pdf
    
                pdf_bytes = create_downloadable_pdf(
                    branch,
                    user,
                    str(date.today()),
                    sys_sales,
                    total_expenses,
                    expense_lines,
                    cash_diff,
                    printer_diff,
                    opay_diff,
                    debit_diff
                )
    
                st.download_button(
                    "📥 Download PDF",
                    pdf_bytes,
                    file_name="shift_report.pdf"
                )
    
            # ================= WhatsApp =================
    
            manager_phone = get_manager_phone()
    
            url = f"https://wa.me/{manager_phone}?text={urllib.parse.quote(wa_text)}"
    
            st.markdown(
                f'<a href="{url}" target="_blank">'
                f'<button style="width:100%;background:#25D366;color:white;'
                f'padding:14px;border-radius:10px;border:none;font-weight:bold;">'
                f'📱 Send To WhatsApp'
                f'</button></a>',
                unsafe_allow_html=True
            )
