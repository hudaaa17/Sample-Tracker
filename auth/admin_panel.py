import streamlit as st
from auth.auth_functions import get_all_requests, update_user_status

def show_admin_panel():
    st.subheader("Admin Panel — Access Requests")

    all_users = get_all_requests()
    for u in all_users:
        st.write(u) 
    all_users = [u for u in all_users if u.get("role") != "admin"] 
    pending = [u for u in all_users if u.get("status") == "pending"]
    others  = [u for u in all_users if u.get("status") != "pending" and u.get("role") != "admin"]

    if not pending:
        st.info("No pending requests.")
    else:
        for user in pending:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.markdown(f"**{user['full_name']}** — `{user['email']}`")
                if col2.button("Approve", key=f"approve_{user['uid']}"):
                    update_user_status(user['uid'], "approved")
                    st.success(f"Approved {user['full_name']}")
                    st.rerun()
                if col3.button("Deny", key=f"deny_{user['uid']}"):
                    update_user_status(user['uid'], "denied")
                    st.warning(f"Denied {user['full_name']}")
                    st.rerun()
            st.divider()

    with st.expander("All Users"):
        for user in others:
            st.markdown(
                f"**{user['full_name']}** — `{user['email']}` "
                f"— Status: `{user['status']}`"
            )
