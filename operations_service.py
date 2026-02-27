# =====================================================
# DAILY OPERATIONS MODULE (FULL VERSION)
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
    # BRANCH & SHIFT
    # =====================================================

    if "branch" not in st.session_state:
        if db.get("branches"):
            st.session_state["branch"] = db["branches"][0]
        else:
            st.session_state["branch"] = "No Branch"

    if "shift" not in st.session_state:
        st.session_state["shift"] = "Morning"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.session_state["branch"] = st.selectbox(
            "📍 Branch",
            db["branches"],
            index=db["branches"].index(st.session_state["branch"])
        )

    with c2:
        st.session_state["shift"] = st.selectbox(
            "🕒 Shift",
            ["Morning", "Between", "Night"],
            index=["Morning", "Between", "Night"].index(
                st.session_state["shift"]
            )
        )

    with c3:
        st.info(f"📅 {date.today()}")

    with c4:
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
            v = st.number_input(
                f"{d} LE",
                min_value=0,
                step=1,
                key=f"open_{d}"
            )
            t_open += v * d

        coins = st.number_input("Coins", step=0.5, key="open_coins")
        t_open += coins

        st.success(f"Total Opening: {t_open:,.2f} LE")
        st.session_state["t_open"] = t_open

        st.divider()
        st.subheader("🖨 Printer Start Counters")

        printer_start = {}

        for printer in get_printers():

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

        st.subheader("🌇 Closing Tasks")

        for task in db["tasks"].get("closing", []):
            st.checkbox(task, key=f"close_task_{task}")

        st.divider()

        st.subheader("💰 Closing Cash")

        sys_sales = st.number_input(
            "System Sales",
            step=1.0,
            key="c_sys_sales"
        )

        insta = st.number_input("Instapay", step=1.0, key="c_insta")
        wallet = st.number_input("Wallet", step=1.0, key="c_wallet")
        visa = st.number_input("Visa", step=1.0, key="c_visa")

        t_digital = insta + wallet + visa
        t_open = st.session_state.get("t_open", 0)

        expenses = st.number_input(
            "Expenses",
            step=1.0,
            key="ex_val"
        )

        expected = t_open + sys_sales - expenses - t_digital

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

        for printer in get_printers():

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
                "sales": sys_sales,
                "cash_diff": st.session_state.get("cash_diff", 0),
                "printer_diff": st.session_state.get("printer_diff", {})
            })

            save_db(db)

            st.success("Archived Successfully ✅")

    with col2:

        wa_text = f"""
Shift Report
Branch: {branch}
Shift: {shift}
Sales: {sys_sales}
Cash Diff: {st.session_state.get("cash_diff", 0)}
"""

        url = f"https://wa.me/{get_manager_phone()}?text={urllib.parse.quote(wa_text)}"

        st.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="width:100%;background:#25D366;color:white;padding:12px;border:none;border-radius:8px;font-weight:bold;">'
            f'📱 Send To WhatsApp'
            f'</button></a>',
            unsafe_allow_html=True
        )
