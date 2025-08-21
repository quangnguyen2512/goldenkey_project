# goldenkey_project/pages/2_📊_Phân_bổ_Danh_mục.py
import streamlit as st
import pandas as pd
from core.portfolio import Portfolio
from utils.visualization import plot_efficient_frontier, prepare_echarts_sunburst_data, plot_cumulative_returns
from config import DEFAULT_STOCK_SYMBOLS, MONTE_CARLO_ITERATIONS
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="Phân bổ Danh mục", page_icon="📊", layout="wide")

st.title("📊 Công cụ Tối ưu hóa Danh mục đầu tư")
st.markdown("Tìm kiếm các danh mục tối ưu dựa trên mô phỏng Monte Carlo theo Lý thuyết Danh mục Hiện đại.")
st.markdown("---")

# --- Hàm hỗ trợ để hiển thị thông tin chi tiết của danh mục ---
def display_portfolio_details(portfolio_obj: Portfolio, portfolio_series: pd.Series, cash_weight: float, risk_free_rate: float, symbols: list, title: str):
    """Hàm hỗ trợ hiển thị thông tin chi tiết cho một danh mục tối ưu."""
    
    st.header(title)
    if "Sharpe" in title:
        st.markdown("Danh mục này cân bằng tốt nhất giữa lợi nhuận và rủi ro.")
    else:
        st.markdown("Danh mục này tập trung vào việc đạt lợi nhuận cao nhất, thường đi kèm với rủi ro cao hơn.")

    st.subheader("Các chỉ số chính của danh mục")
    p_return = portfolio_series['return']
    p_vol = portfolio_series['volatility']
    p_sharpe = portfolio_series['sharpe']

    # Điều chỉnh các chỉ số theo tỷ trọng tiền mặt
    total_return = p_return * (1 - cash_weight) + risk_free_rate * cash_weight
    total_vol = p_vol * (1 - cash_weight)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Lợi nhuận kỳ vọng (toàn DM)", f"{total_return:.2%}")
    c2.metric("Rủi ro (toàn DM)", f"{total_vol:.2%}")
    c3.metric("Tỷ lệ Sharpe (phần cổ phiếu)", f"{p_sharpe:.2f}")

    # Lấy tỷ trọng cổ phiếu
    stock_weights = portfolio_series[symbols].values
    
    # Tính toán hiệu suất tích lũy
    with st.spinner("Đang tính toán hiệu suất lịch sử..."):
        performance_df = portfolio_obj.calculate_cumulative_performance(
            stock_weights=stock_weights,
            cash_weight=cash_weight,
            risk_free_rate=risk_free_rate
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Phân bổ Tỷ trọng")
        # Tạo dataframe tỷ trọng, đã bao gồm tỷ trọng tiền mặt
        weights_df = pd.DataFrame(stock_weights * (1 - cash_weight), index=symbols, columns=['Tỷ trọng'])
        if cash_weight > 0:
            cash_df = pd.DataFrame([cash_weight], index=['Tiền mặt'], columns=['Tỷ trọng'])
            weights_df = pd.concat([weights_df, cash_df])
        st.dataframe(weights_df.style.format({'Tỷ trọng': "{:.2%}"}))

    with col2:
        st.subheader("Biến động của danh mục (1 năm qua)")
        fig_perf = plot_cumulative_returns(performance_df, title=f"Hiệu suất {title}")
        st.plotly_chart(fig_perf, use_container_width=True)

# --- Giao diện nhập liệu ---
st.sidebar.header("Cấu hình Danh mục")
symbols_input = st.sidebar.text_area(
    "Nhập mã cổ phiếu (cách nhau bởi dấu phẩy)",
    ", ".join(DEFAULT_STOCK_SYMBOLS)
)

years_input = st.sidebar.slider("Số năm dữ liệu lịch sử", 1, 10, 3)
risk_free_rate_input = st.sidebar.slider("Lãi suất phi rủi ro (%)", 1.0, 10.0, 4.0, 0.1) / 100
cash_weight_input = st.sidebar.slider("Tỷ trọng tiền mặt trong danh mục (%)", 0, 100, 0, 1) / 100

# --- THÊM PHẦN RÀNG BUỘC ---
st.sidebar.header("Ràng buộc Tỷ trọng Cổ phiếu")
st.sidebar.caption("Áp dụng cho phần danh mục cổ phiếu.")
min_weight_input = st.sidebar.slider("Tỷ trọng tối thiểu cho mỗi CP (%)", 0, 40, 10, 1) / 100
max_weight_input = st.sidebar.slider("Tỷ trọng tối đa cho mỗi CP (%)", 10, 100, 60, 1) / 100

if st.sidebar.button("🚀 Chạy Tối ưu hóa", use_container_width=True):
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
    if len(symbols) < 2:
        st.error("Vui lòng nhập ít nhất hai mã cổ phiếu.")
    else:
        # --- THÊM PHẦN KIỂM TRA RÀNG BUỘC ---
        if min_weight_input >= max_weight_input:
            st.sidebar.error("Tỷ trọng tối thiểu phải nhỏ hơn tỷ trọng tối đa.")
            st.stop()
        
        # Kiểm tra xem ràng buộc có khả thi về mặt toán học không
        if len(symbols) * min_weight_input > 1.0:
            st.sidebar.error(f"Ràng buộc không khả thi: Tổng các tỷ trọng tối thiểu ({len(symbols) * min_weight_input:.0%}) đã vượt quá 100%. Vui lòng giảm số lượng cổ phiếu hoặc giảm tỷ trọng tối thiểu.")
            st.stop()
        
        with st.spinner("Đang tải và xử lý dữ liệu..."):
            portfolio = Portfolio(symbols=symbols)
            if not portfolio.fetch_data(years=years_input):
                st.error("Xảy ra lỗi khi tải dữ liệu. Vui lòng kiểm tra lại mã cổ phiếu.")
                st.stop()
            portfolio.calculate_stats()
        
        with st.spinner(f"Thực hiện mô phỏng Monte Carlo ({MONTE_CARLO_ITERATIONS} lần)... Điều này có thể mất chút thời gian với các ràng buộc chặt."):
            # --- TRUYỀN RÀNG BUỘC VÀO HÀM ---
            mc_results = portfolio.run_monte_carlo(
                risk_free_rate=risk_free_rate_input, 
                iterations=MONTE_CARLO_ITERATIONS,
                min_weight=min_weight_input,
                max_weight=max_weight_input
            )

        # Kiểm tra xem có kết quả trả về không
        if mc_results.empty:
            st.warning("Không tìm thấy danh mục nào thỏa mãn các ràng buộc đã cho. Vui lòng nới lỏng các điều kiện (ví dụ: giảm Tỷ trọng tối thiểu) và thử lại.")
            st.stop()

        max_sharpe_port, max_return_port = portfolio.get_optimal_portfolios_from_mc(mc_results)

        if max_sharpe_port.empty or max_return_port.empty:
             st.warning("Không tìm thấy danh mục tối ưu. Vui lòng thử lại.")
             st.stop()

        st.header("Kết quả Tối ưu hóa Danh mục")
        st.info("Dưới đây là hai danh mục nổi bật được tìm thấy từ hàng ngàn kịch bản mô phỏng.")

        tab1, tab2 = st.tabs(["📊 Danh mục Sharpe Tối đa", "🚀 Danh mục Lợi nhuận Tối đa"])

        with tab1:
            display_portfolio_details(
                portfolio_obj=portfolio,
                portfolio_series=max_sharpe_port,
                cash_weight=cash_weight_input,
                risk_free_rate=risk_free_rate_input,
                symbols=symbols,
                title="Danh mục Sharpe Tối đa"
            )

        with tab2:
            display_portfolio_details(
                portfolio_obj=portfolio,
                portfolio_series=max_return_port,
                cash_weight=cash_weight_input,
                risk_free_rate=risk_free_rate_input,
                symbols=symbols,
                title="Danh mục Lợi nhuận Tối đa"
            )
        
        st.markdown("---")
        st.header("So sánh Phân bổ Danh mục theo Ngành")

        col_sharpe, col_return = st.columns(2)

        with col_sharpe:
            st.subheader("Danh mục Sharpe Tối đa")
            sharpe_stock_weights = max_sharpe_port[symbols]
            sharpe_weights_df = pd.DataFrame(sharpe_stock_weights).rename(columns={max_sharpe_port.name: 'Tỷ trọng'})
            sharpe_weights_df = sharpe_weights_df[sharpe_weights_df['Tỷ trọng'] > 0.001]
            
            if not sharpe_weights_df.empty:
                sharpe_echarts_json = prepare_echarts_sunburst_data(sharpe_weights_df.copy())
                sharpe_echarts_data = json.loads(sharpe_echarts_json)
                
                echarts_html_sharpe = f"""
                <div id="echarts_sharpe" style="width: 100%; height: 500px;"></div>
                <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
                <script type="text/javascript">
                    var chartDomSharpe = document.getElementById('echarts_sharpe');
                    var myChartSharpe = echarts.init(chartDomSharpe);
                    var chartDataSharpe = {json.dumps(sharpe_echarts_data)};
                    var optionSharpe = {{
                        tooltip: {{ trigger: 'item', formatter: function (p) {{ return p.name + ': ' + (p.value * 100).toFixed(2) + '%'; }} }},
                        series: [
                            {{ name: 'Ngành', type: 'pie', selectedMode: 'single', radius: [0, '35%'], label: {{ position: 'inner', fontSize: 12, formatter: '{{b}}\\n{{d}}%' }}, data: chartDataSharpe.innerRingData }},
                            {{ name: 'Cổ phiếu', type: 'pie', radius: ['50%', '70%'], label: {{ formatter: '{{b}}: {{d}}%' }}, data: chartDataSharpe.outerRingData }}
                        ]
                    }};
                    myChartSharpe.setOption(optionSharpe);
                </script>
                """
                components.html(echarts_html_sharpe, height=520)
            else:
                st.info("Không có cổ phiếu để phân tích.")

        with col_return:
            st.subheader("Danh mục Lợi nhuận Tối đa")
            return_stock_weights = max_return_port[symbols]
            return_weights_df = pd.DataFrame(return_stock_weights).rename(columns={max_return_port.name: 'Tỷ trọng'})
            return_weights_df = return_weights_df[return_weights_df['Tỷ trọng'] > 0.001]

            if not return_weights_df.empty:
                return_echarts_json = prepare_echarts_sunburst_data(return_weights_df.copy())
                return_echarts_data = json.loads(return_echarts_json)
                
                echarts_html_return = f"""
                <div id="echarts_return" style="width: 100%; height: 500px;"></div>
                <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
                <script type="text/javascript">
                    var chartDomReturn = document.getElementById('echarts_return');
                    var myChartReturn = echarts.init(chartDomReturn);
                    var chartDataReturn = {json.dumps(return_echarts_data)};
                    var optionReturn = {{
                        tooltip: {{ trigger: 'item', formatter: function (p) {{ return p.name + ': ' + (p.value * 100).toFixed(2) + '%'; }} }},
                        series: [
                            {{ name: 'Ngành', type: 'pie', selectedMode: 'single', radius: [0, '35%'], label: {{ position: 'inner', fontSize: 12, formatter: '{{b}}\\n{{d}}%' }}, data: chartDataReturn.innerRingData }},
                            {{ name: 'Cổ phiếu', type: 'pie', radius: ['50%', '70%'], label: {{ formatter: '{{b}}: {{d}}%' }}, data: chartDataReturn.outerRingData }}
                        ]
                    }};
                    myChartReturn.setOption(optionReturn);
                </script>
                """
                components.html(echarts_html_return, height=520)
            else:
                st.info("Không có cổ phiếu để phân tích.")

        st.markdown("---")
        st.header("Đường biên Hiệu quả & Các Danh mục Mô phỏng")
        fig_ef = plot_efficient_frontier(mc_results, portfolio.symbols)
        st.plotly_chart(fig_ef, use_container_width=True)