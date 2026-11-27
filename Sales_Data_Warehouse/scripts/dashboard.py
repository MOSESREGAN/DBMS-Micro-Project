
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="regan007",
        database="sales_analytics"
    )

    query = """
    SELECT
        f.order_id,
        c.customer_name,
        p.product_name,
        p.category,
        s.store_name,
        s.region,
        d.full_date,
        d.month_name,
        d.quarter,
        d.year,
        f.quantity,
        f.unit_price,
        f.discount_amount,
        f.total_amount,
        f.cost_amount,
        f.profit_amount
    FROM fact_sales f
    JOIN dim_customer c
        ON f.customer_key = c.customer_key
    JOIN dim_product p
        ON f.product_key = p.product_key
    JOIN dim_store s
        ON f.store_key = s.store_key
    JOIN dim_date d
        ON f.date_key = d.date_key
    """

    df = pd.read_sql(query, connection)
    connection.close()

    df["full_date"] = pd.to_datetime(df["full_date"])

    return df


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}
[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #e5e7eb;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
[data-testid="stSidebar"] {
    background-color: #eef2f7;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Sales Analytics Dashboard")
st.sidebar.title("📊 Sales Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Sales Analysis",
        "Product Analysis",
        "Store & Region Analysis",
        "Customer Analysis",
        "Business Insights"
    ]
)
if page == "Overview":
    st.header("📊 Sales Overview")

st.caption("Enterprise Sales Intelligence | MySQL Data Warehouse")
st.caption("MySQL Data Warehouse | Python | Streamlit | Plotly")

try:
    df = load_data()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

    # --------------------------------------------------
# REFRESH DATABASE
# --------------------------------------------------

if st.sidebar.button("🔄 Refresh Data"):
    load_data.clear()
    st.rerun()

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("Dashboard Filters")

min_date = df["full_date"].min().date()
max_date = df["full_date"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

categories = st.sidebar.multiselect(
    "Select Category",
    options=sorted(df["category"].unique()),
    default=sorted(df["category"].unique())
)

regions = st.sidebar.multiselect(
    "Select Region",
    options=sorted(df["region"].unique()),
    default=sorted(df["region"].unique())
)

# --------------------------------------------------
# FILTER DATA
# --------------------------------------------------

filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = filtered_df[
        (filtered_df["full_date"].dt.date >= start_date) &
        (filtered_df["full_date"].dt.date <= end_date)
    ]

filtered_df = filtered_df[
    (filtered_df["category"].isin(categories)) &
    (filtered_df["region"].isin(regions))
]

if filtered_df.empty:
    st.warning("No sales records found for the selected filters.")
    st.stop()

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

# Calculate metrics for use across dashboard pages
total_revenue = filtered_df["total_amount"].sum()
total_profit = filtered_df["profit_amount"].sum()
total_orders = filtered_df["order_id"].nunique()

profit_margin = (
    total_profit / total_revenue * 100
    if total_revenue else 0
)

# Display KPIs only on Overview page
if page == "Overview":

    st.subheader("Business Performance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Total Profit", f"₹{total_profit:,.0f}")
    col3.metric("Total Orders", f"{total_orders:,}")
    col4.metric("Profit Margin", f"{profit_margin:.2f}%")

    st.divider()

    if page == "Sales Analysis":
     st.header("📈 Sales Analysis")
# --------------------------------------------------
# MONTHLY SALES TREND
# --------------------------------------------------

st.subheader("Monthly Sales Analysis")

monthly = (
    filtered_df.groupby(
        pd.Grouper(key="full_date", freq="MS")
    )
    .agg(
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum")
    )
    .reset_index()
)

fig_monthly = px.line(
    monthly,
    x="full_date",
    y=["Revenue", "Profit"],
    markers=True,
    title="Monthly Revenue and Profit Trend",
    labels={
        "full_date": "Month",
        "value": "Amount (₹)",
        "variable": "Metric"
    }
)

st.plotly_chart(fig_monthly, use_container_width=True)

# --------------------------------------------------
# QUARTER-WISE SALES ANALYSIS
# --------------------------------------------------

st.subheader("Quarter-wise Sales Analysis")

quarter_data = (
    filtered_df.groupby("quarter", as_index=False)
    .agg(
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum"),
        Orders=("order_id", "nunique")
    )
)

quarter_data["quarter"] = "Q" + quarter_data["quarter"].astype(str)

fig_quarter = px.bar(
    quarter_data,
    x="quarter",
    y=["Revenue", "Profit"],
    barmode="group",
    title="Quarterly Revenue and Profit",
    labels={
        "quarter": "Quarter",
        "value": "Amount (₹)",
        "variable": "Metric"
    }
)

st.plotly_chart(fig_quarter, use_container_width=True)

st.dataframe(quarter_data, hide_index=True)

if page == "Product Analysis":
    st.header("📦 Product Analysis")

# --------------------------------------------------
# CATEGORY AND REGION ANALYSIS
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    category_data = (
        filtered_df.groupby("category", as_index=False)
        .agg(Revenue=("total_amount", "sum"))
    )

    fig_category = px.bar(
        category_data,
        x="category",
        y="Revenue",
        color="category",
        title="Category-wise Revenue",
        labels={"category": "Product Category", "Revenue": "Revenue (₹)"}
    )

    st.plotly_chart(fig_category, use_container_width=True)

    if page == "Store & Region Analysis":
        st.header("🏬 Store & Region Analysis")

with col2:
    region_data = (
        filtered_df.groupby("region", as_index=False)
        .agg(Revenue=("total_amount", "sum"))
    )

    fig_region = px.pie(
        region_data,
        names="region",
        values="Revenue",
        title="Region-wise Revenue",
        hole=0.4
    )

    st.plotly_chart(fig_region, use_container_width=True)

    # --------------------------------------------------
# STORE PERFORMANCE
# --------------------------------------------------

st.subheader("Store Performance Analysis")

store_data = (
    filtered_df.groupby("store_name", as_index=False)
    .agg(
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum"),
        Orders=("order_id", "nunique")
    )
    .sort_values("Revenue", ascending=False)
)

fig_store = px.bar(
    store_data,
    x="store_name",
    y="Revenue",
    color="Profit",
    title="Store-wise Revenue and Profit",
    hover_data=["Orders", "Profit"],
    labels={
        "store_name": "Store",
        "Revenue": "Revenue (₹)",
        "Profit": "Profit (₹)"
    }
)

st.plotly_chart(fig_store, use_container_width=True)

# --------------------------------------------------
# CATEGORY-WISE PROFIT MARGIN
# --------------------------------------------------

st.subheader("Category-wise Profit Margin")

margin_data = (
    filtered_df.groupby("category", as_index=False)
    .agg(
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum")
    )
)

margin_data["Profit_Margin"] = (
    margin_data["Profit"] / margin_data["Revenue"] * 100
)

fig_margin = px.bar(
    margin_data,
    x="category",
    y="Profit_Margin",
    color="Profit_Margin",
    text=margin_data["Profit_Margin"].round(2),
    title="Profit Margin by Product Category",
    labels={
        "category": "Category",
        "Profit_Margin": "Profit Margin (%)"
    }
)

fig_margin.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig_margin, use_container_width=True)

# --------------------------------------------------
# TOP SELLING PRODUCTS
# --------------------------------------------------

st.subheader("Top Selling Products")

product_data = (
    filtered_df.groupby("product_name", as_index=False)
    .agg(
        Quantity_Sold=("quantity", "sum"),
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum")
    )
    .sort_values("Revenue", ascending=False)
    .head(5)
)

fig_products = px.bar(
    product_data,
    x="Revenue",
    y="product_name",
    orientation="h",
    color="Revenue",
    title="Top 5 Products by Revenue",
    labels={"product_name": "Product", "Revenue": "Revenue (₹)"}
)

fig_products.update_layout(yaxis={"categoryorder": "total ascending"})

st.plotly_chart(fig_products, use_container_width=True)

if page == "Customer Analysis":
    st.header("👥 Customer Analysis")

# --------------------------------------------------
# TOP 5 CUSTOMERS
# --------------------------------------------------

st.subheader("Top 5 Customers by Revenue")

customer_data = (   
    filtered_df.groupby("customer_name", as_index=False)
    .agg(
        Revenue=("total_amount", "sum"),
        Profit=("profit_amount", "sum"),
        Orders=("order_id", "nunique")
    )
    .sort_values("Revenue", ascending=False)
    .head(5)
)

fig_customers = px.bar(
    customer_data,
    x="Revenue",
    y="customer_name",
    orientation="h",
    color="Revenue",
    title="Top 5 Customers",
    hover_data=["Profit", "Orders"],
    labels={
        "customer_name": "Customer",
        "Revenue": "Revenue (₹)"
    }
)

fig_customers.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(fig_customers, use_container_width=True)

if page == "Business Insights":
    st.header("💡 Business Insights")
# --------------------------------------------------
# AUTOMATED BUSINESS INSIGHTS
# --------------------------------------------------

st.subheader("💡 Business Insights")

category_insights = (
    filtered_df.groupby("category")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

region_insights = (
    filtered_df.groupby("region")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

product_insights = (
    filtered_df.groupby("product_name")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Top Category",
    category_insights.index[0],
    f"₹{category_insights.iloc[0]:,.0f} revenue"
)

col2.metric(
    "Best Region",
    region_insights.index[0],
    f"₹{region_insights.iloc[0]:,.0f} revenue"
)

col3.metric(
    "Top Product",
    product_insights.index[0],
    f"₹{product_insights.iloc[0]:,.0f} revenue"
)

st.info(
    f"Overall profit margin for the selected data is "
    f"{profit_margin:.2f}%."
)

# --------------------------------------------------
# SALES PERFORMANCE SUMMARY
# --------------------------------------------------

st.subheader("📈 Sales Performance Summary")

summary_data = pd.DataFrame({
    "Financial Metric": ["Revenue", "Cost", "Profit"],
    "Amount (₹)": [
        filtered_df["total_amount"].sum(),
        filtered_df["cost_amount"].sum(),
        filtered_df["profit_amount"].sum()
    ]
})

fig_summary = px.bar(
    summary_data,
    x="Financial Metric",
    y="Amount (₹)",
    color="Financial Metric",
    text_auto=",.0f",
    title="Revenue vs Cost vs Profit"
)

st.plotly_chart(fig_summary, use_container_width=True)

if page == "Sales Analysis":
    st.subheader("📋 Detailed Sales Records")
# --------------------------------------------------
# SALES DATA TABLE
# --------------------------------------------------

st.subheader("Detailed Sales Records")

st.dataframe(
    filtered_df[
        [
            "order_id",
            "customer_name",
            "product_name",
            "category",
            "store_name",
            "region",
            "full_date",
            "quantity",
            "total_amount",
            "profit_amount"
        ]
    ],
    use_container_width=True,
    hide_index=True
)
st.download_button(
    label="📥 Download Sales Report",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="sales_analytics_report.csv",
    mime="text/csv"
)

st.caption("Sales Data Warehouse | Interactive Analytics Dashboard")
