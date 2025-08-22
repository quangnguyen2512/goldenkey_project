# goldenkey_project/pages/1_📈_Phân_tích_Cổ_phiếu.py
import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
# Bỏ import streamlit.components.v1 không cần thiết

# Thêm thư mục gốc của dự án vào Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.stock import Stock
from core.analyzer import StockAIAnalyzer
# SỬA LỖI: Quay lại sử dụng hàm vẽ biểu đồ của Plotly
from utils.visualization import plot_stock_chart_plotly
from config import GEMINI_API_KEY

# --- Cấu hình trang ---
st.set_page_config(page_title="Phân Tích Cổ Phiếu (AI)", page_icon="📈", layout="wide")
st.markdown("<h1 style='text-align:center;'>Phân tích Cổ phiếu Toàn diện với Goldenkey AI</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Khởi tạo AI Analyzer (chỉ một lần) ---
if 'analyzer' not in st.session_state:
    try:
        api_key = GEMINI_API_KEY or st.secrets.get("GEMINI_API_KEY")
        if not api_key or "YOUR_GEMINI_API_KEY" in api_key:
            st.error("Lỗi: Vui lòng thiết lập Gemini API Key trong `config.py` hoặc Streamlit Secrets.")
            st.stop()
        st.session_state.analyzer = StockAIAnalyzer(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi khi khởi tạo AI: {e}")
        st.stop()

# --- Giao diện nhập liệu ---
st.markdown("### Cấu hình Phân tích:")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker_input = st.text_input("Nhập mã cổ phiếu (ví dụ: FPT, HPG):", key="ticker_input").upper().strip()
with col2:
    years_input = st.slider("Số năm dữ liệu:", 1, 10, 3, key="years_slider")
with col3:
    term_type_map = {"Quý": "quarter", "Năm": "year"}
    term_type_label = st.selectbox("Chu kỳ BCTC:", list(term_type_map.keys()), key="term_type_select")
    term_type_value = term_type_map[term_type_label]

if st.button("🚀 Khởi động Phân tích", type="primary", use_container_width=True):
    if not ticker_input:
        st.error("⚠️ Vui lòng nhập mã cổ phiếu!")
    else:
        st.markdown("---")
        st.header(f"Kết quả phân tích cho cổ phiếu: {ticker_input}")

        # 1. TẠO ĐỐI TƯỢNG STOCK VÀ TẢI DỮ LIỆU
        with st.spinner(f"Đang tải dữ liệu cho {ticker_input}..."):
            stock = Stock(symbol=ticker_input)
            df_price = stock.fetch_price_history(years=years_input)
            if df_price.empty:
                st.error(f"Không thể tải dữ liệu giá cho {ticker_input}. Vui lòng thử lại.")
                st.stop()
            stock.calculate_technical_indicators()

        # (Phần hiển thị thông tin công ty giữ nguyên)

        # 2. PHÂN TÍCH KỸ THUẬT
        st.subheader("1. Phân tích Kỹ thuật")
        
        # SỬA LỖI: Quay lại sử dụng st.plotly_chart
        with st.spinner("Đang vẽ biểu đồ kỹ thuật..."):
            fig = plot_stock_chart_plotly(stock)
            st.plotly_chart(fig, use_container_width=True)

        # (Phần phân tích của AI và phân tích cơ bản giữ nguyên)
        with st.spinner("AI đang phân tích biểu đồ kỹ thuật..."):
            tech_analysis_text = st.session_state.analyzer.analyze_technical(stock)
            with st.expander("Xem kết luận của AI về Phân tích Kỹ thuật", expanded=True):
                st.markdown(tech_analysis_text)
        
        st.subheader("2. Phân tích Cơ bản")
        # ... (toàn bộ code phần phân tích cơ bản và tổng hợp không thay đổi)
        # ...

        st.success("✅ Phân tích toàn diện hoàn tất!")