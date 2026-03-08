# =====================================================
# DAILY OPERATIONS MODULE (ENHANCED FINAL VERSION)
# =====================================================

from datetime import date
import urllib.parse

import streamlit as st

from constants import (
    CASH_DENOMINATIONS,
    ROLE_ACCOUNTS,
    ROLE_CLEANER,
    ROLE_GRAPHIC_DESIGNER,
    ROLE_HR,
    ROLE_MANAGER,
    ROLE_TASK_ACCESS,
    SESSION_BRANCH,
    SESSION_CASH_DIFF,
    SESSION_CLOSE_TOTAL,
    SESSION_DEBIT_CLOSE,
    SESSION_DEBIT_OPEN,
    SESSION_LOGGED_IN,
    SESSION_NBE_CLOSE,
    SESSION_NBE_OPEN,
    SESSION_OPEN_TOTAL,
    SESSION_OPAY_CLOSE,
    SESSION_OPAY_OPEN,
    SESSION_PRINTER_DIFF,
    SESSION_PRINTER_END,
    SESSION_PRINTER_START,
    SESSION_SHIFT,
    SESSION_SHIFT_EXPENSES,
    SESSION_SYSTEM_SALES,
    SESSION_USER,
    SHIFT_MORNING,
    SHIFT_OPTIONS,
    TASK_CLEANING,
    TASK_CLOSING,
    TASK_DESIGN,
    TASK_INTERACTION,
    TASK_OPENING,
    TASK_SOCIAL,
)
from database import get_manager_phone, save_db
from pdf_generator import create_downloadable_pdf
from printer_service import calculate_printer_difference, get_printers


# =====================================================
# Session Helpers
# =====================================================
def ensure_session_defaults() -> None:
    defaults = {
        SESSION_BRANCH: "",
        SESSION_SHIFT: SHIFT_MORNING,
        SESSION_OPEN_TOTAL: 0.0,
        SESSION_CLOSE_TOTAL: 0.0,
        SESSION_CASH_DIFF: 0.0,
        SESSION_SYSTEM_SALES: 0.0,
        SESSION_SHIFT_EXPENSES: [],
        SESSION_PRINTER_START: {},
        SESSION_PRINTER_END: {},
        SESSION_PRINTER_DIFF: {},
        SESSION_OPAY_OPEN: 0.0,
        SESSION_OPAY_CLOSE: 0.0,
        SESSION_DEBIT_OPEN: 0.0,
        SESSION_DEBIT_CLOSE: 0.0,
        SESSION_NBE_OPEN: 0.0,
        SESSION_NBE_CLOSE: 0.0,
        "opening_cash_breakdown": {},
        "closing_cash_breakdown": {},
        "social_notes": "",
        "interaction_notes": "",
        "special_notes": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_current_user_record(db: dict) -> dict:
    username = st.session_state.get(SESSION_USER, "")
    return db.get("users", {}).get(username, {})


def get_current_role(db: dict) -> str:
    return get_current_user_record(db).get("role", "employee")


def get_allowed_task_categories(db: dict) -> list:
    current_role = get_current_role(db)
    return ROLE_TASK_ACCESS.get(current_role, [TASK_OPENING, TASK_CLOSING, TASK_SOCIAL, TASK_INTERACTION])


def get_selected_branch(db: dict) -> str:
    branches = db.get("branches", [])
    if not branches:
        branches = ["No Branch"]

    current_branch = st.session_state.get(SESSION_BRANCH, branches[0])
    if current_branch not in branches:
        current_branch = branches[0]

    selected = st.selectbox(
        "📍 Branch",
        branches,
        index=branches.index(current_branch),
    )
    st.session_state[SESSION_BRANCH] = selected
    return selected


def get_selected_shift() -> str:
    current_shift = st.session_state.get(SESSION_SHIFT, SHIFT_MORNING)
    if current_shift not in SHIFT_OPTIONS:
        current_shift = SHIFT_MORNING

    selected = st.selectbox(
        "🕒 Shift",
        SHIFT_OPTIONS,
        index=SHIFT_OPTIONS.index(current_shift),
    )
    st.session_state[SESSION_SHIFT] = selected
    return selected


# =====================================================
# Generic Helpers
# =====================================================
def render_cash_counter(section_prefix: str, title_suffix: str = "") -> tuple[float, dict]:
    total = 0.0
    breakdown = {}

    for denomination in CASH_DENOMINATIONS:
        qty = st.number_input(
            f"{denomination} LE{title_suffix}",
            min_value=0,
            step=1,
            key=f"{section_prefix}_{denomination}",
        )
        total_value = qty * denomination
        breakdown[str(denomination)] = {
            "qty": qty,
            "total": total_value,
        }
        total += total_value

    coins_label = "Coins" if section_prefix == "open" else "Closing Coins"
    coins = st.number_input(
        coins_label,
        min_value=0.0,
        step=0.5,
        key=f"{section_prefix}_coins",
    )

    breakdown["coins"] = {
        "qty": coins,
        "total": coins,
    }
    total += coins

    return total, breakdown


def format_cash_breakdown_text(breakdown: dict) -> str:
    if not breakdown:
        return "No Cash Breakdown"

    ordered_keys = [str(value) for value in CASH_DENOMINATIONS] + ["coins"]
    lines = []

    for key in ordered_keys:
        if key not in breakdown:
            continue

        label = "Coins" if key == "coins" else f"{key} LE"
        qty = breakdown[key].get("qty", 0)
        total = breakdown[key].get("total", 0)
        lines.append(f"• {label}: {qty} = {float(total):,.2f}")

    return "\n".join(lines)


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
        st.session_state[SESSION_PRINTER_START] = {}
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

    st.session_state[SESSION_PRINTER_START] = printer_start


def render_printer_end_inputs() -> None:
    st.subheader("🖨 Printer End Counters")

    printers = get_printers() or {}
    printer_end = {}

    if not printers:
        st.info("No printers configured.")
        st.session_state[SESSION_PRINTER_END] = {}
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

    st.session_state[SESSION_PRINTER_END] = printer_end


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


def get_staff_display_name(db: dict) -> str:
    username = st.session_state.get(SESSION_USER, "-")
    user_record = db.get("users", {}).get(username, {})
    return user_record.get("full_name") or username


def get_staff_role(db: dict) -> str:
    user_record = get_current_user_record(db)
    return user_record.get("role", "employee")


def get_shift_report_data(db: dict) -> dict:
    sys_sales = float(st.session_state.get(SESSION_SYSTEM_SALES, 0.0) or 0.0)

    opay_open = float(st.session_state.get(SESSION_OPAY_OPEN, 0.0) or 0.0)
    opay_close = float(st.session_state.get(SESSION_OPAY_CLOSE, 0.0) or 0.0)

    debit_open = float(st.session_state.get(SESSION_DEBIT_OPEN, 0.0) or 0.0)
    debit_close = float(st.session_state.get(SESSION_DEBIT_CLOSE, 0.0) or 0.0)

    nbe_open = float(st.session_state.get(SESSION_NBE_OPEN, 0.0) or 0.0)
    nbe_close = float(st.session_state.get(SESSION_NBE_CLOSE, 0.0) or 0.0)

    shift_expenses = st.session_state.get(SESSION_SHIFT_EXPENSES, [])
    total_expenses = calculate_total_expenses(shift_expenses)

    opay_diff = opay_close - opay_open
    debit_diff = debit_close - debit_open
    nbe_diff = nbe_close - nbe_open

    cash_diff = float(st.session_state.get(SESSION_CASH_DIFF, 0.0) or 0.0)
    printer_diff = st.session_state.get(SESSION_PRINTER_DIFF, {})

    opening_cash_breakdown = st.session_state.get("opening_cash_breakdown", {})
    closing_cash_breakdown = st.session_state.get("closing_cash_breakdown", {})

    return {
        "date": str(date.today()),
        "branch": st.session_state.get(SESSION_BRANCH, "-"),
        "shift": st.session_state.get(SESSION_SHIFT, "-"),
        "staff": get_staff_display_name(db),
        "staff_username": st.session_state.get(SESSION_USER, "-"),
        "role": get_staff_role(db),
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
        "t_open": float(st.session_state.get(SESSION_OPEN_TOTAL, 0.0) or 0.0),
        "t_close": float(st.session_state.get(SESSION_CLOSE_TOTAL, 0.0) or 0.0),
        "opening_cash_breakdown": opening_cash_breakdown,
        "closing_cash_breakdown": closing_cash_breakdown,
        "opening_cash_text": format_cash_breakdown_text(opening_cash_breakdown),
        "closing_cash_text": format_cash_breakdown_text(closing_cash_breakdown),
        "social_notes": st.session_state.get("social_notes", "").strip(),
        "interaction_notes": st.session_state.get("interaction_notes", "").strip(),
        "special_notes": st.session_state.get("special_notes", "").strip(),
    }


def archive_shift(db: dict) -> None:
    report = get_shift_report_data(db)

    db.setdefault("history", [])
    db["history"].append(
        {
            "date": report["date"],
            "branch": report["branch"],
            "shift": report["shift"],
            "staff": report["staff"],
            "staff_username": report["staff_username"],
            "role": report["role"],
            "sales": report["sales"],
            "expenses": report["total_expenses"],
            "expenses_list": report["expenses_list"],
            "exp_note": report["expense_lines"],
            "diff": report["cash_diff"],
            "t_open": report["t_open"],
            "t_close": report["t_close"],
            "cash_breakdown": report["opening_cash_breakdown"],
            "closing_cash_breakdown": report["closing_cash_breakdown"],
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
            "social_notes": report["social_notes"],
            "interaction_notes": report["interaction_notes"],
            "special_notes": report["special_notes"],
        }
    )

    save_db(db)


def build_whatsapp_text(db: dict) -> str:
    report = get_shift_report_data(db)

    social_notes = report["social_notes"] or "No Social Notes"
    interaction_notes = report["interaction_notes"] or "No Interaction Notes"
    special_notes = report["special_notes"] or "No Special Notes"

    wa_text = f"""
■ NMS FULL SHIFT REPORT
■■■■■■■■■■■■■■■■■■■

📅 Date: {report["date"]}
🏢 Branch: {report["branch"]}
🕒 Shift: {report["shift"]}
👤 Staff: {report["staff"]}
🧩 Role: {report["role"]}

■■■■■■■■■■■■■■■■■■■
💰 SALES
Total System Sales: {report["sales"]:,.2f}

■■■■■■■■■■■■■■■■■■■
💵 OPENING CASH BREAKDOWN
{report["opening_cash_text"]}

Total Opening Cash: {report["t_open"]:,.2f}

■■■■■■■■■■■■■■■■■■■
💵 CLOSING CASH BREAKDOWN
{report["closing_cash_text"]}

Total Closing Cash: {report["t_close"]:,.2f}

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
🤝 INTERACTION NOTES
{interaction_notes}

■■■■■■■■■■■■■■■■■■■
📱 SOCIAL NOTES
{social_notes}

■■■■■■■■■■■■■■■■■■■
📝 SPECIAL NOTES
{special_notes}

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

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_OPENING, [])):
    st.checkbox(task, key=f"open_task_{idx}_{task}")

    st.divider()

    st.subheader("💰 Opening Cash")
    t_open, opening_breakdown = render_cash_counter("open")
    st.success(f"Total Opening Cash: {t_open:,.2f} LE")
    st.session_state[SESSION_OPEN_TOTAL] = t_open
    st.session_state["opening_cash_breakdown"] = opening_breakdown

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
        st.session_state[SESSION_SHIFT_EXPENSES].append(
            {
                "type": selected_expense,
                "amount": expense_value,
            }
        )
        st.rerun()

    if st.session_state[SESSION_SHIFT_EXPENSES]:
        st.markdown("#### Current Shift Expenses")
        for index, item in enumerate(st.session_state[SESSION_SHIFT_EXPENSES]):
            c1, c2 = st.columns([6, 1])
            with c1:
                st.write(
                    f"• {item.get('type', 'Unknown')} — "
                    f"{float(item.get('amount', 0) or 0):,.2f} LE"
                )
            with c2:
                if st.button("✖️", key=f"remove_exp_{index}"):
                    st.session_state[SESSION_SHIFT_EXPENSES].pop(index)
                    st.rerun()

        if st.button("🧹 Clear All Expenses"):
            st.session_state[SESSION_SHIFT_EXPENSES] = []
            st.rerun()

    total_expenses = calculate_total_expenses(st.session_state[SESSION_SHIFT_EXPENSES])
    st.warning(f"Total Expenses: {total_expenses:,.2f} LE")

    return total_expenses


def render_closing_tab(db: dict) -> None:
    st.subheader("🌇 Closing Tasks")

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_CLOSING, [])):
    st.checkbox(task, key=f"close_task_{idx}_{task}")

    st.divider()
    st.subheader("💰 Closing Section")

    sys_sales = st.number_input(
        "System Sales",
        min_value=0.0,
        step=1.0,
        key=SESSION_SYSTEM_SALES,
    )
    insta = st.number_input("Instapay", min_value=0.0, step=1.0, key="insta_amount")
    wallet = st.number_input("Wallet", min_value=0.0, step=1.0, key="wallet_amount")
    visa = st.number_input("Visa", min_value=0.0, step=1.0, key="visa_amount")

    st.divider()
    st.subheader("💳 Digital Closing")
    render_digital_inputs("close")

    total_expenses = render_expenses_section(db)

    t_digital = insta + wallet + visa
    expected = float(st.session_state.get(SESSION_OPEN_TOTAL, 0.0) or 0.0) + sys_sales - total_expenses - t_digital

    st.metric("Expected Cash", f"{expected:,.2f} LE")

    st.divider()
    st.subheader("🧮 Cash Count")

    t_close, closing_breakdown = render_cash_counter("close", title_suffix=" ")
    diff = t_close - expected

    st.metric("Actual Cash", f"{t_close:,.2f} LE")
    st.metric("Difference", f"{diff:,.2f} LE")

    st.session_state[SESSION_CLOSE_TOTAL] = t_close
    st.session_state[SESSION_CASH_DIFF] = diff
    st.session_state["closing_cash_breakdown"] = closing_breakdown

    st.divider()
    render_printer_end_inputs()

    if st.button("📊 Calculate Printer Usage"):
        diff_p = calculate_printer_difference(
            st.session_state.get(SESSION_PRINTER_START, {}),
            st.session_state.get(SESSION_PRINTER_END, {}),
        )
        st.session_state[SESSION_PRINTER_DIFF] = diff_p
        st.success("Printer Usage Calculated ✅")
        st.json(diff_p)


# =====================================================
# Interaction / Social / Special Tabs
# =====================================================
def render_interaction_section(db: dict) -> None:
    st.subheader("🤝 Interaction Tasks")

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_INTERACTION, [])):
        st.checkbox(task, key=f"interaction_task_{idx}_{task}")

    st.text_area(
        "Interaction Notes",
        key="interaction_notes",
        height=140,
        placeholder="Write customer interaction notes, complaint handling, follow-up status...",
    )


def render_social_section(db: dict) -> None:
    st.subheader("📱 Social Tasks")

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_SOCIAL, [])):
        st.checkbox(task, key=f"social_{idx}_{task}")

    st.text_area(
        "Social Notes",
        key="social_notes",
        height=140,
        placeholder="Write social media updates, responses, stories, inbox follow-up...",
    )


def render_cleaning_section(db: dict) -> None:
    st.subheader("🧹 Cleaning Tasks")

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_CLEANING, [])):
        st.checkbox(task, key=f"cleaning_{idx}_{task}")

    st.text_area(
        "Cleaning Notes",
        key="special_notes",
        height=140,
        placeholder="Write cleaning status, sanitation notes, supplies needed...",
    )


def render_design_section(db: dict) -> None:
    st.subheader("🎨 Design Tasks")

    for idx, task in enumerate(db.get("tasks", {}).get(TASK_DESIGN, [])):
        st.checkbox(task, key=f"design_{idx}_{task}")

    st.text_area(
        "Design Notes",
        key="special_notes",
        height=140,
        placeholder="Write design jobs, pending mockups, export notes, customer approvals...",
    )


def render_role_specific_section(db: dict) -> None:
    role_value = get_current_role(db)

    if role_value == ROLE_CLEANER:
        render_cleaning_section(db)
    elif role_value == ROLE_GRAPHIC_DESIGNER:
        render_design_section(db)
    elif role_value in [ROLE_MANAGER, ROLE_ACCOUNTS, ROLE_HR]:
        st.subheader("📝 Role Notes")
        st.text_area(
            "Special Notes",
            key="special_notes",
            height=140,
            placeholder="Write role-specific notes, approvals, pending items, follow-up remarks...",
        )
    else:
        st.subheader("📝 Special Notes")
        st.text_area(
            "Special Notes",
            key="special_notes",
            height=140,
            placeholder="Write any additional notes for this shift...",
        )


# =====================================================
# Report Tab
# =====================================================
def render_report_tab(db: dict) -> None:
    st.subheader("📦 Archive & Reporting")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Archive Shift", use_container_width=True):
            archive_shift(db)
            st.success("Archived Successfully ✅")

    with col2:
        report = get_shift_report_data(db)

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
                shift=report["shift"],
                staff_role=report["role"],
                opening_cash=report["t_open"],
                closing_cash=report["t_close"],
                opening_cash_text=report["opening_cash_text"],
                closing_cash_text=report["closing_cash_text"],
                nbe_move=report["nbe_diff"],
                social_notes=report["social_notes"],
                interaction_notes=report["interaction_notes"],
                special_notes=report["special_notes"],
                expenses_list=report["expenses_list"],
            )

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                file_name="shift_report.pdf",
            )

        manager_phone = get_manager_phone()
        wa_text = build_whatsapp_text(db)
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
    if not st.session_state.get(SESSION_LOGGED_IN) or not st.session_state.get(SESSION_USER):
        return

    ensure_session_defaults()

    st.title("📊 NMS ERP - Daily Operations")

    get_selected_branch(db)
    get_selected_shift()

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📅 {date.today()}")
    with col2:
        st.info(f"👤 {get_staff_display_name(db)} | {get_staff_role(db)}")

    st.divider()

    allowed_categories = get_allowed_task_categories(db)

    tabs = []
    renderers = []

    if TASK_OPENING in allowed_categories:
        tabs.append("🟢 OPENING")
        renderers.append(lambda: render_opening_tab(db))

    if TASK_CLOSING in allowed_categories:
        tabs.append("🔴 CLOSING")
        renderers.append(lambda: render_closing_tab(db))

    if TASK_INTERACTION in allowed_categories:
        tabs.append("🤝 INTERACTION")
        renderers.append(lambda: render_interaction_section(db))

    if TASK_SOCIAL in allowed_categories:
        tabs.append("📱 SOCIAL")
        renderers.append(lambda: render_social_section(db))

    if TASK_CLEANING in allowed_categories or TASK_DESIGN in allowed_categories:
        tabs.append("🧩 ROLE TASKS")
        renderers.append(lambda: render_role_specific_section(db))

    tabs.append("📦 REPORT")
    renderers.append(lambda: render_report_tab(db))

    tab_objects = st.tabs(tabs)

    for tab_obj, renderer in zip(tab_objects, renderers):
        with tab_obj:
            renderer()
