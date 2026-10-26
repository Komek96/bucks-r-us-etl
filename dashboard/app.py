from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data_loader import load_report


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "output"

st.set_page_config(
    page_title="Bucks-R-Us Retail Analytics",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Bucks-R-Us Retail Analytics")

st.markdown(
    "Interactive retail inventory analytics powered by "
    "PostgreSQL, Python, pandas, and Plotly."
)

refresh_col, regenerate_col = st.columns(2)

with refresh_col:
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

with regenerate_col:
    if st.button("📊 Regenerate Analytics Reports"):
        with st.spinner("Regenerating analytics reports..."):
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "reports.run_all_reports",
                    ],
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                st.error(
                    "Report regeneration timed out after 120 seconds."
                )
            except OSError as exc:
                st.error(f"Unable to run reports: {exc}")
            else:
                if result.returncode == 0:
                    st.success(
                        "Analytics reports regenerated successfully."
                    )
                    st.rerun()
                else:
                    st.error("Report regeneration failed.")
                    with st.expander("View error details"):
                        st.code(
                            result.stderr or result.stdout,
                            language="text",
                        )

st.caption(
    "Refresh reloads existing CSV files. "
    "Regenerate queries PostgreSQL and rebuilds the reports."
)

st.divider()
st.subheader("Inventory Overview")

summary_path = REPORTS_DIR / "002_store_inventory_summary.csv"

if not summary_path.is_file():
    st.error(
        "Store inventory report not found. "
        "Run: python3 -m reports.run_all_reports"
    )
    st.stop()

summary = load_report(summary_path)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Active Stores Represented",
    len(summary),
)

col2.metric(
    "Total Inventory Units",
    int(summary["total_units_on_hand"].sum()),
)

col3.metric(
    "Low-Stock Products",
    int(summary["low_stock_products"].sum()),
)

col4.metric(
    "Out-of-Stock Products",
    int(summary["out_of_stock_products"].sum()),
)

st.caption(
    "Metrics reflect the latest recorded inventory snapshots "
    "included in the generated CSV reports, not live stock levels."
)


st.divider()
st.subheader("Inventory by Product")

product_path = REPORTS_DIR / "003_product_inventory_summary.csv"

if not product_path.is_file():
    st.warning("Product inventory report not found.")
else:
    products = load_report(product_path)

    fig = px.bar(
        products.sort_values("total_units_on_hand"),
        x="total_units_on_hand",
        y="product_name",
        orientation="h",
        color="category",
        title="Current Recorded Inventory by Product",
        labels={
            "total_units_on_hand": "Units on Hand",
            "product_name": "Product",
            "category": "Category",
        },
    )

    fig.update_layout(
        yaxis_title=None,
        xaxis_title="Units on Hand",
    )

    st.plotly_chart(fig, width="stretch")


st.divider()
st.subheader("Low-Stock Alerts")

low_stock_path = REPORTS_DIR / "001_low_stock_report.csv"

if not low_stock_path.is_file():
    st.warning(
        "Low-stock report not found. "
        "Run the reporting pipeline to generate it."
    )
else:
    low_stock = load_report(low_stock_path)

    if low_stock.empty:
        st.success("No low-stock products detected.")
    else:
        st.warning(
            f"{len(low_stock)} low-stock store-product "
            "record(s) require attention."
        )

        display_columns = [
            "store_id",
            "product_name",
            "category",
            "quantity_on_hand",
            "inventory_timestamp",
        ]

        st.dataframe(
            low_stock[display_columns],
            width="stretch",
            hide_index=True,
        )


st.divider()
st.subheader("Closed-Store Inventory Reconciliation")

reconciliation_path = (
    REPORTS_DIR / "005_closed_store_reconciliation.csv"
)

if not reconciliation_path.is_file():
    st.warning(
        "Closed-store reconciliation report not found. "
        "Generate the analytics reports first."
    )
else:
    reconciliation = load_report(reconciliation_path)

    if reconciliation.empty:
        st.success(
            "No closed-store inventory reconciliation "
            "records require review."
        )
    else:
        total_units = int(
            reconciliation["last_recorded_units"].sum()
        )

        st.warning(
            f"{len(reconciliation)} closed-store record(s) "
            f"require review, representing {total_units:,} "
            "last-recorded inventory units."
        )

        display_columns = [
            "store_id",
            "city",
            "state",
            "closed_at",
            "products_needing_review",
            "last_recorded_units",
            "latest_inventory_snapshot",
        ]

        st.dataframe(
            reconciliation[display_columns],
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "These are historical inventory records requiring "
            "reconciliation, not proof of missing merchandise."
        )


st.divider()
st.subheader("Inventory by Store")

store_path = REPORTS_DIR / "002_store_inventory_summary.csv"

if not store_path.is_file():
    st.warning("Store inventory summary report not found.")
else:
    stores = load_report(store_path)

    if stores.empty:
        st.info("No active-store inventory records available.")
    else:
        fig_stores = px.bar(
            stores.sort_values("total_units_on_hand"),
            x="store_id",
            y="total_units_on_hand",
            color="city",
            hover_data=[
                "state",
                "products_tracked",
                "low_stock_products",
                "out_of_stock_products",
            ],
            title="Recorded Inventory Units by Active Store",
            labels={
                "store_id": "Store",
                "total_units_on_hand": "Units on Hand",
                "city": "City",
            },
        )

        fig_stores.update_layout(
            xaxis_title="Store",
            yaxis_title="Units on Hand",
        )

        st.plotly_chart(
            fig_stores,
            width="stretch",
        )


st.divider()
st.subheader("Inventory by Category")

category_path = REPORTS_DIR / "003_product_inventory_summary.csv"

if not category_path.is_file():
    st.warning("Product inventory summary report not found.")
else:
    category_products = load_report(category_path)

    if category_products.empty:
        st.info("No product inventory records available.")
    else:
        category_summary = (
            category_products
            .groupby("category", as_index=False, dropna=False)
            ["total_units_on_hand"]
            .sum()
        )

        fig_categories = px.pie(
            category_summary,
            names="category",
            values="total_units_on_hand",
            hole=0.45,
            title="Share of Recorded Inventory by Category",
        )

        fig_categories.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate=(
                "%{label}<br>"
                "Units: %{value}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )

        st.plotly_chart(
            fig_categories,
            width="stretch",
        )

        st.caption(
            "Category shares are based on recorded inventory "
            "units, not sales or revenue."
        )


st.divider()
st.subheader("Product Explorer")

explorer_path = REPORTS_DIR / "003_product_inventory_summary.csv"

if not explorer_path.is_file():
    st.warning("Product inventory report not found.")
else:
    explorer_products = load_report(explorer_path)

    if explorer_products.empty:
        st.info("No product inventory records available.")
    else:
        categories = sorted(
            explorer_products["category"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_category = st.selectbox(
            "Filter by Product Category",
            options=["All Categories"] + categories,
        )

        if selected_category == "All Categories":
            filtered_products = explorer_products
        else:
            filtered_products = explorer_products[
                explorer_products["category"]
                == selected_category
            ]

        search_term = st.text_input(
            "Search by Product Name or SKU",
            placeholder="e.g. Tomato or SKU-30117",
        ).strip()

        if search_term:
            matches_name = (
                filtered_products["product_name"]
                .fillna("")
                .astype(str)
                .str.contains(search_term, case=False, regex=False)
            )

            matches_sku = (
                filtered_products["sku"]
                .fillna("")
                .astype(str)
                .str.contains(search_term, case=False, regex=False)
            )

            filtered_products = filtered_products[
                matches_name | matches_sku
            ]

        st.metric(
            "Products Matching Filter",
            len(filtered_products),
        )

        export_columns = [
            "sku",
            "product_name",
            "category",
            "stores_tracked",
            "total_units_on_hand",
        ]

        export_data = filtered_products[export_columns]

        st.dataframe(
            export_data,
            width="stretch",
            hide_index=True,
        )

        csv_data = export_data.to_csv(index=False)

        st.download_button(
            label="Download Filtered Inventory (CSV)",
            data=csv_data,
            file_name="bucks_r_us_filtered_inventory.csv",
            mime="text/csv",
            disabled=export_data.empty,
        )


st.divider()
st.subheader("Report Data Freshness")

report_files = sorted(REPORTS_DIR.glob("*.csv"))

if not report_files:
    st.warning("No generated CSV reports were found.")
else:
    report_details = []

    for report_file in report_files:
        modified_time = datetime.fromtimestamp(
            report_file.stat().st_mtime,
            tz=timezone.utc,
        )

        report_details.append({
            "Report": report_file.name,
            "Last Modified (UTC)": modified_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        })

    freshness_df = pd.DataFrame(report_details)

    st.dataframe(
        freshness_df,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Timestamps reflect CSV file modification times, "
        "not the original inventory collection times. "
        "Reports are refreshed by rerunning the reporting pipeline."
    )
