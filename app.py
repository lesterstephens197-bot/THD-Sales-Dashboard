import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面基础配置
st.set_page_config(
    page_title="电商销售数据分析看板",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 1. 数据加载与预处理（解决 UploadedFile 无法被 Hash 的报错）
# ------------------------------------------------------------------------------
@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_data(file):
    if file is not None:
        df = pd.read_csv(file)
    else:
        # 若未上传文件，生成模拟数据供演示
        data = {
            "Line Status": ["Shipped", "Shipped", "Cancelled", "Shipped", "Shipped"] * 20,
            "PO Number": [f"PO{1000+i}" for i in range(100)],
            "Order Date": pd.date_range(end=datetime.today(), periods=100, freq="D"),
            "Merchant SKU": [f"MSKU-{i%5+1}" for i in range(100)],
            "Vendor SKU": [f"VSKU-{i%5+1}" for i in range(100)],
            "OMS ID": [f"OMS-{100+i}" for i in range(100)],
            "产品名称": [f"产品 {chr(65 + i%5)}" for i in range(100)],
            "品牌": ["Brand A", "Brand B"] * 50,
            "产品SKU": [f"SKU-00{i%5+1}" for i in range(100)],
            "产品状态": ["在售"] * 100,
            "运营": ["张三", "李四", "王五"] * 33 + ["张三"],
            "Description": ["商品描述..."] * 100,
            "Unit Cost": [20.0, 35.5, 15.0, 50.0, 10.5] * 20,
            "Unit Cost Currency": ["USD"] * 100,
            "Quantity": [1, 2, 1, 3, 5] * 20,
            "Total Cost": [20.0, 71.0, 15.0, 150.0, 52.5] * 20,
            "ShipTo Name": ["Customer"] * 100,
            "Customer Order Number": [f"ORD-{5000+i}" for i in range(100)],
            "ShipTo Address1": ["Street 1"] * 100,
            "ShipTo Address2": [""] * 100,
            "ShipTo City": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"] * 20,
            "ShipTo State": ["NY", "CA", "IL", "TX", "AZ"] * 20,
            "ShipTo Country": ["US"] * 100,
            "ShipTo Postal Code": ["10001"] * 100,
            "ShipTo Day Phone": ["123456789"] * 100
        }
        df = pd.DataFrame(data)

    # 数据类型转换与清洗
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Total Cost"] = pd.to_numeric(df["Total Cost"], errors="coerce").fillna(0)
    df["Unit Cost"] = pd.to_numeric(df["Unit Cost"], errors="coerce").fillna(0)
    
    return df

# ------------------------------------------------------------------------------
# 2. 侧边栏：文件上传与全局筛选
# ------------------------------------------------------------------------------
st.sidebar.title("🔍 数据筛选与设置")
uploaded_file = st.sidebar.file_uploader("上传 CSV 销售数据", type=["csv"])

df_raw = load_data(uploaded_file)

# 运营人员筛选
all_operators = ["全部"] + list(df_raw["运营"].dropna().unique())
selected_operator = st.sidebar.selectbox("筛选运营人员", all_operators)

# 日期筛选
min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()
date_range = st.sidebar.date_input("选择订单日期范围", [min_date, max_date], min_value=min_date, max_value=max_date)

# 数据过滤逻辑
df = df_raw.copy()

# 剔除已取消的订单（可按需调整）
if "Line Status" in df.columns:
    df = df[df["Line Status"] != "Cancelled"]

if selected_operator != "全部":
    df = df[df["运营"] == selected_operator]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df["Order Date"].dt.date >= start_date) & (df["Order Date"].dt.date <= end_date)]

# 页面标题
st.title("📈 电商销售数据可视化看板")
st.markdown("---")

# ------------------------------------------------------------------------------
# 3. Tab 标签页布局
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. 总数据看板", 
    "📦 2. 产品SKU分析", 
    "👤 3. 运营绩效看板", 
    "🗺️ 4. 全美销量分布"
])

# ==============================================================================
# 模块 1：总数据看板
# ==============================================================================
with tab1:
    st.header("总数据概览")
    
    total_sales = df["Total Cost"].sum()
    total_qty = df["Quantity"].sum()
    total_orders = df["Customer Order Number"].nunique()
    aov = total_sales / total_orders if total_orders > 0 else 0  # 平均客单价

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总销售额 (USD)", f"${total_sales:,.2f}")
    col2.metric("总销量 (件)", f"{total_qty:,}")
    col3.metric("总单量 (笔)", f"{total_orders:,}")
    col4.metric("平均客单价 (AOV)", f"${aov:,.2f}")

    st.markdown("### 销售趋势变化")
    trend_type = st.radio("按时间维度查看趋势", ["按日", "按周", "按月"], horizontal=True)
    
    if trend_type == "按日":
        df_trend = df.groupby(df["Order Date"].dt.date).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()
    elif trend_type == "按周":
        df_trend = df.groupby(df["Order Date"].dt.to_period("W").dt.start_time).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()
    else:
        df_trend = df.groupby(df["Order Date"].dt.to_period("M").dt.start_time).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=df_trend["Order Date"], y=df_trend["Total Cost"], name="销售额 ($)", mode='lines+markers', yaxis="y1"))
    fig_trend.add_trace(go.Bar(x=df_trend["Order Date"], y=df_trend["Quantity"], name="销量 (件)", opacity=0.4, yaxis="y2"))

    fig_trend.update_layout(
        title="销售额与销量趋势",
        xaxis_title="日期",
        yaxis=dict(title="销售额 ($)"),
        yaxis2=dict(title="销量 (件)", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ==============================================================================
# 模块 2：按照产品SKU维度
# ==============================================================================
with tab2:
    st.header("产品 SKU 维度的深入分析")

    if not df.empty:
        latest_date = df["Order Date"].max()
        d7_cutoff = latest_date - timedelta(days=7)
        d15_cutoff = latest_date - timedelta(days=15)

        sku_stats = []
        for sku, group in df.groupby("产品SKU"):
            prod_name = group["产品名称"].iloc[0] if "产品名称" in group.columns else "-"
            total_sales_sku = group["Total Cost"].sum()
            total_qty_sku = group["Quantity"].sum()
            
            # 动销天数 (有销售记录的不同天数)
            active_days = group["Order Date"].dt.date.nunique()
            # 日均销量 (总销量 / 动销天数)
            avg_daily_qty = round(total_qty_sku / active_days, 2) if active_days > 0 else 0
            
            # 近 7 天 & 近 15 天销量
            qty_7d = group[group["Order Date"] >= d7_cutoff]["Quantity"].sum()
            qty_15d = group[group["Order Date"] >= d15_cutoff]["Quantity"].sum()

            sku_stats.append({
                "产品SKU": sku,
                "产品名称": prod_name,
                "总销售额 ($)": total_sales_sku,
                "总销量": total_qty_sku,
                "动销天数": active_days,
                "日均销量": avg_daily_qty,
                "近7天销量": qty_7d,
                "近15天销量": qty_15d
            })

        df_sku_summary = pd.DataFrame(sku_stats).sort_values(by="总销量", ascending=False)
        df_sku_summary["销量排名"] = range(1, len(df_sku_summary) + 1)
        
        cols_order = ["销量排名", "产品SKU", "产品名称", "总销量", "总销售额 ($)", "动销天数", "日均销量", "近7天销量", "近15天销量"]
        df_sku_summary = df_sku_summary[cols_order]

        st.subheader("🏆 SKU 综合排行榜")
        st.dataframe(df_sku_summary, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔍 单个 SKU 历史销量趋势查询")
        
        sku_list = df["产品SKU"].unique()
        selected_sku = st.selectbox("搜索或选择产品 SKU:", sku_list)

        if selected_sku:
            df_single_sku = df[df["产品SKU"] == selected_sku]
            sku_daily = df_single_sku.groupby(df_single_sku["Order Date"].dt.date)["Quantity"].sum().reset_index()
            
            fig_sku = px.line(
                sku_daily, 
                x="Order Date", 
                y="Quantity", 
                title=f"SKU: {selected_sku} 日销量变化趋势",
                markers=True,
                labels={"Order Date": "日期", "Quantity": "销量 (件)"}
            )
            st.plotly_chart(fig_sku, use_container_width=True)
    else:
        st.info("当前筛选条件下无数据。")

# ==============================================================================
# 模块 3：按照运营维度的数据看板
# ==============================================================================
with tab3:
    st.header("运营人员业绩看板")

    if not df.empty and "运营" in df.columns:
        op_summary = df.groupby("运营").agg(
            总销售额=("Total Cost", "sum"),
            总销量=("Quantity", "sum"),
            订单总数=("Customer Order Number", "nunique"),
            负责SKU数=("产品SKU", "nunique")
        ).reset_index()

        op_summary["客单价"] = (op_summary["总销售额"] / op_summary["订单总数"]).round(2)
        op_summary = op_summary.sort_values(by="总销售额", ascending=False)

        st.subheader("👥 运营绩效汇总表")
        st.dataframe(op_summary, use_container_width=True, hide_index=True)

        col_op1, col_op2 = st.columns(2)
        with col_op1:
            fig_op_sales = px.bar(
                op_summary, 
                x="运营", 
                y="总销售额", 
                text_auto=".2s",
                title="各运营人员总销售额对比",
                color="运营"
            )
            st.plotly_chart(fig_op_sales, use_container_width=True)

        with col_op2:
            fig_op_qty = px.pie(
                op_summary, 
                names="运营", 
                values="总销量", 
                title="各运营人员总销量贡献占比",
                hole=0.4
            )
            st.plotly_chart(fig_op_qty, use_container_width=True)
    else:
        st.info("当前筛选条件下无数据。")

# ==============================================================================
# 模块 4：全美销量地图分布
# ==============================================================================
with tab4:
    st.header("全美各州销量地理分布")

    if not df.empty and "ShipTo State" in df.columns:
        state_df = df.groupby("ShipTo State").agg(
            总销量=("Quantity", "sum"),
            总销售额=("Total Cost", "sum"),
            订单数=("Customer Order Number", "nunique")
        ).reset_index()

        st.subheader("🗺️ 美国地图热力分布 (Choropleth Map)")
        
        fig_map = px.choropleth(
            state_df,
            locations="ShipTo State", 
            locationmode="USA-states",
            color="总销量",
            scope="usa",
            hover_data=["ShipTo State", "总销量", "总销售额", "订单数"],
            color_continuous_scale="Reds",
            title="全美各州订单销量分布图"
        )
        
        fig_map.update_layout(
            geo=dict(lakecolor='rgb(255, 255, 255)'),
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("📋 各州数据明细排名")
        state_df_sorted = state_df.sort_values(by="总销量", ascending=False)
        st.dataframe(state_df_sorted, use_container_width=True, hide_index=True)
    else:
        st.info("当前筛选条件下无州份数据。")
