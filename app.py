import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as px_go

# 页面基础配置
st.set_page_config(page_title="RTV退货与出单分析看板", layout="wide")

st.title("📦 RTV 退货与出单分析 Dashboard")

# -----------------------------------------------------------------------------
# 1. 侧边栏：文件上传与配置
# -----------------------------------------------------------------------------
st.sidebar.header("📁 数据文件上传")

# 1.1 出单/销售数据上传（新指定的表头结构）
order_file = st.sidebar.file_uploader(
    "1️⃣ 上传【出单数据】(.xlsx)", 
    type=["xlsx", "xls"],
    help="表头包含：Line Status, PO Number, Order Date, Merchant SKU, Vendor SKU, 产品名称, 产品SKU, Quantity 等"
)

# 1.2 RTV 退货数据上传
rtv_file = st.sidebar.file_uploader("2️⃣ 上传【RTV 退货数据】(.xlsx)", type=["xlsx", "xls"])

# -----------------------------------------------------------------------------
# 2. 数据处理函数
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(order_file, rtv_file):
    if not order_file or not rtv_file:
        return None, None

    # 读取出单表
    df_order = pd.read_excel(order_file)
    # 读取 RTV 退货表
    df_rtv = pd.read_excel(rtv_file)

    # ---------------- 2.1 处理出单数据 ----------------
    # 确保日期格式正确
    df_order['Order Date'] = pd.to_datetime(df_order['Order Date'], errors='coerce')
    df_order['YearMonth'] = df_order['Order Date'].dt.to_period('M').astype(str)
    
    # 确保 Quantity 数量字段为数值型
    df_order['Quantity'] = pd.to_numeric(df_order['Quantity'], errors='coerce').fillna(0)
    
    # 统一 SKU 字段名称与字符串格式
    df_order['产品SKU'] = df_order['产品SKU'].astype(str).str.strip()

    # ---------------- 2.2 处理 RTV 退货数据 ----------------
    # 根据实际列名调整（如 Return Date / RTV Date、Return Qty、Refund Amount、SKU 等）
    # 自动识别可能存在的列名
    rtv_date_col = next((col for col in ['Order Date', 'Return Date', 'RTV Date', '退货日期', '日期'] if col in df_rtv.columns), df_rtv.columns[0])
    rtv_sku_col = next((col for col in ['产品SKU', 'Merchant SKU', 'SKU', '产品sku'] if col in df_rtv.columns), df_rtv.columns[1])
    rtv_qty_col = next((col for col in ['Quantity', 'Return Qty', '退货数量', '数量'] if col in df_rtv.columns), None)
    rtv_amount_col = next((col for col in ['Total Cost', 'Refund Amount', '退款金额', '金额'] if col in df_rtv.columns), None)

    df_rtv['Return_Date'] = pd.to_datetime(df_rtv[rtv_date_col], errors='coerce')
    df_rtv['YearMonth'] = df_rtv['Return_Date'].dt.to_period('M').astype(str)
    df_rtv['产品SKU'] = df_rtv[rtv_sku_col].astype(str).str.strip()
    
    df_rtv['Return_Qty'] = pd.to_numeric(df_rtv[rtv_qty_col], errors='coerce').fillna(0) if rtv_qty_col else 1
    df_rtv['Refund_Amount'] = pd.to_numeric(df_rtv[rtv_amount_col], errors='coerce').fillna(0) if rtv_amount_col else 0

    return df_order, df_rtv

# -----------------------------------------------------------------------------
# 3. 主页面渲染与计算
# -----------------------------------------------------------------------------
if order_file and rtv_file:
    df_order, df_rtv = load_data(order_file, rtv_file)

    if df_order is not None and df_rtv is not None:
        
        # ---------------- 3.1 基础聚合计算 ----------------
        # 按月份 + SKU 聚合出单量
        order_sku_monthly = df_order.groupby(['YearMonth', '产品SKU'])['Quantity'].sum().reset_index()
        order_sku_monthly.rename(columns={'Quantity': '出单数量'}, inplace=True)

        # 按月份 + SKU 聚合退货量和退款金额
        rtv_sku_monthly = df_rtv.groupby(['YearMonth', '产品SKU']).agg(
            退货数量=('Return_Qty', 'sum'),
            退款金额=('Refund_Amount', 'sum')
        ).reset_index()

        # 合并出单与退货数据
        merged_df = pd.merge(order_sku_monthly, rtv_sku_monthly, on=['YearMonth', '产品SKU'], how='outer').fillna(0)
        
        # 计算退货率 (%)
        merged_df['退货率 (%)'] = np.where(
            merged_df['出单数量'] > 0, 
            (merged_df['退货数量'] / merged_df['出单数量']) * 100, 
            0
        )

        # ---------------- 3.2 月度整体趋势汇总 ----------------
        monthly_summary = merged_df.groupby('YearMonth').agg(
            总出单量=('出单数量', 'sum'),
            总退货量=('退货数量', 'sum'),
            总退款金额=('退款金额', 'sum')
        ).reset_index()

        monthly_summary['月度退货率 (%)'] = np.where(
            monthly_summary['总出单量'] > 0,
            (monthly_summary['总退货量'] / monthly_summary['总出单量']) * 100,
            0
        )

        # ---------------- 3.3 图表渲染 ----------------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("月度退货数量与退款金额趋势 (Order Date)")
            fig1 = px_go.Figure()
            # 柱状图：退货数量
            fig1.add_trace(px_go.Bar(
                x=monthly_summary['YearMonth'], 
                y=monthly_summary['总退货量'], 
                name='退货数量 (件)', 
                marker_color='#d62728'
            ))
            # 折线图：退款金额
            fig1.add_trace(px_go.Scatter(
                x=monthly_summary['YearMonth'], 
                y=monthly_summary['总退货金额'], 
                name='退款金额 ($)', 
                yaxis='y2', 
                line=dict(color='#ff7f0e', width=3)
            ))
            fig1.update_layout(
                xaxis=dict(title='月份'),
                yaxis=dict(title='退货数量 (件)'),
                yaxis2=dict(title='退款金额 ($)', overlaying='y', side='right'),
                legend=dict(x=0.7, y=1.1, orientation="h")
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("月度退货率 (%) 趋势 (Order Date)")
            fig2 = px.line(
                monthly_summary, 
                x='YearMonth', 
                y='月度退货率 (%)', 
                markers=True,
                labels={'月度退货率 (%)': '退货率 (%)', 'YearMonth': 'YearMonth'}
            )
            fig2.update_traces(line_color='#0068c9', line_width=2.5)
            st.plotly_chart(fig2, use_container_width=True)

        # ---------------- 3.4 透视对比表 ----------------
        st.markdown("---")
        st.subheader("📦 各产品 SKU 的月度退货对比表")

        metric_option = st.selectbox("选择透视分析的指标:", ["退货率 (%)", "退货数量", "出单数量", "退款金额"])

        # 生成透视表
        pivot_df = merged_df.pivot_table(
            index='产品SKU', 
            columns='YearMonth', 
            values=metric_option, 
            aggfunc='sum', 
            fill_value=0
        ).reset_index()

        # 计算累计/平均指标
        if metric_option == "退货率 (%)":
            sku_total = merged_df.groupby('产品SKU').agg(
                总出量=('出单数量', 'sum'),
                总退量=('退货数量', 'sum')
            )
            sku_total['累计平均退货率 (%)'] = np.where(sku_total['总出量'] > 0, (sku_total['总退量'] / sku_total['总出量']) * 100, 0)
            pivot_df = pivot_df.merge(sku_total[['累计平均退货率 (%)']], on='产品SKU', how='left')
        else:
            pivot_df['合计'] = pivot_df.iloc[:, 1:].sum(axis=1)

        # 格式化显示数值
        st.dataframe(pivot_df.style.format(precision=2), use_container_width=True)

else:
    st.info("💡 请在左侧边栏上传【出单数据】与【RTV退货数据】以开始分析。")
