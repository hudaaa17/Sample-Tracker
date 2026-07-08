"""
Pipeline Analytics — metrics and charts for the sample pipeline.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from samples_new.sample_constants import SAMPLE_CSS, CHART_COLORS, chart_layout
from sample_pipeline.sample_pipeline_firestore import load_pipeline_entries, STAGES
import html


def render_html_table(
    df: pd.DataFrame,
    max_height: int = 400,
    align_right_cols: list | None = None,
    key: str | None = None,
):
    """
    Render a DataFrame as a styled, vertically scrollable HTML table.
 
    Parameters
    ----------
    df : pd.DataFrame
        Already renamed/formatted the way you want it displayed.
        Values are converted with str() — format numbers before calling
        this (e.g. round floats, cast ints) since no NumberColumn-style
        formatting is applied here.
    max_height : int
        Max pixel height before the table body scrolls. Header stays
        pinned (sticky) while scrolling.
    align_right_cols : list[str] | None
        Column names (post-rename) to right-align — typically numeric
        columns. Defaults to None (everything left-aligned).
    key : str | None
        Unused currently, reserved in case you want to namespace CSS
        if you render multiple tables with different styling later.
    """
    if df is None or df.empty:
        st.caption("No data to display.")
        return
 
    align_right_cols = set(align_right_cols or [])
    cols = list(df.columns)
 
    # Build header row
    header_cells = []
    for c in cols:
        align = "right" if c in align_right_cols else "left"
        header_cells.append(
            f'<th style="text-align:{align};">{html.escape(str(c))}</th>'
        )
    header_html = "<tr>" + "".join(header_cells) + "</tr>"
 
    # Build body rows
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            val = row[c]
            if pd.isna(val):
                val_str = ""
            else:
                val_str = str(val)
            align = "right" if c in align_right_cols else "left"
            cells.append(
                f'<td style="text-align:{align};">{html.escape(val_str)}</td>'
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    body_html = "".join(body_rows)
 
    table_html = f"""
    <style>
    .ht-wrap {{
        border: 1px solid #DDD5C5;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(27,42,74,0.06);
        background: #FFFFFF;
    }}
    .ht-scroll {{
        max-height: {max_height}px;
        overflow-y: auto;
        overflow-x: auto;
    }}
    .ht-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Outfit', sans-serif;
        font-size: 0.88rem;
        color: #1B2A4A;
        background: #FFFFFF;
    }}
    .ht-table thead th {{
        position: sticky;
        top: 0;
        background: #1B2A4A;
        color: #E9C766;
        font-weight: 600;
        font-size: 0.78rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 12px 18px;
        white-space: nowrap;
        z-index: 1;
    }}
    .ht-table thead th:first-child {{
        border-top-left-radius: 9px;
    }}
    .ht-table thead th:last-child {{
        border-top-right-radius: 9px;
    }}
    .ht-table tbody td {{
        padding: 11px 18px;
        border-bottom: 1px solid #EFEAE0;
        white-space: nowrap;
        background: #FFFFFF;
    }}
    .ht-table tbody tr:nth-child(even) td {{
        background: #FBF8F2;
    }}
    .ht-table tbody tr:last-child td {{
        border-bottom: none;
    }}
    .ht-table tbody tr:hover td {{
        background: #FCF3DC;
    }}
    .ht-table tbody td:first-child {{
        font-weight: 600;
        color: #1B2A4A;
        border-left: 3px solid transparent;
    }}
    .ht-table tbody tr:hover td:first-child {{
        border-left: 3px solid #C9A84C;
    }}
    </style>
    <div class="ht-wrap">
        <div class="ht-scroll">
            <table class="ht-table">
                <thead>{header_html}</thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    
def show_pipeline_analytics(fdf: pd.DataFrame = None):
    st.markdown(SAMPLE_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="sd-hero">
        <div class="sd-eyebrow">Sample Pipeline</div>
        <div class="sd-title">Pipeline <em>Analytics</em></div>
        <div class="sd-sub">Fulfilment times, supplier performance and conversion metrics.</div>
        <div class="sd-divider"></div>
    </div>""", unsafe_allow_html=True)

    # If not passed from router, load internally as fallback
    if fdf is None:
        with st.spinner("Loading pipeline data..."):
            fdf = load_pipeline_entries()

    if fdf is None or fdf.empty:
        st.info("No pipeline data yet. Add enquiries to start seeing analytics.")
        return

    total        = len(fdf)
    handed_over  = fdf[fdf["stage"] == "handed_over"]
    in_stock_yes = fdf[fdf["in_stock"] == "Yes"]
    in_stock_no  = fdf[fdf["in_stock"] == "No"]
    purchased    = fdf[fdf["purchased"].str.strip().str.lower() == "yes"] \
                   if "purchased" in fdf.columns else pd.DataFrame()

    # ── Compute time metrics ──
    def days_between(df, col1, col2):
        c1 = pd.to_datetime(df[col1], errors="coerce")
        c2 = pd.to_datetime(df[col2], errors="coerce")
        return (c2 - c1).dt.days.dropna()

    # Total fulfilment time (enquiry → handover)
    if "enquiry_date" in fdf.columns and "handover_date" in fdf.columns:
        fulfilment = days_between(handed_over, "enquiry_date", "handover_date")
        avg_fulfilment = round(fulfilment.mean(), 1) if len(fulfilment) > 0 else None
    else:
        avg_fulfilment = None

    # Supplier response time (supplier_enquiry → shipped)
    if "supplier_enquiry_date" in fdf.columns and "supplier_shipment_date" in fdf.columns:
        sup_response = days_between(
            fdf[fdf["in_stock"] == "No"],
            "supplier_enquiry_date", "supplier_shipment_date"
        )
        avg_sup_response = round(sup_response.mean(), 1) if len(sup_response) > 0 else None
    else:
        avg_sup_response = None

    # Internal processing (stock_received → handover)
    if "stock_received_date" in fdf.columns and "handover_date" in fdf.columns:
        internal = days_between(handed_over, "stock_received_date", "handover_date")
        avg_internal = round(internal.mean(), 1) if len(internal) > 0 else None
    else:
        avg_internal = None

    conv_pct = f"{len(purchased)/len(handed_over)*100:.0f}%" \
               if len(handed_over) > 0 else "—"
    in_stock_pct = f"{len(in_stock_yes)/total*100:.0f}%" if total > 0 else "—"

    # ── KPI Cards ──
    def kpi(label, value, sub="", variant="default"):
        card_cls = f"kpi-card {variant}" if variant != "default" else "kpi-card"
        val_cls  = variant if variant != "default" else ""
        st.markdown(f"""
        <div class="{card_cls}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {val_cls}">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    c1,c3,c4 = st.columns(3)
    with c1: kpi("Total Enquiries",      total)
    #with c2: kpi("In Stock %",           in_stock_pct,      "fulfilled directly")
    with c3: kpi("Avg Fulfilment",       f"{avg_fulfilment}d" if avg_fulfilment else "—",
                                         "enquiry → handover")
    with c4: kpi("Avg Supplier Response",f"{avg_sup_response}d" if avg_sup_response else "—",
                                         "contacted → shipped")
    #with c5: kpi("Avg Internal Process", f"{avg_internal}d" if avg_internal else "—",
                                        # "received → handover")
    #with c6: kpi("Conversion %",         conv_pct,          "purchased after sample", "green")

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Row 1: Stage distribution + In Stock vs Sourced ──
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown('<div class="sd-section">Current Stage Distribution</div>',
                   unsafe_allow_html=True)
        stage_counts = fdf["stage_label"].value_counts().reset_index()
        stage_counts.columns = ["Stage", "Count"]
        stage_colors = {
            "Enquiry Received":   "#6B7A99",
            "Supplier Contacted": "#F57F17",
            "Supplier Shipped":   "#1565C0",
            "Stock Received":     "#6A1B9A",
            "Handed Over":        "#2E7D32",
            "Legacy Entry":       "#DDD5C5",
        }
        fig1 = px.pie(
            stage_counts, names="Stage", values="Count",
            color="Stage", color_discrete_map=stage_colors, hole=0.5
        )
        fig1.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(chart_layout(fig1), width = 'stretch',
                       config={"displayModeBar": False}, key="pa_stage_pie")

    with col_b:
        st.markdown('<div class="sd-section">In Stock vs Sourced from Supplier</div>',
                   unsafe_allow_html=True)
        stock_data = pd.DataFrame({
            "Type":  ["In Stock", "Sourced from Supplier"],
            "Count": [len(in_stock_yes), len(in_stock_no)]
        })
        fig2 = px.pie(
            stock_data, names="Type", values="Count",
            color="Type",
            color_discrete_map={
                "In Stock":              "#2E7D32",
                "Sourced from Supplier": "#F57F17"
            }, hole=0.5
        )
        fig2.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(chart_layout(fig2), width='stretch',
                       config={"displayModeBar": False}, key="pa_stock_pie")

    # ── Row 2: Fulfilment time distribution ──
    if len(fulfilment) > 0:
        st.markdown('<div class="sd-section">Fulfilment Time Distribution (Days)</div>',
                   unsafe_allow_html=True)
        fig3 = px.histogram(
            fulfilment, nbins=20,
            color_discrete_sequence=[CHART_COLORS[0]],
            labels={"value": "Days", "count": "Count"}
        )
        fig3.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig3, height=280), width='stretch',
                       config={"displayModeBar": False}, key="pa_fulfilment_hist")

    # ── Row 3: Supplier performance ──
    if len(in_stock_no) > 0 and "supplier" in fdf.columns:
        st.markdown('<div class="sd-section">Supplier Performance</div>',
                   unsafe_allow_html=True)

        sup_df = in_stock_no[in_stock_no["supplier"].notna()].copy()
        sup_df = sup_df[sup_df["supplier"].str.strip().ne("")]

        if not sup_df.empty and "supplier_enquiry_date" in sup_df.columns \
                and "supplier_shipment_date" in sup_df.columns:
            sup_df["response_days"] = days_between(
                sup_df, "supplier_enquiry_date", "supplier_shipment_date"
            )
            sup_perf = (
                sup_df.dropna(subset=["response_days"])
                .groupby("supplier")
                .agg(
                    Avg_Response=("response_days", "mean"),
                    Total_Orders=("supplier",       "count")
                )
                .reset_index()
                .sort_values("Avg_Response")
            )
            sup_perf["Avg_Response"] = sup_perf["Avg_Response"].round(1)
            render_html_table(
                sup_perf.rename(columns={
                    "supplier":      "Supplier",
                    "Avg_Response":  "Avg Days to Ship",
                    "Total_Orders":  "Total Orders"
                }),
                align_right_cols=["Avg Days to Ship", "Total Orders"],
                max_height=320,
            )


    # ── Row 5: Branch-wise enquiries ──
    if "branch" in fdf.columns:
        st.markdown('<div class="sd-section">Branch-wise Enquiries</div>',
                   unsafe_allow_html=True)
        branch_counts = fdf["branch"].value_counts().reset_index()
        branch_counts.columns = ["Branch", "Count"]
        fig6 = px.bar(
            branch_counts, x="Branch", y="Count",
            color_discrete_sequence=[CHART_COLORS[0]], text="Count"
        )
        fig6.update_traces(textposition="outside")
        st.plotly_chart(chart_layout(fig6, height=280), width = 'content',
                       config={"displayModeBar": False}, key="pa_branch_bar")