# =====================================================
# BIRTHDAY UI
# Birthday celebration page and wishes
# =====================================================

import streamlit as st

from auth_service import get_current_username
from database import load_db
from birthday_service import (
    get_birthday_users,
    get_birthday_messages_for_user,
    send_birthday_message,
    is_username_birthday_today,
)


def render_birthday_banner(full_name: str):
    st.markdown(
        f"""
        <div style="
            padding: 28px;
            border-radius: 18px;
            text-align: center;
            background: linear-gradient(90deg, #ff9a9e, #fad0c4, #fad0c4);
            color: #222;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 18px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.10);
            border: 1px solid rgba(255,255,255,0.6);
        ">
            🎉 Happy Birthday {full_name}! 🎂<br>
            <span style="font-size:16px; font-weight:500;">
                Wishing you a beautiful day full of happiness, success, and unforgettable moments.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_birthday_person_card(full_name: str, username: str):
    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 14px;
            background: #fff8fb;
            border: 1px solid #f3d7df;
            margin-bottom: 12px;
        ">
            <div style="font-size: 20px; font-weight: 700; color: #222;">
                🎂 {full_name}
            </div>
            <div style="font-size: 13px; color: #666; margin-top: 4px;">
                @{username}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message_card(sender_username: str, message_text: str):
    st.markdown(
        f"""
        <div style="
            border: 1px solid #e8e8e8;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        ">
            <div style="font-weight: 700; color: #333; margin-bottom: 6px;">
                💌 {sender_username}
            </div>
            <div style="color: #444; line-height: 1.7;">
                {message_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def birthday_ui():
    db = load_db()
    current_user = get_current_username()

    st.title("🎂 Birthday Celebration")

    birthday_users = get_birthday_users(db)

    if not birthday_users:
        st.info("No birthdays today.")
        return

    st.subheader("🎉 Today's Birthdays")

    # لو المستخدم الحالي نفسه عيد ميلاده النهارده
    if current_user and is_username_birthday_today(db, current_user):
        current_user_record = db.get("users", {}).get(current_user, {})
        current_full_name = current_user_record.get("full_name") or current_user
        render_birthday_banner(current_full_name)
        st.balloons()
        st.success("🎊 Today is your special day! Enjoy every moment.")

    for user in birthday_users:
        username = user.get("username", "")
        full_name = user.get("full_name", username or "Unknown")

        with st.container():
            render_birthday_person_card(full_name, username)

            # لو الشخص ده صاحب عيد الميلاد الحالي
            if current_user != username and is_username_birthday_today(db, username):
                st.info(f"🎉 Celebrate {full_name} today and send them a beautiful wish!")

            # ==========================================
            # Messages
            # ==========================================
            st.markdown("#### 🎁 Birthday Wishes")

            messages = get_birthday_messages_for_user(db, username)

            if messages:
                for msg in messages:
                    render_message_card(
                        msg.get("sender_username", "Unknown"),
                        msg.get("message_text", ""),
                    )
            else:
                st.info("No birthday wishes yet.")

            # ==========================================
            # Send message
            # ==========================================
            if current_user and current_user != username:
                st.markdown("#### ✉ Send Birthday Wish")

                message = st.text_area(
                    "Write your message",
                    key=f"birthday_msg_{username}",
                    placeholder=f"Write a lovely birthday wish for {full_name}...",
                    height=110,
                )

                if st.button(
                    "Send Wish",
                    key=f"send_birthday_{username}",
                    use_container_width=True,
                ):
                    success, msg = send_birthday_message(
                        sender_username=current_user,
                        receiver_username=username,
                        message_text=message,
                    )

                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            elif current_user == username:
                st.markdown(
                    """
                    <div style="
                        padding:12px;
                        border-radius:10px;
                        background:#fff4cc;
                        color:#5c4400;
                        font-weight:600;
                        margin-top:10px;
                    ">
                        🥳 This is your birthday card today. Enjoy your day!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.divider()
