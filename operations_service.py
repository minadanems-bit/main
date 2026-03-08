# operations_service.py
import streamlit as st
from datetime import date
import urllib.parse
from database_service import load_db, save_db, get_manager_phone
from printer_service import get_printers, calculate_printer_difference
from pdf_generator import create_downloadable_pdf

def daily_operations_ui(db=None):
    if db is None:
        db = load_db()

    if "user" not in st.session_state:
        return

    st.title("📊 NMS ERP - Daily Operations")

    branches = db.get("branches", []) or ["No Branch"]
    st.session_state["branch"] = st.selectbox("📍 Branch", branches, index=0)
    shifts = ["Morning","Between","Night"]
    st.session_state["shift"] = st.selectbox("🕒 Shift", shifts, index=0)

    col1, col2 = st.columns(2)
    with col1: st.info(f"📅 {date.today()}")
    with col2: st.info(f"👤 {st.session_state.get('user')}")

    tab1, tab2, tab3 = st.tabs(["🟢 OPENING","🔴 CLOSING","📱 SOCIAL"])

    # --- OPENING
    with tab1:
        st.subheader("🌅 Opening Tasks")
        for t in db["tasks"].get("opening", []):
            st.checkbox(t, key=f"open_task_{t}")
        st.divider()
        st.subheader("💰 Opening Cash")
        t_open = 0.0
        for d in [200,100,50,20,10,5]:
            v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"open_{d}")
            t_open += v * d
        coins = st.number_input("Coins", step=0.5, key="open_coins")
        t_open += coins
        # digital opens
        for k in ("opay_open","debit_open","nbe_open"):
            if k not in st.session_state: st.session_state[k]=0.0
        st.session_state["opay_open"] = st.number_input("💳 Opay Opening", min_value=0.0, step=1.0, value=float(st.session_state["opay_open"]))
        st.session_state["debit_open"] = st.number_input("💳 Debit Opening", min_value=0.0, step=1.0, value=float(st.session_state["debit_open"]))
        st.session_state["nbe_open"] = st.number_input("🏦 NBE Wallet Opening", min_value=0.0, step=1.0, value=float(st.session_state["nbe_open"]))
        st.success(f"Total Opening Cash: {t_open:,.2f} LE")
        st.session_state["t_open"] = t_open

        st.divider()
        st.subheader("🖨 Printer Start Counters")
        printer_start = {}
        printers = get_printers() or {}
        for pr in printers.keys():
            st.markdown(f"##### 📠 {pr}")
            total = st.number_input(f"{pr} ✔ Total", min_value=0, key=f"{pr}_start_total")
            one = st.number_input(f"{pr} ✔ 1 Side", min_value=0, key=f"{pr}_start_one")
            two = st.number_input(f"{pr} ✔ 2 Side", min_value=0, key=f"{pr}_start_two")
            err = st.number_input(f"{pr} ❌ Errors", min_value=0, key=f"{pr}_start_err")
            jam = st.number_input(f"{pr} ⚠ Jam", min_value=0, key=f"{pr}_start_jam")
            printer_start[pr] = {"Total": total, "One Side": one, "Two Side": two, "Errors": err, "Jam": jam}
            st.divider()
        st.session_state["printer_start"] = printer_start

    # --- CLOSING
    with tab2:
        st.subheader("🌇 Closing Tasks")
        for t in db["tasks"].get("closing", []):
            st.checkbox(t, key=f"close_task_{t}")
        st.divider()
        st.subheader("💰 Closing Cash")
        sys_sales = st.number_input("System Sales", step=1.0, key="c_sys_sales")
        insta = st.number_input("Instapay", step=1.0, key="c_insta")
        wallet = st.number_input("Wallet", step=1.0, key="c_wallet")
        visa = st.number_input("Visa", step=1.0, key="c_visa")

        for k in ("opay_close","debit_close","nbe_close"):
            if k not in st.session_state: st.session_state[k]=0.0
        st.session_state["opay_close"] = st.number_input("💳 Opay Closing", min_value=0.0, step=1.0, value=float(st.session_state["opay_close"]))
        st.session_state["debit_close"] = st.number_input("💳 Debit Closing", min_value=0.0, step=1.0, value=float(st.session_state["debit_close"]))
        st.session_state["nbe_close"] = st.number_input("🏦 NBE Wallet Closing", min_value=0.0, step=1.0, value=float(st.session_state["nbe_close"]))

        st.divider()
        st.subheader("💸 Expenses")
        expense_categories = db.get("expense_categories", []) or []
        if "shift_expenses" not in st.session_state:
            st.session_state["shift_expenses"] = []
        c1, c2 = st.columns(2)
        with c1:
            sel_exp = st.selectbox("Expense Type", expense_categories) if expense_categories else st.text_input("Expense Type (no categories)")
        with c2:
            exp_val = st.number_input("Amount", min_value=0.0, step=1.0)
        if st.button("➕ Add Expense"):
            st.session_state["shift_expenses"].append({"type": sel_exp, "amount": exp_val})
        total_exp = sum(e["amount"] for e in st.session_state["shift_expenses"])
        st.warning(f"Total Expenses: {total_exp:,.2f} LE")

        # calculate expected cash
        t_digital = insta + wallet + visa
        expected = st.session_state.get("t_open",0) + sys_sales - total_exp - t_digital
        st.metric("Expected Cash", f"{expected:,.2f}")

        st.divider()
        st.subheader("🧮 Cash Count")
        t_close = 0
        for d in [200,100,50,20,10,5]:
            v = st.number_input(f"{d} LE", min_value=0, step=1, key=f"close_{d}")
            t_close += v * d
        coins = st.number_input("Closing Coins", step=0.5, key="close_coins")
        t_close += coins
        diff = t_close - expected
        st.metric("Difference", f"{diff:,.2f}")
        st.session_state["cash_diff"] = diff
        st.session_state["t_close"] = t_close

        st.divider()
        st.subheader("🖨 Printer End Counters")
        printer_end = {}
        printers = get_printers() or {}
        for pr in printers.keys():
            st.markdown(f"##### 📠 {pr}")
            total_end = st.number_input(f"{pr} ✔ End Total", min_value=0, key=f"{pr}_end_total")
            one_end = st.number_input(f"{pr} ✔ End 1 Side", min_value=0, key=f"{pr}_end_one")
            two_end = st.number_input(f"{pr} ✔ End 2 Side", min_value=0, key=f"{pr}_end_two")
            err_end = st.number_input(f"{pr} ❌ End Errors", min_value=0, key=f"{pr}_end_err")
            jam_end = st.number_input(f"{pr} ⚠ End Jam", min_value=0, key=f"{pr}_end_jam")
            printer_end[pr] = {"Total": total_end, "One Side": one_end, "Two Side": two_end, "Errors": err_end, "Jam": jam_end}
            st.divider()
        st.session_state["printer_end"] = printer_end

        if st.button("📊 Calculate Printer Usage"):
            start = st.session_state.get("printer_start", {})
            end = st.session_state.get("printer_end", {})
            d = calculate_printer_difference(start, end)
            st.session_state["printer_diff"] = d
            st.success("Printer usage calculated")
            st.json(d)

    # --- SOCIAL / ARCHIVE / REPORT
    with tab3:
        st.subheader("📱 Social Tasks")
        for t in db["tasks"].get("social", []):
            st.checkbox(t, key=f"social_{t}")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Archive Shift", use_container_width=True):
                db.setdefault("history", []).append({
                    "date": str(date.today()),
                    "branch": st.session_state.get("branch"),
                    "shift": st.session_state.get("shift"),
                    "staff": st.session_state.get("user"),
                    "sales": st.session_state.get("c_sys_sales",0),
                    "expenses": st.session_state.get("shift_expenses", []),
                    "opay_open": st.session_state.get("opay_open",0),
                    "opay_close": st.session_state.get("opay_close",0),
                    "debit_open": st.session_state.get("debit_open",0),
                    "debit_close": st.session_state.get("debit_close",0),
                    "nbe_open": st.session_state.get("nbe_open",0),
                    "nbe_close": st.session_state.get("nbe_close",0),
                    "cash_diff": st.session_state.get("cash_diff",0)
                })
                save_db(db)
                st.success("Archived Successfully ✅")
        # report buttons
        with col2:
            branch = st.session_state.get("branch")
            user = st.session_state.get("user")
            shift = st.session_state.get("shift")
            sys_sales = st.session_state.get("c_sys_sales", 0.0)
            shift_expenses = st.session_state.get("shift_expenses", [])
            total_expenses = sum(e.get("amount",0) for e in shift_expenses)
            opay_diff = st.session_state.get("opay_close",0)-st.session_state.get("opay_open",0)
            debit_diff = st.session_state.get("debit_close",0)-st.session_state.get("debit_open",0)
            nbe_diff = st.session_state.get("nbe_close",0)-st.session_state.get("nbe_open",0)
            cash_diff = st.session_state.get("cash_diff",0)
            printer_diff = st.session_state.get("printer_diff", {})

            # build whatsapp text
            expense_lines = "\n".join(f"• {e['type']} : {e['amount']:,.2f}" for e in shift_expenses) or "No expenses"
            printer_lines = "\n\n".join(
                f"📠 {n}\nUsed: {v.get('used',0)} | Jam: {v.get('jam',0)} | 1s:{v.get('1s',0)} | 2s:{v.get('2s',0)}"
                for n,v in (printer_diff or {}).items()
            ) or "No printer data"

            wa_text = f"""📊 NMS FULL SHIFT REPORT
Date: {date.today()}
Branch: {branch}
Shift: {shift}
Staff: {user}

SALES: {sys_sales:,.2f}

DIGITAL:
OPAY: {st.session_state.get('opay_open',0):,.2f} ➜ {st.session_state.get('opay_close',0):,.2f} (Δ {opay_diff:,.2f})
DEBIT: {st.session_state.get('debit_open',0):,.2f} ➜ {st.session_state.get('debit_close',0):,.2f} (Δ {debit_diff:,.2f})
NBE: {st.session_state.get('nbe_open',0):,.2f} ➜ {st.session_state.get('nbe_close',0):,.2f} (Δ {nbe_diff:,.2f})

EXPENSES: {total_expenses:,.2f}
{expense_lines}

PRINTERS:
{printer_lines}

CASH DIFF: {cash_diff:,.2f}
"""

            wa_text = wa_text[:3500]
            manager = get_manager_phone()
            if st.button("📄 Generate PDF", use_container_width=True):
                pdf_bytes = create_downloadable_pdf(
                    branch=branch, staff_name=user, date_str=str(date.today()),
                    sales=sys_sales, expenses=total_expenses, exp_note=expense_lines,
                    diff=cash_diff, printer_diff=printer_diff, opay_move=opay_diff, debit_v22=debit_diff
                )
                st.download_button("📥 Download PDF", pdf_bytes, file_name=f"shift_{date.today()}.pdf")
            st.markdown(f'<a href="https://wa.me/{manager}?text={urllib.parse.quote(wa_text)}" target="_blank"><button style="width:100%;background:#25D366;color:white;padding:12px;border-radius:8px;border:none;font-weight:bold;">📱 Send To WhatsApp</button></a>', unsafe_allow_html=True)
