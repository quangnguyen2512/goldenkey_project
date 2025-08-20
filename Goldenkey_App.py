# Goldenkey_App.py

import streamlit as st

# --- Cấu hình trang (phải là lệnh đầu tiên của Streamlit) ---
st.set_page_config(
    page_title="Trang chủ | Dự án Goldenkey",
    page_icon="🔑",
    layout="centered", # 'centered' hoặc 'wide'
    initial_sidebar_state="auto" # 'auto', 'expanded', 'collapsed'
)

# --- Nội dung Trang chủ ---

# 🚀 Tiêu đề và Giới thiệu
st.title("🔑 Chào mừng đến với Dự án Goldenkey")
st.markdown(
    "Một nền tảng phân tích và đầu tư chứng khoán thông minh, "
    "sử dụng sức mạnh của Trí tuệ Nhân tạo để mang lại những góc nhìn chuyên sâu."
)
st.markdown("---")


# 🧭 Hướng dẫn sử dụng
st.header("Bắt đầu như thế nào?")
st.info("Sử dụng thanh điều hướng bên trái để truy cập các công cụ phân tích chính:")

st.subheader("1. 📈 Phân tích Cổ phiếu")
st.write(
    "Đi sâu vào phân tích toàn diện một mã cổ phiếu duy nhất. Công cụ sẽ cung cấp: "
    "\n- Biểu đồ kỹ thuật trực quan với các chỉ báo quan trọng."
    "\n- Phân tích chi tiết về Báo cáo Tài chính (Cơ bản)."
    "\n- Đánh giá và khuyến nghị từ Goldenkey AI."
)

st.subheader("2. 📊 Phân bổ Danh mục")
st.write(
    "Xây dựng và tối ưu hóa danh mục đầu tư của bạn dựa trên Lý thuyết Danh mục Hiện đại. Công cụ giúp bạn:"
    "\n- Tìm ra tỷ trọng phân bổ tối ưu để giảm thiểu rủi ro cho một mức lợi nhuận mục tiêu."
    "\n- So sánh hiệu suất của danh mục với các chỉ số thị trường."
    "\n- Trực quan hóa đường biên hiệu quả."
)

st.subheader("3. 📥 Tải dữ liệu")
st.write(
    "Dễ dàng xuất dữ liệu giá lịch sử của nhiều mã cổ phiếu ra file Excel để phục vụ cho các nhu cầu phân tích riêng."
)


# --- Chân trang ---
st.markdown("---")
st.markdown(
    "<p style='text-align:center; font-size: 0.9rem; color: #888;'>"
    "Được phát triển bởi NTDStock | Thông tin chỉ mang tính chất tham khảo."
    "</p>",
    unsafe_allow_html=True
)