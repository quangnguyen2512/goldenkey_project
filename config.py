# goldenkey_project/config.py

# --- API Keys ---
# Thay thế "YOUR_GEMINI_API_KEY" bằng khóa API thực của bạn từ Google AI Studio.
# Rất quan trọng: Không chia sẻ file này công khai khi đã điền API key.
# Cách tốt nhất là sử dụng Streamlit Secrets.
GEMINI_API_KEY = "AIzaSyAAWTpTdWA1s-9tm5Ghd803cG-NB6BMB44"


# --- Hằng số ứng dụng ---
DEFAULT_STOCK_SYMBOLS = ["FPT", "HPG", "ACB", "VCB", "MWG"]
DEFAULT_BENCHMARK = "VNINDEX"
MONTE_CARLO_ITERATIONS = 10000
VN_STOCK_SOURCE = 'VCI'