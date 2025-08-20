# goldenkey_project/core/analyzer.py

import pandas as pd
import google.generativeai as genai
from core.stock import Stock
from datetime import datetime

def _process_financial_df_for_gemini(df_for_ai: pd.DataFrame):
    """Hàm helper để xử lý dataframe tài chính trước khi gửi cho AI."""
    if df_for_ai.empty: return "Không có dữ liệu."
    df_processed = df_for_ai.copy()
    if 'reportDate' in df_processed.columns:
        df_processed['period_key'] = pd.to_datetime(df_processed['reportDate']).dt.strftime('%Y-%m-%d')
    elif 'year' in df_processed.columns and 'quarter' in df_processed.columns:
         df_processed['period_key'] = df_processed['year'].astype(str) + '-Q' + df_processed['quarter'].astype(str)
    if 'period_key' in df_processed.columns:
        df_processed = df_processed.set_index('period_key').sort_index(ascending=False)
    df_processed_transposed = df_processed.T
    return df_processed_transposed.to_markdown(index=True)


class StockAIAnalyzer:
    """
    Sử dụng AI (Gemini) để thực hiện các phân tích dựa trên dữ liệu từ Stock.
    """
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-latest'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(temperature=0.1)
        )

    def _generate_analysis(self, prompt: str) -> str:
        """Hàm nội bộ để gửi prompt đến AI và nhận phản hồi."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi khi tạo phân tích từ AI: {e}"

    def analyze_technical(self, stock_obj: Stock) -> str:
        """
        Tạo phân tích kỹ thuật cho cổ phiếu, có tối ưu hóa token.
        """
        if stock_obj.price_history.empty:
            return "Không có dữ liệu giá để phân tích kỹ thuật."

        # --- TỐI ƯU HÓA TOKEN ---
        # 1. Chỉ lấy 90 phiên gần nhất để phân tích
        df_recent = stock_obj.price_history.tail(90).copy()

        # 2. Làm tròn số để giảm số ký tự (token)
        cols_to_round = {
            'open': 1, 'high': 1, 'low': 1, 'close': 1,
            'volume': 2, # triệu cổ phiếu
            'MA20': 1, 'MA50': 1, 'MA100': 1,
            'MACD': 2, 'MACD_hist': 2, 'MACD_signal': 2, 'RSI': 1
        }
        df_recent['volume'] /= 1_000_000 # Chuyển khối lượng sang đơn vị triệu
        
        for col, decimals in cols_to_round.items():
            if col in df_recent.columns:
                df_recent[col] = df_recent[col].round(decimals)

        # Chọn các cột cần thiết cho AI
        ai_columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'MA20', 'MA50', 'MACD', 'MACD_signal', 'RSI']
        df_to_analyze = df_recent[[col for col in ai_columns if col in df_recent.columns]]
        
        price_data_md = df_to_analyze.to_markdown(index=False)
        last_price_md = df_recent.tail(1)[['close', 'volume', 'RSI', 'MACD']].to_markdown(index=False)
        
        # --- CẬP NHẬT PROMPT ---
        prompt = f"""
        Bạn là một nhà phân tích kỹ thuật (chartist CMT) chuyên nghiệp của Quỹ đầu tư Goldenkey.
        Nhiệm vụ của bạn là đưa ra một phân tích chuyên sâu, khách quan về cổ phiếu {stock_obj.symbol}
        dựa trên dữ liệu giá và các chỉ báo kỹ thuật trong 90 phiên gần nhất.

        **Dữ liệu cung cấp:**
        - Dữ liệu giá và chỉ báo (khối lượng tính bằng triệu cổ phiếu):
        ```{price_data_md}```
        - Dữ liệu phiên gần nhất:
        ```{last_price_md}```

        **Yêu cầu Phân tích (trả lời từng điểm một cách cụ thể, định lượng):**
        1.  **Xu hướng & Động lượng (Price Action & MAs):**
            * Xác định rõ xu hướng chính (ngắn hạn) dựa trên vị trí của giá so với các đường MA (MA20, MA50).
            * Phân tích hành động giá và khối lượng của 5-10 phiên gần nhất. Có tín hiệu nào đáng chú ý (nến tăng/giảm mạnh, khối lượng đột biến)?

        2.  **Phân tích Chỉ báo MACD:**
            * Trạng thái hiện tại của MACD: Đường MACD đang cắt lên hay cắt xuống đường Signal? Hay đang hội tụ/phân kỳ?
            * Histogram của MACD đang dương hay âm, đang tăng hay giảm? Điều này nói lên điều gì về động lượng mua/bán?

        3.  **Phân tích Chỉ báo RSI:**
            * Giá trị RSI hiện tại đang ở vùng nào (quá mua > 70, quá bán < 30, hay trung tính)?
            * Có tín hiệu phân kỳ (divergence) âm hoặc dương giữa RSI và đường giá trong 30 phiên gần nhất không? Đây là tín hiệu rất quan trọng.

        4.  **Tổng hợp & Kịch bản:**
            * Tổng hợp các tín hiệu trên: Các chỉ báo đang đồng thuận hay mâu thuẫn với nhau?
            * Đưa ra hai kịch bản (Tăng giá và Giảm giá) cho cổ phiếu trong ngắn hạn (1-2 tuần tới). Mỗi kịch bản cần nêu rõ các **vùng giá hỗ trợ và kháng cự then chốt**.
        """
        return self._generate_analysis(prompt)

    def analyze_financial_report(self, report_df: pd.DataFrame, report_name: str, symbol: str) -> str:
        """Tạo phân tích cho một báo cáo tài chính cụ thể."""
        fundamental_prompts = {
            "income_statement": """
            Với vai trò là chuyên gia phân tích tài chính doanh nghiệp, hãy phân tích sâu Báo cáo Kết quả Kinh doanh này.
            1.  **Tăng trưởng Doanh thu & Lợi nhuận:** Tính toán tốc độ tăng trưởng của Doanh thu thuần và Lợi nhuận sau thuế qua các kỳ. Tốc độ này đang tăng tốc hay chậm lại?
            2.  **Phân tích Biên lợi nhuận:** Biên lợi nhuận gộp và biên lợi nhuận ròng đang cải thiện hay xấu đi? Điều này nói lên điều gì về hiệu quả hoạt động và khả năng cạnh tranh của công ty?
            3.  **Cơ cấu Chi phí:** Có khoản mục chi phí nào (giá vốn, chi phí bán hàng, chi phí quản lý) tăng bất thường so với tốc độ tăng của doanh thu không?
            """,
            "balance_sheet": """
            Với vai trò là chuyên gia phân tích tài chính doanh nghiệp, hãy phân tích sâu Bảng cân đối kế toán này.
            1.  **Sức khỏe Nợ vay:** Phân tích cơ cấu Nợ phải trả, đặc biệt là tỷ lệ Nợ vay trên Vốn chủ sở hữu. Tỷ lệ này có đang ở mức an toàn không và xu hướng của nó ra sao?
            2.  **Chất lượng Tài sản:** Nhận xét về sự thay đổi của các khoản mục lớn trong tài sản như Hàng tồn kho và Các khoản phải thu. Các khoản mục này có tăng nhanh hơn doanh thu không? Nếu có, đây có thể là rủi ro gì?
            3.  **Thanh khoản:** Dựa vào Tỷ số thanh khoản hiện hành (Tài sản ngắn hạn / Nợ ngắn hạn), khả năng thanh toán các nghĩa vụ nợ ngắn hạn của công ty có tốt không?
            """,
            "cash_flow": """
            Với vai trò là chuyên gia phân tích tài chính doanh nghiệp, hãy phân tích sâu Báo cáo Lưu chuyển tiền tệ.
            1.  **Dòng tiền từ HĐ Kinh doanh (CFO):** Công ty có tạo ra dòng tiền dương và tăng trưởng đều đặn từ hoạt động kinh doanh cốt lõi không? Dòng tiền này có tương xứng với lợi nhuận kế toán không?
            2.  **Hoạt động Đầu tư (CFI) & Tài chính (CFF):** Công ty đang dùng tiền để làm gì? Có đang đầu tư mạnh vào tài sản cố định (Capex) không (thể hiện qua CFI âm)? Công ty đang trả nợ hay vay thêm?
            3.  **Dòng tiền tự do (FCF):** Ước tính Dòng tiền tự do (CFO - Capex), công ty có tạo ra đủ tiền mặt sau khi đã đầu tư để duy trì và mở rộng sản xuất không?
            """,
            "ratio": """
            Với vai trò là chuyên gia phân tích tài chính doanh nghiệp, hãy phân tích sâu các Chỉ số tài chính này.
            1.  **Khả năng sinh lời (ROA, ROE):** Các chỉ số này đang ở mức nào so với các kỳ trước? Xu hướng này cho thấy hiệu quả sử dụng tài sản và vốn chủ sở hữu của ban lãnh đạo đang tốt lên hay xấu đi?
            2.  **Định giá (P/E, P/B):** Các chỉ số P/E và P/B nói lên điều gì về mức độ đắt hay rẻ của cổ phiếu tại các thời điểm báo cáo?
            3.  **Chọn 1 chỉ số bất thường:** Tìm một chỉ số bất kỳ trong bảng có sự thay đổi đột biến nhất qua các kỳ và đưa ra giả thuyết tại sao lại có sự thay đổi đó.
            """
        }

        report_specific_prompt = fundamental_prompts.get(report_name, "Hãy đưa ra những đánh giá trọng yếu, chuyên sâu, chuyên nghiệp dưới góc độ nhà phân tích tài chính về báo cáo này.")
        financial_data_md = _process_financial_df_for_gemini(report_df)
        
        report_prompt = f"""
        {report_specific_prompt}

        **Hãy trình bày phân tích một cách chuyên nghiệp, có định lượng (sử dụng con số cụ thể từ bảng) và tránh các nhận xét chung chung, cảm tính. Tập trung vào các xu hướng và những thay đổi đáng kể.**
        Dữ liệu phân tích cho cổ phiếu {symbol}: ```{(financial_data_md)}```
        """
        return self._generate_analysis(report_prompt)

    def generate_overall_summary(self, symbol: str, technical_analysis: str, fundamental_analyses: list) -> str:
        """Tạo bản tóm tắt tổng thể kết hợp cả phân tích cơ bản và kỹ thuật."""
        today = datetime.now().strftime('%Y-%m-%d')
        prompt = f"""
        Bạn là Chuyên gia Phân tích của Quỹ đầu tư Goldenkey. Hãy tổng hợp tất cả các phân tích chi tiết về cổ phiếu {symbol} để trình bày cho Giám đốc Đầu tư.
        Bài trình bày phải súc tích, sắc sảo và đưa ra một khuyến nghị rõ ràng.

        **Ngày phân tích:** {today}

        **1. Tổng hợp Điểm nhấn Chính:**
        * **Về Cơ bản:** Nêu 2 điểm mạnh nhất và 1-2 rủi ro lớn nhất từ các phân tích BCTC.
        * **Về Kỹ thuật:** Nêu tín hiệu và luận điểm quan trọng nhất từ phân tích biểu đồ (xu hướng, MACD, RSI).

        **2. Luận điểm Đầu tư & Rủi ro:**
        * **Luận điểm chính:** Dựa trên sự tổng hợp trên, tại sao nên MUA/BÁN/NẮM GIỮ cổ phiếu này ngay bây giờ?
        * **Rủi ro chính:** Rủi ro lớn nhất có thể làm luận điểm đầu tư này thất bại là gì (cả về cơ bản và kỹ thuật)?

        **3. Khuyến nghị và Hành động:**
        * **Khuyến nghị:** Chọn một: **MUA MẠNH, MUA, NẮM GIỮ, BÁN, hoặc BÁN MẠNH**.
        * **Vùng giá hành động:** Đề xuất một vùng giá hợp lý để mua vào hoặc một mức cắt lỗ/chốt lời dựa trên các phân tích kỹ thuật.

        --- DỮ LIỆU PHÂN TÍCH CHI TIẾT ĐỂ TỔNG HỢP ---
        **Phân tích Kỹ thuật:**
        {technical_analysis}

        **Tổng hợp Phân tích Cơ bản:**
        {"".join(fundamental_analyses)}
        """
        return self._generate_analysis(prompt)