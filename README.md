# 🔑 Dự án Goldenkey - Nền tảng Phân tích Chứng khoán bằng AI

![Goldenkey](https://lh3.googleusercontent.com/IptI0l4qwnBlf_bgWVNu19cTkMHRlYaoDTHc0eluOC65CqEhRIYtI9BiwL0wci6Bo6CV3ptwhVMvzSuMu6HPMZItLQyLCdy4=w150-rw)

**Dự án Goldenkey** là một ứng dụng web được xây dựng bằng Streamlit, cung cấp bộ công cụ mạnh mẽ để phân tích và tối ưu hóa đầu tư chứng khoán tại thị trường Việt Nam. Nền tảng này kết hợp dữ liệu thị trường, các mô hình tài chính định lượng và sức mạnh của Trí tuệ Nhân tạo (Google Gemini) để đưa ra những phân tích sâu sắc và trực quan.

---

## ✨ Các tính năng chính

- **Phân tích Cổ phiếu Toàn diện**:
  - 📈 **Phân tích Kỹ thuật**: Biểu đồ giá nến tương tác với các chỉ báo phổ biến như MA, MACD, RSI và các ngưỡng Fibonacci.
  - 🏦 **Phân tích Cơ bản**: Tự động truy xuất, hiển thị và trực quan hóa các báo cáo tài chính.
  - 🤖 **Phân tích của AI**: Tận dụng mô hình Google Gemini để đưa ra các nhận định, đánh giá và tóm tắt về cả kỹ thuật và cơ bản một cách tự động.

- **Tối ưu hóa Danh mục đầu tư**:
  - 📊 **Lý thuyết Danh mục Hiện đại (Markowitz)**: Tìm ra tỷ trọng phân bổ tối ưu để tối thiểu hóa rủi ro cho một mức lợi nhuận mục tiêu.
  - 💵 **Tùy chọn Tiền mặt**: Cho phép thêm tỷ trọng tiền mặt vào danh mục để quản lý rủi ro linh hoạt.
  - 🌐 **Đường biên Hiệu quả**: Trực quan hóa hàng ngàn danh mục mô phỏng qua Monte Carlo để tìm ra các danh mục tối ưu.

- **Tiện ích Dữ liệu**:
  - 📥 **Tải dữ liệu**: Dễ dàng xuất dữ liệu giá lịch sử của nhiều mã cổ phiếu ra file Excel.

---

## 🚀 Cài đặt và Khởi chạy

Để chạy dự án trên máy của bạn, hãy làm theo các bước sau:

### 1. Yêu cầu tiên quyết
- [Python 3.8+](https://www.python.org/downloads/)

### 2. Sao chép (Clone) Repository
Mở Terminal hoặc Command Prompt và chạy lệnh sau:

git clone [https://github.com/your-username/goldenkey-project.git](https://github.com/quangnguyen2512/goldenkey_project.git)
cd goldenkey-project

3. Cài đặt các thư viện cần thiết
Tạo một môi trường ảo (khuyến khích) và cài đặt các gói từ tệp requirements.txt.

# Tạo và kích hoạt môi trường ảo (macOS/Linux)
python3 -m venv .venv
source .venv/bin/activate

# Tạo và kích hoạt môi trường ảo (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# Cài đặt các thư viện
pip install -r requirements.txt
4. Cấu hình API Key
Tạo tệp secrets: Bên trong thư mục dự án, tạo một thư mục mới có tên .streamlit.

Thêm API Key: Bên trong thư mục .streamlit, tạo một tệp mới tên là secrets.toml và thêm vào nội dung sau:

Ini, TOML

# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
(Lưu ý: Thay thế YOUR_GEMINI_API_KEY_HERE bằng API Key của bạn lấy từ Google AI Studio.)

5. Khởi chạy ứng dụng
Sau khi cài đặt xong, chạy lệnh sau từ thư mục gốc của dự án:

Bash

streamlit run Goldenkey_App.py
Ứng dụng sẽ tự động mở trên trình duyệt của bạn.

🛠️ Công nghệ sử dụng
Ngôn ngữ: Python

Giao diện Web: Streamlit

Thư viện Phân tích Dữ liệu: Pandas, NumPy

Dữ liệu Chứng khoán Việt Nam: vnstock

Mô hình AI: Google Gemini

Trực quan hóa Dữ liệu: Plotly, Matplotlib, Seaborn

Tối ưu hóa Danh mục: CVXPY

Chỉ báo Kỹ thuật: Pandas TA

📂 Cấu trúc Dự án
Dự án được tổ chức theo cấu trúc module hóa, tách biệt rõ ràng giữa logic nghiệp vụ, giao diện người dùng và các tiện ích.

Bash

goldenkey_project/
├── .streamlit/
│   └── secrets.toml          # Tệp chứa API key và các biến môi trường bí mật
├── core/                     # Chứa logic nghiệp vụ cốt lõi (bộ não của ứng dụng)
│   ├── __init__.py
│   ├── stock.py              # Lớp quản lý dữ liệu và nghiệp vụ cho một cổ phiếu
│   ├── portfolio.py          # Lớp quản lý danh mục, tính toán tối ưu hóa
│   └── analyzer.py           # Lớp chuyên trách tương tác với AI để phân tích
├── pages/                    # Mỗi file .py là một trang trên ứng dụng
│   ├── __init__.py
│   ├── 1_📈_Phân_tích_Cổ_phiếu.py
│   ├── 2_📊_Phân_bổ_Danh_mục.py
│   └── 3_📥_Tải_dữ_liệu.py
├── utils/                    # Chứa các hàm hỗ trợ, tiện ích tái sử dụng
│   ├── __init__.py
│   ├── visualization.py      # Các hàm chuyên vẽ biểu đồ
│   └── helpers.py            # Các hàm hỗ trợ chung khác
├── config.py                 # File cấu hình các hằng số, cài đặt chung
├── Goldenkey_App.py          # Điểm khởi đầu để chạy ứng dụng Streamlit
├── requirements.txt          # Danh sách các thư viện Python cần thiết
└── README.md                 # Tệp tài liệu hướng dẫn này
⚠️ Tuyên bố miễn trừ trách nhiệm
Ứng dụng này được phát triển cho mục đích học tập và nghiên cứu. Mọi thông tin, phân tích và khuyến nghị được tạo ra bởi công cụ này chỉ mang tính chất tham khảo, không được xem là lời khuyên đầu tư chính thức. Luôn tự mình nghiên cứu kỹ lưỡng hoặc tham khảo ý kiến chuyên gia tài chính trước khi đưa ra bất kỳ quyết định đầu tư nào.