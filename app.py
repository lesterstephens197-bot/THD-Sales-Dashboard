import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面基础配置
st.set_page_config(
    page_title="电商销售与RTV退货分析看板",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------------------------------------
# 1. 数据加载与预处理
# ------------------------------------------------------------------------------
@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_sales_data(file):
    if file is not None:
        df = pd.read_excel(file)
    else:
        # 未上传文件时生成演示出单数据
        data = {
            "Line Status": ["Shipped"] * 100,
            "PO Number": [f"PO{1000 + (i % 30)}" for i in range(100)],
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
            "Quantity": [2, 3, 1, 4, 5] * 20,
            "Total Cost": [40.0, 106.5, 15.0, 200.0, 52.5] * 20,
            "ShipTo Name": ["Customer"] * 100,
            "Customer Order Number": [f"ORD-{5000+(i%30)}" for i in range(100)],
            "ShipTo Address1": ["Street 1"] * 100,
            "ShipTo Address2": [""] * 100,
            "ShipTo City": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"] * 20,
            "ShipTo State": ["NY", "CA", "IL", "TX", "AZ"] * 20,
            "ShipTo Country": ["US"] * 100,
            "ShipTo Postal Code": ["10001"] * 100,
            "ShipTo Day Phone": ["123456789"] * 100
        }
        df = pd.DataFrame(data)

    # 数据格式清洗
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    if "Total Cost" in df.columns:
        df["Total Cost"] = pd.to_numeric(df["Total Cost"], errors="coerce").fillna(0)
    if "Unit Cost" in df.columns:
        df["Unit Cost"] = pd.to_numeric(df["Unit Cost"], errors="coerce").fillna(0)
    
    return df


@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_rtv_data(file):
    if file is not None:
        df_rtv = pd.read_excel(file)
    else:
        # 未上传文件时生成演示 RTV 数据
        data_rtv = {
            "RTV Date": pd.date_range(end=datetime.today(), periods=20, freq="2D"),
            "RTV Number": [f"RTV-{8000+i}" for i in range(20)],
            "Store": ["Store A", "Store B"] * 10,
            "PO#": [f"PO{1000 + (i % 15)}" for i in range(20)],
            "Order Date": pd.date_range(end=datetime.today() - timedelta(days=15), periods=20, freq="2D"),
            "PART#": [f"P-{10+i}" for i in range(20)],
            "产品SKU": [f"SKU-00{i%5+1}" for i in range(20)],
            "产品名称": [f"产品 {chr(65 + i%5)}" for i in range(20)],
            "Brand": ["Brand A", "Brand B"] * 10,
            "Carrier": ["FedEx", "UPS", "DHL"] * 6 + ["FedEx", "UPS"],
            "Reason": ["Defective", "Customer Cancel", "Wrong Item", "Damaged"] * 5,
            "QTY": [1, 2, 1, 1, 3] * 4,
            "UNIT COST": [20.0, 35.5, 15.0, 50.0, 10.5] * 4,
            "Total Cost": [20.0, 71.0, 15.0, 50.0, 31.5] * 4,
            "10%运费": [2.0, 7.1, 1.5, 5.0, 3.15] * 4,
            "总扣款": [22.0, 78.1, 16.5, 55.0, 34.65] * 4
        }
        df_rtv = pd.DataFrame(data_rtv)

    # 日期及数值格式转化
    date_cols = ["RTV Date", "Order Date"]
    for col in date_cols:
        if col in df_rtv.columns:
            df_rtv[col] = pd.to_datetime(df_rtv[col], errors="coerce")

    num_cols = ["QTY", "UNIT COST", "Total Cost", "10%运费", "总扣款"]
    for col in num_cols:
        if col in df_rtv.columns:
            df_rtv[col] = pd.to_numeric(df_rtv[col], errors="coerce").fillna(0)

    return df_rtv

# ------------------------------------------------------------------------------
# 2. 侧边栏：文件上传与全局筛选
# ------------------------------------------------------------------------------
st.sidebar.title("🔍 数据上传与筛选")

st.sidebar.subheader("1. 销售出单表")
uploaded_sales_file = st.sidebar.file_uploader("上传出单表 (Excel)", type=["xlsx", "xls"], key="sales_uploader")

st.sidebar.subheader("2. RTV 退货表")
uploaded_rtv_file = st.sidebar.file_uploader("上传 RTV 表格 (Excel)", type=["xlsx", "xls"], key="rtv_uploader")

df_raw = load_sales_data(uploaded_sales_file)
df_rtv_raw = load_rtv_data(uploaded_rtv_file)

# 运营人员筛选
all_operators = ["全部"] + list(df_raw["运营"].dropna().unique()) if "运营" in df_raw.columns else ["全部"]
selected_operator = st.sidebar.selectbox("筛选运营人员", all_operators)

# 出单表日期筛选
valid_dates = df_raw["Order Date"].dropna() if "Order Date" in df_raw.columns else pd.Series()
if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input("选择订单日期范围", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = None

# 数据筛选过滤
df = df_raw.copy()

if selected_operator != "全部" and "运营" in df.columns:
    df = df[df["运营"] == selected_operator]

if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and "Order Date" in df.columns:
    start_date, end_date = date_range
    date_mask = df["Order Date"].dt.date.between(start_date, end_date) | df["Order Date"].isna()
    df = df[date_mask]

def get_unique_orders_count(data_frame):
    return len(data_frame)

# 主页面标题
st.title("📈 电商销售与 RTV 数据分析看板")
st.markdown("---")

# ------------------------------------------------------------------------------
# 3. Tab 标签页配置
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. 总数据看板", 
    "📦 2. 产品SKU分析", 
    "👤 3. 运营绩效看板", 
    "🗺️ 4. 全美销量分布",
    "📅 5. 周销量环比对比",
    "🔄 6. RTV 退货分析看板"
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
        trend_type = st.radio("按时间维度查看趋势", ["按日", "按周", "按月"], horizontal=True, key="t1_trend")
        
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
        selected_sku = st.selectbox("搜索或选择产品 SKU:", sku_list, key="t2_sku")

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
                selected_week_str = st.selectbox("🎯 选择基准目标周 (W):", week_options_str, index=default_idx, key="week_select")
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

            # 图表
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

            # 明细表格
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

        else:
            st.warning("数据集中可用的周数据不足，请扩大筛选日期范围。")
    else:
        st.info("当前数据集中没有有效的日期字段 (Order Date)。")

# ==============================================================================
# 模块 6：RTV 退货数据看板 (新板块)
# ==============================================================================
with tab6:
    st.header("🔄 RTV 退货分析看板")

    df_rtv = df_rtv_raw.copy()

    if df_rtv.empty:
        st.warning("⚠️ 暂无 RTV 数据，请在侧边栏上传 RTV 退货 Excel 表格。")
    else:
        # 1. 顶部筛选项：SKU 选择
        rtv_skus = sorted(list(df_rtv["产品SKU"].dropna().unique())) if "产品SKU" in df_rtv.columns else []
        selected_rtv_sku = st.multiselect("🔍 筛选产品 SKU (留空默认看全部):", rtv_skus, key="rtv_sku_filter")

        if selected_rtv_sku:
            df_rtv_filtered = df_rtv[df_rtv["产品SKU"].isin(selected_rtv_sku)]
            df_sales_rtv_filtered = df[df["产品SKU"].isin(selected_rtv_sku)]
        else:
            df_rtv_filtered = df_rtv.copy()
            df_sales_rtv_filtered = df.copy()

        # 核心指标展板
        total_rtv_qty = df_rtv_filtered["QTY"].sum() if "QTY" in df_rtv_filtered.columns else 0
        total_rtv_cost = df_rtv_filtered["Total Cost"].sum() if "Total Cost" in df_rtv_filtered.columns else 0.0
        total_rtv_freight = df_rtv_filtered["10%运费"].sum() if "10%运费" in df_rtv_filtered.columns else 0.0
        total_rtv_deduction = df_rtv_filtered["总扣款"].sum() if "总扣款" in df_rtv_filtered.columns else 0.0

        # 计算总出单量用于总体退货率计算
        total_sales_qty = df_sales_rtv_filtered["Quantity"].sum() if "Quantity" in df_sales_rtv_filtered.columns else 0
        overall_rtv_rate = (total_rtv_qty / total_sales_qty * 100) if total_sales_qty > 0 else 0.0

        st.subheader("📌 RTV 核心退货指标")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("总退货数量 (QTY)", f"{int(total_rtv_qty):,} 件")
        kpi2.metric("总退款金额", f"${total_rtv_cost:,.2f}")
        kpi3.metric("10% 运费扣款", f"${total_rtv_freight:,.2f}")
        kpi4.metric("总扣款金额", f"${total_rtv_deduction:,.2f}")
        kpi5.metric("总体退货率 (%)", f"{overall_rtv_rate:.2f}%")

        st.markdown("---")

        # 2. 两个视角的退货分析 (RTV 日期 vs 订单日期)
        st.subheader("🔍 双视角退货趋势与退货率分析")
        view_perspective = st.radio(
            "选择分析基准视角:",
            ["📅 视角 1：以 RTV 日期为基准 (按月看当期退货处理)", "🛒 视角 2：以订单日期为基准 (匹配出单日算真实退货率)"],
            horizontal=True
        )

        if "视角 1" in view_perspective:
            # RTV 日期视角
            if "RTV Date" in df_rtv_filtered.columns and not df_rtv_filtered["RTV Date"].dropna().empty:
                df_rtv_filtered["RTV_Month"] = df_rtv_filtered["RTV Date"].dt.to_period("M").astype(str)
                
                # RTV 按月汇总
                rtv_monthly = df_rtv_filtered.groupby("RTV_Month").agg({
                    "QTY": "sum",
                    "Total Cost": "sum",
                    "总扣款": "sum"
                }).reset_index()

                # 出单表按月汇总（用于算退货率）
                if "Order Date" in df_sales_rtv_filtered.columns and not df_sales_rtv_filtered["Order Date"].dropna().empty:
                    df_sales_rtv_filtered["Order_Month"] = df_sales_rtv_filtered["Order Date"].dt.to_period("M").astype(str)
                    sales_monthly = df_sales_rtv_filtered.groupby("Order_Month")["Quantity"].sum().reset_index()
                    sales_monthly.rename(columns={"Quantity": "当期订单销量"}, inplace=True)
                else:
                    sales_monthly = pd.DataFrame(columns=["Order_Month", "当期订单销量"])

                merged_view1 = pd.merge(rtv_monthly, sales_monthly, left_on="RTV_Month", right_on="Order_Month", how="left").fillna(0)
                merged_view1["当期退货率 (%)"] = merged_view1.apply(
                    lambda r: round((r["QTY"] / r["当期订单销量"] * 100), 2) if r["当期订单销量"] > 0 else 0.0, axis=1
                )

                st.markdown("#### 📊 按 RTV 日期月份趋势分析")
                
                fig_v1 = go.Figure()
                fig_v1.add_trace(go.Bar(x=merged_view1["RTV_Month"], y=merged_view1["QTY"], name="退货数量 (件)", marker_color='coral'))
                fig_v1.add_trace(go.Scatter(x=merged_view1["RTV_Month"], y=merged_view1["当期退货率 (%)"], name="退货率 (%)", yaxis="y2", mode='lines+markers+text', text=[f"{p}%" for p in merged_view1["当期退货率 (%)"]], textposition="top center", line=dict(color='crimson', width=3)))

                fig_v1.update_layout(
                    title="各月 RTV 退货数量与退货率趋势 (RTV 日期维度)",
                    xaxis_title="RTV 月份",
                    yaxis=dict(title="退货数量 (件)"),
                    yaxis2=dict(title="退货率 (%)", overlaying="y", side="right"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_v1, use_container_width=True)

                st.markdown("#### 📋 月度 RTV 退货明细汇总")
                st.dataframe(merged_view1[["RTV_Month", "QTY", "Total Cost", "总扣款", "当期订单销量", "当期退货率 (%)"]], use_container_width=True, hide_index=True)
            else:
                st.info("RTV 表格中缺乏有效 RTV Date 数据。")

        else:
            # 订单日期视角
            if "Order Date" in df_rtv_filtered.columns and not df_rtv_filtered["Order Date"].dropna().empty:
                df_rtv_filtered["Order_Month"] = df_rtv_filtered["Order Date"].dt.to_period("M").astype(str)
                
                rtv_by_ord_month = df_rtv_filtered.groupby("Order_Month").agg({
                    "QTY": "sum",
                    "Total Cost": "sum",
                    "总扣款": "sum"
                }).reset_index().rename(columns={"QTY": "退货数量", "Total Cost": "退款金额"})

                if "Order Date" in df_sales_rtv_filtered.columns and not df_sales_rtv_filtered["Order Date"].dropna().empty:
                    df_sales_rtv_filtered["Order_Month"] = df_sales_rtv_filtered["Order Date"].dt.to_period("M").astype(str)
                    sales_by_ord_month = df_sales_rtv_filtered.groupby("Order_Month")["Quantity"].sum().reset_index().rename(columns={"Quantity": "订单总销量"})
                else:
                    sales_by_ord_month = pd.DataFrame(columns=["Order_Month", "订单总销量"])

                merged_view2 = pd.merge(sales_by_ord_month, rtv_by_ord_month, on="Order_Month", how="left").fillna(0)
                merged_view2["订单真实退货率 (%)"] = merged_view2.apply(
                    lambda r: round((r["退货数量"] / r["订单总销量"] * 100), 2) if r["订单总销量"] > 0 else 0.0, axis=1
                )

                st.markdown("#### 📊 按下单月份归因的退货率分析")

                fig_v2 = go.Figure()
                fig_v2.add_trace(go.Bar(x=merged_view2["Order_Month"], y=merged_view2["订单总销量"], name="订单销量 (件)", marker_color='royalblue', opacity=0.6))
                fig_v2.add_trace(go.Bar(x=merged_view2["Order_Month"], y=merged_view2["退货数量"], name="退货件数 (件)", marker_color='firebrick'))
                fig_v2.add_trace(go.Scatter(x=merged_view2["Order_Month"], y=merged_view2["订单真实退货率 (%)"], name="真实退货率 (%)", yaxis="y2", mode='lines+markers+text', text=[f"{p}%" for p in merged_view2["订单真实退货率 (%)"]], textposition="top center", line=dict(color='darkorange', width=3)))

                fig_v2.update_layout(
                    title="各下单月份的订单销量、退货量及真实退货率 (订单日期维度)",
                    xaxis_title="订单月份",
                    yaxis=dict(title="数量 (件)"),
                    yaxis2=dict(title="退货率 (%)", overlaying="y", side="right"),
                    barmode='group',
                    hovermode="x unified"
                )
                st.plotly_chart(fig_v2, use_container_width=True)

                st.markdown("#### 📋 订单日期维度退货汇总表")
                st.dataframe(merged_view2[["Order_Month", "订单总销量", "退货数量", "退款金额", "总扣款", "订单真实退货率 (%)"]], use_container_width=True, hide_index=True)
            else:
                st.info("RTV 表格中缺乏有效 Order Date 字段，无法按照订单日期归因。")

        st.markdown("---")

        # 3. 按产品 SKU 维度的月度退货分析明细
        st.subheader("📦 按产品 SKU & 月度的退货明细对比")

        if "产品SKU" in df_rtv_filtered.columns:
            # 建立 SKU 与月份交叉统计
            date_col_for_month = "Order Date" if "视角 2" in view_perspective else "RTV Date"
            
            if date_col_for_month in df_rtv_filtered.columns and not df_rtv_filtered[date_col_for_month].dropna().empty:
                df_rtv_filtered["Month_Period"] = df_rtv_filtered[date_col_for_month].dt.to_period("M").astype(str)
                
                sku_monthly_rtv = df_rtv_filtered.groupby(["产品SKU", "Month_Period"]).agg({
                    "QTY": "sum",
                    "Total Cost": "sum",
                    "总扣款": "sum"
                }).reset_index()

                # 出单数据
                if "Order Date" in df_sales_rtv_filtered.columns and not df_sales_rtv_filtered["Order Date"].dropna().empty:
                    df_sales_rtv_filtered["Month_Period"] = df_sales_rtv_filtered["Order Date"].dt.to_period("M").astype(str)
                    sku_monthly_sales = df_sales_rtv_filtered.groupby(["产品SKU", "Month_Period"])["Quantity"].sum().reset_index()
                else:
                    sku_monthly_sales = pd.DataFrame(columns=["产品SKU", "Month_Period", "Quantity"])

                # 合并出单与退货数据
                sku_rtv_merge = pd.merge(
                    sku_monthly_rtv, 
                    sku_monthly_sales, 
                    on=["产品SKU", "Month_Period"], 
                    how="outer"
                ).fillna(0)

                sku_rtv_merge.rename(columns={
                    "Month_Period": "月份",
                    "QTY": "退货数量",
                    "Total Cost": "退款金额",
                    "Quantity": "订单销量"
                }, inplace=True)

                sku_rtv_merge["退货率 (%)"] = sku_rtv_merge.apply(
                    lambda r: round((r["退货数量"] / r["订单销量"] * 100), 2) if r["订单销量"] > 0 else 0.0, axis=1
                )

                # 按退货数量倒序排列
                sku_rtv_merge = sku_rtv_merge.sort_values(by=["月份", "退货数量"], ascending=[False, False])

                st.dataframe(
                    sku_rtv_merge[["产品SKU", "月份", "订单销量", "退货数量", "退款金额", "总扣款", "退货率 (%)"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("缺少日期字段，无法生成月度 SKU 交叉表格。")

        st.markdown("---")
        # 4. RTV 原始表数据展示
        st.subheader("📄 RTV 原始退货表格查看")
        st.dataframe(df_rtv_filtered, use_container_width=True, hide_index=True)
