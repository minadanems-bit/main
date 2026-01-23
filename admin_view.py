if st.session_state['role'] == "admin":
        st.switch_page("admin_view.py")
    else:
        st.switch_page("user_view.py")
