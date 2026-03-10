# =====================================================
# DAILY OPERATIONS MODULE (ROLE-BASED VERSION - CLEAN)
# =====================================================

from datetime import date
import urllib.parse

import streamlit as st

from constants import (
    CASH_DENOMINATIONS,
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
from cash_service import build_cash_breakdown_from_quantities, build_cash_summary
from database import get_manager_phone, get_supabase
from pdf_generator import create_downloadable_pdf
from printer_service import calculate_printer_difference, get_printers
from report_service import (
    build_role_report_data,
    build_whatsapp_text as build_role_whatsapp_text,
)
from role_service import get_allowed_tabs, get_normalized_current_role


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
        "insta_amount": 0.0,
        "wallet_amount": 0.0,
        "visa_amount": 0.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_current_user_record(db: dict) -> dict:
    username = st.session_state.get(SESSION_USER, "")
    return db.get("users", {}).get(username, {})


def get_current_role(_: dict) -> str:
    return get_normalized_current_role()


def get_staff_display_name(db: dict) -> str:
    username = st.session_state.get(SESSION_USER, "-")
    user_record = db.get("users", {}).get(username, {})
    return user_record.get("full_name") or username


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
# Generic Render Helpers
# =====================================================
def render_task_checklist(tasks: list[str], key_prefix: str) -> None:
    for idx, task in enumerate(tasks):
        st.checkbox(task, key=f"{key_prefix}_{idx}_{task}")


def render_notes_area(label: str, key: str, placeholder: str, height: int = 140) -> None:
    st.text_area(
        label,
        key=key,
        height=height,
        placeholder=placeholder,
    )


# =====================================================
# Cash Helpers
# =====================================================
def render_cash_counter(section_prefix: str, title_suffix: str = "") -> tuple[float, dict]:
    quantities = {}

    for denomination in CASH_DENOMINATIONS:
        qty = st.number_input(
            f"{denomination} LE{title_suffix}",
            min_value=0,
            step=1,
            key=f"{section_prefix}_{denomination}",
        )
        quantities[str(denomination)] = qty

    coins_label = "Coins" if section_prefix == "open" else "Closing Coins"
    coins = st.number_input(
        coins_label,
        min_value=0.0,
        step=0.5,
        key=f"{section_prefix}_coins",
    )
    quantities["coins"] = coins

    breakdown = build_cash_breakdown_from_quantities(quantities)
    total = breakdown.get("_meta", {}).get("grand_total", 0.0)
    return total, breakdown


# =====================================================
# Other Inputs
# =====================================================
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

    for idx, printer_name in enumerate(printers.keys()):
        st.markdown(f"##### 📠 {printer_name}")

        total = st.number_input(
            f"{printer_name} ✔ Total",
            min_value=0,
            key=f"{printer_name}_start_total_{idx}",
        )

        printer_start[printer_name] = {"Total": total}
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

    for idx, printer_name in enumerate(printers.keys()):
        st.markdown(f"##### 📠 {printer_name}")

        total_end = st.number_input(
            f"{printer_name} ✔ End Total",
            min_value=0,
            key=f"{printer_name}_end_total_{idx}",
        )
        one_end = st.number_input(
            f"{printer_name} ✔ End 1 Side",
            min_value=0,
            key=f"{printer_name}_end_one_{idx}",
        )
        two_end = st.number_input(
            f"{printer_name} ✔ End 2 Side",
            min_value=0,
            key=f"{printer_name}_end_two_{idx}",
        )
        err_end = st.number_input(
            f"{printer_name} ❌ End Errors",
            min_value=0,
            key=f"{printer_name}_end_err_{idx}",
        )
        jam_end = st.number_input(
            f"{printer_name} ⚠ End Jam",
            min_value=0,
            key=f"{printer_name}_end_jam_{idx}",
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


# =====================================================
# Report / Archive Helpers
# =====================================================
def get_shift_report_data(db: dict) -> dict:
    return build_role_report_data(db, st.session_state)


def archive_shift(db: dict) -> None:
    report = get_shift_report_data(db)
    supabase = get_supabase()

    row = {
        "report_date": report["date"],
        "branch": report["branch"],
        "shift": report["shift"],
        "staff": report["staff"],
        "staff_username": report["staff_username"],
        "role": report["role"],
        "job_title": report.get("job_title", ""),
        "report_type": report.get("report_type", ""),
        "sales": float(report["sales"] or 0),
        "expenses": float(report["total_expenses"] or 0),
        "expenses_list": report.get("expenses_list", []),
        "exp_note": report.get("expense_lines", ""),
        "diff": float(report["cash_diff"] or 0),
        "t_open": float(report["t_open"] or 0),
        "t_close": float(report["t_close"] or 0),
        "cash_breakdown": report.get("opening_cash_breakdown", {}),
        "closing_cash_breakdown": report.get("closing_cash_breakdown", {}),
        "opay_open": float(report["opay_open"] or 0),
        "opay_close": float(report["opay_close"] or 0),
        "opay_diff": float(report["opay_diff"] or 0),
        "debit_open": float(report["debit_open"] or 0),
        "debit_close": float(report["debit_close"] or 0),
        "debit_diff": float(report["debit_diff"] or 0),
        "nbe_open": float(report["nbe_open"] or 0),
        "nbe_close": float(report["nbe_close"] or 0),
        "nbe_diff": float(report["nbe_diff"] or 0),
        "printer_diff": report.get("printer_diff", {}),
        "social_notes": report.get("social_notes", ""),
        "interaction_notes": report.get("interaction_notes", ""),
        "special_notes": report.get("special_notes", ""),
        "visible_sections": report.get("visible_sections", []),
    }

    supabase.table("shift_history").insert(row).execute()


# =====================================================
# Opening
# =====================================================
def render_opening_tab(db: dict) -> None:
    st.subheader("🌅 Opening Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_OPENING, []), "open_task")

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
# Closing
# =====================================================
def render_expenses_section(db: dict) -> float:
    st.divider()
    st.subheader("💸 Expenses")

    expense_categories = db.get("expense_categories", []) or ["General Expense"]

    col1, col2 = st.columns(2)

    with col1:
        selected_expense = st.selectbox(
            "Expense Type",
            expense_categories,
            key="expense_type_select",
        )

    with col2:
        expense_value = st.number_input(
            "Amount",
            min_value=0.0,
            step=1.0,
            key="expense_value_input",
        )

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

    return sum(
        float(item.get("amount", 0) or 0)
        for item in st.session_state[SESSION_SHIFT_EXPENSES]
    )


def render_closing_tab(db: dict) -> None:
    st.subheader("🌇 Closing Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_CLOSING, []), "close_task")

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

    render_expenses_section(db)

    st.divider()
    st.subheader("🧮 Cash Count")

    t_close, closing_breakdown = render_cash_counter("close", title_suffix=" ")

    cash_summary = build_cash_summary(
        opening_breakdown=st.session_state.get("opening_cash_breakdown", {}),
        closing_breakdown=closing_breakdown,
        sales=sys_sales,
        expenses=st.session_state.get(SESSION_SHIFT_EXPENSES, []),
        instapay=insta,
        wallet=wallet,
        visa=visa,
    )

    st.metric("Expected Cash", f"{cash_summary['expected_cash']:,.2f} LE")
    st.metric("Actual Cash", f"{cash_summary['closing_total']:,.2f} LE")
    st.metric("Difference", f"{cash_summary['difference']:,.2f} LE")

    st.session_state[SESSION_CLOSE_TOTAL] = t_close
    st.session_state[SESSION_CASH_DIFF] = cash_summary["difference"]
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
# Interaction / Social / Special
# =====================================================
def render_interaction_section(db: dict) -> None:
    st.subheader("🤝 Interaction Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_INTERACTION, []), "interaction_task")

    render_notes_area(
        "Interaction Notes",
        "interaction_notes",
        "Write customer interaction notes, complaint handling, follow-up status...",
    )


def render_social_section(db: dict) -> None:
    st.subheader("📱 Social Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_SOCIAL, []), "social_task")

    render_notes_area(
        "Social Notes",
        "social_notes",
        "Write social media updates, responses, stories, inbox follow-up...",
    )


def render_cleaning_section(db: dict) -> None:
    st.subheader("🧹 Cleaning Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_CLEANING, []), "cleaning_task")

    render_notes_area(
        "Cleaning Notes",
        "special_notes",
        "Write cleaning status, sanitation notes, supplies needed...",
    )


def render_design_section(db: dict) -> None:
    st.subheader("🎨 Design Tasks")
    render_task_checklist(db.get("tasks", {}).get(TASK_DESIGN, []), "design_task")

    render_notes_area(
        "Design Notes",
        "special_notes",
        "Write design jobs, pending mockups, export notes, customer approvals...",
    )


def render_role_specific_section(db: dict) -> None:
    role_value = get_normalized_current_role()

    if role_value == "cleaner":
        render_cleaning_section(db)
    elif role_value == "graphic_designer":
        render_design_section(db)
    else:
        st.subheader("📝 Special Notes")
        render_notes_area(
            "Special Notes",
            "special_notes",
            "Write role-specific notes...",
        )


# =====================================================
# Report
# =====================================================
def render_report_tab(db: dict) -> None:
    st.subheader("📦 Archive & Reporting")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Archive Shift", use_container_width=True):
            try:
                archive_shift(db)
                st.success("Archived Successfully ✅")
            except Exception as e:
                st.error(f"Archive failed: {e}")

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
                report_type=report.get("report_type", "operations"),
                visible_sections=report.get("visible_sections", []),
                job_title=report.get("job_title", ""),
                opening_tasks_completed=report.get("opening_tasks_completed", []),
                opening_tasks_pending=report.get("opening_tasks_pending", []),
                closing_tasks_completed=report.get("closing_tasks_completed", []),
                closing_tasks_pending=report.get("closing_tasks_pending", []),
                interaction_tasks_completed=report.get("interaction_tasks_completed", []),
                interaction_tasks_pending=report.get("interaction_tasks_pending", []),
                social_tasks_completed=report.get("social_tasks_completed", []),
                social_tasks_pending=report.get("social_tasks_pending", []),
                cleaning_tasks_completed=report.get("cleaning_tasks_completed", []),
                cleaning_tasks_pending=report.get("cleaning_tasks_pending", []),
                design_tasks_completed=report.get("design_tasks_completed", []),
                design_tasks_pending=report.get("design_tasks_pending", []),
            )

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                file_name="shift_report.pdf",
            )

        manager_phone = get_manager_phone()
        wa_text = build_role_whatsapp_text(db, st.session_state)

        with st.expander("🔍 WhatsApp Preview", expanded=False):
            st.code(wa_text)

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
        st.info(f"👤 {get_staff_display_name(db)} | {get_current_role(db)}")

    st.divider()

    allowed_tabs = get_allowed_tabs()

    tabs = []
    renderers = []

    if "opening" in allowed_tabs:
        tabs.append("🟢 OPENING")
        renderers.append(lambda: render_opening_tab(db))

    if "closing" in allowed_tabs:
        tabs.append("🔴 CLOSING")
        renderers.append(lambda: render_closing_tab(db))

    if "interaction" in allowed_tabs:
        tabs.append("🤝 INTERACTION")
        renderers.append(lambda: render_interaction_section(db))

    if "social" in allowed_tabs:
        tabs.append("📱 SOCIAL")
        renderers.append(lambda: render_social_section(db))

    if "cleaning" in allowed_tabs or "design" in allowed_tabs:
        tabs.append("🧩 ROLE TASKS")
        renderers.append(lambda: render_role_specific_section(db))

    if "report" in allowed_tabs:
        tabs.append("📦 REPORT")
        renderers.append(lambda: render_report_tab(db))

    if not tabs:
        st.info("No operational modules are available for this role.")
        return

    tab_objects = st.tabs(tabs)

    for tab_obj, renderer in zip(tab_objects, renderers):
        with tab_obj:
            renderer()
