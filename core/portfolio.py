# goldenkey_project/core/portfolio.py
import pandas as pd
import numpy as np
import vnstock
from datetime import datetime, timedelta
from config import VN_STOCK_SOURCE

class Portfolio:
    """
    Quản lý một danh mục cổ phiếu, thực hiện các tính toán và tối ưu hóa.
    """
    def __init__(self, symbols: list, benchmark: str = "VNINDEX"):
        self.symbols = [s.upper().strip() for s in symbols]
        self.benchmark = benchmark.upper().strip()
        self.client = vnstock.Vnstock()
        self.adj_close = pd.DataFrame()
        self.returns = pd.DataFrame()
        self.cov_matrix = pd.DataFrame()

    def fetch_data(self, years: int = 3) -> bool:
        """Tải dữ liệu giá lịch sử cho tất cả cổ phiếu trong danh mục và benchmark."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(years * 365.25))
        
        all_symbols = self.symbols + [self.benchmark]
        data = {}
        
        for symbol in all_symbols:
            try:
                stock_data = self.client.stock(symbol=symbol, source=VN_STOCK_SOURCE)
                df = stock_data.quote.history(
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d')
                )
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                data[symbol] = df['close']
            except Exception as e:
                print(f"Không thể tải dữ liệu cho {symbol}: {e}")
                return False
        
        self.adj_close = pd.DataFrame(data).dropna()
        return True

    def calculate_stats(self):
        """Tính toán lợi suất hàng ngày và ma trận hiệp phương sai."""
        self.returns = self.adj_close.pct_change().dropna()
        asset_returns = self.returns[self.symbols]
        self.cov_matrix = asset_returns.cov() * 252 # Annualized

    def run_monte_carlo(self, iterations: int = 10000, risk_free_rate: float = 0.04, min_weight: float = 0.10, max_weight: float = 0.60) -> pd.DataFrame:
        """
        Thực hiện mô phỏng Monte Carlo với các ràng buộc về tỷ trọng cho phần danh mục cổ phiếu.

        Args:
            iterations (int): Số lượng danh mục hợp lệ cần tìm.
            risk_free_rate (float): Lãi suất phi rủi ro.
            min_weight (float): Tỷ trọng tối thiểu cho mỗi cổ phiếu.
            max_weight (float): Tỷ trọng tối đa cho mỗi cổ phiếu.

        Returns:
            pd.DataFrame: DataFrame chứa kết quả các danh mục hợp lệ.
        """
        results = []
        num_assets = len(self.symbols)
        mean_returns = self.returns[self.symbols].mean() * 252 # Annualized
        
        # Giới hạn số lần thử để tránh vòng lặp vô tận nếu ràng buộc quá chặt
        # Ví dụ: nếu cần 10,000 danh mục, thử tối đa 2,000,000 lần
        attempt_limit = iterations * 200 
        attempts = 0

        # Lặp cho đến khi tìm đủ số danh mục hợp lệ hoặc hết số lần thử
        while len(results) < iterations and attempts < attempt_limit:
            attempts += 1
            
            # Tạo tỷ trọng ngẫu nhiên
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            
            # Kiểm tra xem tất cả các tỷ trọng có nằm trong khoảng cho phép không
            if np.all((weights >= min_weight) & (weights <= max_weight)):
                # Nếu hợp lệ, tính toán và lưu kết quả
                p_return = np.sum(mean_returns * weights)
                p_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
                sharpe_ratio = (p_return - risk_free_rate) / p_volatility
                
                results.append([p_return, p_volatility, sharpe_ratio] + list(weights))
        
        # In cảnh báo nếu không tìm đủ danh mục
        if len(results) < iterations:
            print(f"Cảnh báo: Đã đạt đến giới hạn {attempt_limit} lần thử nhưng chỉ tìm thấy {len(results)}/{iterations} danh mục hợp lệ. Ràng buộc có thể quá chặt.")

        columns = ['return', 'volatility', 'sharpe'] + self.symbols
        return pd.DataFrame(results, columns=columns)

    def get_optimal_portfolios_from_mc(self, mc_results: pd.DataFrame) -> (pd.Series, pd.Series):
        """
        Lấy ra danh mục có tỷ lệ Sharpe tối đa và lợi nhuận tối đa từ kết quả Monte Carlo.
        """
        if mc_results.empty:
            return pd.Series(), pd.Series()
            
        max_sharpe_portfolio = mc_results.loc[mc_results['sharpe'].idxmax()]
        max_return_portfolio = mc_results.loc[mc_results['return'].idxmax()]
        
        return max_sharpe_portfolio, max_return_portfolio

    def calculate_cumulative_performance(self, stock_weights: np.ndarray, cash_weight: float, risk_free_rate: float) -> pd.DataFrame:
        """
        Tính toán hiệu suất tích lũy của danh mục và so sánh với benchmark.
        """
        one_year_ago = self.returns.index.max() - pd.DateOffset(years=1)
        recent_returns = self.returns[self.returns.index >= one_year_ago]

        if recent_returns.empty:
            return pd.DataFrame()

        asset_returns = recent_returns[self.symbols]
        benchmark_returns = recent_returns[self.benchmark]
        
        portfolio_stock_returns = asset_returns.dot(stock_weights)
        daily_risk_free_rate = (1 + risk_free_rate)**(1/252) - 1
        stock_portion_weight = 1 - cash_weight
        portfolio_total_returns = (portfolio_stock_returns * stock_portion_weight) + (daily_risk_free_rate * cash_weight)

        performance_df = pd.DataFrame({
            'Danh mục': (1 + portfolio_total_returns).cumprod(),
            f'{self.benchmark}': (1 + benchmark_returns).cumprod()
        })
        
        return performance_df