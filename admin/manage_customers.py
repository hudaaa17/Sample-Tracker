import streamlit as st
from auth.firebase_config import get_db
from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter


# ─────────────────────────────────────────
# FIRESTORE HELPERS
# ─────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_customers():
    """
    Load all customers from Firestore.
    Returns list of dicts with branch, area, name, industry.
    Cached for 5 minutes.
    """
    db = get_db()
    docs = db.collection("customers").order_by("name").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]


def add_customer(branch, area, name, industry):
    """Add a new customer to Firestore."""
    db = get_db()

    # Check duplicate
    existing = db.collection("customers")\
                 .where(filter=FieldFilter("name", "==", name.strip()))\
                 .where(filter=FieldFilter("branch", "==", branch))\
                 .get()
    if existing:
        return False, f"Customer '{name}' already exists under {branch}."

    db.collection("customers").add({
        "branch":     branch,
        "area":       area.strip(),
        "name":       name.strip(),
        "industry":   industry.strip(),
        "created_at": datetime.now().isoformat(),
    })

    # Clear cache so dropdowns refresh
    load_customers.clear()
    return True, f"Customer '{name}' added successfully!"


def update_customer(doc_id, branch, area, name, industry):
    """Update an existing customer."""
    db = get_db()
    db.collection("customers").document(doc_id).update({
        "branch":     branch,
        "area":       area.strip(),
        "name":       name.strip(),
        "industry":   industry.strip(),
        "updated_at": datetime.now().isoformat(),
    })
    load_customers.clear()
    return True, "Customer updated!"


def delete_customer(doc_id, name):
    """Delete a customer."""
    db = get_db()
    db.collection("customers").document(doc_id).delete()
    load_customers.clear()
    return True, f"Customer '{name}' deleted."


# ─────────────────────────────────────────
# DRILL-DOWN HELPERS (used in entry_form)
# ─────────────────────────────────────────

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
        if c.get("branch") == branch and c.get("area") == area and c.get("name")
    )


def get_industry(customers, name):
    for c in customers:
        if c.get("name") == name:
            return c.get("industry", "")
    return ""


# ─────────────────────────────────────────
# MANAGE CUSTOMERS PAGE
# ─────────────────────────────────────────

BRANCH_OPTIONS = ["KOTTAYAM", "COIMBATORE", "THRISSUR", "CHANGANACHERRY", "MUMBAI", "KOZHIKODE"]

def show_manage_customers():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Outfit:wght@300;400;500;600&display=swap');

    :root {
        --navy:      #1B2A4A;
        --gold:      #C9A84C;
        --gold-lt:   #E8C96A;
        --cream:     #FAF7F2;
        --warm-gray: #F0EBE1;
        --border:    #DDD5C5;
        --muted:     #6B7A99;
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
    [data-testid="stSidebar"] {
        background-color: var(--navy) !important;
    }
    [data-testid="stSidebar"] button {
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        background-color: transparent !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(201, 168, 76, 0.15) !important;
        border-color: var(--gold) !important;
        color: #FFFFFF !important;
    }

    /* ── Header ── */
    .mc-header {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--navy);
        margin-bottom: 0.1rem;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .mc-sub {
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        font-weight: 400;
        color: var(--muted);
        margin-bottom: 1.8rem;
        line-height: 1.5;
    }

    /* ── Section Label ── */
    .mc-section {
        font-family: 'Outfit', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--gold);
        border-bottom: 2px solid var(--border);
        padding-bottom: 8px;
        margin: 2rem 0 1rem 0;
        position: relative;
    }
    .mc-section::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 40px;
        height: 2px;
        background: var(--gold);
    }

    /* ── Widget labels ── */
    [data-testid="stWidgetLabel"] p,
    label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: var(--navy) !important;
    }

    /* ── Inputs ── */
    input, textarea,
    [data-testid="stTextInput"] input {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        color: var(--navy) !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
    }
    input:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.12) !important;
    }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
        min-height: 46px !important;
    }
    [data-testid="stSelectbox"] input {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ── Tab styling ── */
    [data-testid="stTabs"] [role="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: var(--muted) !important;
        padding: 8px 20px !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--navy) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--gold) !important;
    }

    /* ── Customer row card ── */
    .customer-row {
        background: #FFFFFF;
        border: 1.5px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 1px 4px rgba(27, 42, 74, 0.04);
    }
    .customer-row:hover {
        border-color: var(--gold);
        box-shadow: 0 4px 16px rgba(27, 42, 74, 0.08);
    }
    .customer-name {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        color: var(--navy);
        font-size: 1rem;
        margin-bottom: 4px;
    }
    .customer-meta {
        font-family: 'Outfit', sans-serif;
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 4px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    /* ── Badge ── */
    .badge {
        display: inline-flex;
        align-items: center;
        background: var(--warm-gray);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 2px 10px;
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--navy);
        white-space: nowrap;
    }

    /* ── Found count text ── */
    [data-testid="stMarkdownContainer"] div[style*="font-size:0.8rem"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] summary {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: var(--navy) !important;
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

    /* ── Search input ── */
    [data-testid="stTextInput"] input[placeholder*="Search"] {
        background: #FFFFFF !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding-left: 12px !important;
    }
    </style>
    """, unsafe_allow_html = True)
    st.markdown('<div class="mc-header">👥 𝑴𝒂𝒏𝒂𝒈𝒆 𝑪𝒖𝒔𝒕𝒐𝒎𝒆𝒓𝒔</div>', unsafe_allow_html=True)
    st.markdown('<div class="mc-sub">Add, edit or remove customers from the master list used in visit entry forms.</div>', unsafe_allow_html=True)

    if st.button("← Back", key="back_from_customers"):
        st.session_state["page"] = "samples"
        st.rerun()

    st.divider()

    ITEMS_PER_PAGE = 20

    page_num = st.session_state.get("mc_page", 0)

    # ── Tabs ──
    tab1, tab2 = st.tabs(["📋  Customer List", "➕  Add New Customer"])

    # ══════════════════════════════════════
    # TAB 1 — Customer List
    # ══════════════════════════════════════
    with tab1:
        customers = load_customers()

        if not customers:
            st.info("No customers added yet. Use the 'Add New Customer' tab to get started.")
        else:
            # ── Search + Filter ──
            col_s, col_b = st.columns([3, 1])
            with col_s:
                search = st.text_input(
                    "🔍 Search",
                    placeholder="Search by name, area, industry...",
                    key="mc_search",
                    label_visibility="collapsed"
                )
            with col_b:
                filter_branch = st.selectbox(
                    "Branch", ["All"] + BRANCH_OPTIONS,
                    key="mc_filter_branch",
                    label_visibility="collapsed"
                )

            # ── Reset page if filters changed ──
            prev_search = st.session_state.get("_prev_mc_search", "")
            prev_branch = st.session_state.get("_prev_mc_branch", "All")

            if search != prev_search or filter_branch != prev_branch:
                st.session_state["mc_page"]          = 0
                st.session_state["_prev_mc_search"]  = search
                st.session_state["_prev_mc_branch"]  = filter_branch

            # ── Apply filters ──
            filtered = customers
            if filter_branch != "All":
                filtered = [c for c in filtered if c.get("branch") == filter_branch]
            if search:
                s        = search.lower()
                filtered = [c for c in filtered if
                            s in c.get("name",     "").lower() or
                            s in c.get("area",     "").lower() or
                            s in c.get("industry", "").lower()]

            # ── Pagination ──
            ITEMS_PER_PAGE = 20
            page_num       = st.session_state.get("mc_page", 0)
            total_filtered = len(filtered)
            total_pages    = max(1, (total_filtered - 1) // ITEMS_PER_PAGE + 1)
            start          = page_num * ITEMS_PER_PAGE
            end            = start + ITEMS_PER_PAGE
            page_customers = filtered[start:end]

            st.markdown(
                f"<div style='font-family:Outfit,sans-serif;font-size:0.8rem;"
                f"color:#5A6A85;margin-bottom:0.8rem;'>"
                f"Showing {start+1}–{min(end, total_filtered)} of {total_filtered} customer(s)</div>",
                unsafe_allow_html=True
            )

            # ── Customer rows ──
            for c in page_customers:
                with st.container():
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"""
                        <div class="customer-row">
                            <div class="customer-name">{c.get('name', '—')}</div>
                            <div class="customer-meta">
                                <span class="badge">📍 {c.get('branch', '—')}</span>
                                <span class="badge">🗺 {c.get('area', '—')}</span>
                                <span class="badge">🏭 {c.get('industry', '—')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        with st.expander("⋮"):
                            new_branch   = st.selectbox("Branch", BRANCH_OPTIONS,
                                                        index=BRANCH_OPTIONS.index(c["branch"])
                                                        if c.get("branch") in BRANCH_OPTIONS else 0,
                                                        key=f"eb_{c['id']}")
                            new_area     = st.text_input("Area",     value=c.get("area",""),     key=f"ea_{c['id']}")
                            new_name     = st.text_input("Name",     value=c.get("name",""),     key=f"en_{c['id']}")
                            new_industry = st.text_input("Industry", value=c.get("industry",""), key=f"ei_{c['id']}")
                            col_save, col_del = st.columns(2)
                            with col_save:
                                if st.button("💾 Save", key=f"save_{c['id']}", width='content'):
                                    ok, msg = update_customer(c["id"], new_branch, new_area, new_name, new_industry)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with col_del:
                                if st.button("🗑 Delete", key=f"del_{c['id']}", width='content', type="primary"):
                                    ok, msg = delete_customer(c["id"], c.get("name",""))
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

            # ── Pagination controls ──
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("← Prev", disabled=(page_num == 0), key="mc_prev", width='content'):
                    st.session_state["mc_page"] = page_num - 1
                    st.rerun()
            with col_info:
                st.markdown(
                    f"<div style='text-align:center;font-family:Outfit,sans-serif;"
                    f"font-size:0.85rem;color:#6B7A99;padding-top:6px;'>"
                    f"Page {page_num+1} of {total_pages}</div>",
                    unsafe_allow_html=True
                )
            with col_next:
                if st.button("Next →", disabled=(page_num >= total_pages - 1), key="mc_next", width='content'):
                    st.session_state["mc_page"] = page_num + 1
                    st.rerun()          

    # ══════════════════════════════════════
    # TAB 2 — Add New Customer
    # ══════════════════════════════════════
    with tab2:
        st.markdown('<div class="mc-section">Customer Details</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            new_branch = st.selectbox("Branch *", BRANCH_OPTIONS, key="nc_branch")
        with col2:
            new_area = st.text_input("Area *", placeholder="e.g. Coimbatore", key="nc_area")

        col3, col4 = st.columns(2)
        with col3:
            new_name = st.text_input("Customer Name *", placeholder="e.g. ABC Rubber Pvt Ltd", key="nc_name")
        with col4:
            new_industry = st.text_input("Industry *", placeholder="e.g. Rubber, Automotive", key="nc_industry")

        st.divider()

        if st.button("➕ Add Customer", type="primary", width='content', key="nc_submit"):
            if not new_area.strip() or not new_name.strip() or not new_industry.strip():
                st.error("⚠️ All fields are required.")
            else:
                ok, msg = add_customer(new_branch, new_area, new_name, new_industry)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)