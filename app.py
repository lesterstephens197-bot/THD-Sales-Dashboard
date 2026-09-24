import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(
    page_title="数据分析 Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 数据分析与退货率看板")

# ---------------------------------------------------------
# Sidebar: 侧边栏文件上传
# ---------------------------------------------------------
st.sidebar.header("📁 数据文件上传")

# 1. 销售数据上传
sales_file = st.sidebar.file_uploader(
    "1️⃣ 销售数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="sales_upload"
)

# 2. RTV 退货数据上传
rtv_file = st.sidebar.file_uploader(
    "2️⃣ RTV 退货数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="rtv_upload"
)

# 3. 出单数据上传
order_file = st.sidebar.file_uploader(
    "3️⃣ 出单数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="order_upload"
)

# 全局筛选器变量
st.sidebar.markdown("---")
st.sidebar.header("🔍 全局筛选过滤")

# ---------------------------------------------------------
# 数据读取与预处理函数
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    if file is None:
        return None
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"读取文件 {file.name} 失败: {e}")
        return None

sales_df = load_data(sales_file)
rtv_df = load_data(rtv_file)
order_df = load_data(order_file)

# 数据标准化处理逻辑
def preprocess_rtv(df):
    if df is None:
        return None
    df = df.copy()
    # 兼容常见的日期列名
    date_col = next((c for c in df.columns if c in ['Order Date', 'OrderDate', '退货日期', 'Date']), None)
    sku_col = next((c for c in df.columns if c in ['产品SKU', 'Merchant SKU', 'SKU', 'Vendor SKU']), None)
    qty_col = next((c for c in df.columns if c in ['Quantity', '退货数量', 'Qty']), None)
    amount_col = next((c for c in df.columns if c in ['Total Cost', '退款金额', 'Amount', 'Total Amount']), None)

    if date_col:
        df['Order Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    if sku_col:
        df['SKU_Key'] = df[sku_col].astype(str).str.strip()
    if qty_col:
        df['RTV_Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    else:
        df['RTV_Qty'] = 1  # 默认计数
    if amount_col:
        df['RTV_Amount'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
    else:
        df['RTV_Amount'] = 0.0

    return df

def preprocess_orders(df):
    if df is None:
        return None
    df = df.copy()
    # 根据指定的出单表表头进行识别匹配
    date_col = next((c for c in df.columns if c in ['Order Date', 'OrderDate', '出单日期']), None)
    sku_col = next((c for c in df.columns if c in ['产品SKU', 'Merchant SKU', 'Vendor SKU']), None)
    qty_col = next((c for c in df.columns if c in ['Quantity', '数量']), None)

    if date_col:
        df['Order Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    if sku_col:
        df['SKU_Key'] = df[sku_col].astype(str).str.strip()
    if qty_col:
        df['Order_Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    else:
        df['Order_Qty'] = 1

    return df

# 处理数据
rtv_processed = preprocess_rtv(rtv_df)
order_processed = preprocess_orders(order_df)

# ---------------------------------------------------------
# 主界面展示逻辑
# ---------------------------------------------------------
if rtv_processed is not None and order_processed is not None:
    
    # 1. 按年月汇总 RTV 与 出单数据
    rtv_monthly = rtv_processed.groupby('YearMonth').agg(
        RTV_Qty=('RTV_Qty', 'sum'),
        RTV_Amount=('RTV_Amount', 'sum')
    ).reset_index()

    order_monthly = order_processed.groupby('YearMonth').agg(
        Order_Qty=('Order_Qty', 'sum')
    ).reset_index()

    # 合并月度数据
    monthly_merged = pd.merge(rtv_monthly, order_monthly, on='YearMonth', how='outer').fillna(0)
    monthly_merged['Return_Rate'] = (monthly_merged['RTV_Qty'] / monthly_merged['Order_Qty']).fillna(0)
    monthly_merged = monthly_merged.sort_values('YearMonth')

    # 图表区域 1：月度退货数量与退款金额趋势 & 月度退货率趋势
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("月度退货数量与退款金额趋势 (Order Date)")
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=monthly_merged['YearMonth'],
            y=monthly_merged['RTV_Qty'],
            name='退货数量 (件)',
            marker_color='#d62728'
        ))
        fig1.add_trace(go.Scatter(
            x=monthly_merged['YearMonth'],
            y=monthly_merged['RTV_Amount'],
            name='退款金额 ($)',
            yaxis='y2',
            line=dict(color='#ff7f0e', width=3)
        ))
        fig1.update_layout(
            xaxis_title="月份",
            yaxis=dict(title="退货数量 (件)"),
            yaxis2=dict(title="退款金额 ($)", overlaying='y', side='right'),
            legend=dict(x=0.7, y=1.1, orientation="h")
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("月度退货率 (%) 趋势 (Order Date)")
        fig2 = px.line(
            monthly_merged,
            x='YearMonth',
            y='Return_Rate',
            markers=True,
            labels={'Return_Rate': '退货率', 'YearMonth': 'YearMonth'}
        )
        fig2.update_traces(line_color='#1f77b4', line_width=3)
        fig2.update_layout(yaxis_tickformat='.2%')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 2. 各产品 SKU 的月度退货对比表（数据透视）
    st.subheader("📦 各产品 SKU 的月度退货对比表")

    metric_choice = st.selectbox(
        "选择透视分析的指标:",
        ["退货率 (%)", "退货数量 (件)", "出单数量 (件)", "退款金额 ($)"]
    )

    # 按 SKU 和 YearMonth 聚合 RTV 与 出单数据
    rtv_sku_monthly = rtv_processed.groupby(['SKU_Key', 'YearMonth']).agg(
        RTV_Qty=('RTV_Qty', 'sum'),
        RTV_Amount=('RTV_Amount', 'sum')
    ).reset_index()

    order_sku_monthly = order_processed.groupby(['SKU_Key', 'YearMonth']).agg(
        Order_Qty=('Order_Qty', 'sum')
    ).reset_index()

    sku_merged = pd.merge(rtv_sku_monthly, order_sku_monthly, on=['SKU_Key', 'YearMonth'], how='outer').fillna(0)
    sku_merged['Return_Rate'] = (sku_merged['RTV_Qty'] / sku_merged['Order_Qty']).fillna(0)

    # 透视表构建
    if metric_choice == "退货率 (%)":
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='Return_Rate').fillna(0)
        # 计算累计平均退货率
        total_rtv = sku_merged.groupby('SKU_Key')['RTV_Qty'].sum()
        total_order = sku_merged.groupby('SKU_Key')['Order_Qty'].sum()
        pivot_df['累计平均退货率 (%)'] = (total_rtv / total_order).fillna(0)
        
        # 格式化展示为百分比
        formatted_df = pivot_df.applymap(lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
        
    elif metric_choice == "退货数量 (件)":
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='RTV_Qty').fillna(0)
        pivot_df['累计总退货量'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df

    elif metric_choice == "出单数量 (件)":
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='Order_Qty').fillna(0)
        pivot_df['累计总出单量'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df

    else:
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='RTV_Amount').fillna(0)
        pivot_df['累计总退款金额'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df.applymap(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)

    st.dataframe(formatted_df, use_container_width=True)

elif rtv_processed is None or order_processed is None:
    st.info("💡 请在左侧侧边栏上传 **RTV 退货数据** 和 **出单数据** 以计算和展示退货率分析看板。")

# 运行命令: streamlit run app.py
