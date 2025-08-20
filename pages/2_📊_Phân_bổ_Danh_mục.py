# goldenkey_project/pages/2_📊_Phân_bổ_Danh_mục.py
import streamlit as st
import pandas as pd
from core.portfolio import Portfolio
from utils.visualization import plot_efficient_frontier, plot_portfolio_pie
from config import DEFAULT_STOCK_SYMBOLS

st.set_page_config(page_title="Phân bổ Danh mục", page_icon="📊", layout="wide")

st.title("📊 Công cụ Tối ưu hóa Danh mục đầu tư")
st.markdown("Xây dựng danh mục tối ưu dựa trên Lý thuyết Danh mục Hiện đại (Markowitz).")
st.markdown("---")

# --- Giao diện nhập liệu ---
st.sidebar.header("Cấu hình Danh mục")
symbols_input = st.sidebar.text_area(
    "Nhập mã cổ phiếu (cách nhau bởi dấu phẩy)",
    ", ".join(DEFAULT_STOCK_SYMBOLS)
)

years_input = st.sidebar.slider("Số năm dữ liệu lịch sử", 1, 10, 3)
target_return_input = st.sidebar.slider("Lợi nhuận mục tiêu hàng năm (%)", 5.0, 50.0, 15.0, 0.5) / 100
risk_free_rate_input = st.sidebar.slider("Lãi suất phi rủi ro (%)", 1.0, 10.0, 4.0, 0.1) / 100

if st.sidebar.button("🚀 Chạy Tối ưu hóa", use_container_width=True):
    symbols = [s.strip() for s in symbols_input.split(',')]
    if len(symbols) < 2:
        st.error("Vui lòng nhập ít nhất hai mã cổ phiếu.")
    else:
        with st.spinner("Đang tải và xử lý dữ liệu..."):
            portfolio = Portfolio(symbols=symbols)
            if not portfolio.fetch_data(years=years_input):
                st.error("Xảy ra lỗi khi tải dữ liệu. Vui lòng kiểm tra lại mã cổ phiếu.")
                st.stop()
            portfolio.calculate_stats()
        
        with st.spinner("Thực hiện mô phỏng Monte Carlo..."):
            mc_results = portfolio.run_monte_carlo(risk_free_rate=risk_free_rate_input)

        with st.spinner("Tìm kiếm danh mục tối ưu với CVXPY..."):
            optimal_weights, status = portfolio.optimize_portfolio(target_return=target_return_input)
        
        st.success("Phân tích hoàn tất!")
        st.markdown("---")
        
        # --- Hiển thị kết quả ---
        st.header("Kết quả Phân bổ Tối ưu")
        
        if optimal_weights is not None:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader(f"Lợi nhuận mục tiêu: {target_return_input:.2%}")
                st.write("Tỷ trọng phân bổ để tối thiểu hóa rủi ro:")
                weights_df = pd.DataFrame(optimal_weights, index=symbols, columns=['Tỷ trọng'])
                st.dataframe(weights_df.style.format({'Tỷ trọng': "{:.2%}"}))
            with col2:
                fig_pie = plot_portfolio_pie(weights_df)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning(f"Không tìm thấy danh mục tối ưu cho mức lợi nhuận mục tiêu. Trạng thái: {status}")

        st.markdown("---")
        st.header("Đường biên Hiệu quả & Các Danh mục Mô phỏng")
        fig_ef = plot_efficient_frontier(mc_results, portfolio.symbols)
        st.plotly_chart(fig_ef, use_container_width=True)