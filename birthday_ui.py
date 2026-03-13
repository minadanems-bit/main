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
        padding:25px;
        border-radius:15px;
        text-align:center;
        background: linear-gradient(90deg,#ff9a9e,#fad0c4);
        color:#000;
        font-size:22px;
        font-weight:bold;
        ">
        🎉 Happy Birthday {full_name}! 🎂  
        Wishing you a beautiful day full of happiness and success.
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

    for user in birthday_users:
        username = user["username"]
        full_name = user["full_name"]

        with st.container():

            if is_username_birthday_today(db, username):
                render_birthday_banner(full_name)

            st.write(f"**{full_name}**")

            # ==========================================
            # Messages
            # ==========================================
            st.markdown("#### 🎁 Birthday Wishes")

            messages = get_birthday_messages_for_user(db, username)

            if messages:
                for msg in messages:
                    st.markdown(
                        f"""
                        <div style="
                        border:1px solid #ddd;
                        padding:10px;
                        border-radius:8px;
                        margin-bottom:8px;">
                        <b>{msg["sender_username"]}</b>  
                        {msg["message_text"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No birthday wishes yet.")

            # ==========================================
            # Send message
            # ==========================================
            if current_user != username:

                st.markdown("#### ✉ Send Birthday Wish")

                message = st.text_area(
                    "Write your message",
                    key=f"birthday_msg_{username}",
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

            st.divider()
