# =====================================================
# UI HELPERS
# Dashboard widgets + role cards + attendance clocks
# =====================================================

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from constants import (
    HR_RECORD_KEYS,
    ROLE_ADMIN,
    ROLE_CLEANER,
    ROLE_EMPLOYEE,
    ROLE_MANAGER,
)


# =====================================================
# Generic counters
# =====================================================
def get_user_warning_count(user_info: dict) -> int:
    return len(user_info.get("warnings", []))


def get_user_records_count(user_info: dict) -> int:
    total = 0

    for category in HR_RECORD_KEYS:
        total += len(user_info.get(category, []))

    total += len(user_info.get("advances", []))
    total += len(user_info.get("late_penalties", []))
    total += len(user_info.get("absence_penalties", []))
    return total


def get_branch_count(db: dict) -> int:
    return len(db.get("branches", []))


def get_employee_count(db: dict) -> int:
    return len(db.get("users", {}))


def get_history_count(db: dict) -> int:
    return len(db.get("history", []))


def get_tasks_count(db: dict) -> int:
    total = 0
    tasks = db.get("tasks", {})
    for items in tasks.values():
        total += len(items or [])
    return total


def get_printer_count(db: dict) -> int:
    return len(db.get("printers", {}))


# =====================================================
# Salary helper
# =====================================================
def calculate_salary_breakdown(user_info: dict) -> dict:
    salary_basic = float(user_info.get("salary_basic", 0) or 0)
    transport_allowance = float(user_info.get("transport_allowance", 0) or 0)
    communication_allowance = float(user_info.get("communication_allowance", 0) or 0)
    other_allowance = float(user_info.get("other_allowance", 0) or 0)

    total_fixed = (
        salary_basic
        + transport_allowance
        + communication_allowance
        + other_allowance
    )

    total_bonus = sum(float(item.get("amount", 0) or 0) for item in user_info.get("bonus", []))
    total_overtime = sum(float(item.get("amount", 0) or 0) for item in user_info.get("overtime", []))
    total_deductions = sum(float(item.get("amount", 0) or 0) for item in user_info.get("deductions", []))
    total_advances = sum(float(item.get("amount", 0) or 0) for item in user_info.get("advances", []))
    total_late_penalties = sum(float(item.get("amount", 0) or 0) for item in user_info.get("late_penalties", []))
    total_absence_penalties = sum(float(item.get("amount", 0) or 0) for item in user_info.get("absence_penalties", []))

    gross_salary = total_fixed + total_bonus + total_overtime
    total_withheld = total_deductions + total_advances + total_late_penalties + total_absence_penalties
    net_salary = gross_salary - total_withheld

    return {
        "salary_basic": salary_basic,
        "transport_allowance": transport_allowance,
        "communication_allowance": communication_allowance,
        "other_allowance": other_allowance,
        "total_fixed": total_fixed,
        "total_bonus": total_bonus,
        "total_overtime": total_overtime,
        "total_deductions": total_deductions,
        "total_advances": total_advances,
        "total_late_penalties": total_late_penalties,
        "total_absence_penalties": total_absence_penalties,
        "gross_salary": gross_salary,
        "total_withheld": total_withheld,
        "net_salary": net_salary,
    }


# =====================================================
# Clock widgets
# =====================================================
def render_attendance_clock_widget(height: int = 300) -> None:
    components.html(
        """
        <div style="
            margin: 8px 0 18px 0;
            padding: 22px;
            border-radius: 22px;
            background: linear-gradient(135deg, #020617, #0f172a, #1e293b);
            color: white;
            box-shadow: 0 14px 32px rgba(0,0,0,0.22);
            border: 1px solid rgba(255,255,255,0.08);
        ">
            <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:28px;">
                <div style="min-width:260px;">
                    <div style="font-size:14px; opacity:0.8; margin-bottom:10px; letter-spacing:0.5px;">
                        ⏰ Current Attendance Time
                    </div>

                    <div id="digital-clock-login"
                         style="font-size:42px; font-weight:800; letter-spacing:2px; line-height:1;">
                        --:--:--
                    </div>

                    <div id="digital-ampm-login"
                         style="font-size:18px; font-weight:700; color:#38bdf8; margin-top:8px;">
                        --
                    </div>

                    <div id="digital-date-login"
                         style="font-size:14px; opacity:0.82; margin-top:10px;">
                        --
                    </div>
                </div>

                <div style="display:flex; justify-content:center; align-items:center; min-width:190px;">
                    <div id="analog-clock-login"
                         style="
                            position:relative;
                            width:165px;
                            height:165px;
                            border:6px solid rgba(255,255,255,0.88);
                            border-radius:50%;
                            background: radial-gradient(circle, #1e293b 55%, #0f172a 100%);
                            box-shadow: inset 0 0 20px rgba(255,255,255,0.06);
                         ">

                        <div style="position:absolute; top:50%; left:50%; width:12px; height:12px; background:#ffffff; border-radius:50%; transform:translate(-50%,-50%); z-index:10;"></div>

                        <div style="position:absolute; top:12px; left:76px; color:white; font-size:13px;">12</div>
                        <div style="position:absolute; top:72px; right:12px; color:white; font-size:13px;">3</div>
                        <div style="position:absolute; bottom:10px; left:78px; color:white; font-size:13px;">6</div>
                        <div style="position:absolute; top:72px; left:12px; color:white; font-size:13px;">9</div>

                        <div id="hour-hand-login"
                             style="position:absolute; width:5px; height:46px; background:#ffffff; top:36px; left:77px; transform-origin:bottom center; border-radius:4px;"></div>

                        <div id="minute-hand-login"
                             style="position:absolute; width:3px; height:62px; background:#cbd5e1; top:20px; left:78px; transform-origin:bottom center; border-radius:4px;"></div>

                        <div id="second-hand-login"
                             style="position:absolute; width:2px; height:70px; background:#38bdf8; top:12px; left:78.5px; transform-origin:bottom center; border-radius:4px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function updateClockLogin() {
                const now = new Date();

                const hh24 = now.getHours();
                const mm = String(now.getMinutes()).padStart(2, '0');
                const ss = String(now.getSeconds()).padStart(2, '0');

                const ampm = hh24 >= 12 ? 'PM' : 'AM';
                let hh12 = hh24 % 12;
                if (hh12 === 0) hh12 = 12;
                const hh12Text = String(hh12).padStart(2, '0');

                const dateText = now.toLocaleDateString(undefined, {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });

                const digital = document.getElementById("digital-clock-login");
                const ampmEl = document.getElementById("digital-ampm-login");
                const dateEl = document.getElementById("digital-date-login");
                const hourHand = document.getElementById("hour-hand-login");
                const minuteHand = document.getElementById("minute-hand-login");
                const secondHand = document.getElementById("second-hand-login");

                if (!digital || !ampmEl || !dateEl || !hourHand || !minuteHand || !secondHand) return;

                digital.innerText = `${hh12Text}:${mm}:${ss}`;
                ampmEl.innerText = ampm;
                dateEl.innerText = dateText;

                const seconds = now.getSeconds();
                const minutes = now.getMinutes();
                const hours = now.getHours();

                const secondDeg = seconds * 6;
                const minuteDeg = (minutes * 6) + (seconds * 0.1);
                const hourDeg = ((hours % 12) * 30) + (minutes * 0.5);

                secondHand.style.transform = `rotate(${secondDeg}deg)`;
                minuteHand.style.transform = `rotate(${minuteDeg}deg)`;
                hourHand.style.transform = `rotate(${hourDeg}deg)`;
            }

            updateClockLogin();
            setInterval(updateClockLogin, 1000);
        </script>
        """,
        height=height,
    )


def render_login_clock_widget(height: int = 180) -> None:
    components.html(
        """
        <div style="
            margin: 0 0 16px 0;
            padding: 18px;
            border-radius: 18px;
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 10px 24px rgba(0,0,0,0.16);
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;">
                <div>
                    <div style="font-size:13px; opacity:0.75; margin-bottom:6px;">Current Attendance Time</div>
                    <div id="login-digital-clock" style="font-size:30px; font-weight:800;">--:--:--</div>
                    <div id="login-ampm" style="font-size:13px; opacity:0.9; margin-top:4px;">--</div>
                    <div id="login-digital-date" style="font-size:13px; opacity:0.75; margin-top:6px;">--</div>
                </div>

                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="font-size:26px;">🕒</div>
                    <div style="font-size:14px; line-height:1.7; opacity:0.92;">
                        اختر الشيفت والفرع ووقت الحضور<br/>
                        بشكل واضح قبل الدخول للنظام
                    </div>
                </div>
            </div>
        </div>

        <script>
            function updateLoginClock() {
                const now = new Date();

                const hh24 = now.getHours();
                const mm = String(now.getMinutes()).padStart(2, '0');
                const ss = String(now.getSeconds()).padStart(2, '0');
                const ampm = hh24 >= 12 ? "PM" : "AM";

                let hh12 = hh24 % 12;
                if (hh12 === 0) hh12 = 12;
                const hh12Text = String(hh12).padStart(2, '0');

                const dateText = now.toLocaleDateString(undefined, {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });

                const digital = document.getElementById("login-digital-clock");
                const ampmEl = document.getElementById("login-ampm");
                const dateEl = document.getElementById("login-digital-date");

                if (!digital || !ampmEl || !dateEl) return;

                digital.innerText = `${hh12Text}:${mm}:${ss}`;
                ampmEl.innerText = ampm;
                dateEl.innerText = dateText;
            }

            updateLoginClock();
            setInterval(updateLoginClock, 1000);
        </script>
        """,
        height=height,
    )


# =====================================================
# Time input
# =====================================================
def render_professional_time_picker(
    title: str,
    default_hour_24: int,
    default_minute: int,
    key_prefix: str,
) -> tuple[int, int]:
    st.markdown(f"### {title}")

    hour_options_12 = list(range(1, 13))
    minute_options = list(range(0, 60, 5))

    default_ampm = "AM" if default_hour_24 < 12 else "PM"
    default_hour_12 = default_hour_24 % 12
    if default_hour_12 == 0:
        default_hour_12 = 12

    if default_minute not in minute_options:
        closest_minute = min(minute_options, key=lambda x: abs(x - default_minute))
    else:
        closest_minute = default_minute

    hour_key = f"{key_prefix}_hour_12"
    minute_key = f"{key_prefix}_minute"
    ampm_key = f"{key_prefix}_ampm"

    c1, c2, c3 = st.columns([1.2, 1.2, 1])

    with c1:
        selected_hour_12 = st.selectbox(
            "🕐 Hour",
            hour_options_12,
            index=hour_options_12.index(default_hour_12),
            key=hour_key,
        )

    with c2:
        selected_minute = st.selectbox(
            "⏱ Minute",
            minute_options,
            index=minute_options.index(closest_minute),
            format_func=lambda x: f"{x:02d}",
            key=minute_key,
        )

    with c3:
        selected_ampm = st.selectbox(
            "🌗 AM / PM",
            ["AM", "PM"],
            index=0 if default_ampm == "AM" else 1,
            key=ampm_key,
        )

    hour_24 = selected_hour_12 % 12
    if selected_ampm == "PM":
        hour_24 += 12

    display_12 = f"{selected_hour_12:02d}:{selected_minute:02d} {selected_ampm}"
    display_24 = f"{hour_24:02d}:{selected_minute:02d}"

    st.info(f"✅ Selected Time: {display_12}  |  24H Format: {display_24}")

    return int(hour_24), int(selected_minute)


# =====================================================
# Dashboard cards
# =====================================================
def render_dashboard_cards_for_admin(db: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Employees", get_employee_count(db))
    with c2:
        st.metric("Branches", get_branch_count(db))
    with c3:
        st.metric("Tasks", get_tasks_count(db))
    with c4:
        st.metric("Printers", get_printer_count(db))

    c5, c6 = st.columns(2)
    with c5:
        st.metric("Archived Reports", get_history_count(db))
    with c6:
        st.metric("Training Records", len(db.get("training_records", {})))


def render_dashboard_cards_for_manager(db: dict) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Employees", get_employee_count(db))
    with c2:
        st.metric("Branches", get_branch_count(db))
    with c3:
        st.metric("Archived Reports", get_history_count(db))


def render_dashboard_cards_for_employee(user_info: dict) -> None:
    salary_summary = calculate_salary_breakdown(user_info)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Warnings", get_user_warning_count(user_info))
    with c2:
        st.metric("My Records", get_user_records_count(user_info))
    with c3:
        st.metric("Net Salary", f"{salary_summary['net_salary']:,.2f} LE")


def render_dashboard_cards_for_cleaner(user_info: dict, training_info: dict | None = None) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Warnings", get_user_warning_count(user_info))
    with c2:
        st.metric("Training", (training_info or {}).get("status", "pending"))
    with c3:
        st.metric("Job", "Cleaner")


def render_dashboard_cards_default(user_info: dict, db: dict, training_info: dict | None = None) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Warnings", get_user_warning_count(user_info))
    with c2:
        st.metric("Training", (training_info or {}).get("status", "pending"))
    with c3:
        st.metric("Archived Reports", get_history_count(db))


def render_role_dashboard_cards(
    normalized_role: str,
    user_info: dict,
    db: dict,
    training_info: dict | None = None,
) -> None:
    if normalized_role == ROLE_ADMIN:
        render_dashboard_cards_for_admin(db)
    elif normalized_role == ROLE_MANAGER:
        render_dashboard_cards_for_manager(db)
    elif normalized_role == ROLE_EMPLOYEE:
        render_dashboard_cards_for_employee(user_info)
    elif normalized_role == ROLE_CLEANER:
        render_dashboard_cards_for_cleaner(user_info, training_info)
    else:
        render_dashboard_cards_default(user_info, db, training_info)
