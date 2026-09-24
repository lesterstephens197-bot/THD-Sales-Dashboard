import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 页面基本配置
st.set_page_config(
    page_title="全流程数据分析看板 (销售/RTV/出单)",
    page_icon="📊",
    layout="wide"
)

st.title("📊 综合数据分析 Dashboard")

# ---------------------------------------------------------
# Sidebar: 3 个数据文件上传入口
# ---------------------------------------------------------
st.sidebar.header("📁 数据文件上传")

sales_file = st.sidebar.file_uploader(
    "1️⃣ 销售数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="sales_upload"
)

rtv_file = st.sidebar.file_uploader(
    "2️⃣ RTV 退货数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="rtv_upload"
)

order_file = st.sidebar.file_uploader(
    "3️⃣ 出单数据 (.xlsx / .csv)", 
    type=["xlsx", "xls", "csv"],
    key="order_upload"
)

st.sidebar.markdown("---")
st.sidebar.header("🔍 全局筛选")

# ---------------------------------------------------------
# 数据读取与清洗函数
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    if file is None:
        return None
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"读取文件 {file.name} 失败: {e}")
        return None

sales_df_raw = load_data(sales_file)
rtv_df_raw = load_data(rtv_file)
order_df_raw = load_data(order_file)

# 1. 销售表清洗
def process_sales(df):
    if df is None:
        return None
    df = df.copy()
    date_col = next((c for c in df.columns if c in ['Order Date', 'Date', '销售日期', '日期']), None)
    sku_col = next((c for c in df.columns if c in ['产品SKU', 'Merchant SKU', 'SKU', 'Vendor SKU']), None)
    qty_col = next((c for c in df.columns if c in ['Quantity', '销售数量', 'Qty', '销量']), None)
    sales_col = next((c for c in df.columns if c in ['Total Cost', '销售金额', 'Total Sales', 'Amount', 'Sales']), None)

    if date_col:
        df['Order Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    if sku_col:
        df['SKU_Key'] = df[sku_col].astype(str).str.strip()
    if qty_col:
        df['Sales_Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    else:
        df['Sales_Qty'] = 1
    if sales_col:
        df['Sales_Amount'] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)
    else:
        df['Sales_Amount'] = 0.0
    return df

# 2. RTV退货表清洗
def process_rtv(df):
    if df is None:
        return None
    df = df.copy()
    date_col = next((c for c in df.columns if c in ['Order Date', 'OrderDate', '退货日期', 'Date']), None)
    sku_col = next((c for c in df.columns if c in ['产品SKU', 'Merchant SKU', 'Vendor SKU', 'SKU']), None)
    qty_col = next((c for c in df.columns if c in ['Quantity', '退货数量', 'Qty']), None)
    amount_col = next((c for c in df.columns if c in ['Total Cost', '退款金额', 'Amount']), None)

    if date_col:
        df['Order Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    if sku_col:
        df['SKU_Key'] = df[sku_col].astype(str).str.strip()
    if qty_col:
        df['RTV_Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    else:
        df['RTV_Qty'] = 1
    if amount_col:
        df['RTV_Amount'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
    else:
        df['RTV_Amount'] = 0.0
    return df

# 3. 出单表清洗（作为退货率的分母依据）
def process_orders(df):
    if df is None:
        return None
    df = df.copy()
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

sales_df = process_sales(sales_df_raw)
rtv_df = process_rtv(rtv_df_raw)
order_df = process_orders(order_df_raw)

# ---------------------------------------------------------
# Dashboard 主内容展示
# ---------------------------------------------------------

# 1. 销售核心指标卡（Sales Overview）
if sales_df is not None:
    st.subheader("📈 销售核心数据概览")
    total_sales_amount = sales_df['Sales_Amount'].sum()
    total_sales_qty = sales_df['Sales_Qty'].sum()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("总销售额 (\()", f"\){total_sales_amount:,.2f}")
    kpi2.metric("总销售量 (件)", f"{int(total_sales_qty):,}")
    
    if rtv_df is not None:
        total_rtv_qty = rtv_df['RTV_Qty'].sum()
        total_rtv_amount = rtv_df['RTV_Amount'].sum()
        kpi3.metric("总退货量 (件)", f"{int(total_rtv_qty):,}")
        kpi4.metric("总退款金额 (\()", f"\){total_rtv_amount:,.2f}")
    st.markdown("---")

# 2. 图表区：月度趋势分析（销售 vs 出单 vs RTV退货）
st.subheader("📊 月度趋势分析与退货率匹配")

# 汇总按月数据
monthly_data = []

if sales_df is not None and 'YearMonth' in sales_df.columns:
    s_m = sales_df.groupby('YearMonth').agg(Sales_Qty=('Sales_Qty', 'sum'), Sales_Amount=('Sales_Amount', 'sum')).reset_index()
    monthly_data.append(s_m)

if rtv_df is not None and 'YearMonth' in rtv_df.columns:
    r_m = rtv_df.groupby('YearMonth').agg(RTV_Qty=('RTV_Qty', 'sum'), RTV_Amount=('RTV_Amount', 'sum')).reset_index()
    monthly_data.append(r_m)

if order_df is not None and 'YearMonth' in order_df.columns:
    o_m = order_df.groupby('YearMonth').agg(Order_Qty=('Order_Qty', 'sum')).reset_index()
    monthly_data.append(o_m)

if monthly_data:
    # 关联所有月度数据
    monthly_merged = monthly_data[0]
    for df_item in monthly_data[1:]:
        monthly_merged = pd.merge(monthly_merged, df_item, on='YearMonth', how='outer')
    
    monthly_merged = monthly_merged.fillna(0).sort_values('YearMonth')
    
    # 计算退货率: 优先使用 [出单表 Order_Qty] 作为基数，若未上传出单表则降级使用 [销售表 Sales_Qty]
    if 'Order_Qty' in monthly_merged.columns and monthly_merged['Order_Qty'].sum() > 0:
        monthly_merged['Return_Rate'] = (monthly_merged['RTV_Qty'] / monthly_merged['Order_Qty']).fillna(0)
        base_label = "出单表数量"
    elif 'Sales_Qty' in monthly_merged.columns and monthly_merged['Sales_Qty'].sum() > 0:
        monthly_merged['Return_Rate'] = (monthly_merged['RTV_Qty'] / monthly_merged['Sales_Qty']).fillna(0)
        base_label = "销售表数量"
    else:
        monthly_merged['Return_Rate'] = 0.0
        base_label = "未指定基数"

    # 左侧：退货数量与退款金额趋势图
    col1, col2 = st.columns(2)
    with col1:
        st.write("**月度退货数量与退款金额趋势 (Order Date)**")
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=monthly_merged['YearMonth'],
            y=monthly_merged['RTV_Qty'] if 'RTV_Qty' in monthly_merged.columns else [0]*len(monthly_merged),
            name='退货数量 (件)',
            marker_color='#d62728'
        ))
        fig1.add_trace(go.Scatter(
            x=monthly_merged['YearMonth'],
            y=monthly_merged['RTV_Amount'] if 'RTV_Amount' in monthly_merged.columns else [0]*len(monthly_merged),
            name='退款金额 ($)',
            yaxis='y2',
            line=dict(color='#ff7f0e', width=3)
        ))
        fig1.update_layout(
            xaxis_title="月份",
            yaxis=dict(title="退货数量 (件)"),
            yaxis2=dict(title="退款金额 ($)", overlaying='y', side='right'),
            legend=dict(x=0.01, y=1.15, orientation="h")
        )
        st.plotly_chart(fig1, use_container_width=True)

    # 右侧：根据出单表计算的退货率折线图
    with col2:
        st.write(f"**月度退货率 (%) 趋势 (对比基数: {base_label})**")
        fig2 = px.line(
            monthly_merged,
            x='YearMonth',
            y='Return_Rate',
            markers=True,
            labels={'Return_Rate': '退货率 (%)', 'YearMonth': '月份'}
        )
        fig2.update_traces(line_color='#1f77b4', line_width=3)
        fig2.update_layout(yaxis_tickformat='.2%')
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 3. 各产品 SKU 的月度退货与销售对比透视表
st.subheader("📦 各产品 SKU 的月度数据透视对比")

metric_choice = st.selectbox(
    "选择透视分析的指标:",
    ["退货率 (%) [RTV/出单表]", "销售金额 (\()", "销售数量 (件)", "出单数量 (件)", "RTV退货数量 (件)", "RTV退款金额 (\))"]
)

# 构建 SKU 粒度的整合数据
sku_dfs = []
if sales_df is not None and 'SKU_Key' in sales_df.columns:
    sku_dfs.append(sales_df.groupby(['SKU_Key', 'YearMonth']).agg(Sales_Qty=('Sales_Qty', 'sum'), Sales_Amount=('Sales_Amount', 'sum')).reset_index())
if rtv_df is not None and 'SKU_Key' in rtv_df.columns:
    sku_dfs.append(rtv_df.groupby(['SKU_Key', 'YearMonth']).agg(RTV_Qty=('RTV_Qty', 'sum'), RTV_Amount=('RTV_Amount', 'sum')).reset_index())
if order_df is not None and 'SKU_Key' in order_df.columns:
    sku_dfs.append(order_df.groupby(['SKU_Key', 'YearMonth']).agg(Order_Qty=('Order_Qty', 'sum')).reset_index())

if sku_dfs:
    sku_merged = sku_dfs[0]
    for d in sku_dfs[1:]:
        sku_merged = pd.merge(sku_merged, d, on=['SKU_Key', 'YearMonth'], how='outer')
    sku_merged = sku_merged.fillna(0)

    # 计算 SKU 级别的退货率 (优先使用出单表)
    if 'Order_Qty' in sku_merged.columns:
        sku_merged['Return_Rate'] = (sku_merged['RTV_Qty'] / sku_merged['Order_Qty']).fillna(0)
    elif 'Sales_Qty' in sku_merged.columns:
        sku_merged['Return_Rate'] = (sku_merged['RTV_Qty'] / sku_merged['Sales_Qty']).fillna(0)
    else:
        sku_merged['Return_Rate'] = 0.0

    # 生成透视表
    if "退货率" in metric_choice:
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='Return_Rate').fillna(0)
        # 计算累计平均退货率
        total_rtv = sku_merged.groupby('SKU_Key')['RTV_Qty'].sum()
        total_base = sku_merged.groupby('SKU_Key')['Order_Qty'].sum() if 'Order_Qty' in sku_merged.columns else sku_merged.groupby('SKU_Key')['Sales_Qty'].sum()
        pivot_df['累计平均退货率 (%)'] = (total_rtv / total_base).fillna(0)
        formatted_df = pivot_df.applymap(lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)

    elif "销售金额" in metric_choice:
        val = 'Sales_Amount' if 'Sales_Amount' in sku_merged.columns else 'RTV_Amount'
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values=val).fillna(0)
        pivot_df['累计销售金额'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df.applymap(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)

    elif "销售数量" in metric_choice:
        val = 'Sales_Qty' if 'Sales_Qty' in sku_merged.columns else 'RTV_Qty'
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values=val).fillna(0)
        pivot_df['累计销售量'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df

    elif "出单数量" in metric_choice:
        val = 'Order_Qty' if 'Order_Qty' in sku_merged.columns else 'Sales_Qty'
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values=val).fillna(0)
        pivot_df['累计出单量'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df

    elif "RTV退货数量" in metric_choice:
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='RTV_Qty').fillna(0)
        pivot_df['累计退货量'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df

    else:
        pivot_df = sku_merged.pivot(index='SKU_Key', columns='YearMonth', values='RTV_Amount').fillna(0)
        pivot_df['累计退款金额'] = pivot_df.sum(axis=1)
        formatted_df = pivot_df.applymap(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)

    st.dataframe(formatted_df, use_container_width=True)

else:
    st.info("💡 请在侧边栏上传数据文件（销售表、RTV表、出单表）以展示透视分析。")
