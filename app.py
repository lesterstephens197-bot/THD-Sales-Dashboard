import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面基础配置
st.set_page_config(
    page_title="电商销售与退货分析看板",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 1. 数据加载与预处理
# ------------------------------------------------------------------------------
@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_order_data(file):
    """加载并清洗出单表"""
    if file is not None:
        df = pd.read_excel(file)
    else:
        # 默认生成模拟出单数据
        data = {
            "Line Status": ["Shipped", "Shipped", "Cancelled", "Shipped", "Shipped"] * 20,
            "PO Number": [f"PO{1000+i}" for i in range(100)],
            "Order Date": pd.date_range(end=datetime.today(), periods=100, freq="D"),
            "Merchant SKU": [f"MSKU-{i%5+1}" for i in range(100)],
            "Vendor SKU": [f"VSKU-{i%5+1}" for i in range(100)],
            "产品名称": [f"产品 {chr(65 + i%5)}" for i in range(100)],
            "产品SKU": [f"SKU-00{i%5+1}" for i in range(100)],
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

    # 清洗出单表类型
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    for num_col in ["Quantity", "Total Cost", "Unit Cost"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)
            
    return df

@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_rtv_data(file):
    """加载并清洗 RTV 退货表"""
    if file is not None:
        df = pd.read_excel(file)
    else:
        # 默认生成模拟 RTV 数据
        data = {
            "RTV Date": pd.date_range(end=datetime.today(), periods=20, freq="2D"),
            "RTV Number": [f"RTV-{8000+i}" for i in range(20)],
            "Store": ["Store A", "Store B"] * 10,
            "PO#": [f"PO{1000+i*3}" for i in range(20)],
            "Order Date": pd.date_range(end=datetime.today() - timedelta(days=10), periods=20, freq="2D"),
            "PART#": [f"P-{i}" for i in range(20)],
            "产品SKU": [f"SKU-00{i%5+1}" for i in range(20)],
            "产品名称": [f"产品 {chr(65 + i%5)}" for i in range(20)],
            "Brand": ["Brand A", "Brand B"] * 10,
            "Carrier": ["FedEx", "UPS"] * 10,
            "Reason": ["Defective", "Customer Cancel", "Wrong Item", "Damaged"] * 5,
            "QTY": [1, 1, 2, 1, 1] * 4,
            "UNIT COST": [20.0, 35.5, 15.0, 50.0, 10.5] * 4,
            "Total Cost": [20.0, 35.5, 30.0, 50.0, 10.5] * 4,
            "10%运费": [2.0, 3.55, 3.0, 5.0, 1.05] * 4,
            "总扣款": [22.0, 39.05, 33.0, 55.0, 11.55] * 4
        }
        df = pd.DataFrame(data)

    # 清洗 RTV 表日期和数字类型
    for date_col in ["RTV Date", "Order Date"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    for num_col in ["QTY", "UNIT COST", "Total Cost", "10%运费", "总扣款"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)
            
    return df

# ------------------------------------------------------------------------------
# 2. 侧边栏：文件上传与全局筛选
# ------------------------------------------------------------------------------
st.sidebar.title("🔍 数据上传与筛选设置")

uploaded_order_file = st.sidebar.file_uploader("1. 上传【出单表】 Excel", type=["xlsx", "xls"], key="order_file")
uploaded_rtv_file = st.sidebar.file_uploader("2. 上传【RTV退货表】 Excel", type=["xlsx", "xls"], key="rtv_file")

df_raw = load_order_data(uploaded_order_file)
rtv_raw = load_rtv_data(uploaded_rtv_file)

# 运营人员筛选
all_operators = ["全部"] + list(df_raw["运营"].dropna().unique()) if "运营" in df_raw.columns else ["全部"]
selected_operator = st.sidebar.selectbox("筛选运营人员", all_operators)

# 日期筛选：基于出单表的 Order Date
valid_dates = df_raw["Order Date"].dropna() if "Order Date" in df_raw.columns else pd.Series()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input("选择订单日期范围", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = None

# 数据过滤逻辑
df = df_raw.copy()
rtv_df = rtv_raw.copy()

# 1. 运营人员过滤
if selected_operator != "全部" and "运营" in df.columns:
    df = df[df["运营"] == selected_operator]

# 2. 日期范围过滤 (出单表)
if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and "Order Date" in df.columns:
    start_date, end_date = date_range
    date_mask = df["Order Date"].dt.date.between(start_date, end_date) | df["Order Date"].isna()
    df = df[date_mask]

# 单量统计逻辑
def get_unique_orders_count(data_frame):
    return len(data_frame)

# 页面标题
st.title("📈 电商销售与退货分析综合看板")
st.markdown("---")

# ------------------------------------------------------------------------------
# 3. Tab 标签页布局
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. 总数据看板", 
    "📦 2. 产品SKU分析", 
    "👤 3. 运营绩效看板", 
    "🗺️ 4. 全美销量分布",
    "📅 5. 周销量环比对比",
    "🔄 6. RTV退货专项分析"
])

# ==============================================================================
# 模块 1：总数据看板
# ==============================================================================
with tab1:
    st.header("总数据概览")
    
    total_sales = df["Total Cost"].sum() if "Total Cost" in df.columns else 0.0
    total_qty = df["Quantity"].sum() if "Quantity" in df.columns else 0
    total_orders = get_unique_orders_count(df)
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
            
            active_days = group["Order Date"].dt.date.nunique() if "Order Date" in group.columns else 1
            avg_daily_qty = round(total_qty_sku / active_days, 2) if active_days > 0 else 0
            
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
# 模块 5：周销量环比对比看板
# ==============================================================================
with tab5:
    st.header("📅 周销量环比对比 (前一周 vs 当前周 vs 后一周)")
    
    df_week_base = df.copy()

    if not df_week_base.empty and "Order Date" in df_week_base.columns:
        df_week_valid = df_week_base.dropna(subset=["Order Date"]).copy()
        df_week_valid["Week_Start"] = df_week_valid["Order Date"].dt.to_period("W").dt.start_time
        
        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            all_skus_available = sorted(list(df_week_valid["产品SKU"].dropna().unique())) if "产品SKU" in df_week_valid.columns else []
            selected_skus = st.multiselect(
                "🔍 选择筛选产品 SKU (支持多选，留空默认为全部):", 
                options=all_skus_available,
                default=[],
                key="multiselect_skus"
            )

        if selected_skus:
            df_week_filtered = df_week_valid[df_week_valid["产品SKU"].isin(selected_skus)]
            sku_label_str = ", ".join(selected_skus[:3]) + (f" 等{len(selected_skus)}个" if len(selected_skus) > 3 else "")
        else:
            df_week_filtered = df_week_valid.copy()
            sku_label_str = "全部 SKU"

        all_weeks = sorted(df_week_valid["Week_Start"].unique())
        
        if len(all_weeks) >= 1:
            with col_w2:
                week_options_str = [w.strftime("%Y-%m-%d (周一)") for w in all_weeks]
                default_idx = len(all_weeks) - 1
                selected_week_str = st.selectbox("🎯 选择基准目标周 (W):", week_options_str, index=default_idx)
                chosen_week = all_weeks[week_options_str.index(selected_week_str)]

            prev_week = chosen_week - pd.Timedelta(days=7)
            next_week = chosen_week + pd.Timedelta(days=7)

            def get_week_metrics(data_df, target_week):
                sub_df = data_df[data_df["Week_Start"] == target_week]
                qty = sub_df["Quantity"].sum() if "Quantity" in sub_df.columns else 0
                sales = sub_df["Total Cost"].sum() if "Total Cost" in sub_df.columns else 0.0
                return qty, sales

            qty_prev, sales_prev = get_week_metrics(df_week_filtered, prev_week)
            qty_curr, sales_curr = get_week_metrics(df_week_filtered, chosen_week)
            qty_next, sales_next = get_week_metrics(df_week_filtered, next_week)

            def calc_delta(current, baseline):
                if baseline == 0:
                    return "N/A" if current == 0 else "+100%"
                diff = current - baseline
                pct = (diff / baseline) * 100
                return f"{pct:+.1f}%"

            st.markdown("---")
            st.subheader(f"📊 【{sku_label_str}】3周核心数据对比指标")

            col_m1, col_m2, col_m3 = st.columns(3)

            with col_m1:
                st.info(f"⬅️ **前一周 (W-1)**\n\n起始日期: {prev_week.strftime('%Y-%m-%d')}")
                st.metric("前一周销量 (件)", f"{qty_prev:,}")
                st.metric("前一周销售额 (USD)", f"${sales_prev:,.2f}")

            with col_m2:
                delta_qty_vs_prev = calc_delta(qty_curr, qty_prev)
                delta_sales_vs_prev = calc_delta(sales_curr, sales_prev)
                
                st.success(f"🎯 **基准周 (W)**\n\n起始日期: {chosen_week.strftime('%Y-%m-%d')}")
                st.metric("当前周销量 (件)", f"{qty_curr:,}", delta=f"较前一周: {delta_qty_vs_prev}")
                st.metric("当前周销售额 (USD)", f"${sales_curr:,.2f}", delta=f"较前一周: {delta_sales_vs_prev}")

            with col_m3:
                delta_qty_vs_curr = calc_delta(qty_next, qty_curr)
                delta_sales_vs_curr = calc_delta(sales_next, sales_curr)

                st.warning(f"➡️ **后一周 (W+1)**\n\n起始日期: {next_week.strftime('%Y-%m-%d')}")
                st.metric("后一周销量 (件)", f"{qty_next:,}", delta=f"较基准周: {delta_qty_vs_curr}")
                st.metric("后一周销售额 (USD)", f"${sales_next:,.2f}", delta=f"较基准周: {delta_sales_vs_curr}")

            st.markdown("### 📈 3周总销量与销售额柱状对比图")
            compare_df = pd.DataFrame([
                {"period": "前一周 (W-1)", "qty": qty_prev, "sales": sales_prev},
                {"period": "基准周 (W)", "qty": qty_curr, "sales": sales_curr},
                {"period": "后一周 (W+1)", "qty": qty_next, "sales": sales_next}
            ])

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=compare_df["period"], 
                y=compare_df["qty"], 
                name="销量 (件)", 
                text=compare_df["qty"], 
                textposition='auto',
                marker_color='indigo'
            ))
            fig_comp.add_trace(go.Scatter(
                x=compare_df["period"], 
                y=compare_df["sales"], 
                name="销售额 ($)", 
                mode='lines+markers+text',
                text=[f"${s:,.0f}" for s in compare_df["sales"]],
                textposition='top center',
                yaxis="y2",
                line=dict(color='firebrick', width=3)
            ))

            fig_comp.update_layout(
                title=f"【{sku_label_str}】前/中/后三周总量趋势",
                xaxis_title="对比周期",
                yaxis=dict(title="销量 (件)"),
                yaxis2=dict(title="销售额 ($)", overlaying="y", side="right"),
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            st.markdown("---")
            st.subheader("📦 各 SKU 详细三周销量对比表")
            
            three_weeks = [prev_week, chosen_week, next_week]
            df_3w_skus = df_week_filtered[df_week_filtered["Week_Start"].isin(three_weeks)]
            
            if not df_3w_skus.empty and "产品SKU" in df_3w_skus.columns:
                sku_pivot = df_3w_skus.pivot_table(
                    index=["产品SKU"], 
                    columns="Week_Start", 
                    values="Quantity", 
                    aggfunc="sum", 
                    fill_value=0
                ).reset_index()

                col_rename = {
                    prev_week: "前一周销量 (W-1)",
                    chosen_week: "基准周销量 (W)",
                    next_week: "后一周销量 (W+1)"
                }
                sku_pivot.rename(columns=col_rename, inplace=True)
                
                for col in ["前一周销量 (W-1)", "基准周销量 (W)", "后一周销量 (W+1)"]:
                    if col not in sku_pivot.columns:
                        sku_pivot[col] = 0

                sku_pivot["较前一周变化 (%)"] = sku_pivot.apply(
                    lambda r: calc_delta(r["基准周销量 (W)"], r["前一周销量 (W-1)"]), axis=1
                )
                sku_pivot["较后一周变化 (%)"] = sku_pivot.apply(
                    lambda r: calc_delta(r["后一周销量 (W+1)"], r["基准周销量 (W)"]), axis=1
                )

                sku_pivot = sku_pivot.sort_values(by="基准周销量 (W)", ascending=False)
                
                st.dataframe(
                    sku_pivot[["产品SKU", "前一周销量 (W-1)", "基准周销量 (W)", "较前一周变化 (%)", "后一周销量 (W+1)", "较后一周变化 (%)"]],
                    use_container_width=True,
                    hide_index=True
                )

                if selected_skus and len(selected_skus) > 1:
                    st.markdown("### 📊 所选 SKU 的三周销量分组对比")
                    df_melted = pd.melt(
                        sku_pivot, 
                        id_vars=["产品SKU"], 
                        value_vars=["前一周销量 (W-1)", "基准周销量 (W)", "后一周销量 (W+1)"],
                        var_name="周期", 
                        value_name="销量 (件)"
                    )
                    fig_sku_group = px.bar(
                        df_melted, 
                        x="产品SKU", 
                        y="销量 (件)", 
                        color="周期", 
                        barmode="group",
                        text_auto=True,
                        title="分 SKU 柱状对比图"
                    )
                    st.plotly_chart(fig_sku_group, use_container_width=True)

        else:
            st.warning("数据集中可用的周数据不足，请扩大筛选日期范围。")
    else:
        st.info("当前数据集中没有有效的日期字段 (Order Date)。")

# ==============================================================================
# 模块 6：RTV 退货专项分析 (新增)
# ==============================================================================
with tab6:
    st.header("🔄 RTV 退货专项分析")

    if rtv_df.empty:
        st.warning("未检测到有效的 RTV 退货数据。")
    else:
        # 统一关键列名取值
        rtv_qty_col = "QTY" if "QTY" in rtv_df.columns else "Quantity"
        rtv_cost_col = "总扣款" if "总扣款" in rtv_df.columns else ("Total Cost" if "Total Cost" in rtv_df.columns else "")
        
        # 1. 整体核心退货 KPI
        total_rtv_qty = rtv_df[rtv_qty_col].sum() if rtv_qty_col in rtv_df.columns else 0
        total_rtv_cost = rtv_df[rtv_cost_col].sum() if rtv_cost_col != "" else 0.0
        
        # 获取出单表总销售量与总销售额作为退货率基数
        base_order_qty = df["Quantity"].sum() if "Quantity" in df.columns else 0
        base_order_sales = df["Total Cost"].sum() if "Total Cost" in df.columns else 0.0
        
        overall_qty_return_rate = (total_rtv_qty / base_order_qty * 100) if base_order_qty > 0 else 0.0
        overall_cost_return_rate = (total_rtv_cost / base_order_sales * 100) if base_order_sales > 0 else 0.0

        st.subheader("📌 核心退货指标概览")
        rk1, rk2, rk3, rk4 = st.columns(4)
        rk1.metric("总退货数量 (件)", f"{int(total_rtv_qty):,}")
        rk2.metric("总退款金额 / 扣款 (USD)", f"${total_rtv_cost:,.2f}")
        rk3.metric("数量退货率 (件数)", f"{overall_qty_return_rate:.2f}%")
        rk4.metric("金额退货率 (金额)", f"{overall_cost_return_rate:.2f}%")

        st.markdown("---")

        # 2. 以产品 SKU 维度的每月退货分析
        st.subheader("📦 SKU 每月退货明细看板 (退货数量 / 退款金额 / 退货率)")
        
        # 视角选择
        sku_month_view = st.radio("选择时间归属视角:", ["按 RTV 日期 (实际退货发生月份)", "按订单日期 (出单发生月份)"], horizontal=True)
        date_col_selected = "RTV Date" if "RTV 日期" in sku_month_view else "Order Date"

        if date_col_selected in rtv_df.columns and "产品SKU" in rtv_df.columns:
            rtv_valid_date = rtv_df.dropna(subset=[date_col_selected]).copy()
            rtv_valid_date["Year_Month"] = rtv_valid_date[date_col_selected].dt.to_period("M").astype(str)
            
            # 聚合 RTV 表
            rtv_sku_month = rtv_valid_date.groupby(["产品SKU", "Year_Month"]).agg(
                退货数量=(rtv_qty_col, "sum"),
                退款金额=(rtv_cost_col, "sum")
            ).reset_index()

            # 聚合出单表 (以 Order Date 的月份为基准计算销量)
            if "Order Date" in df.columns and "产品SKU" in df.columns:
                df_order_valid = df.dropna(subset=["Order Date"]).copy()
                df_order_valid["Year_Month"] = df_order_valid["Order Date"].dt.to_period("M").astype(str)
                order_sku_month = df_order_valid.groupby(["产品SKU", "Year_Month"]).agg(
                    订单销量=("Quantity", "sum"),
                    订单销售额=("Total Cost", "sum")
                ).reset_index()

                # 合并出单与退货数据
                merged_sku_month = pd.merge(rtv_sku_month, order_sku_month, on=["产品SKU", "Year_Month"], how="left").fillna(0)
            else:
                merged_sku_month = rtv_sku_month.copy()
                merged_sku_month["订单销量"] = 0
                merged_sku_month["订单销售额"] = 0.0

            # 计算退货率
            merged_sku_month["数量退货率 (%)"] = merged_sku_month.apply(
                lambda r: round((r["退货数量"] / r["订单销量"] * 100), 2) if r["订单销量"] > 0 else 0.0, axis=1
            )
            merged_sku_month["金额退货率 (%)"] = merged_sku_month.apply(
                lambda r: round((r["退款金额"] / r["订单销售额"] * 100), 2) if r["订单销售额"] > 0 else 0.0, axis=1
            )

            # 重新排列并显示表格
            show_cols = ["产品SKU", "Year_Month", "退货数量", "退款金额", "订单销量", "数量退货率 (%)", "金额退货率 (%)"]
            merged_sku_month = merged_sku_month.sort_values(by=["Year_Month", "退货数量"], ascending=[False, False])
            st.dataframe(merged_sku_month[show_cols], use_container_width=True, hide_index=True)

            # 绘图：重点 SKU 退货趋势
            fig_rtv_sku = px.bar(
                merged_sku_month,
                x="Year_Month",
                y="退货数量",
                color="产品SKU",
                title="各 SKU 月度退货数量趋势",
                barmode="group"
            )
            st.plotly_chart(fig_rtv_sku, use_container_width=True)

        st.markdown("---")

        # 3. 视角对比分析：RTV 日期 vs 订单日期 深度对比
        st.subheader("🔍 视角对比分析：RTV 日期 vs 订单日期")
        st.markdown("""
        * **RTV 日期视角**：记录财务/仓库实际收到退货扣款的时间，适用于财务结算与退货库存入库监控。
        * **订单日期视角**：将退货追溯会原始发货订单的月份，适用于评估特定批次/时间段销售产品的质量与退货表现。
        """)

        col_v1, col_v2 = st.columns(2)

        # 【视角 A】：按 RTV 日期
        with col_v1:
            st.markdown("#### 视角 A：按 RTV 日期统计")
            if "RTV Date" in rtv_df.columns:
                rtv_a = rtv_df.dropna(subset=["RTV Date"]).copy()
                rtv_a["RTV_Month"] = rtv_a["RTV Date"].dt.to_period("M").astype(str)
                
                summary_a = rtv_a.groupby("RTV_Month").agg(
                    退货数量=(rtv_qty_col, "sum"),
                    退款金额=(rtv_cost_col, "sum")
                ).reset_index()

                # 匹配当月发货总量计算宏观退货率
                if "Order Date" in df.columns:
                    df_m = df.dropna(subset=["Order Date"]).copy()
                    df_m["Month"] = df_m["Order Date"].dt.to_period("M").astype(str)
                    order_m = df_m.groupby("Month").agg(出单量=("Quantity", "sum")).reset_index()
                    summary_a = pd.merge(summary_a, order_m, left_on="RTV_Month", right_on="Month", how="left").fillna(0)
                    summary_a["当月退货率 (%)"] = round(summary_a["退货数量"] / summary_a["出单量"] * 100, 2)

                st.dataframe(summary_a, use_container_width=True, hide_index=True)
                fig_a = px.line(summary_a, x="RTV_Month", y="退货数量", title="按 RTV 日期退货数量趋势", markers=True)
                st.plotly_chart(fig_a, use_container_width=True)

        # 【视角 B】：按 订单日期
        with col_v2:
            st.markdown("#### 视角 B：按 订单日期追溯统计")
            if "Order Date" in rtv_df.columns:
                rtv_b = rtv_df.dropna(subset=["Order Date"]).copy()
                rtv_b["Order_Month"] = rtv_b["Order Date"].dt.to_period("M").astype(str)
                
                summary_b = rtv_b.groupby("Order_Month").agg(
                    退货数量=(rtv_qty_col, "sum"),
                    退款金额=(rtv_cost_col, "sum")
                ).reset_index()

                if "Order Date" in df.columns:
                    df_m = df.dropna(subset=["Order Date"]).copy()
                    df_m["Month"] = df_m["Order Date"].dt.to_period("M").astype(str)
                    order_m = df_m.groupby("Month").agg(出单量=("Quantity", "sum")).reset_index()
                    summary_b = pd.merge(summary_b, order_m, left_on="Order_Month", right_on="Month", how="left").fillna(0)
                    summary_b["对应批次退货率 (%)"] = round(summary_b["退货数量"] / summary_b["出单量"] * 100, 2)

                st.dataframe(summary_b, use_container_width=True, hide_index=True)
                fig_b = px.line(summary_b, x="Order_Month", y="退货数量", title="按 订单日期追溯退货数量趋势", markers=True, color_discrete_sequence=['orange'])
                st.plotly_chart(fig_b, use_container_width=True)

        # 退货原因分布统计
        if "Reason" in rtv_df.columns:
            st.markdown("---")
            st.subheader("❓ 主要退货原因分析")
            reason_df = rtv_df.groupby("Reason").agg(
                退货次数=(rtv_qty_col, "count"),
                退货总量=(rtv_qty_col, "sum"),
                退款金额=(rtv_cost_col, "sum")
            ).reset_index().sort_values(by="退货总量", ascending=False)

            fig_reason = px.pie(reason_df, names="Reason", values="退货总量", title="退货原因占比 (按件数)", hole=0.4)
            st.plotly_chart(fig_reason, use_container_width=True)
