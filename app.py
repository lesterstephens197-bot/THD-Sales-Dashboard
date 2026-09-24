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
# 1. 数据加载与预处理
# ------------------------------------------------------------------------------
@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_data(file):
    if file is not None:
        df = pd.read_excel(file)
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
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    if "Total Cost" in df.columns:
        df["Total Cost"] = pd.to_numeric(df["Total Cost"], errors="coerce").fillna(0)
    if "Unit Cost" in df.columns:
        df["Unit Cost"] = pd.to_numeric(df["Unit Cost"], errors="coerce").fillna(0)
    
    return df

# ------------------------------------------------------------------------------
# 2. 侧边栏：文件上传与全局筛选
# ------------------------------------------------------------------------------
st.sidebar.title("🔍 数据筛选与设置")
uploaded_file = st.sidebar.file_uploader("上传 Excel 销售数据", type=["xlsx", "xls"])

df_raw = load_data(uploaded_file)

# 运营人员筛选
all_operators = ["全部"] + list(df_raw["运营"].dropna().unique()) if "运营" in df_raw.columns else ["全部"]
selected_operator = st.sidebar.selectbox("筛选运营人员", all_operators)

# 日期筛选：如果数据包含有效的 Order Date
valid_dates = df_raw["Order Date"].dropna() if "Order Date" in df_raw.columns else pd.Series()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input("选择订单日期范围", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = None

# 数据过滤逻辑
df = df_raw.copy()

# 1. 运营人员过滤
if selected_operator != "全部" and "运营" in df.columns:
    df = df[df["运营"] == selected_operator]

# 2. 日期范围过滤
if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and "Order Date" in df.columns:
    start_date, end_date = date_range
    date_mask = df["Order Date"].dt.date.between(start_date, end_date) | df["Order Date"].isna()
    df = df[date_mask]

# 单量统计逻辑
def get_unique_orders_count(data_frame):
    return len(data_frame)

# 页面标题
st.title("📈 电商销售数据可视化看板")
st.markdown("---")

# ------------------------------------------------------------------------------
# 3. Tab 标签页布局（新增 Tab 5：7天环比对比）
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 1. 总数据看板", 
    "📦 2. 产品SKU分析", 
    "👤 3. 运营绩效看板", 
    "🗺️ 4. 全美销量分布",
    "🔄 5. 7天 vs 7天对比"
])

# ==============================================================================
# 模块 1：总数据看板
# ==============================================================================
with tab1:
    st.header("总数据概览")
    
    total_sales = df["Total Cost"].sum() if "Total Cost" in df.columns else 0.0
    total_qty = df["Quantity"].sum() if "Quantity" in df.columns else 0
    total_orders = get_unique_orders_count(df)
    
    # 客单价 = 总销售额 ÷ 总销量
    aov = total_sales / total_qty if total_qty > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总销售额 (USD)", f"${total_sales:,.2f}")
    col2.metric("总销量 (件)", f"{total_qty:,}")
    col3.metric("总单量 (笔)", f"{total_orders:,}")
    col4.metric("平均客单价 (AOV)", f"${aov:,.2f}")

    if "Order Date" in df.columns and not df["Order Date"].dropna().empty:
        st.markdown("### 销售趋势变化")
        trend_type = st.radio("按时间维度查看趋势", ["按日", "按周", "按月"], horizontal=True)
        
        df_valid_date = df.dropna(subset=["Order Date"])
        if trend_type == "按日":
            df_trend = df_valid_date.groupby(df_valid_date["Order Date"].dt.date).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()
        elif trend_type == "按周":
            df_trend = df_valid_date.groupby(df_valid_date["Order Date"].dt.to_period("W").dt.start_time).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()
        else:
            df_trend = df_valid_date.groupby(df_valid_date["Order Date"].dt.to_period("M").dt.start_time).agg({"Total Cost": "sum", "Quantity": "sum"}).reset_index()

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

    if not df.empty and "产品SKU" in df.columns:
        valid_dates = df["Order Date"].dropna() if "Order Date" in df.columns else pd.Series()
        latest_date = valid_dates.max() if not valid_dates.empty else datetime.today()
        d7_cutoff = latest_date - timedelta(days=7)
        d15_cutoff = latest_date - timedelta(days=15)

        sku_stats = []
        for sku, group in df.groupby("产品SKU"):
            prod_name = group["产品名称"].iloc[0] if "产品名称" in group.columns else "-"
            total_sales_sku = group["Total Cost"].sum() if "Total Cost" in group.columns else 0
            total_qty_sku = group["Quantity"].sum() if "Quantity" in group.columns else 0
            
            # 动销天数
            active_days = group["Order Date"].dt.date.nunique() if "Order Date" in group.columns else 1
            avg_daily_qty = round(total_qty_sku / active_days, 2) if active_days > 0 else 0
            
            # 近 7 天 & 近 15 天销量
            if "Order Date" in group.columns:
                qty_7d = group[group["Order Date"] >= d7_cutoff]["Quantity"].sum()
                qty_15d = group[group["Order Date"] >= d15_cutoff]["Quantity"].sum()
            else:
                qty_7d, qty_15d = 0, 0

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

        if selected_sku and "Order Date" in df.columns:
            df_single_sku = df[df["产品SKU"] == selected_sku].dropna(subset=["Order Date"])
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
        st.info("当前筛选条件下无 SKU 数据。")

# ==============================================================================
# 模块 3：按照运营维度的数据看板
# ==============================================================================
with tab3:
    st.header("运营人员业绩看板")

    if not df.empty and "运营" in df.columns:
        op_list = []
        for op, group in df.groupby("运营"):
            op_sales = group["Total Cost"].sum() if "Total Cost" in group.columns else 0
            op_qty = group["Quantity"].sum() if "Quantity" in group.columns else 0
            op_orders = get_unique_orders_count(group)
            op_skus = group["产品SKU"].nunique() if "产品SKU" in group.columns else 0
            
            # 客单价 = 销售额 ÷ 销量
            op_aov = round(op_sales / op_qty, 2) if op_qty > 0 else 0

            op_list.append({
                "运营": op,
                "总销售额": op_sales,
                "总销量": op_qty,
                "订单总数": op_orders,
                "客单价": op_aov,
                "负责SKU数": op_skus
            })

        op_summary = pd.DataFrame(op_list).sort_values(by="总销售额", ascending=False)

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
        st.info("当前筛选条件下无运营人员数据。")

# ==============================================================================
# 模块 4：全美销量地图分布
# ==============================================================================
with tab4:
    st.header("全美各州销量地理分布")

    if not df.empty and "ShipTo State" in df.columns:
        state_list = []
        for state, group in df.groupby("ShipTo State"):
            state_qty = group["Quantity"].sum() if "Quantity" in group.columns else 0
            state_sales = group["Total Cost"].sum() if "Total Cost" in group.columns else 0
            state_orders = get_unique_orders_count(group)

            state_list.append({
                "ShipTo State": state,
                "总销量": state_qty,
                "总销售额": state_sales,
                "订单数": state_orders
            })

        state_df = pd.DataFrame(state_list)

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

# ==============================================================================
# 模块 5：前 7 天与后 7 天销量对比分析（新增）
# ==============================================================================
with tab5:
    st.header("🔄 前 7 天 vs 后 7 天 销量环比对比")

    df_valid = df.dropna(subset=["Order Date"]) if "Order Date" in df.columns else pd.DataFrame()

    if not df_valid.empty:
        # 以数据中最晚日期作为基准日期
        max_dt = df_valid["Order Date"].max().date()
        
        # 1. 后 7 天（最近 7 天，含今天/最高日期）
        recent_7_start = max_dt - timedelta(days=6)
        recent_7_end = max_dt
        
        # 2. 前 7 天（较早 7 天）
        prior_7_start = max_dt - timedelta(days=13)
        prior_7_end = max_dt - timedelta(days=7)

        # 提示当前对比的时间区间
        st.info(f"📅 **对比区间展示**：\n"
                f"- **【前 7 天】**：`{prior_7_start}` 至 `{prior_7_end}`\n"
                f"- **【后 7 天】**：`{recent_7_start}` 至 `{recent_7_end}`")

        # 数据切片
        mask_prior = df_valid["Order Date"].dt.date.between(prior_7_start, prior_7_end)
        mask_recent = df_valid["Order Date"].dt.date.between(recent_7_start, recent_7_end)

        df_prior = df_valid[mask_prior]
        df_recent = df_valid[mask_recent]

        # ------------------ 1. 核心指标对比卡片 ------------------
        p_sales = df_prior["Total Cost"].sum()
        r_sales = df_recent["Total Cost"].sum()
        sales_diff = r_sales - p_sales
        sales_pct = (sales_diff / p_sales * 100) if p_sales > 0 else 0

        p_qty = df_prior["Quantity"].sum()
        r_qty = df_recent["Quantity"].sum()
        qty_diff = r_qty - p_qty
        qty_pct = (qty_diff / p_qty * 100) if p_qty > 0 else 0

        p_orders = get_unique_orders_count(df_prior)
        r_orders = get_unique_orders_count(df_recent)
        orders_diff = r_orders - p_orders
        orders_pct = (orders_diff / p_orders * 100) if p_orders > 0 else 0

        p_aov = p_sales / p_qty if p_qty > 0 else 0
        r_aov = r_sales / r_qty if r_qty > 0 else 0
        aov_diff = r_aov - p_aov
        aov_pct = (aov_diff / p_aov * 100) if p_aov > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("后7天 销售额 (\()", f"\){r_sales:,.2f}", f"{sales_pct:+.1f}\% (${sales_diff:+,.2f})")
        c2.metric("后7天 销量 (件)", f"{r_qty:,}", f"{qty_pct:+.1f}% ({qty_diff:+,}件)")
        c3.metric("后7天 单量 (笔)", f"{r_orders:,}", f"{orders_pct:+.1f}% ({orders_diff:+,}笔)")
        c4.metric("后7天 客单价 (\()", f"\){r_aov:,.2f}", f"{aov_pct:+.1f}\% (${aov_diff:+,.2f})")

        st.markdown("---")

        # ------------------ 2. SKU 维度升降对比表 ------------------
        st.subheader("📦 SKU 销量升降变化表")

        if "产品SKU" in df_valid.columns:
            # 前7天按SKU统计
            prior_sku = df_prior.groupby("产品SKU").agg(
                前7天销量=("Quantity", "sum"),
                前7天销售额=("Total Cost", "sum")
            ).reset_index()

            # 后7天按SKU统计
            recent_sku = df_recent.groupby("产品SKU").agg(
                后7天销量=("Quantity", "sum"),
                后7天销售额=("Total Cost", "sum")
            ).reset_index()

            # 合并数据
            sku_diff_df = pd.merge(recent_sku, prior_sku, on="产品SKU", how="outer").fillna(0)
            
            sku_diff_df["销量变化(件)"] = sku_diff_df["后7天销量"] - sku_diff_df["前7天销量"]
            sku_diff_df["销量增长率(%)"] = sku_diff_df.apply(
                lambda row: (row["销量变化(件)"] / row["前7天销量"] * 100) if row["前7天销量"] > 0 else (100.0 if row["后7天销量"] > 0 else 0.0), 
                axis=1
            )
            sku_diff_df["销售额变化($)"] = sku_diff_df["后7天销售额"] - sku_diff_df["前7天销售额"]

            # 按销量增量从大到小排序
            sku_diff_df = sku_diff_df.sort_values(by="销量变化(件)", ascending=False)

            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("#### 🔥 销量增长最快 Top 5 SKU")
                st.dataframe(
                    sku_diff_df.head(5)[["产品SKU", "前7天销量", "后7天销量", "销量变化(件)", "销量增长率(%)"]], 
                    use_container_width=True, hide_index=True
                )

            with col_right:
                st.markdown("#### 📉 销量下滑最严重 Top 5 SKU")
                st.dataframe(
                    sku_diff_df.sort_values(by="销量变化(件)", ascending=True).head(5)[["产品SKU", "前7天销量", "后7天销量", "销量变化(件)", "销量增长率(%)"]], 
                    use_container_width=True, hide_index=True
                )

            st.markdown("#### 完整 SKU 7天对比明细")
            st.dataframe(sku_diff_df, use_container_width=True, hide_index=True)

            # ------------------ 3. 可视化柱状图 ------------------
            st.markdown("---")
            st.subheader("📊 销量变化 Top 10 SKU 柱状对比图")
            
            top10_diff = sku_diff_df.head(10)
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(x=top10_diff["产品SKU"], y=top10_diff["前7天销量"], name="前 7 天销量", marker_color='lightslategrey'))
            fig_compare.add_trace(go.Bar(x=top10_diff["产品SKU"], y=top10_diff["后7天销量"], name="后 7 天销量", marker_color='crimson'))

            fig_compare.update_layout(
                barmode='group',
                title="前 7 天 vs 后 7 天 Top SKU 销量直观对比",
                xaxis_title="产品 SKU",
                yaxis_title="销量 (件)",
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_compare, use_container_width=True)

    else:
        st.info("当前筛选条件下无日期数据，无法生成 7 天对比看板。")
