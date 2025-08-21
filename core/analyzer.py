# goldenkey_project/core/analyzer.py

import pandas as pd
import google.generativeai as genai
import logging
from datetime import datetime
from typing import Dict, List, Any

# Cấu hình logging để ghi lại các lỗi từ AI
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Forward declaration để type hinting hoạt động với class 'Stock'
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.stock import Stock

class StockAIAnalyzer:
    """
    Lớp chuyên trách tương tác với Generative AI (Gemini) để thực hiện các
    phân tích chuyên sâu dựa trên dữ liệu từ đối tượng Stock.
    
    Attributes:
        model: Đối tượng mô hình Generative AI đã được cấu hình.
    """

    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash-latest'):
        """
        Khởi tạo AI Analyzer với API key và tên mô hình.

        Args:
            api_key (str): Khóa API từ Google AI Studio.
            model_name (str): Tên mô hình Gemini cần sử dụng.
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(temperature=0.2) # Giảm temp để kết quả nhất quán hơn
            )
            logging.info(f"Khởi tạo thành công mô hình AI: {model_name}")
        except Exception as e:
            logging.error(f"Lỗi nghiêm trọng khi cấu hình Gemini: {e}")
            raise ValueError("Không thể khởi tạo mô hình AI. Vui lòng kiểm tra API Key.") from e

    # --- Phương thức lõi gọi AI ---

    def _generate_analysis(self, prompt: str) -> str:
        """
        Hàm nội bộ để gửi prompt đến AI và nhận phản hồi đã được xử lý.

        Args:
            prompt (str): Chuỗi prompt hoàn chỉnh để gửi đến mô hình AI.

        Returns:
            str: Phản hồi dạng text từ AI hoặc thông báo lỗi.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Lỗi khi gọi API của Gemini: {e}")
            return f"⚠️ **Lỗi từ AI:** Không thể tạo phân tích. Vui lòng thử lại sau. (Chi tiết: {e})"

    # --- Các phương thức phân tích chính ---

    def analyze_technical(self, stock_obj: 'Stock') -> str:
        """
        Tạo phân tích kỹ thuật cho cổ phiếu dựa trên dữ liệu giá 90 ngày gần nhất.
        """
        if stock_obj.price_history.empty:
            return "Không có dữ liệu giá để phân tích kỹ thuật."

        # Đóng gói logic chuẩn bị dữ liệu vào hàm riêng
        tech_data = self._prepare_technical_data(stock_obj.price_history)
        
        # Lấy template và điền dữ liệu
        prompt_template = self._get_technical_prompt_template()
        prompt = prompt_template.format(
            symbol=stock_obj.symbol,
            price_data_md=tech_data['price_data_md'],
            last_price_md=tech_data['last_price_md']
        )
        return self._generate_analysis(prompt)

    def analyze_financial_report(self, report_df: pd.DataFrame, report_name: str, symbol: str) -> str:
        """
        Tạo phân tích cho một báo cáo tài chính cụ thể.
        """
        if report_df.empty:
            return f"Không có dữ liệu cho báo cáo '{report_name}'."
        
        # Lấy template và dữ liệu
        report_specific_prompt = self._get_financial_prompt_template(report_name)
        financial_data_md = self._format_df_for_prompt(report_df)
        
        # Tạo prompt hoàn chỉnh
        prompt = (
            f"{report_specific_prompt}\n\n"
            "**Hãy trình bày phân tích một cách chuyên nghiệp, có định lượng (sử dụng con số cụ thể từ bảng) "
            "và tránh các nhận xét chung chung, cảm tính. Tập trung vào các xu hướng và những thay đổi đáng kể.**\n"
            f"Dữ liệu phân tích cho cổ phiếu **{symbol}**:\n"
            f"```markdown\n{financial_data_md}\n```"
        )
        return self._generate_analysis(prompt)

    def analyze_news_sentiment(self, news_df: pd.DataFrame, symbol: str) -> str:
        """
        Phân tích sắc thái và tóm tắt các tin tức quan trọng.
        """
        if news_df.empty:
            return "Không tìm thấy tin tức gần đây để phân tích."
        
        # Lấy template và dữ liệu
        news_markdown = self._format_df_for_prompt(news_df[['title', 'source']])
        prompt_template = self._get_news_prompt_template()

        # Tạo prompt hoàn chỉnh
        prompt = prompt_template.format(symbol=symbol, news_markdown=news_markdown)
        return self._generate_analysis(prompt)

    def generate_overall_summary(self, symbol: str, analyses: Dict[str, str]) -> str:
        """
        Tạo bản tóm tắt tổng thể kết hợp tất cả các phân tích.

        Args:
            symbol (str): Mã cổ phiếu.
            analyses (Dict[str, str]): Một dictionary chứa các bài phân tích chi tiết.
                                       Ví dụ: {'technical': '...', 'financial': '...', 'news': '...'}
        """
        prompt_template = self._get_summary_prompt_template()
        
        # Tạo prompt hoàn chỉnh
        prompt = prompt_template.format(
            symbol=symbol,
            today=datetime.now().strftime('%d-%m-%Y'),
            technical_analysis=analyses.get('technical', 'Không có phân tích kỹ thuật.'),
            fundamental_analyses=analyses.get('financial', 'Không có phân tích cơ bản.'),
            news_analysis=analyses.get('news', 'Không có phân tích tin tức.')
        )
        return self._generate_analysis(prompt)

    # --- Các phương thức Helper và quản lý Prompt ---

    @staticmethod
    def _format_df_for_prompt(df: pd.DataFrame) -> str:
        """
        Helper tĩnh để xử lý và chuyển đổi DataFrame thành chuỗi Markdown cho AI.
        Hàm này không phụ thuộc vào trạng thái của đối tượng (self).
        """
        if df.empty:
            return "Không có dữ liệu."
        
        df_processed = df.copy()
        
        # Logic xử lý đặc biệt cho BCTC
        if 'reportDate' in df_processed.columns:
            df_processed['period_key'] = pd.to_datetime(df_processed['reportDate']).dt.strftime('%Y-%m-%d')
            df_processed = df_processed.set_index('period_key').sort_index(ascending=False).T
        elif 'year' in df_processed.columns and 'quarter' in df_processed.columns:
            df_processed['period_key'] = df_processed['year'].astype(str) + '-Q' + df_processed['quarter'].astype(str)
            df_processed = df_processed.set_index('period_key').sort_index(ascending=False).T

        return df_processed.to_markdown(index=True)

    def _prepare_technical_data(self, price_history_df: pd.DataFrame) -> Dict[str, str]:
        """
        Đóng gói logic chuẩn bị dữ liệu kỹ thuật để gửi cho AI.
        Tối ưu hóa token bằng cách chỉ lấy dữ liệu gần đây, làm tròn số và chuyển đổi đơn vị.
        """
        df_recent = price_history_df.tail(90).copy()
        
        cols_to_round = {
            'open': 1, 'high': 1, 'low': 1, 'close': 1,
            'volume': 2,
            'MA20': 1, 'MA50': 1, 'MA100': 1,
            'MACD': 2, 'MACD_hist': 2, 'MACD_signal': 2, 'RSI': 1
        }
        df_recent['volume'] /= 1_000_000  # Chuyển khối lượng sang đơn vị triệu
        
        for col, decimals in cols_to_round.items():
            if col in df_recent.columns:
                df_recent[col] = df_recent[col].round(decimals)

        ai_columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'MA20', 'MA50', 'MACD', 'MACD_signal', 'RSI']
        df_to_analyze = df_recent[[col for col in ai_columns if col in df_recent.columns]]
        
        return {
            "price_data_md": df_to_analyze.to_markdown(index=False),
            "last_price_md": df_recent.tail(1)[['close', 'volume', 'RSI', 'MACD']].to_markdown(index=False)
        }

    def _get_technical_prompt_template(self) -> str:
        """Trả về mẫu prompt cho phân tích kỹ thuật."""
        return """
        Bạn là một nhà phân tích kỹ thuật (chartist CMT) chuyên nghiệp của Quỹ đầu tư Goldenkey.
        Nhiệm vụ của bạn là đưa ra một phân tích chuyên sâu, khách quan về cổ phiếu **{symbol}**
        dựa trên dữ liệu giá và các chỉ báo kỹ thuật trong 90 phiên gần nhất.

        **Dữ liệu cung cấp:**
        - Dữ liệu giá và chỉ báo (khối lượng tính bằng triệu cổ phiếu):
        ```markdown
        {price_data_md}
        ```
        - Dữ liệu phiên gần nhất:
        ```markdown
        {last_price_md}
        ```

        **Yêu cầu Phân tích (trả lời từng điểm một cách cụ thể, định lượng):**
        1.  **Xu hướng & Động lượng (Price Action & MAs):**
            * Xác định rõ xu hướng chính (ngắn hạn) dựa trên vị trí của giá so với các đường MA (MA20, MA50).
            * Phân tích hành động giá và khối lượng của 5-10 phiên gần nhất. Có tín hiệu nào đáng chú ý không?

        2.  **Phân tích Chỉ báo MACD:**
            * Trạng thái hiện tại của MACD: Đường MACD đang cắt lên hay cắt xuống đường Signal?
            * Histogram của MACD đang dương hay âm, đang tăng hay giảm? Điều này nói lên điều gì về động lượng?

        3.  **Phân tích Chỉ báo RSI:**
            * Giá trị RSI hiện tại đang ở vùng nào (quá mua > 70, quá bán < 30, hay trung tính)?
            * Có tín hiệu phân kỳ âm hoặc dương giữa RSI và đường giá trong 30 phiên gần nhất không?

        4.  **Tổng hợp & Kịch bản:**
            * Tổng hợp các tín hiệu: Các chỉ báo đang đồng thuận hay mâu thuẫn?
            * Đưa ra hai kịch bản (Tăng giá và Giảm giá) cho cổ phiếu trong ngắn hạn (1-2 tuần tới), nêu rõ các **vùng giá hỗ trợ và kháng cự then chốt**.
        """

    def _get_financial_prompt_template(self, report_name: str) -> str:
        """Trả về mẫu prompt phù hợp cho từng loại báo cáo tài chính."""
        prompts = {
            "income_statement": """
            Với vai trò là chuyên gia phân tích tài chính, hãy phân tích sâu **Báo cáo Kết quả Kinh doanh**.
            1.  **Tăng trưởng Doanh thu & Lợi nhuận:** Phân tích tốc độ tăng trưởng của Doanh thu thuần và Lợi nhuận sau thuế qua các kỳ. Tốc độ này đang tăng tốc hay chậm lại?
            2.  **Phân tích Biên lợi nhuận:** Biên lợi nhuận gộp và biên lợi nhuận ròng đang cải thiện hay xấu đi? Điều này nói lên điều gì về hiệu quả hoạt động?
            3.  **Cơ cấu Chi phí:** Có khoản mục chi phí nào (giá vốn, chi phí bán hàng, chi phí quản lý) tăng bất thường không?
            """,
            "balance_sheet": """
            Với vai trò là chuyên gia phân tích tài chính, hãy phân tích sâu **Bảng cân đối kế toán**.
            1.  **Sức khỏe Nợ vay:** Phân tích cơ cấu Nợ phải trả, đặc biệt là tỷ lệ Nợ vay trên Vốn chủ sở hữu. Tỷ lệ này có an toàn không và xu hướng ra sao?
            2.  **Chất lượng Tài sản:** Nhận xét về sự thay đổi của các khoản mục lớn như Hàng tồn kho và Các khoản phải thu. Các khoản mục này có tăng nhanh hơn doanh thu không?
            """,
            "cash_flow": """
            Với vai trò là chuyên gia phân tích tài chính, hãy phân tích sâu **Báo cáo Lưu chuyển tiền tệ**.
            1.  **Dòng tiền từ HĐ Kinh doanh (CFO):** Công ty có tạo ra dòng tiền dương và tăng trưởng đều đặn từ hoạt động cốt lõi không? Dòng tiền này có tương xứng với lợi nhuận không?
            2.  **Hoạt động Đầu tư (CFI) & Tài chính (CFF):** Công ty đang dùng tiền để làm gì? Có đang đầu tư mạnh (CFI âm) hay trả nợ/vay thêm (CFF)?
            """,
            "ratio": """
            Với vai trò là chuyên gia phân tích tài chính, hãy phân tích sâu các **Chỉ số tài chính**.
            1.  **Khả năng sinh lời (ROA, ROE):** Các chỉ số này đang ở mức nào so với các kỳ trước? Xu hướng này cho thấy hiệu quả sử dụng tài sản và vốn của ban lãnh đạo ra sao?
            2.  **Định giá (P/E, P/B):** Các chỉ số P/E và P/B nói lên điều gì về mức độ đắt hay rẻ của cổ phiếu tại các thời điểm báo cáo?
            """
        }
        return prompts.get(report_name, "Hãy đưa ra những đánh giá trọng yếu và chuyên sâu về báo cáo này.")

    def _get_news_prompt_template(self) -> str:
        """Trả về mẫu prompt cho phân tích tin tức."""
        return """
        Bạn là một chuyên gia phân tích truyền thông tài chính.
        Dưới đây là các tin tức gần đây về cổ phiếu **{symbol}**:
        ```markdown
        {news_markdown}
        ```

        Hãy thực hiện các yêu cầu sau:
        1.  **Đánh giá Sắc thái chung:** Đưa ra đánh giá tổng quan về tâm lý thị trường dựa trên các tin tức này (ví dụ: Tích cực, Tiêu cực, Trung lập, Có thông tin trọng yếu...).
        2.  **Tóm tắt Tin tức Chính:** Tóm tắt ngắn gọn 1-2 tin tức có thể có ảnh hưởng lớn nhất đến giá cổ phiếu trong ngắn hạn.
        """

    def _get_summary_prompt_template(self) -> str:
        """Trả về mẫu prompt cho phần tổng hợp cuối cùng."""
        return """
        Bạn là Chuyên gia Phân tích Cấp cao của Quỹ đầu tư Goldenkey. Hãy tổng hợp tất cả các phân tích chi tiết về cổ phiếu **{symbol}** để trình bày cho Giám đốc Đầu tư.
        Bài trình bày phải súc tích, sắc sảo và đưa ra một khuyến nghị rõ ràng.

        **Ngày phân tích:** {today}

        ### 1. Tổng hợp Điểm nhấn Chính
        * **Về Cơ bản:** Nêu 2 điểm mạnh nhất và 1-2 rủi ro lớn nhất từ các phân tích BCTC.
        * **Về Kỹ thuật:** Nêu tín hiệu và luận điểm quan trọng nhất từ phân tích biểu đồ (xu hướng, động lượng).
        * **Về Tin tức & Tâm lý Thị trường:** Tóm tắt ngắn gọn sắc thái và các thông tin chính từ tin tức gần đây.

        ### 2. Luận điểm Đầu tư & Rủi ro
        * **Luận điểm chính:** Dựa trên sự tổng hợp trên, tại sao nên **MUA/BÁN/NẮM GIỮ** cổ phiếu này ngay bây giờ? Kết hợp cả 3 yếu tố trên.
        * **Rủi ro chính:** Rủi ro lớn nhất có thể làm luận điểm đầu tư này thất bại là gì (về cơ bản, kỹ thuật, và thông tin)?

        ### 3. Khuyến nghị và Hành động
        * **Khuyến nghị:** Chọn một: **MUA MẠNH, MUA, NẮM GIỮ, BÁN, hoặc BÁN MẠNH**.
        * **Vùng giá hành động:** Đề xuất một vùng giá hợp lý để mua vào hoặc một mức cắt lỗ/chốt lời dựa trên các phân tích kỹ thuật.

        ---
        ### DỮ LIỆU PHÂN TÍCH CHI TIẾT ĐỂ TỔNG HỢP
        
        **Phân tích Kỹ thuật:**
        {technical_analysis}

        **Tổng hợp Phân tích Cơ bản:**
        {fundamental_analyses}

        **Phân tích Tin tức:**
        {news_analysis}
        """