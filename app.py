import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 页面配置
st.set_page_config(page_title="RTV退货与出单数据分析", layout="wide")

st.title("📊 RTV 退货与出单分析看板")

# ==========================================
# 1. 侧边栏：文件上传
# ==========================================
st.sidebar.header("📁 数据文件上传")

# 1. 出单/销售数据上传
orders_file = st.sidebar.file_uploader(
    "1️⃣ 出单/销售数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"], 
    key="orders_file"
)

# 2. RTV 退货数据上传
rtv_file = st.sidebar.file_uploader(
    "2️⃣ RTV 退货数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"], 
    key="rtv_file"
)

# 全局筛选过滤
st.sidebar.markdown("---")
st.sidebar.header("🔍 全局筛选过滤")

# ==========================================
# 2. 数据处理函数
# ==========================================
@st.cache_data
def load_data(file):
    if file is not None:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    return None

df_orders = load_data(orders_file)
df_rtv = load_data(rtv_file)

if df_orders is not None and df_rtv is not None:
    # --------------------------------------
    # 2.1 出单表数据清洗与标准化
    # --------------------------------------
    # 指定出单表的期望表头
    order_columns = [
        "Line Status", "PO Number", "Order Date", "Merchant SKU", "Vendor SKU", 
        "产品名称", "产品SKU", "Description", "Unit Cost", "Unit Cost Currency", 
        "Quantity", "Total Cost", "ShipTo Name", "Customer Order Number", 
        "ShipTo Address1", "ShipTo Address2", "ShipTo City", "ShipTo State", 
        "ShipTo Country", "ShipTo Postal Code", "ShipTo Day Phone"
    ]
    
    # 日期转换与格式化
    df_orders['Order Date'] = pd.to_datetime(df_orders['Order Date'], errors='coerce')
    df_orders['YearMonth'] = df_orders['Order Date'].dt.to_period('M').astype(str)
    
    # 数量确保为数值型
    df_orders['Quantity'] = pd.to_numeric(df_orders['Quantity'], errors='coerce').fillna(0)
    
    # SKU 规范化（如果产品SKU缺失，借用 Merchant SKU）
    if '产品SKU' in df_orders.columns:
        df_orders['SKU'] = df_orders['产品SKU'].fillna(df_orders['Merchant SKU'])
    else:
        df_orders['SKU'] = df_orders['Merchant SKU']
        
    # --------------------------------------
    # 2.2 RTV 退货数据清洗与标准化
    # --------------------------------------
    # 假设 RTV 表包含 Date/Order Date, SKU, Return Quantity, Refund Amount 等
    # 自动识别日期列
    rtv_date_col = next((c for c in df_rtv.columns if 'date' in c.lower() or '日期' in c), df_rtv.columns[0])
    rtv_sku_col = next((c for c in df_rtv.columns if 'sku' in c.lower() or '产品' in c), df_rtv.columns[1])
    rtv_qty_col = next((c for c in df_rtv.columns if 'qty' in c.lower() or '数量' in c or 'return' in c.lower()), None)
    rtv_amount_col = next((c for c in df_rtv.columns if 'amount' in c.lower() or '金额' in c or 'refund' in c.lower()), None)

    df_rtv['Return Date'] = pd.to_datetime(df_rtv[rtv_date_col], errors='coerce')
    df_rtv['YearMonth'] = df_rtv['Return Date'].dt.to_period('M').astype(str)
    df_rtv['SKU'] = df_rtv[rtv_sku_col].astype(str)
    
    df_rtv['Return_Qty'] = pd.to_numeric(df_rtv[rtv_qty_col], errors='coerce').fillna(1) if rtv_qty_col else 1
    df_rtv['Refund_Amount'] = pd.to_numeric(df_rtv[rtv_amount_col], errors='coerce').fillna(0) if rtv_amount_col else 0

    # --------------------------------------
    # 2.3 侧边栏人员/维度筛选
    # --------------------------------------
    if '运营人员' in df_orders.columns:
        operators = ["全部"] + list(df_orders['运营人员'].dropna().unique())
        selected_op = st.sidebar.selectbox("筛选运营人员", operators)
        if selected_op != "全部":
            df_orders = df_orders[df_orders['运营人员'] == selected_op]

    # --------------------------------------
    # 2.4 数据聚合与退货率匹配
    # --------------------------------------
    # 1. 按月份与SKU汇总出单量
    orders_summary = df_orders.groupby(['YearMonth', 'SKU'])['Quantity'].sum().reset_index()
    orders_summary.rename(columns={'Quantity': 'Order_Qty'}, inplace=True)

    # 2. 按月份与SKU汇总退货量及退货金额
    rtv_summary = df_rtv.groupby(['YearMonth', 'SKU']).agg({
        'Return_Qty': 'sum',
        'Refund_Amount': 'sum'
    }).reset_index()

    # 3. 合并出单表与退货表
    merged_df = pd.merge(orders_summary, rtv_summary, on=['YearMonth', 'SKU'], how='outer').fillna(0)

    # 4. 计算退货率 (%)
    merged_df['Return_Rate'] = np.where(
        merged_df['Order_Qty'] > 0, 
        (merged_df['Return_Qty'] / merged_df['Order_Qty']) * 100, 
        0
    )

    # 按月份汇总（用于顶部图表）
    monthly_trend = merged_df.groupby('YearMonth').agg({
        'Order_Qty': 'sum',
        'Return_Qty': 'sum',
        'Refund_Amount': 'sum'
    }).reset_index()

    monthly_trend['Monthly_Return_Rate'] = np.where(
        monthly_trend['Order_Qty'] > 0, 
        monthly_trend['Return_Qty'] / monthly_trend['Order_Qty'], 
        0
    )

    # ==========================================
    # 3. 可视化图表展示
    # ==========================================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("月度退货数量与退款金额趋势 (Order Date)")
        fig_trend = go.Figure()
        
        # 退货数量柱状图
        fig_trend.add_trace(go.Bar(
            x=monthly_trend['YearMonth'], 
            y=monthly_trend['Return_Qty'], 
            name="退货数量 (件)", 
            marker_color='#DC143C'
        ))
        
        # 退款金额折线图（双 Y 轴）
        fig_trend.add_trace(go.Scatter(
            x=monthly_trend['YearMonth'], 
            y=monthly_trend['Refund_Amount'], 
            name="退款金额 ($)", 
            yaxis="y2", 
            mode='lines+markers', 
            line=dict(color='#FFA500', width=3)
        ))

        fig_trend.update_layout(
            yaxis=dict(title="退货数量 (件)"),
            yaxis2=dict(title="退款金额 ($)", overlaying="y", side="right"),
            legend=dict(x=0.7, y=1.1, orientation="h"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader("月度退货率 (%) 趋势 (Order Date)")
        fig_rate = px.line(
            monthly_trend, 
            x='YearMonth', 
            y='Monthly_Return_Rate', 
            markers=True,
            text=monthly_trend['Monthly_Return_Rate'].apply(lambda x: f"{x:.2%}")
        )
        fig_rate.update_traces(textposition="top center", line_color='#0055FF')
        fig_rate.update_layout(
            yaxis_title="退货率 (%)",
            yaxis=dict(tickformat=".1%"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_rate, use_container_width=True)

    # ==========================================
    # 4. 各产品 SKU 的月度退货对比表
    # ==========================================
    st.markdown("---")
    st.subheader("📦 各产品 SKU 的月度退货对比表")

    metric_choice = st.selectbox("选择透视分析的指标:", ["退货率 (%)", "退货数量", "出单数量", "退款金额"])

    metric_map = {
        "退货率 (%)": 'Return_Rate',
        "退货数量": 'Return_Qty',
        "出单数量": 'Order_Qty',
        "退款金额": 'Refund_Amount'
    }

    # 透视表构建
    pivot_df = merged_df.pivot_table(
        index='SKU', 
        columns='YearMonth', 
        values=metric_map[metric_choice], 
        aggfunc='sum', 
        fill_value=0
    )

    # 计算累计平均或合计
    if metric_choice == "退货率 (%)":
        # 累计平均退货率 = 累计总退货量 / 累计总出单量
        sku_total = merged_df.groupby('SKU').agg({'Return_Qty': 'sum', 'Order_Qty': 'sum'})
        pivot_df['累计平均退货率 (%)'] = np.where(
            sku_total['Order_Qty'] > 0, 
            (sku_total['Return_Qty'] / sku_total['Order_Qty']) * 100, 
            0
        )
        # 格式化输出
        formatted_pivot = pivot_df.applymap(lambda x: f"{x:.2f}%")
    else:
        pivot_df['总计'] = pivot_df.sum(axis=1)
        formatted_pivot = pivot_df.applymap(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)

    st.dataframe(formatted_pivot, use_container_width=True)

else:
    st.info("💡 请在左侧边栏上传 **出单/销售数据** 和 **RTV 退货数据** 以开始分析。")
