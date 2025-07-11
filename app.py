import streamlit as st
import pandas as pd

tab1, tab2 = st.tabs(["以损定仓", "期望值模拟器"])
# 页面配置
st.set_page_config(page_title="多币种以损定仓计算器", layout="wide")
st.title("📈 多币种以损定仓位风险控制计算器（按止损百分比 + 吃单手续费）")

# 基础参数输入
account_balance = st.number_input("账户总资金（USDT）", min_value=100.0, value=10000.0, step=100.0)
risk_percent = st.number_input("单笔风险控制比例（%）", min_value=0.1, max_value=100.0, value=3.0, step=0.1)
fee_rate = 0.0005  # 吃单手续费 0.05%

st.markdown("---")
st.subheader("📋 币种参数批量输入")

# 默认数据
default_data = pd.DataFrame({
    '币种': ['BTC', 'ETH'],
    '开仓价格（USDT）': [65000.0, 3500.0],
    '止损幅度（%）': [0.5, 0.6],
    '杠杆倍数': [20, 10]
})

# 表格输入
coin_input = st.data_editor(
    default_data,
    use_container_width=True,
    num_rows="dynamic",
    key="coin_input"
)

st.markdown("---")

# 计算逻辑
if st.button("📊 开始计算"):
    results = []
    risk_amount = account_balance * (risk_percent / 100)
    error_coins = []

    for index, row in coin_input.iterrows():
        try:
            symbol = row['币种']
            entry_price = float(row['开仓价格（USDT）'])
            stop_loss_pct = float(row['止损幅度（%）'])
            leverage = float(row['杠杆倍数'])

            # ✅ 新增：止损点位 = 开仓价 × 止损幅度
            stop_loss_point = entry_price * (stop_loss_pct / 100)
            total_risk_per_coin = stop_loss_point + entry_price * fee_rate
            position_size = risk_amount / total_risk_per_coin
            position_value = position_size * entry_price
            margin_used = position_value / leverage
            total_fee = position_value * fee_rate

            results.append({
                "币种": symbol,
                "开仓价": entry_price,
                "止损%": f"{stop_loss_pct:.2f}%",
                "止损点位（USDT）": round(stop_loss_point, 6),  # ✅ 显示止损点位
                "手续费": round(total_fee * 2, 2),
                "最大亏损": round(risk_amount, 2),
                "可开仓位（币）": round(position_size, 4),
                "持仓价值": round(position_value, 2),
                "所需保证金": round(margin_used, 2),
                "保证金占比": f"{margin_used / account_balance * 100:.2f}%"
            })

        except Exception as e:
            st.warning(f"⚠️ {row['币种']} 行数据异常，跳过：{e}")

    if error_coins:
        st.error("❌ 以下币种止损幅度超过 0.75%，请修改后再计算：\n" + "\n".join(error_coins))
    elif results:
        df_result = pd.DataFrame(results)
        st.success("✅ 计算完成")
        st.dataframe(df_result, use_container_width=True)

        csv = df_result.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下载结果为 CSV 文件", data=csv, file_name="risk_position_result.csv", mime="text/csv")
    else:
        st.warning("⚠️ 没有有效的币种可以计算，请检查输入内容。")

with tab2:
    st.header("🎯 期望值收益模拟器（优化版）")

    def simulate_expectancy(win_rate, rr_ratio, trades_per_month, capital, risk_pct):
        win_rate_pct = win_rate
        win_rate /= 100
        risk_pct /= 100
        risk_amount = capital * risk_pct

        expected_value = win_rate * rr_ratio + (1 - win_rate) * -1
        expected_per_trade = expected_value * risk_amount
        monthly_profit = expected_per_trade * trades_per_month
        monthly_return = monthly_profit / capital
        annual_return = (1 + monthly_return) ** 12 - 1

        st.markdown("### 🧮 模拟结果")
        st.info(f'''
        - ✅ 每单风险金额：`{risk_amount:.2f} USDT`
        - ✅ 每单期望收益：`{expected_per_trade:.2f} USDT`
        - 📈 月预期收益：`{monthly_profit:.2f} USDT`
        - 💰 月收益率：`{monthly_return * 100:.2f}%`
        - 📊 年化收益率（复利）：`{annual_return * 100:.2f}%`
        - ⚖️ 期望值（EV）：`{expected_value:.3f}` （大于0为正期望）
        ''')

        if expected_value < 0:
            st.error("⚠️ 当前组合为 **负期望值策略**，请重新评估胜率或盈亏比。")
        elif expected_value == 0:
            st.warning("⚠️ 当前组合为 **零期望策略**，长期预期收益为 0。")
        else:
            st.success("✅ 当前组合为 **正期望值策略**，具备稳定盈利潜力。")

    with st.form("expectancy_form"):
        col1, col2 = st.columns(2)
        with col1:
            win_rate = st.number_input("胜率（%）", min_value=0.0, max_value=100.0, value=60.0)
            rr_ratio = st.number_input("盈亏比（R:R）", min_value=0.1, step=0.1, value=2.0)
            trades_per_month = st.number_input("每月交易次数", min_value=1, value=30)
        with col2:
            capital = st.number_input("账户本金（USDT）", min_value=10.0, value=10000.0)
            risk_pct = st.number_input("每单风险比例（%）", min_value=0.1, max_value=100.0, value=2.0)

        submitted = st.form_submit_button("📈 开始模拟")
        if submitted:
            simulate_expectancy(win_rate, rr_ratio, trades_per_month, capital, risk_pct)
