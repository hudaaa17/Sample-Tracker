"""
Add New Sample entry page.
- Drill-down customer from Firebase customers collection
- Optional initial feedback with classification
- Hold feedback status supported
"""
import streamlit as st
from datetime import datetime, date
from auth.firebase_config import get_db
from samples_new.sample_constants import (
    SAMPLE_CSS, load_sample_data,
    COL_BRANCH, COL_AREA, COL_ENQ_DATE, COL_HO_DATE,
    COL_CUSTOMER, COL_CONTACT, COL_CUST_PROD,
    COL_SAMPLE_PROD, COL_QTY, COL_HO_BY, COL_FEEDBACK
)


# ─────────────────────────────────────────
# LOAD CUSTOMERS FROM FIREBASE
# ─────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_customers_for_entry() -> list:
    """Load customer master list from Firebase customers collection."""
    try:
        db   = get_db()
        docs = db.collection("customers").order_by("name").stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        st.error(f"Failed to load customers: {e}")
        return []


def get_branches(customers):
    return sorted(set(c["branch"] for c in customers if c.get("branch")))


def get_areas(customers, branch):
    return sorted(set(
        c["area"] for c in customers
        if c.get("branch") == branch and c.get("area")
    ))


def get_customer_names(customers, branch, area):
    return sorted(
        c["name"] for c in customers
        if c.get("branch") == branch
        and c.get("area") == area
        and c.get("name")
    )


def get_industry(customers, name):
    for c in customers:
        if c.get("name") == name:
            return c.get("industry", "")
    return ""


# ─────────────────────────────────────────
# SYNC TO SHEET
# ─────────────────────────────────────────
def sync_new_samples_to_sheet():
    import gspread
    from google.oauth2.service_account import Credentials
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    db       = get_db()
    unsynced = list(
        db.collection("sample_entries")
          .where("synced", "==", False)
          .stream()
    )
    if not unsynced:
        return 0, 0
    try:
        creds     = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPE
        )
        client    = gspread.authorize(creds)
        sheet_id  = st.secrets["spreadsheets"]["samples"]
        worksheet = client.open_by_key(sheet_id).sheet1
        synced = 0
        errors = 0
        for doc in unsynced:
            try:
                d = doc.to_dict()
                worksheet.append_row([
                    d.get(COL_BRANCH, ""),
                    d.get(COL_AREA, ""),
                    d.get(COL_ENQ_DATE, ""),
                    d.get(COL_HO_DATE, ""),
                    d.get(COL_CUSTOMER, ""),
                    d.get(COL_CONTACT, ""),
                    d.get(COL_CUST_PROD, ""),
                    d.get(COL_SAMPLE_PROD, ""),
                    d.get("Supplier Name", ""),
                    d.get(COL_QTY, ""),
                    d.get(COL_HO_BY, ""),
                    d.get(COL_FEEDBACK, ""),
                ], value_input_option="USER_ENTERED")
                db.collection("sample_entries").document(doc.id).update({
                    "synced":    True,
                    "synced_at": datetime.now().isoformat()
                })
                synced += 1
            except Exception:
                errors += 1
        load_sample_data.clear()
        return synced, errors
    except Exception:
        return 0, len(unsynced)


# ─────────────────────────────────────────
# SUCCESS DIALOG
# ─────────────────────────────────────────
@st.dialog("Entry Submitted! 🎉")
def show_success_dialog():
    st.markdown("✅ **Sample entry saved and synced to the sheet!**")
    st.balloons()
    if st.button("OK", type="primary", width='stretch'):
        st.rerun()


# ─────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────
def show_sample_entry():
    st.markdown(SAMPLE_CSS, unsafe_allow_html=True)

    # ── Extra styles ──
    st.markdown("""
    <style>
    .se-section {
        font-family: 'Outfit', sans-serif;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #C9A84C;
        border-bottom: 2px solid #DDD5C5;
        padding-bottom: 8px;
        margin: 2rem 0 1rem 0;
        position: relative;
    }
    .se-section::after {
        content: '';
        position: absolute;
        bottom: -2px; left: 0;
        width: 40px; height: 2px;
        background: #C9A84C;
    }
    .auto-fill-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #E8F5E9;
        border: 1px solid #A5D6A7;
        border-radius: 20px;
        padding: 3px 12px;
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        color: #2E7D32;
        margin-top: 6px;
    }
    .fb-toggle-yes {
        background: #E8F5E9 !important;
        border: 1.5px solid #A5D6A7 !important;
        color: #2E7D32 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sd-hero">
        <div class="sd-eyebrow">Sample Intelligence</div>
        <div class="sd-title">Add New <em>Sample</em></div>
        <div class="sd-sub">Record a new sample entry. It will be saved and synced to the sheet.</div>
        <div class="sd-divider"></div>
    </div>""", unsafe_allow_html=True)

    st.caption(f"Logged in as **{st.session_state.get('email','')}**")

    # ── Load customers ──
    with st.spinner("Loading customer master list..."):
        customers = load_customers_for_entry()

    if not customers:
        st.warning("⚠️ No customers found in master list. Contact admin.")
        return

    # ══════════════════════════════════════
    # SECTION 1 — Visit Info
    # ══════════════════════════════════════
    st.markdown('<div class="se-section">📍 Sample & Customer Info</div>',
               unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ns_enq_date = st.date_input(
            "Enquiry Sent to Principal Date *",
            value=None, key="ns_enq_date"
        )
    with col2:
        ns_ho_date = st.date_input(
            "Hand Over to Customer Date *",
            value=None, key="ns_ho_date"
        )

    # ── Drill-down: Branch → Area → Customer ──
    branches = get_branches(customers)
    col3, col4 = st.columns(2)
    with col3:
        ns_branch = st.selectbox(
            "Branch *",
            ["— Select —"] + branches,
            key="ns_branch"
        )
    with col4:
        if ns_branch and ns_branch != "— Select —":
            areas    = get_areas(customers, ns_branch)
            ns_area  = st.selectbox(
                "Area *",
                ["— Select —"] + areas,
                key="ns_area"
            )
        else:
            st.selectbox("Area *", ["Select branch first"],
                        disabled=True, key="ns_area_dis")
            ns_area = ""

    col5, col6 = st.columns(2)
    with col5:
        if ns_area and ns_area != "— Select —":
            cust_names  = get_customer_names(customers, ns_branch, ns_area)
            ns_customer = st.selectbox(
                "Customer *",
                ["— Select —"] + cust_names,
                key="ns_customer"
            )
        else:
            st.selectbox("Customer *", ["Select area first"],
                        disabled=True, key="ns_customer_dis")
            ns_customer = ""

    with col6:
        if ns_customer and ns_customer != "— Select —":
            industry = get_industry(customers, ns_customer)
            st.text_input(
                "Industry",
                value=industry,
                disabled=True,
                key="ns_industry"
            )
            st.markdown(
                '<span class="auto-fill-badge">✓ Auto-filled</span>',
                unsafe_allow_html=True
            )
        else:
            st.text_input("Industry", value="", disabled=True,
                         key="ns_industry_empty")

    col7, col8 = st.columns(2)
    with col7:
        ns_contact = st.text_input(
            "Contact Person",
            placeholder="e.g. Mr. Raj (Purchase)",
            key="ns_contact"
        )
    with col8:
        ns_cust_prod = st.text_input(
            "Product Mfgd. by Customer",
            placeholder="e.g. Mat",
            key="ns_cust_prod"
        )

    # ══════════════════════════════════════
    # SECTION 2 — Sample Info
    # ══════════════════════════════════════
    st.markdown('<div class="se-section">🧪 Sample Details</div>',
               unsafe_allow_html=True)

    col9, col10, col11 = st.columns(3)
    with col9:
        ns_sample_prod = st.text_input(
            "Our Sample Product Name *",
            placeholder="e.g. Yasho- TBzTD",
            key="ns_sample_prod"
        )
    with col10:
        ns_supplier = st.text_input(
            "Supplier Name",
            placeholder="e.g. Auropol",
            key="ns_supplier"
        )
    with col11:
        ns_qty = st.text_input(
            "Sample Quantity *",
            placeholder="e.g. 500g, 1kg",
            key="ns_qty"
        )

    ns_ho_by = st.text_input(
        "Handed Over By *",
        placeholder="e.g. Mr. Rajan",
        key="ns_ho_by"
    )

    # ══════════════════════════════════════
    # SECTION 3 — Initial Feedback (optional)
    # ══════════════════════════════════════
    st.markdown('<div class="se-section">💬 Initial Feedback</div>',
               unsafe_allow_html=True)

    st.markdown(
        "<div style='font-family:Outfit,sans-serif;font-size:0.88rem;"
        "color:#6B7A99;margin-bottom:0.8rem;'>"
        "Do you have an initial feedback to record?</div>",
        unsafe_allow_html=True
    )

    fb_choice = st.radio(
        "Initial feedback available?",
        ["No", "Yes"],
        horizontal=True,
        key="ns_fb_choice",
        label_visibility="collapsed"
    )

    ns_feedback      = ""
    ns_fb_date       = None
    ns_fb_status     = "Pending"

    if fb_choice == "Yes":
        col_fd, col_fs = st.columns(2)
        with col_fd:
            ns_fb_date = st.date_input(
                "Feedback Date *",
                value=date.today(),
                key="ns_fb_date"
            )
        with col_fs:
            ns_fb_status = st.selectbox(
                "Feedback Classification *",
                ["Positive", "Negative", "Pending", "Hold"],
                key="ns_fb_status"
            )
        ns_feedback = st.text_area(
            "Feedback Text *",
            placeholder="Enter initial feedback from the customer...",
            height=100,
            key="ns_feedback"
        )
        if ns_fb_status == "Positive":
            ns_purchased = st.selectbox(
                "Purchased?",
                ["Yes", "Not Yet", "No"],
                key="ns_purchased"
            )
        elif ns_fb_status == "Negative":
            ns_purchased = "No"
            st.selectbox("Purchased?", ["No"], disabled=True, key="ns_purchased_dis")
        else:
            ns_purchased = "Purchase Data Not Available"

    st.divider()

    # ══════════════════════════════════════
    # SUBMIT
    # ══════════════════════════════════════
    if st.button("➕ Add Sample Entry", type="primary",
                width='stretch', key="ns_submit"):
        errors = []

        if not ns_enq_date:
            errors.append("Enquiry Date is required")
        if not ns_ho_date:
            errors.append("Handover Date is required")
        if not ns_branch or ns_branch == "— Select —":
            errors.append("Branch is required")
        if not ns_area or ns_area == "— Select —":
            errors.append("Area is required")
        if not ns_customer or ns_customer == "— Select —":
            errors.append("Customer is required")
        if not ns_sample_prod.strip():
            errors.append("Sample Product is required")
        if not ns_qty.strip():
            errors.append("Sample Quantity is required")
        if not ns_ho_by.strip():
            errors.append("Handed Over By is required")
        if ns_enq_date and ns_ho_date and ns_enq_date > ns_ho_date:
            errors.append("Enquiry date cannot be after handover date")
        if fb_choice == "Yes" and not ns_feedback.strip():
            errors.append("Please enter feedback text or select 'No' for initial feedback")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            try:
                db = get_db()

                # ── Save sample entry to Firestore ──
                db.collection("sample_entries").add({
                    COL_BRANCH:      ns_branch,
                    COL_AREA:        ns_area,
                    COL_ENQ_DATE:    str(ns_enq_date),
                    COL_HO_DATE:     str(ns_ho_date),
                    COL_CUSTOMER:    ns_customer,
                    COL_CONTACT:     ns_contact.strip(),
                    COL_CUST_PROD:   ns_cust_prod.strip(),
                    COL_SAMPLE_PROD: ns_sample_prod.strip(),
                    COL_QTY:         ns_qty.strip(),
                    COL_HO_BY:       ns_ho_by.strip(),
                    COL_FEEDBACK:    ns_feedback.strip(),
                    COL_SAMPLE_PROD: ns_sample_prod.strip(),
                    "Supplier Name": ns_supplier.strip(),   
                    "submitted_by":  st.session_state.get("email", ""),
                    "submitted_at":  datetime.now().isoformat(),
                    "synced":        False,
                })

                # ── If initial feedback provided, save to feedback subcollection ──
                if fb_choice == "Yes" and ns_feedback.strip():
                    from samples_new.sample_firestore import add_feedback_with_status
                    add_feedback_with_status(
                        customer    = ns_customer,
                        product     = ns_sample_prod.strip(),
                        ho_date     = str(ns_ho_date),
                        feedback_text = ns_feedback.strip(),
                        feedback_date = ns_fb_date,
                        fb_status   = ns_fb_status,
                        purchased     = ns_purchased,
                    )

                # ── Sync to sheet ──
                sync_new_samples_to_sheet()

                # ── Clear form ──
                for key in ["ns_enq_date", "ns_ho_date", "ns_contact",
                            "ns_supplier",
                           "ns_cust_prod", "ns_sample_prod", "ns_qty",
                           "ns_ho_by", "ns_feedback", "ns_fb_choice"]:
                    st.session_state.pop(key, None)

                st.session_state["ns_show_success"] = True

            except Exception as e:
                st.error(f"Failed to save: {e}")

    if st.session_state.get("ns_show_success"):
        st.session_state.pop("ns_show_success", None)
        show_success_dialog()