# =====================================================
# DAILY OPERATIONS MODULE (REFACTORED VERSION)
# =====================================================

from datetime import date
import urllib.parse

import streamlit as st

from database import save_db, get_manager_phone
from pdf_generator import create_downloadable_pdf
from printer_service import calculate_printer_difference, get_printers


# =====================================================
# Constants
# =====================================================
SHIFT_OPTIONS = ["Morning", "Between", "Night"]
CASH_DENOMINATIONS = [200, 100, 50, 20, 10, 5]


# =====================================================
# Session Helpers
# =====================================================
def ensure_session_defaults() -> None:
    defaults = {
        "branch": "",
        "shift": "Morning",
        "t_open": 0.0,
        "t_close": 0.0,
        "cash_diff": 0.0,
        "c_sys_sales": 0.0,
        "shift_expenses": [],
        "printer_start": {},
        "printer_end": {},
        "printer_diff": {},
        "opay_open": 0.0,
        "opay_close": 0.0,
        "debit_open": 0.0,
        "debit_close": 0.0,
        "nbe_open": 0.0,
        "nbe_close": 0.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_selected_branch(db: dict) -> str:
    branches = db.get("branches", [])
    if not branches:
        branches = ["No Branch"]

    current_branch = st.session_state.get("branch", branches[0])
    if current_branch not in branches:
        current_branch = branches[0]

    selected = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(current_branch),
    )
    st.session_state["branch"] = selected
    return selected


def get_selected_shift() -> str:
    current_shift = st.session_state.get("shift", "Morning")
    if current_shift not in SHIFT_OPTIONS:
        current_shift = "Morning"

    selected = st.selectbox(
        "🕒 Shift",
        SHIFT_OPTIONS,
        index=SHIFT_OPTIONS.index(current_shift),
    )
    st.session_state["shift"] = selected
    return selected


# =====================================================
# Generic Helpers
# =====================================================
def render_cash_counter(section_prefix: str, title_suffix: str = "") -> float:
    total = 0.0

    for denomination in CASH_DENOMINATIONS:
        qty = st.number_input(
            f"{denomination} LE{title_suffix}",
            min_value=0,
            step=1,
            key=f"{section_prefix}_{denomination}",
        )
        total += qty * denomination

    coins = st.number_input(
        f"{'Coins' if section_prefix == 'open' else 'Closing Coins'}",
        min_value=0.0,
        step=0.5,
        key=f"{section_prefix}_coins",
    )
    total += coins

    return total


def render_digital_inputs(mode: str) -> tuple[float, float, float]:
    opay_key = f"opay_{mode}"
    debit_key = f"debit_{mode}"
    nbe_key = f"nbe_{mode}"

    st.session_state[opay_key] = st.number_input(
        f"💳 Opay {mode.capitalize()}",
        min_value=0.0,
        step=1.0,
        value=float(st.session_state.get(opay_key, 0.0)),
    )

    st.session_state[debit_key] = st.number_input(
        f"💳 Debit {mode.capitalize()}",
        min_value=0.0,
        step=1.0,
        value=float(st.session_state.get(debit_key, 0.0)),
    )

    st.session_state[nbe_key] = st.number_input(
        f"🏦 NBE Wallet {mode.capitalize()}",
        min_value=0.0,
        step=1.0,
        value=float(st.session_state.get(nbe_key, 0.0)),
    )

    return (
        float(st.session_state[opay_key]),
        float(st.session_state[debit_key]),
        float(st.session_state[nbe_key]),
    )


def render_printer_start_inputs() -> None:
    st.subheader("🖨 Printer Start Counters")

    printers = get_printers() or {}
    printer_start = {}

    if not printers:
        st.info("No printers configured.")
        st.session_state["printer_start"] = {}
        return

    for printer_name in printers.keys():
        st.markdown(f"##### 📠 {printer_name}")

        total = st.number_input(
            f"{printer_name} ✔ Total",
            min_value=0,
            key=f"{printer_name}_start_total",
        )

        printer_start[printer_name] = {
            "Total": total,
        }

        st.divider()

    st.session_state["printer_start"] = printer_start


def render_printer_end_inputs() -> None:
    st.subheader("🖨 Printer End Counters")

    printers = get_printers() or {}
    printer_end = {}

    if not printers:
        st.info("No printers configured.")
        st.session_state["printer_end"] = {}
        return

    for printer_name in printers.keys():
        st.markdown(f"##### 📠 {printer_name}")

        total_end = st.number_input(
            f"{printer_name} ✔ End Total",
            min_value=0,
            key=f"{printer_name}_end_total",
        )
        one_end = st.number_input(
            f"{printer_name} ✔ End 1 Side",
            min_value=0,
            key=f"{printer_name}_end_one",
        )
        two_end = st.number_input(
            f"{printer_name} ✔ End 2 Side",
            min_value=0,
            key=f"{printer_name}_end_two",
        )
        err_end = st.number_input(
            f"{printer_name} ❌ End Errors",
            min_value=0,
            key=f"{printer_name}_end_err",
        )
        jam_end = st.number_input(
            f"{printer_name} ⚠ End Jam",
            min_value=0,
            key=f"{printer_name}_end_jam",
        )

        printer_end[printer_name] = {
            "Total": total_end,
            "One Side": one_end,
            "Two Side": two_end,
            "Errors": err_end,
            "Jam": jam_end,
        }

        st.divider()

    st.session_state["printer_end"] = printer_end


def calculate_total_expenses(expenses: list) -> float:
    return sum(float(item.get("amount", 0) or 0) for item in expenses)


def build_expense_lines(expenses: list) -> str:
    if not expenses:
        return "No Expenses Recorded"

    return "\n".join(
        f"• {item.get('type', 'Unknown')} : {float(item.get('amount', 0) or 0):,.2f}"
        for item in expenses
    )


def build_printer_lines(printer_diff: dict) -> str:
    if not printer_diff:
        return "No Printer Data\n"

    lines = []
    for printer_name, values in printer_diff.items():
        lines.append(
            "\n".join(
                [
                    f"📠 {printer_name}",
                    f"Used: {values.get('used', 0)}",
                    f"Jam: {values.get('jam', 0)}",
                    f"1-Side: {values.get('1s', 0)}",
                    f"2-Side: {values.get('2s', 0)}",
                    "------------------------",
                ]
            )
        )

    return "\n\n".join(lines)


def get_shift_report_data() -> dict:
    sys_sales = float(st.session_state.get("c_sys_sales", 0.0) or 0.0)

    opay_open = float(st.session_state.get("opay_open", 0.0) or 0.0)
    opay_close = float(st.session_state.get("opay_close", 0.0) or 0.0)

    debit_open = float(st.session_state.get("debit_open", 0.0) or 0.0)
    debit_close = float(st.session_state.get("debit_close", 0.0) or 0.0)

    nbe_open = float(st.session_state.get("nbe_open", 0.0) or 0.0)
    nbe_close = float(st.session_state.get("nbe_close", 0.0) or 0.0)

    shift_expenses = st.session_state.get("shift_expenses", [])
    total_expenses = calculate_total_expenses(shift_expenses)

    opay_diff = opay_close - opay_open
    debit_diff = debit_close - debit_open
    nbe_diff = nbe_close - nbe_open

    cash_diff = float(st.session_state.get("cash_diff", 0.0) or 0.0)
    printer_diff = st.session_state.get("printer_diff", {})

    return {
        "date": str(date.today()),
        "branch": st.session_state.get("branch", "-"),
        "shift": st.session_state.get("shift", "-"),
        "staff": st.session_state.get("user", "-"),
        "sales": sys_sales,
        "expenses_list": shift_expenses,
        "total_expenses": total_expenses,
        "expense_lines": build_expense_lines(shift_expenses),
        "cash_diff": cash_diff,
        "printer_diff": printer_diff,
        "printer_lines": build_printer_lines(printer_diff),
        "opay_open": opay_open,
        "opay_close": opay_close,
        "opay_diff": opay_diff,
        "debit_open": debit_open,
        "debit_close": debit_close,
        "debit_diff": debit_diff,
        "nbe_open": nbe_open,
        "nbe_close": nbe_close,
        "nbe_diff": nbe_diff,
        "t_open": float(st.session_state.get("t_open", 0.0) or 0.0),
        "t_close": float(st.session_state.get("t_close", 0.0) or 0.0),
    }


def archive_shift(db: dict) -> None:
    report = get_shift_report_data()

    db.setdefault("history", [])
    db["history"].append(
        {
            "date": report["date"],
            "branch": report["branch"],
            "shift": report["shift"],
            "staff": report["staff"],
            "sales": report["sales"],
            "expenses": report["total_expenses"],
            "expenses_list": report["expenses_list"],
            "exp_note": report["expense_lines"],
            "diff": report["cash_diff"],
            "t_open": report["t_open"],
            "t_close": report["t_close"],
            "opay_open": report["opay_open"],
            "opay_close": report["opay_close"],
            "opay_diff": report["opay_diff"],
            "debit_open": report["debit_open"],
            "debit_close": report["debit_close"],
            "debit_diff": report["debit_diff"],
            "nbe_open": report["nbe_open"],
            "nbe_close": report["nbe_close"],
            "nbe_diff": report["nbe_diff"],
            "printer_diff": report["printer_diff"],
        }
    )

    save_db(db)


def build_whatsapp_text() -> str:
    report = get_shift_report_data()

    wa_text = f"""
■ NMS FULL SHIFT REPORT
■■■■■■■■■■■■■■■■■■■

📅 Date: {report["date"]}
🏢 Branch: {report["branch"]}
🕒 Shift: {report["shift"]}
👤 Staff: {report["staff"]}

■■■■■■■■■■■■■■■■■■■
💰 SALES
Total System Sales: {report["sales"]:,.2f}

■■■■■■■■■■■■■■■■■■■
💳 DIGITAL PAYMENTS

🟢 OPAY
Open: {report["opay_open"]:,.2f}
Close: {report["opay_close"]:,.2f}
Diff: {report["opay_diff"]:,.2f}

🔵 DEBIT
Open: {report["debit_open"]:,.2f}
Close: {report["debit_close"]:,.2f}
Diff: {report["debit_diff"]:,.2f}

🟡 NBE
Open: {report["nbe_open"]:,.2f}
Close: {report["nbe_close"]:,.2f}
Diff: {report["nbe_diff"]:,.2f}

■■■■■■■■■■■■■■■■■■■
💸 EXPENSES
Total Expenses: {report["total_expenses"]:,.2f}

{report["expense_lines"]}

■■■■■■■■■■■■■■■■■■■
🖨 PRINTER DIFFERENCES

{report["printer_lines"]}

■■■■■■■■■■■■■■■■■■■
💵 CASH DIFFERENCE
{report["cash_diff"]:,.2f}

■■■■■■■■■■■■■■■■■■■
Generated by NMS System
"""
    return wa_text.strip()[:3500]


# =====================================================
# Opening Tab
# =====================================================
def render_opening_tab(db: dict) -> None:
    st.subheader("🌅 Opening Tasks")

    for task in db.get("tasks", {}).get("opening", []):
        st.checkbox(task, key=f"open_task_{task}")

    st.divider()

    st.subheader("💰 Opening Cash")
    t_open = render_cash_counter("open")
    st.success(f"Total Opening Cash: {t_open:,.2f} LE")
    st.session_state["t_open"] = t_open

    st.divider()
    st.subheader("💳 Digital Opening")
    render_digital_inputs("open")

    st.divider()
    render_printer_start_inputs()


# =====================================================
# Closing Tab
# =====================================================
def render_expenses_section(db: dict) -> float:
    st.divider()
    st.subheader("💸 Expenses")

    expense_categories = db.get("expense_categories", [])
    if not expense_categories:
        expense_categories = ["General Expense"]

    col1, col2 = st.columns(2)

    with col1:
        selected_expense = st.selectbox("Expense Type", expense_categories)

    with col2:
        expense_value = st.number_input("Amount", min_value=0.0, step=1.0)

    if st.button("➕ Add Expense"):
        st.session_state["shift_expenses"].append(
            {
                "type": selected_expense,
                "amount": expense_value,
            }
        )
        st.rerun()

    if st.session_state["shift_expenses"]:
        st.markdown("#### Current Shift Expenses")
        for index, item in enumerate(st.session_state["shift_expenses"]):
            c1, c2 = st.columns([6, 1])
            with c1:
                st.write(f"• {item.get('type', 'Unknown')} — {float(item.get('amount', 0) or 0):,.2f} LE")
            with c2:
                if st.button("✖️", key=f"remove_exp_{index}"):
                    st.session_state["shift_expenses"].pop(index)
                    st.rerun()

        if st.button("🧹 Clear All Expenses"):
            st.session_state["shift_expenses"] = []
            st.rerun()

    total_expenses = calculate_total_expenses(st.session_state["shift_expenses"])
    st.warning(f"Total Expenses: {total_expenses:,.2f} LE")

    return total_expenses


def render_closing_tab(db: dict) -> None:
    st.subheader("🌇 Closing Tasks")

    for task in db.get("tasks", {}).get("closing", []):
        st.checkbox(task, key=f"close_task_{task}")

    st.divider()
    st.subheader("💰 Closing Section")

    sys_sales = st.number_input("System Sales", min_value=0.0, step=1.0, key="c_sys_sales")
    insta = st.number_input("Instapay", min_value=0.0, step=1.0, key="insta_amount")
    wallet = st.number_input("Wallet", min_value=0.0, step=1.0, key="wallet_amount")
    visa = st.number_input("Visa", min_value=0.0, step=1.0, key="visa_amount")

    st.divider()
    st.subheader("💳 Digital Closing")
    render_digital_inputs("close")

    total_expenses = render_expenses_section(db)

    t_digital = insta + wallet + visa
    expected = float(st.session_state.get("t_open", 0.0) or 0.0) + sys_sales - total_expenses - t_digital

    st.metric("Expected Cash", f"{expected:,.2f} LE")

    st.divider()
    st.subheader("🧮 Cash Count")

    t_close = render_cash_counter("close", title_suffix=" ")
    diff = t_close - expected

    st.metric("Actual Cash", f"{t_close:,.2f} LE")
    st.metric("Difference", f"{diff:,.2f} LE")

    st.session_state["t_close"] = t_close
    st.session_state["cash_diff"] = diff

    st.divider()
    render_printer_end_inputs()

    if st.button("📊 Calculate Printer Usage"):
        diff_p = calculate_printer_difference(
            st.session_state.get("printer_start", {}),
            st.session_state.get("printer_end", {}),
        )
        st.session_state["printer_diff"] = diff_p
        st.success("Printer Usage Calculated ✅")
        st.json(diff_p)


# =====================================================
# Social / Archive / Report Tab
# =====================================================
def render_social_tab(db: dict) -> None:
    st.subheader("📱 Social Tasks")

    for task in db.get("tasks", {}).get("social", []):
        st.checkbox(task, key=f"social_{task}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Archive Shift", use_container_width=True):
            archive_shift(db)
            st.success("Archived Successfully ✅")

    with col2:
        report = get_shift_report_data()

        if st.button("📄 Generate PDF", use_container_width=True):
            pdf_bytes = create_downloadable_pdf(
                branch=report["branch"],
                staff_name=report["staff"],
                date_str=report["date"],
                sales=report["sales"],
                expenses=report["total_expenses"],
                exp_note=report["expense_lines"],
                diff=report["cash_diff"],
                printer_diff=report["printer_diff"],
                opay_move=report["opay_diff"],
                debit_v22=report["debit_diff"],
            )

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                file_name="shift_report.pdf",
            )

        manager_phone = get_manager_phone()
        wa_text = build_whatsapp_text()
        url = f"https://wa.me/{manager_phone}?text={urllib.parse.quote(wa_text)}"

        st.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="width:100%;background:#25D366;color:white;'
            f'padding:14px;border-radius:10px;border:none;font-weight:bold;">'
            f'📱 Send To WhatsApp'
            f'</button></a>',
            unsafe_allow_html=True,
        )


# =====================================================
# Main UI
# =====================================================
def daily_operations_ui(db: dict) -> None:
    if "user" not in st.session_state:
        return

    ensure_session_defaults()

    st.title("📊 NMS ERP - Daily Operations")

    get_selected_branch(db)
    get_selected_shift()

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📅 {date.today()}")
    with col2:
        st.info(f"👤 {st.session_state.get('user')}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING", "🔴 CLOSING", "📱 SOCIAL"])

    with tab1:
        render_opening_tab(db)

    with tab2:
        render_closing_tab(db)

    with tab3:
        render_social_tab(db)
