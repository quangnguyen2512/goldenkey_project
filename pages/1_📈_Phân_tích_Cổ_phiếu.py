# goldenkey_project/pages/1_📈_Phân_tích_Cổ_phiếu.py
import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Thêm thư mục gốc của dự án vào Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.stock import Stock
from core.analyzer import StockAIAnalyzer
from utils.visualization import plot_stock_chart
# Không import API key từ config nữa

# --- Cấu hình trang ---
st.set_page_config(page_title="Phân Tích Cổ Phiếu (AI)", page_icon="📈", layout="wide")

st.markdown("<h1 style='text-align:center;'>Phân tích Cổ phiếu Toàn diện với Goldenkey AI</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- CACHING: Khởi tạo AI Analyzer (chỉ một lần) ---
@st.cache_resource
def get_ai_analyzer():
    """Khởi tạo và cache đối tượng AI analyzer."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Lỗi: Vui lòng thiết lập Gemini API Key trong Streamlit Secrets (`.streamlit/secrets.toml`).")
            st.stop()
        return StockAIAnalyzer(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi khi khởi tạo AI: {e}")
        st.stop()

analyzer = get_ai_analyzer()

# --- CACHING: Hàm tải và xử lý dữ liệu cổ phiếu ---
@st.cache_data(ttl=3600) # Cache trong 1 giờ
def load_and_process_stock(symbol, years):
    """Tải, xử lý và cache dữ liệu cho một cổ phiếu."""
    stock = Stock(symbol=symbol)
    df_price = stock.fetch_price_history(years=years)
    if df_price.empty:
        return None
    stock.calculate_technical_indicators()
    return stock

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

        # 1. TẠO ĐỐI TƯỢNG STOCK VÀ TẢI DỮ LIỆU (SỬ DỤNG HÀM CACHED)
        with st.spinner(f"Đang tải và xử lý dữ liệu cho {ticker_input}... (có thể nhanh hơn nhờ cache)"):
            stock = load_and_process_stock(ticker_input, years_input)
            if stock is None:
                st.error(f"Không thể tải dữ liệu giá cho {ticker_input}. Vui lòng thử lại.")
                st.stop()

        # Hiển thị thông tin công ty
        with st.expander("ℹ️ Thông tin Tổng quan Doanh nghiệp"):
            # ... (Phần này giữ nguyên không đổi)
            profile_df = stock.get_company_profile()
            if not profile_df.empty:
                profile = profile_df.iloc[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Sàn niêm yết", profile.get('exchange', 'N/A'))
                c2.metric("Vốn hóa (tỷ VND)", f"{profile.get('marketCap', 0):,.0f}")
                c3.metric("Ngành (EN)", profile.get('industryEn', 'N/A'))
                c4.metric("Website", profile.get('website', 'N/A'))
            else:
                st.warning("Không thể tải thông tin doanh nghiệp.")

        # 2. PHÂN TÍCH KỸ THUẬT
        st.subheader("1. Phân tích Kỹ thuật")
        fig = plot_stock_chart(stock)
        st.plotly_chart(fig, use_container_width=True)

        with st.spinner("AI đang phân tích kỹ thuật..."):
            tech_analysis_text = analyzer.analyze_technical(stock)
            with st.expander("Xem kết luận của AI về Phân tích Kỹ thuật", expanded=True):
                st.markdown(tech_analysis_text)
        
        # 3. PHÂN TÍCH CƠ BẢN
        # ... (Phần này giữ nguyên không đổi)
        st.subheader("2. Phân tích Cơ bản")
        fundamental_analyses = []
        report_map = {
            "Báo cáo KQKD": "income_statement",
            "Bảng CĐKT": "balance_sheet",
            "Lưu chuyển tiền tệ": "cash_flow",
            "Chỉ số tài chính": "ratio"
        }
        
        tabs = st.tabs(list(report_map.keys()))
        
        for i, (report_label, report_name) in enumerate(report_map.items()):
            with tabs[i]:
                # ... (Nội dung bên trong tab giữ nguyên)
                with st.spinner(f"Đang xử lý {report_label}..."):
                    df_report = stock.get_financial_report(
                        report_name, period=term_type_value, years=years_input
                    )
                    if not df_report.empty:
                        st.dataframe(df_report)
                        
                        if report_name == 'income_statement':
                            try:
                                fig_income = px.bar(
                                    df_report.sort_values(by=['year', 'quarter']), 
                                    x='reportDate', y=['revenue', 'profitAfterTax'],
                                    title='Tăng trưởng Doanh thu & Lợi nhuận',
                                    labels={'value': 'Tỷ VND', 'reportDate': 'Kỳ báo cáo'},
                                    barmode='group'
                                )
                                st.plotly_chart(fig_income, use_container_width=True)
                            except Exception as e:
                                st.warning(f"Không thể vẽ biểu đồ: {e}")

                        analysis_text = analyzer.analyze_financial_report(df_report, report_name, stock.symbol)
                        fundamental_analyses.append(f"**Phân tích {report_label}:**\n{analysis_text}\n\n")
                        with st.expander(f"Xem phân tích của AI về {report_label}"):
                            st.markdown(analysis_text)
                    else:
                        st.warning(f"Không có dữ liệu cho {report_label}.")

        # 4. TÍCH HỢP PHÂN TÍCH TIN TỨC MỚI
        st.subheader("3. Phân tích Tin tức & Tâm lý Thị trường")
        with st.spinner(f"AI đang tìm và phân tích tin tức về {ticker_input}..."):
            news_df = stock.get_related_news()
            news_analysis_text = analyzer.analyze_news_sentiment(stock.symbol, news_df)
            with st.expander("Xem phân tích của AI về Tin tức", expanded=True):
                st.markdown(news_analysis_text)
                if not news_df.empty:
                    st.dataframe(news_df, use_container_width=True)

        # 5. TỔNG HỢP VÀ ĐƯA RA KHUYẾN NGHỊ (Cập nhật)
        st.subheader("4. Đánh giá Tổng thể & Khuyến nghị của Goldenkey AI")
        with st.spinner("AI đang tổng hợp và đưa ra đánh giá cuối cùng..."):
            summary_text = analyzer.generate_overall_summary(
                stock.symbol, 
                tech_analysis_text, 
                fundamental_analyses,
                news_analysis_text # Thêm dữ liệu phân tích tin tức
            )
            st.markdown(summary_text)

        st.success("✅ Phân tích toàn diện hoàn tất!")