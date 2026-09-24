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



# ------------------------------------------------------------------------------

# 单量统计逻辑

# ------------------------------------------------------------------------------

def get_unique_orders_count(data_frame):

    return len(data_frame)



# 页面标题

st.title("📈 电商销售数据可视化看板")

st.markdown("---")



# ------------------------------------------------------------------------------

# 3. Tab 标签页布局

# ------------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([

    "📊 1. 总数据看板", 

    "📦 2. 产品SKU分析", 

    "👤 3. 运营绩效看板", 

    "🗺️ 4. 全美销量分布",

    "📅 5. 周销量环比对比"

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

# 模块 5：周销量环比对比看板（前一周 / 当前周 / 后一周）

# ==============================================================================

with tab5:

    st.header("📅 周销量环比对比 (前一周 vs 当前周 vs 后一周)")

    

    df_week_base = df.copy()



    if not df_week_base.empty and "Order Date" in df_week_base.columns:

        df_week_valid = df_week_base.dropna(subset=["Order Date"]).copy()

        df_week_valid["Week_Start"] = df_week_valid["Order Date"].dt.to_period("W").dt.start_time

        

        # 1. 产品 SKU 多筛选机制

        col_w1, col_w2 = st.columns([1, 1])

        with col_w1:

            all_skus_available = sorted(list(df_week_valid["产品SKU"].dropna().unique())) if "产品SKU" in df_week_valid.columns else []

            selected_skus = st.multiselect(

                "🔍 选择筛选产品 SKU (支持多选，留空默认为全部):", 

                options=all_skus_available,

                default=[],

                key="multiselect_skus"

            )



        # SKU 过滤处理

        if selected_skus:

            df_week_filtered = df_week_valid[df_week_valid["产品SKU"].isin(selected_skus)]

            sku_label_str = ", ".join(selected_skus[:3]) + (f" 等{len(selected_skus)}个" if len(selected_skus) > 3 else "")

        else:

            df_week_filtered = df_week_valid.copy()

            sku_label_str = "全部 SKU"



        # 获取当前数据集所有的自然周（按起始日期排序）

        all_weeks = sorted(df_week_valid["Week_Start"].unique())

        

        if len(all_weeks) >= 1:

            with col_w2:

                week_options_str = [w.strftime("%Y-%m-%d (周一)") for w in all_weeks]

                default_idx = len(all_weeks) - 1  # 默认选中最新一周

                selected_week_str = st.selectbox("🎯 选择基准目标周 (W):", week_options_str, index=default_idx)

                chosen_week = all_weeks[week_options_str.index(selected_week_str)]



            # 对应的前一周与后一周

            prev_week = chosen_week - pd.Timedelta(days=7)

            next_week = chosen_week + pd.Timedelta(days=7)



            # 获取周指标数据函数

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



            # 图表展现

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



            # 如果用户筛选了 SKU 或想看分 SKU 细分对比

            st.markdown("---")

            st.subheader("📦 各 SKU 详细三周销量对比表")

            

            # 提取这三周的所有 SKU 销量数据

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



                # 重命名列名以便阅读

                col_rename = {

                    prev_week: "前一周销量 (W-1)",

                    chosen_week: "基准周销量 (W)",

                    next_week: "后一周销量 (W+1)"

                }

                sku_pivot.rename(columns=col_rename, inplace=True)

                

                # 确保所需列存在

                for col in ["前一周销量 (W-1)", "基准周销量 (W)", "后一周销量 (W+1)"]:

                    if col not in sku_pivot.columns:

                        sku_pivot[col] = 0



                # 计算环比变化率

                sku_pivot["较前一周变化 (%)"] = sku_pivot.apply(

                    lambda r: calc_delta(r["基准周销量 (W)"], r["前一周销量 (W-1)"]), axis=1

                )

                sku_pivot["较后一周变化 (%)"] = sku_pivot.apply(

                    lambda r: calc_delta(r["后一周销量 (W+1)"], r["基准周销量 (W)"]), axis=1

                )



                # 按基准周销量排序

                sku_pivot = sku_pivot.sort_values(by="基准周销量 (W)", ascending=False)

                

                # 展现表格

                st.dataframe(

                    sku_pivot[["产品SKU", "前一周销量 (W-1)", "基准周销量 (W)", "较前一周变化 (%)", "后一周销量 (W+1)", "较后一周变化 (%)"]],

                    use_container_width=True,

                    hide_index=True

                )



                # 如果选择了具体多个 SKU，展示分 SKU 的多柱状对比图

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
