import streamlit as st
import pandas as pd

st.set_page_config(page_title="数据表处理工具", layout="wide")

st.title("📊 数据表上传与处理工具")
st.write("请在下方分别上传对应的数据表格：")

# 创建三列展示 3 个上传窗口
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. 销售数据表")
    sales_file = st.file_uploader("上传销售数据表", type=["xlsx", "xls", "csv"], key="sales")

with col2:
    st.subheader("2. RTV表")
    rtv_file = st.file_uploader("上传RTV表", type=["xlsx", "xls", "csv"], key="rtv")

with col3:
    st.subheader("3. 出单表")
    order_file = st.file_uploader("上传出单表", type=["xlsx", "xls", "csv"], key="order")

# 辅助读取函数
def load_data(file):
    if file is not None:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    return None

# 读取上传的文件
df_sales = load_data(sales_file)
df_rtv = load_data(rtv_file)
df_order = load_data(order_file)

st.divider()

# 显示已上传文件的预览
st.header("🔍 数据预览")

if df_sales is not None:
    with st.expander("销售数据表预览", expanded=True):
        st.dataframe(df_sales.head())
else:
    st.info("👈 请上传 销售数据表")

if df_rtv is not None:
    with st.expander("RTV表预览", expanded=True):
        st.dataframe(df_rtv.head())
else:
    st.info("👈 请上传 RTV表")

if df_order is not None:
    with st.expander("出单表预览", expanded=True):
        st.dataframe(df_order.head())
else:
    st.info("👈 请上传 出单表")

# 当 3 个表格都上传完成后，可进行数据处理
if df_sales is not None and df_rtv is not None and df_order is not None:
    st.success("🎉 所有表格已成功上传！")
    
    if st.button("开始处理数据", type="primary"):
        # TODO: 在此处添加你的数据处理/匹配逻辑
        st.write("正在处理数据，请稍候...")
        
        # 示例逻辑：你可以替换为实际业务逻辑
        # processed_df = ... 
        
        st.success("数据处理完成！")
