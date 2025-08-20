# goldenkey_project/core/portfolio.py
import pandas as pd
import numpy as np
import cvxpy as cp
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
        # Lấy ma trận hiệp phương sai của các tài sản (không bao gồm benchmark)
        asset_returns = self.returns[self.symbols]
        self.cov_matrix = asset_returns.cov() * 252 # Annualized

    def run_monte_carlo(self, iterations: int = 10000, risk_free_rate: float = 0.04) -> pd.DataFrame:
        """Thực hiện mô phỏng Monte Carlo để tìm đường biên hiệu quả."""
        results = []
        num_assets = len(self.symbols)
        mean_returns = self.returns[self.symbols].mean() * 252 # Annualized
        
        for i in range(iterations):
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            
            p_return = np.sum(mean_returns * weights)
            p_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe_ratio = (p_return - risk_free_rate) / p_volatility
            
            results.append([p_return, p_volatility, sharpe_ratio] + list(weights))
        
        columns = ['return', 'volatility', 'sharpe'] + self.symbols
        return pd.DataFrame(results, columns=columns)

    def optimize_portfolio(self, target_return: float, risk_free_rate: float, cash_weight: float) -> (np.ndarray, str):
        """
        Tối ưu hóa danh mục để tối thiểu rủi ro cho một mức lợi nhuận mục tiêu,
        có tính đến tỷ trọng tiền mặt.
        """
        # Xử lý trường hợp đặc biệt: 100% tiền mặt
        if cash_weight >= 1.0:
            return np.zeros(len(self.symbols)), "OPTIMAL" # Trả về 0 cho tất cả các cổ phiếu

        num_assets = len(self.symbols)
        weights = cp.Variable(num_assets)
        mean_returns = self.returns[self.symbols].mean() * 252

        # 1. Điều chỉnh lợi nhuận mục tiêu cho phần danh mục rủi ro (cổ phiếu)
        # Công thức: R_cổ_phiếu = (R_tổng - w_tiền_mặt * R_phi_rủi_ro) / (1 - w_tiền_mặt)
        if (1 - cash_weight) == 0: # Tránh lỗi chia cho 0
             adjusted_target_return = 0
        else:
             adjusted_target_return = (target_return - cash_weight * risk_free_rate) / (1 - cash_weight)

        portfolio_return = mean_returns.values @ weights
        portfolio_risk = cp.quad_form(weights, self.cov_matrix)
        
        objective = cp.Minimize(portfolio_risk)
        
        # 2. Sửa đổi các ràng buộc
        constraints = [
            # Tổng trọng số các cổ phiếu bằng phần còn lại sau khi trừ đi tiền mặt
            cp.sum(weights) == 1 - cash_weight,
            
            # Lợi nhuận của phần cổ phiếu phải đạt mức mục tiêu đã điều chỉnh
            portfolio_return >= adjusted_target_return,
            
            # Không bán khống
            weights >= 0
        ]
        
        problem = cp.Problem(objective, constraints)
        problem.solve()
        
        if problem.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
            return weights.value, problem.status
        else:
            return None, problem.status