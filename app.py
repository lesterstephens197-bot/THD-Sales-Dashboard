import pandas as pd

def get_sku_monthly_returns(df_sales, df_returns, target_sku):
    """
    df_sales: 销售数据表，需包含 ['date', 'sku', 'quantity', 'amount']
    df_returns: 退货数据表，需包含 ['date', 'sku', 'return_quantity', 'return_amount']
    target_sku: 需要查询的 SKU
    """
    # 过滤指定 SKU
    sales_sku = df_sales[df_sales['sku'] == target_sku].copy()
    returns_sku = df_returns[df_returns['sku'] == target_sku].copy()
    
    # 提取月份 (1-12)
    sales_sku['month'] = pd.to_datetime(sales_sku['date']).dt.month
    returns_sku['month'] = pd.to_datetime(returns_sku['date']).dt.month
    
    # 按月汇总销售和退货
    sales_monthly = sales_sku.groupby('month').agg(
        total_sales_qty=('quantity', 'sum'),
        total_sales_amt=('amount', 'sum')
    ).reset_index()
    
    returns_monthly = returns_sku.groupby('month').agg(
        return_qty=('return_quantity', 'sum'),
        return_amt=('return_amount', 'sum')
    ).reset_index()
    
    # 创建 1-12 月的基础数据框，防止某些月份无数据
    result = pd.DataFrame({'month': range(1, 13)})
    result = result.merge(sales_monthly, on='month', how='left').fillna(0)
    result = result.merge(returns_monthly, on='month', how='left').fillna(0)
    
    # 计算退货率
    result['return_rate_qty'] = (result['return_qty'] / result['total_sales_qty'].replace(0, pd.NA)).fillna(0) * 100
    
    # 整理输出列
    result_display = result[['month', 'return_qty', 'return_amt', 'return_rate_qty']].copy()
    result_display.columns = ['月份', '退货数量', '退货金额', '退货率(%)']
    
    return result_display

# 使用示例
# df_result = get_sku_monthly_returns(df_sales, df_returns, 'SKU12345')
# print(df_result)
