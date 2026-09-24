import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面基础配置
st.set_page_config(
    page_title="电商销售与 RTV 分析看板",
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
        # 默认生成模拟销售数据
        data = {
            "Line Status": ["Shipped", "Shipped", "Cancelled", "Shipped", "Shipped"] * 20,
            "PO Number": [f"PO{1000+(i%30)}" for i in range(100)],
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

    # 清洗列数据
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    if "Total Cost" in df.columns:
        df["Total Cost"] = pd.to_numeric(df["Total Cost"], errors="coerce").fillna(0)
    if "Unit Cost" in df.columns:
        df["Unit Cost"] = pd.to_numeric(df["Unit Cost"], errors="coerce").fillna(0)
    if "PO Number" in df.columns:
        df["PO Number"] = df["PO Number"].astype(str).str.strip()
    if "PO#" in df.columns and "PO Number" not in df.columns:
        df["PO Number"] = df["PO#"].astype(str).str.strip()

    return df


@st.cache_data(hash_funcs={"streamlit.runtime.uploaded_file_manager.UploadedFile": lambda x: x.name}, show_spinner=False)
def load_rtv_data(file):
    required_cols = [
        "RTV Date", "RTV Number", "Store", "PO#", "Order Date", "PART#",
        "产品SKU", "产品名称", "Brand", "Carrier", "Reason", "QTY",
        "UNIT COST", "Total Cost", "10%运费", "总扣款"
    ]
    
    if file is not None:
        df = pd.read_excel(file)
        # 确保所有标准列存在
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan
    else:
        # 生成模拟 RTV 退货数据供测试演示
        data = {
            "RTV Date": pd.date_range(end=datetime.today(), periods=20, freq="W"),
            "RTV Number": [f"RTV-{2000+i}" for i in range(20)],
            "Store": ["Store A", "Store B"] * 10,
            "PO#": [f"PO{1000+(i%10)}" for i in range(20)],
            "Order Date": pd.date_range(end=datetime.today() - timedelta(days=20), periods=20, freq="W"),
            "PART#": [f"P-{i+1}" for i in range(20)],
            "产品SKU": [f"SKU-00{i%5+1}" for i in range(20)],
            "产品名称": [f"产品 {chr(65 + i%5)}" for i in range(20)],
            "Brand": ["Brand A", "Brand B"] * 10,
            "Carrier": ["FedEx", "UPS", "DHL"] * 6 + ["FedEx", "UPS"],
            "Reason": ["Damaged", "Defective", "Customer Return", "Wrong Item"] * 5,
            "QTY": [1, 2, 1, 3, 2] * 4,
            "UNIT COST": [20.0, 35.5, 15.0, 50.0, 10.5] * 4,
            "Total Cost": [20.0, 71.0, 15.0, 150.0, 21.0] * 4,
            "10%运费": [2.0, 7.1, 1.5, 15.0, 2.1] * 4,
            "总扣款": [22.0, 78.1, 16.5, 165.0, 23.1] * 4
        }
        df = pd.DataFrame(data)

    # 类型清洗
    df["RTV Date"] = pd.to_datetime(df["RTV Date"], errors="coerce")
    df["Order Date"] = pd.date_range(end=datetime.today(), periods=len(df)) if df["Order Date"].isna().all() else pd.to_datetime(df["Order Date"], errors="coerce")
    df["QTY"] = pd.to_numeric(df["QTY"], errors="coerce").fillna(0)
    df["UNIT COST"] = pd.to_numeric(df["UNIT COST"], errors="coerce").fillna(0)
    
    # 计算 Total Cost / 10%运费 / 总扣款 (若数据未填或缺损)
    df["Total Cost"] = df["QTY"] * df["UNIT COST"]
    df["10%运费"] = df["Total Cost"] * 0.10
    df["总扣款"] = df["Total Cost"] + df["10%运费"]
    
    if "PO#" in df.columns:
        df["PO#"] = df["PO#"].astype(str).str.strip()

    return df[required_cols]

# ------------------------------------------------------------------------------
# 2. 侧边栏：三大文件上传窗口与全局筛选
# ------------------------------------------------------------------------------
st.sidebar.title("📁 数据文件上传")

st.sidebar.markdown("### 1️⃣ 出单/销售数据")
uploaded_sales_file = st.sidebar.file_uploader("上传销售数据 (.xlsx)", type=["xlsx", "xls"], key="sales_file")

st.sidebar.markdown("### 2️⃣ RTV 退货数据")
uploaded_rtv_file = st.sidebar.file_uploader("上传 RTV 退货数据 (.xlsx)", type=["xlsx", "xls"], key="rtv_file")

st.sidebar.markdown("### 3️⃣ 其他/补充数据 (可选)")
uploaded_extra_file = st.sidebar.file_uploader("上传其他数据 (.xlsx)", type=["xlsx", "xls"], key="extra_file")

# 加载数据
df_sales_raw = load_sales_data(uploaded_sales_file)
df_rtv_raw = load_rtv_data(uploaded_rtv_file)

st.sidebar.markdown("---")
st.sidebar.title("🔍 全局筛选过滤")

# 运营人员筛选
all_operators = ["全部"] + list(df_sales_raw["运营"].dropna().unique()) if "运营" in df_sales_raw.columns else ["全部"]
selected_operator = st.sidebar.selectbox("筛选运营人员", all_operators)

# 过滤销售数据
df_sales = df_sales_raw.copy()
if selected_operator != "全部" and "运营" in df_sales.columns:
    df_sales = df_sales[df_sales["运营"] == selected_operator]

# RTV 匹配 PO 筛选，若筛选了特定运营，将 RTV 过滤为对应运营的 PO
if selected_operator != "全部" and "PO Number" in df_sales_raw.columns:
    valid_pos = df_sales_raw[df_sales_raw["运营"] == selected_operator]["PO Number"].unique()
    df_rtv = df_rtv_raw[df_rtv_raw["PO#"].isin(valid_pos)].copy()
else:
    df_rtv = df_rtv_raw.copy()

def get_unique_orders_count(data_frame):
    return len(data_frame)

# 页面标题
st.title("📈 电商销售与 RTV 数据分析可视化看板")
st.markdown("---")

# ------------------------------------------------------------------------------
# 3. Tab 标签页布局 (包含 RTV 退货看板)
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. 总数据看板", 
    "📦 2. 产品SKU分析", 
    "👤 3. 运营绩效看板", 
    "🗺️ 4. 全美销量分布",
    "📅 5. 周销量环比对比",
    "📦 6. RTV 退货分析看板"
])

# ==============================================================================
# 模块 1：总数据看板
# ==============================================================================
with tab1:
    st.header("总数据概览")
    
    total_sales = df_sales["Total Cost"].sum() if "Total Cost" in df_sales.columns else 0.0
    total_qty = df_sales["Quantity"].sum() if "Quantity" in df_sales.columns else 0
    total_orders = get_unique_orders_count(df_sales)
    aov = total_sales / total_qty if total_qty > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总销售额 (USD)", f"${total_sales:,.2f}")
    col2.metric("总销量 (件)", f"{total_qty:,}")
    col3.metric("总单量 (笔)", f"{total_orders:,}")
    col4.metric("平均客单价 (AOV)", f"${aov:,.2f}")

    if "Order Date" in df_sales.columns and not df_sales["Order Date"].dropna().empty:
        st.markdown("### 销售趋势变化")
        trend_type = st.radio("按时间维度查看趋势", ["按日", "按周", "按月"], horizontal=True)
        
        df_valid_date = df_sales.dropna(subset=["Order Date"])
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

    if not df_sales.empty and "产品SKU" in df_sales.columns:
        valid_dates = df_sales["Order Date"].dropna() if "Order Date" in df_sales.columns else pd.Series()
        latest_date = valid_dates.max() if not valid_dates.empty else datetime.today()
        d7_cutoff = latest_date - timedelta(days=7)
        d15_cutoff = latest_date - timedelta(days=15)

        sku_stats = []
        for sku, group in df_sales.groupby("产品SKU"):
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
        
        sku_list = df_sales["产品SKU"].unique()
        selected_sku = st.selectbox("搜索或选择产品 SKU:", sku_list)

        if selected_sku and "Order Date" in df_sales.columns:
            df_single_sku = df_sales[df_sales["产品SKU"] == selected_sku].dropna(subset=["Order Date"])
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
# 模块 3：按运营绩效
# ==============================================================================
with tab3:
    st.header("运营人员业绩看板")

    if not df_sales.empty and "运营" in df_sales.columns:
        op_list = []
        for op, group in df_sales.groupby("运营"):
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
            fig_op_sales = px.bar(op_summary, x="运营", y="总销售额", text_auto=".2s", title="各运营人员总销售额对比", color="运营")
            st.plotly_chart(fig_op_sales, use_container_width=True)
        with col_op2:
            fig_op_qty = px.pie(op_summary, names="运营", values="总销量", title="各运营人员总销量贡献占比", hole=0.4)
            st.plotly_chart(fig_op_qty, use_container_width=True)

# ==============================================================================
# 模块 4：全美地图
# ==============================================================================
with tab4:
    st.header("全美各州销量地理分布")

    if not df_sales.empty and "ShipTo State" in df_sales.columns:
        state_list = []
        for state, group in df_sales.groupby("ShipTo State"):
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
        st.plotly_chart(fig_map, use_container_width=True)

# ==============================================================================
# 模块 5：周销量环比对比
# ==============================================================================
with tab5:
    st.header("📅 周销量环比对比 (前一周 vs 当前周 vs 后一周)")
    
    df_week_base = df_sales.copy()

    if not df_week_base.empty and "Order Date" in df_week_base.columns:
        df_week_valid = df_week_base.dropna(subset=["Order Date"]).copy()
        df_week_valid["Week_Start"] = df_week_valid["Order Date"].dt.to_period("W").dt.start_time
        
        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            all_skus_available = sorted(list(df_week_valid["产品SKU"].dropna().unique())) if "产品SKU" in df_week_valid.columns else []
            selected_skus = st.multiselect("🔍 选择筛选产品 SKU (可多选):", options=all_skus_available, default=[])

        if selected_skus:
            df_week_filtered = df_week_valid[df_week_valid["产品SKU"].isin(selected_skus)]
        else:
            df_week_filtered = df_week_valid.copy()

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
                return f"{(diff / baseline) * 100:+.1f}%"

            st.markdown("---")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("前一周销量 (件)", f"{qty_prev:,}", f"${sales_prev:,.2f}")
            col_m2.metric("当前周销量 (件)", f"{qty_curr:,}", delta=f"较前一周: {calc_delta(qty_curr, qty_prev)}")
            col_m3.metric("后一周销量 (件)", f"{qty_next:,}", delta=f"较基准周: {calc_delta(qty_next, qty_curr)}")

# ==============================================================================
# 模块 6：RTV 退货分析看板（重点新增与重构）
# ==============================================================================
with tab6:
    st.header("📦 RTV 退货分析看板")

    if df_rtv.empty:
        st.warning("⚠️ 当前暂无 RTV 退货数据，请在左侧栏上传 RTV 退货表格文件。")
    else:
        # 补充：尝试从出单表中根据 PO# / 产品SKU 补全 RTV 中的 Order Date
        if "PO Number" in df_sales_raw.columns and "Order Date" in df_sales_raw.columns:
            po_date_map = df_sales_raw.dropna(subset=["Order Date"]).groupby("PO Number")["Order Date"].min().to_dict()
            
            # 若 RTV 中 Order Date 为空，通过 PO# 进行补全
            df_rtv["Order Date"] = df_rtv.apply(
                lambda r: po_date_map.get(str(r["PO#"]).strip(), r["Order Date"]), axis=1
            )

        # 核心汇总计算
        total_rtv_qty = df_rtv["QTY"].sum()
        total_rtv_cost = df_rtv["Total Cost"].sum()
        total_rtv_shipping = df_rtv["10%运费"].sum()
        total_rtv_deduction = df_rtv["总扣款"].sum()

        total_sales_qty = df_sales["Quantity"].sum() if "Quantity" in df_sales.columns else 0
        overall_rtv_rate = (total_rtv_qty / total_sales_qty * 100) if total_sales_qty > 0 else 0.0

        # KPI 统计卡片
        st.subheader("📌 退货与扣款核心指标")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("总退货数量 (件)", f"{int(total_rtv_qty):,}")
        kpi2.metric("总退款金额 (USD)", f"${total_rtv_cost:,.2f}")
        kpi3.metric("10% 运费扣款 (USD)", f"${total_rtv_shipping:,.2f}")
        kpi4.metric("总扣款金额 (USD)", f"${total_rtv_deduction:,.2f}")
        kpi5.metric("整体退货率 (%)", f"{overall_rtv_rate:.2f}%")

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 双视角对比：RTV 日期 vs 订单日期
        # ----------------------------------------------------------------------
        st.subheader("🔄 两个视角的退货数据分析 (RTV 日期 vs 订单日期)")
        
        view_mode = st.radio(
            "选择分析视角 / 维度基准：",
            options=["📅 视角一：按 RTV 发生日期 (RTV Date)", "🛒 视角二：按订单原始日期 (Order Date)"],
            horizontal=True
        )

        date_col = "RTV Date" if "RTV Date" in view_mode else "Order Date"

        # 准备月度聚合数据
        df_rtv_valid = df_rtv.dropna(subset=[date_col]).copy()
        df_rtv_valid["YearMonth"] = df_rtv_valid[date_col].dt.to_period("M").astype(str)

        # 月度 RTV 数据汇总
        rtv_monthly = df_rtv_valid.groupby("YearMonth").agg(
            退货数量=("QTY", "sum"),
            退款金额=("Total Cost", "sum"),
            总扣款金额=("总扣款", "sum")
        ).reset_index()

        # 出单表月度销售汇总（以 Order Date 算）
        if not df_sales.empty and "Order Date" in df_sales.columns:
            df_sales_valid = df_sales.dropna(subset=["Order Date"]).copy()
            df_sales_valid["YearMonth"] = df_sales_valid["Order Date"].dt.to_period("M").astype(str)
            sales_monthly = df_sales_valid.groupby("YearMonth").agg(出单数量=("Quantity", "sum")).reset_index()

            # 合并出单与退货计算退货率
            merged_monthly = pd.merge(rtv_monthly, sales_monthly, on="YearMonth", how="left").fillna(0)
            merged_monthly["退货率 (%)"] = (merged_monthly["退货数量"] / merged_monthly["出单数量"] * 100).round(2)
            merged_monthly["退货率 (%)"] = merged_monthly["退货率 (%)"].replace([np.inf, -np.inf], 0).fillna(0)
        else:
            merged_monthly = rtv_monthly
            merged_monthly["出单数量"] = 0
            merged_monthly["退货率 (%)"] = 0.0

        # 月度退货趋势图
        col_rtv_g1, col_rtv_g2 = st.columns(2)

        with col_rtv_g1:
            fig_rtv_m = go.Figure()
            fig_rtv_m.add_trace(go.Bar(x=merged_monthly["YearMonth"], y=merged_monthly["退货数量"], name="退货数量 (件)", marker_color="crimson"))
            fig_rtv_m.add_trace(go.Scatter(x=merged_monthly["YearMonth"], y=merged_monthly["退款金额"], name="退款金额 ($)", yaxis="y2", line=dict(color="orange", width=3)))

            fig_rtv_m.update_layout(
                title=f"月度退货数量与退款金额趋势 ({date_col})",
                xaxis_title="月份",
                yaxis=dict(title="退货数量 (件)"),
                yaxis2=dict(title="退款金额 ($)", overlaying="y", side="right"),
                hovermode="x unified"
            )
            st.plotly_chart(fig_rtv_m, use_container_width=True)

        with col_rtv_g2:
            fig_rtv_rate = px.line(
                merged_monthly,
                x="YearMonth",
                y="退货率 (%)",
                markers=True,
                title=f"月度退货率 (%) 趋势 ({date_col})",
                text="退货率 (%)"
            )
            fig_rtv_rate.update_traces(textposition="top center")
            st.plotly_chart(fig_rtv_rate, use_container_width=True)

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 以产品 SKU 为维度的月度退货数量 / 退款金额 / 退货率对比
        # ----------------------------------------------------------------------
        st.subheader("📦 各产品 SKU 的月度退货对比表")

        sku_rtv_group = df_rtv_valid.groupby(["产品SKU", "YearMonth"]).agg(
            退货数量=("QTY", "sum"),
            退款金额=("Total Cost", "sum"),
            总扣款=("总扣款", "sum")
        ).reset_index()

        # 合并对应 SKU 和月度的出单量
        if not df_sales.empty and "Order Date" in df_sales.columns and "产品SKU" in df_sales.columns:
            df_sales_valid = df_sales.dropna(subset=["Order Date"]).copy()
            df_sales_valid["YearMonth"] = df_sales_valid["Order Date"].dt.to_period("M").astype(str)
            sku_sales_group = df_sales_valid.groupby(["产品SKU", "YearMonth"]).agg(出单数量=("Quantity", "sum")).reset_index()

            sku_rtv_merged = pd.merge(sku_rtv_group, sku_sales_group, on=["产品SKU", "YearMonth"], how="left").fillna(0)
        else:
            sku_rtv_merged = sku_rtv_group
            sku_rtv_merged["出单数量"] = 0

        sku_rtv_merged["退货率 (%)"] = (sku_rtv_merged["退货数量"] / sku_rtv_merged["出单数量"] * 100).round(2)
        sku_rtv_merged["退货率 (%)"] = sku_rtv_merged["退货率 (%)"].replace([np.inf, -np.inf], 0).fillna(0)

        # 指标选择
        metric_choice = st.selectbox(
            "选择透视分析的指标:",
            ["退货数量", "退款金额", "退货率 (%)", "总扣款"]
        )

        sku_pivot_rtv = sku_rtv_merged.pivot_table(
            index="产品SKU",
            columns="YearMonth",
            values=metric_choice,
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        # 添加合计列
        if metric_choice == "退货率 (%)":
            # 重新计算整体累计退货率
            sku_total_rtv = sku_rtv_merged.groupby("产品SKU")["退货数量"].sum()
            sku_total_sales = sku_rtv_merged.groupby("产品SKU")["出单数量"].sum()
            sku_total_rate = (sku_total_rtv / sku_total_sales * 100).round(2).replace([np.inf, -np.inf], 0).fillna(0)
            sku_pivot_rtv["累计平均退货率 (%)"] = sku_pivot_rtv["产品SKU"].map(sku_total_rate)
            sku_pivot_rtv = sku_pivot_rtv.sort_values(by="累计平均退货率 (%)", ascending=False)
        else:
            sku_pivot_rtv["合计"] = sku_pivot_rtv.iloc[:, 1:].sum(axis=1)
            sku_pivot_rtv = sku_pivot_rtv.sort_values(by="合计", ascending=False)

        st.dataframe(sku_pivot_rtv, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 退货原因与品牌分布
        # ----------------------------------------------------------------------
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.subheader("🔍 退货原因分布 (Reason)")
            if "Reason" in df_rtv.columns:
                reason_df = df_rtv.groupby("Reason").agg(退货数量=("QTY", "sum"), 退款金额=("Total Cost", "sum")).reset_index()
                fig_reason = px.pie(reason_df, names="Reason", values="退货数量", title="各原因退货数量占比", hole=0.4)
                st.plotly_chart(fig_reason, use_container_width=True)

        with col_r2:
            st.subheader("🏷️ 品牌/门店扣款排行 (Brand / Store)")
            if "Brand" in df_rtv.columns:
                brand_df = df_rtv.groupby("Brand").agg(总扣款=("总扣款", "sum")).reset_index().sort_values(by="总扣款", ascending=False)
                fig_brand = px.bar(brand_df, x="Brand", y="总扣款", title="各品牌 RTV 总扣款金额", text_auto=".2s", color="Brand")
                st.plotly_chart(fig_brand, use_container_width=True)

        # ----------------------------------------------------------------------
        # RTV 原始数据明细表
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 RTV 详细数据列表")
        st.dataframe(df_rtv, use_container_width=True, hide_index=True)
