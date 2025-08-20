# goldenkey_project/core/stock.py
import pandas as pd
import vnstock
from datetime import datetime, timedelta
from config import VN_STOCK_SOURCE
import pandas_ta as ta

class Stock:
    """
    Đại diện cho một cổ phiếu, quản lý việc truy xuất và xử lý dữ liệu.
    """
    def __init__(self, symbol: str):
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("Mã cổ phiếu phải là một chuỗi không rỗng.")
        self.symbol = symbol.upper().strip()
        self.client = vnstock.Vnstock()
        self.stock_data = self.client.stock(symbol=self.symbol, source=VN_STOCK_SOURCE)
        self.price_history = pd.DataFrame()

    def fetch_price_history(self, years: int = 3, interval: str = '1D') -> pd.DataFrame:
        """Tải dữ liệu giá lịch sử cho cổ phiếu."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(years * 365.25))
            df = self.stock_data.quote.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=interval
            )
            df.dropna(subset=['volume'], inplace=True)
            df['time'] = pd.to_datetime(df['time'])
            self.price_history = df
            return self.price_history
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu giá cho {self.symbol}: {e}")
            return pd.DataFrame()

    def get_company_profile(self) -> pd.DataFrame:
        """Lấy thông tin tổng quan về công ty."""
        try:
            profile_df = self.stock_data.company.profile()
            return profile_df
        except Exception as e:
            print(f"Lỗi khi lấy thông tin công ty {self.symbol}: {e}")
            return pd.DataFrame()

    def calculate_technical_indicators(self):
        """
        Tính toán tất cả các chỉ báo kỹ thuật cần thiết: MA, MACD, RSI.
        """
        if self.price_history.empty:
            print("Dữ liệu giá chưa được tải. Hãy gọi fetch_price_history() trước.")
            return

        # Tính toán các đường MA
        for window in [20, 50, 100]:
            self.price_history[f'MA{window}'] = self.price_history['close'].rolling(window).mean()

        # Tính toán MACD (sử dụng pandas_ta)
        self.price_history.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)

        # Tính toán RSI (sử dụng pandas_ta)
        self.price_history.ta.rsi(close='close', length=14, append=True)

        # Đổi tên cột cho dễ đọc
        self.price_history.rename(columns={
            "MACD_12_26_9": "MACD",
            "MACDh_12_26_9": "MACD_hist",
            "MACDs_12_26_9": "MACD_signal",
            "RSI_14": "RSI"
        }, inplace=True)

    def calculate_fibonacci_levels(self) -> tuple:
        """Tính toán các ngưỡng Fibonacci Retracement."""
        if self.price_history.empty: return None, None, None
        highest_high = self.price_history['close'].max()
        lowest_low = self.price_history['close'].min()
        price_range = highest_high - lowest_low
        if price_range == 0: return None, None, None
        levels = {
            "Fib 0.236": round(highest_high - (price_range * 0.236), 1),
            "Fib 0.382": round(highest_high - (price_range * 0.382), 1),
            "Fib 0.5": round(highest_high - (price_range * 0.5), 1),
            "Fib 0.618": round(highest_high - (price_range * 0.618), 1),
            "Fib 0.786": round(highest_high - (price_range * 0.786), 1),
        }
        return levels, highest_high, lowest_low

    def get_financial_report(self, report_type: str, period: str = 'quarter', years: int = 3) -> pd.DataFrame:
        """Lấy dữ liệu báo cáo tài chính."""
        try:
            api_method = getattr(self.stock_data.finance, report_type)
            df_report = api_method(period=period, lang='vi')
            if df_report.empty: return pd.DataFrame()
            current_year = datetime.now().year
            start_year_filter = current_year - years
            df_report['year'] = pd.to_numeric(df_report['year'], errors='coerce')
            df_filtered = df_report[df_report['year'] >= start_year_filter]
            return df_filtered
        except Exception as e:
            print(f"Lỗi khi truy xuất {report_type} cho {self.symbol}: {e}")
            return pd.DataFrame()