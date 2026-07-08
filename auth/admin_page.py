import streamlit as st
from auth.auth_functions import (
    get_pending_requests, get_all_users, get_denied_requests,
    approve_user, deny_request,
    remove_user, change_user_password,
    create_user_directly, restore_request,
    delete_request_permanently 
)



ADMIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
 
:root {
    --navy:      #1B2A4A;
    --gold:      #C9A84C;
    --gold-lt:   #E8C96A;
    --cream:     #FAF7F2;
    --warm-gray: #F0EBE1;
    --border:    #DDD5C5;
    --muted:     #6B7A99;
    --text:      #1B2A4A;
    --green:     #155724;
    --green-bg:  #D4EDDA;
    --green-bd:  #C3E6CB;
    --red:       #721C24;
    --red-bg:    #F8D7DA;
    --red-bd:    #F5C6CB;
    --yellow:    #856404;
    --yellow-bg: #FFF3CD;
    --yellow-bd: #FFEAA7;
}
 
/* ── Page background ── */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background-color: var(--cream) !important;
}
[data-testid="stHeader"] {
    background-color: var(--cream) !important;
}
 
/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--navy) !important;
    border-right: 3px solid var(--gold) !important;
}
section[data-testid="stSidebar"] * {
    color: #E8E4DC !important;
    font-family: 'Outfit', sans-serif !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #E8C97A !important;
    border: 1px solid var(--gold) !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    margin-bottom: 4px !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(201, 168, 76, 0.15) !important;
    border-color: var(--gold-lt) !important;
    color: #FFFFFF !important;
}
 
/* ── Page title ── */
.admin-header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: var(--navy);
    line-height: 1.1;
    letter-spacing: -0.5px;
    margin-bottom: 0.2rem;
}
.admin-sub {
    font-family: 'Outfit', sans-serif;
    font-size: 1rem;
    font-weight: 400;
    color: var(--muted);
    margin-bottom: 0.5rem;
}
 
/* ── Section titles ── */
.section-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--navy);
    border-bottom: 2px solid var(--border);
    padding-bottom: 8px;
    margin: 2.5rem 0 1.2rem 0;
    position: relative;
}
.section-title::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 50px;
    height: 2px;
    background: var(--gold);
}
 
/* ── Column headers ── */
.col-header {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    padding-bottom: 4px;
}
 
/* ── User name & email ── */
.user-name {
    font-family: 'Outfit', sans-serif;
    font-size: 0.98rem;
    font-weight: 600;
    color: var(--navy);
    margin-bottom: 2px;
    padding-top: 8px;
}
.user-email {
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    font-weight: 400;
    color: var(--muted);
    padding-bottom: 8px;
}
 
/* ── Status badges ── */
.badge-pending {
    background: var(--yellow-bg);
    color: var(--yellow);
    border: 1px solid var(--yellow-bd);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 0.05em;
    display: inline-block;
    margin-top: 10px;
}
.badge-approved {
    background: var(--green-bg);
    color: var(--green);
    border: 1px solid var(--green-bd);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    display: inline-block;
    margin-top: 10px;
}
.badge-denied {
    background: var(--red-bg);
    color: var(--red);
    border: 1px solid var(--red-bd);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    display: inline-block;
    margin-top: 10px;
}
 
/* ── Buttons ── */
.stButton > button {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
    background: var(--navy) !important;
    color: #E8C97A !important;
    border: 1.5px solid var(--gold) !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: var(--gold) !important;
    color: var(--navy) !important;
}
 
/* ── Sync button — larger and distinct ── */
.sync-btn .stButton > button {
    font-size: 1rem !important;
    padding: 12px 20px !important;
    background: var(--gold) !important;
    color: var(--navy) !important;
    border: none !important;
    font-weight: 700 !important;
}
.sync-btn .stButton > button:hover {
    background: var(--gold-lt) !important;
    box-shadow: 0 4px 16px rgba(201, 168, 76, 0.3) !important;
}
 
/* ── Inputs ── */
[data-testid="stTextInput"] input {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    background: #FFFFFF !important;
    color: var(--navy) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.12) !important;
}
[data-testid="stWidgetLabel"] p,
[data-testid="stTextInput"] label {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: var(--navy) !important;
}
 
/* ── Expander ── */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1.5px solid var(--border) !important;
    border-left: 4px solid var(--red-bd) !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(27,42,74,0.06) !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--red) !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"]:has(summary:contains("Create")),
[data-testid="stExpander"]:has(summary:contains("View")) {
    border-left: 4px solid var(--gold) !important;
}
[data-testid="stExpander"]:has(summary:contains("Create")) summary,
[data-testid="stExpander"]:has(summary:contains("View")) summary {
    color: var(--navy) !important;
}
 
/* ── Alerts ── */
.stAlert {
    border-radius: 8px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
}
 
/* ── Dividers ── */
hr {
    border-color: var(--border) !important;
    margin: 6px 0 !important;
}
 
/* ── st.code ── */
.stCode {
    font-size: 0.9rem !important;
    border-radius: 6px !important;
    background: var(--warm-gray) !important;
}
 
/* ── Sync section card ── */
.sync-card {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-left: 5px solid var(--gold);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-top: 2rem;
    box-shadow: 0 2px 12px rgba(27,42,74,0.06);
}
.sync-card-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--navy);
    margin-bottom: 0.3rem;
}
.sync-card-sub {
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 1rem;
}
</style>
"""
 
ADMIN_TITLE_HTML = """
<div style="margin-bottom: 0.5rem;">
    <div class="admin-header">⚙️ Admin <em style="color:#C9A84C; font-style:italic;">Panel</em></div>
    <div class="admin-sub">Manage access requests, users and sync visit data.</div>
    <div style="width:60px; height:3px; background:linear-gradient(90deg,#C9A84C,#E8C96A); border-radius:2px; margin-top:0.8rem;"></div>
</div>
"""
 
SYNC_CARD_HTML = """
<div class="sync-card">
    <div class="sync-card-title">🔄 Sync Visit Entries</div>
    <div class="sync-card-sub">Push all pending Firestore entries to Google Sheets. Safe to run anytime — only unsynced entries are processed.</div>
</div>
"""

def show_admin_page():

    st.markdown(ADMIN_CSS, unsafe_allow_html=True)
    st.markdown(ADMIN_TITLE_HTML, unsafe_allow_html=True)
    if st.button("← Back", key="back_from_admin"):
        st.session_state["page"] = "samples"
        st.rerun()

    st.divider()

    # ══════════════════════════════════════
    # PENDING REQUESTS
    # ══════════════════════════════════════
    st.markdown('<div class="section-title">Pending Access Requests</div>',
                unsafe_allow_html=True)

    pending = get_pending_requests()
    active_pending = [p for p in pending if p.get("status") == "pending"]

    if not active_pending:
        st.info("No pending requests.")
    else:
        # Table header
        hc1, hc2, hc3, hc4, hc5 = st.columns([3, 3, 2, 1, 1])
        hc1.markdown("<span style='font-family:Libre Baskerville,serif; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#5A6A85;'>Name</span>", unsafe_allow_html=True)
        hc2.markdown("<span style='font-family:Libre Baskerville,serif; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#5A6A85;'>Email</span>", unsafe_allow_html=True)
        hc3.markdown("<span style='font-family:Libre Baskerville,serif; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#5A6A85;'>Set Password</span>", unsafe_allow_html=True)
        hc4.markdown("<span style='font-family:Libre Baskerville,serif; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#5A6A85;'>Approve</span>", unsafe_allow_html=True)
        hc5.markdown("<span style='font-family:Libre Baskerville,serif; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#5A6A85;'>Deny</span>", unsafe_allow_html=True)

        st.markdown("<hr style='margin:4px 0 8px 0; border-color:#D9D0BE;'>", unsafe_allow_html=True)

        for req in active_pending:
            c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 1, 1])

            with c1:
                st.markdown(f"""
                    <div class="user-name">{req['full_name']}</div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown(f"""
                    <div class="user-email">{req['email']}</div>
                """, unsafe_allow_html=True)

            with c3:
                new_pass = st.text_input(
                    "Password",
                    key=f"pass_{req['doc_id']}",
                    type="password",
                    placeholder="Min. 6 chars",
                    label_visibility="collapsed"
                )

            with c4:
                if st.button("✓ Approve", key=f"approve_{req['doc_id']}",
                            width='stretch'):
                    if not new_pass:
                        st.error("Set a password first.")
                    else:
                        ok, msg = approve_user(
                            req['email'], req['full_name'],
                            req['doc_id'], new_pass
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with c5:
                if st.button("✗ Deny", key=f"deny_{req['doc_id']}",
                             width='stretch'):
                    deny_request(req['doc_id'])
                    st.warning(f"Denied {req['full_name']}")
                    st.rerun()

            st.markdown("<hr style='margin:4px 0; border-color:#EDE8DF;'>",
                        unsafe_allow_html=True)
    # ══════════════════════════════════════
    # DENIED REQUESTS — hidden in expander
    # ══════════════════════════════════════
    denied = get_denied_requests()

    if denied:
        with st.expander(f"🚫  Denied Requests ({len(denied)})", expanded=False):
            
            dh1, dh2, dh3, dh4 = st.columns([3, 3, 2, 2])
            for col, label in zip(
                [dh1, dh2, dh3, dh4],
                ["Name", "Email", "Set Password", "Actions"]
            ):
                col.markdown(
                    f"<span style='font-family:Libre Baskerville,serif; font-size:11px;"
                    f"font-weight:700; letter-spacing:1px; text-transform:uppercase;"
                    f"color:#5A6A85;'>{label}</span>",
                    unsafe_allow_html=True
                )

            st.markdown("<hr style='margin:4px 0 8px 0; border-color:#D9D0BE;'>",
                        unsafe_allow_html=True)

            for req in denied:
                d1, d2, d3, d4 = st.columns([3, 3, 2, 2])

                with d1:
                    st.markdown(
                        f'<div class="user-name" style="color:#721C24;">'
                        f'{req["full_name"]}</div>',
                        unsafe_allow_html=True
                    )

                with d2:
                    st.markdown(
                        f'<div class="user-email">{req["email"]}</div>',
                        unsafe_allow_html=True
                    )

                with d3:
                    restore_pass = st.text_input(
                        "Password",
                        key=f"rpass_{req['doc_id']}",
                        type="password",
                        placeholder="To approve directly",
                        label_visibility="collapsed"
                    )

                with d4:
                    ca, cb, cc = st.columns(3)
                    with ca:
                        if st.button("↩", key=f"restore_{req['doc_id']}",
                                     width='stretch',
                                     help="Restore to pending"):
                            restore_request(req['doc_id'])
                            st.success(f"Restored {req['full_name']} to pending.")
                            st.rerun()
                    with cb:
                        if st.button("✓", key=f"dapprove_{req['doc_id']}",
                                     width='stretch',
                                     help="Approve directly"):
                            if not restore_pass:
                                st.error("Set a password first.")
                            else:
                                ok, msg = approve_user(
                                    req['email'], req['full_name'],
                                    req['doc_id'], restore_pass
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with cc:
                        if st.button("🗑", key=f"delete_{req['doc_id']}",
                                     width='stretch',
                                     help="Delete permanently"):
                            delete_request_permanently(req['doc_id'])
                            st.success(f"Deleted {req['full_name']} permanently.")
                            st.rerun()

                st.markdown("<hr style='margin:4px 0; border-color:#EDE8DF;'>",
                            unsafe_allow_html=True)
    # ══════════════════════════════════════
    # ALL USERS
    # ══════════════════════════════════════
    st.markdown('<div class="section-title">All Users</div>', unsafe_allow_html=True)

    all_users = get_all_users()
    all_users = [u for u in all_users if u.get("role") != "admin"]
    
    if not all_users:
        st.info("No users yet.")
    else:
        # Table header
        uh1, uh2, uh3, uh4, uh5 = st.columns([3, 3, 1, 2, 1])
        for col, label in zip(
            [uh1, uh2, uh3, uh4, uh5],
            ["Name", "Email", "Status", "Password", "Action"]
        ):
            col.markdown(
                f"<span style='font-family:Libre Baskerville,serif; font-size:11px;"
                f"font-weight:700; letter-spacing:1px; text-transform:uppercase;"
                f"color:#5A6A85;'>{label}</span>",
                unsafe_allow_html=True
            )

        st.markdown("<hr style='margin:4px 0 8px 0; border-color:#D9D0BE;'>",
                    unsafe_allow_html=True)

        for user in all_users:
            u1, u2, u3, u4, u5 = st.columns([3, 3, 1, 2, 1])

            with u1:
                st.markdown(f'<div class="user-name">{user["full_name"]}</div>',
                            unsafe_allow_html=True)

            with u2:
                st.markdown(f'<div class="user-email">{user["email"]}</div>',
                            unsafe_allow_html=True)

            with u3:
                status = user.get("status", "approved")
                badge_class = f"badge-{status}"
                st.markdown(f'<span class="{badge_class}">{status.capitalize()}</span>',
                            unsafe_allow_html=True)

            with u4:
                with st.expander("View / Change"):
                    stored = user.get("password_plain", "–")
                    st.code(stored, language=None)
                    new_p = st.text_input(
                        "New password",
                        key=f"newp_{user['uid']}",
                        type="password",
                        placeholder="New password"
                    )
                    if st.button("Update", key=f"updp_{user['uid']}",
                                 width='stretch'):
                        if new_p:
                            change_user_password(user['email'], new_p, user['uid'])
                            st.success("Updated!")
                            st.rerun()
                        else:
                            st.error("Enter a new password.")

            with u5:
                st.write("")
                if st.button("Remove", key=f"remove_{user['uid']}",
                             width='stretch'):
                    remove_user(user['uid'], user['email'])
                    st.warning(f"Removed {user['full_name']}")
                    st.rerun()

            st.markdown("<hr style='margin:4px 0; border-color:#EDE8DF;'>",
                        unsafe_allow_html=True)
    # ══════════════════════════════════════
    # CREATE USER
    # ══════════════════════════════════════
    st.markdown('<div class="section-title">Create User</div>', unsafe_allow_html=True)

    with st.expander("➕  Create a new user directly", expanded=False):
        cc1, cc2, cc3, cc4 = st.columns([2, 2, 2, 1])

        with cc1:
            new_full_name = st.text_input("Full Name", key="create_full_name",
                                           placeholder="e.g. John Smith")
        with cc2:
            new_email = st.text_input("Email Address", key="create_email",
                                       placeholder="e.g. john@company.com")
        with cc3:
            new_password = st.text_input("Password", key="create_password",
                                          type="password", placeholder="Min. 6 chars")
        with cc4:
            st.write("")
            st.write("")
            create_clicked = st.button("Create User", key="create_user_btn",
                                        width='stretch')

        if create_clicked:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

            # ── Validation ──
            if not new_full_name or not new_email or not new_password:
                st.error("Please fill in all fields.")
            elif len(new_full_name.strip()) < 2:
                st.error("Please enter a valid full name.")
            elif any(char.isdigit() for char in new_full_name):
                st.error("Name should not contain numbers.")
            elif not re.match(email_pattern, new_email.strip()):
                st.error("Please enter a valid email address (e.g. name@example.com)")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                # Reuse approve_user but pass a fake doc_id since
                # there's no pending request to delete
                ok, msg = create_user_directly(
                    new_email.strip(), new_full_name.strip(), new_password
                )
                if ok:
                    st.success(f"✅ User {new_full_name} created successfully!")
                else:
                    st.error(msg)
    
