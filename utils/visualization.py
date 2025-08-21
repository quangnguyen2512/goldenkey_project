# goldenkey_project/utils/visualization.py

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import TYPE_CHECKING, List
import json
from vnstock import Company

if TYPE_CHECKING:
    from core.stock import Stock
    from core.portfolio import Portfolio

def plot_stock_chart(stock_obj: 'Stock') -> go.Figure:
    """
    Vẽ biểu đồ giá cổ phiếu với MA, Fibonacci, Khối lượng, MACD và RSI.
    """
    df = stock_obj.price_history
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.55, 0.15, 0.15, 0.15]
    )

    fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'],
                                 low=df['low'], close=df['close'], name='Giá'), row=1, col=1)
    for col in ['MA20', 'MA50', 'MA100']:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df['time'], y=df[col], name=col,
                                     line=dict(width=1.5)), row=1, col=1)

    fib_levels, _, _ = stock_obj.calculate_fibonacci_levels()
    if fib_levels:
        for level_name, price_level in fib_levels.items():
            fig.add_hline(y=price_level, line_dash="dash", line_color="gray",
                          annotation_text=f"{level_name.split(' ')[1]} ({price_level:,.0f})",
                          annotation_position="bottom right", row=1, col=1)

    volume_colors = ['#26A69A' if row['close'] >= row['open'] else '#EF5350' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['time'], y=df['volume'], name='Khối lượng',
                         marker_color=volume_colors), row=2, col=1)

    if 'MACD' in df.columns and 'MACD_hist' in df.columns and 'MACD_signal' in df.columns:
        macd_colors = ['#26A69A' if val >= 0 else '#EF5350' for val in df['MACD_hist']]
        fig.add_trace(go.Bar(x=df['time'], y=df['MACD_hist'], name='MACD Hist', marker_color=macd_colors), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['time'], y=df['MACD'], name='MACD', line=dict(color='blue', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['time'], y=df['MACD_signal'], name='Signal', line=dict(color='orange', width=1.5)), row=3, col=1)

    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df['time'], y=df['RSI'], name='RSI', line=dict(color='purple', width=1.5)), row=4, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1, annotation_text="70 Quá mua")
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1, annotation_text="30 Quá bán")

    fig.update_layout(
        title_text=f"Biểu đồ Phân tích Kỹ thuật Cổ phiếu {stock_obj.symbol}",
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        yaxis_title="Giá (VND)",
        yaxis2_title="Khối lượng",
        yaxis3_title="MACD",
        yaxis4_title="RSI"
    )
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(showticklabels=False, row=3, col=1)

    return fig

def plot_efficient_frontier(mc_results: pd.DataFrame, symbols: List[str]) -> go.Figure:
    if mc_results.empty:
        return go.Figure().update_layout(title="Không có dữ liệu để vẽ đường biên hiệu quả.")

    max_sharpe_portfolio = mc_results.loc[mc_results['sharpe'].idxmax()]
    min_vol_portfolio = mc_results.loc[mc_results['volatility'].idxmin()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mc_results['volatility'], y=mc_results['return'], mode='markers',
        marker=dict(
            color=mc_results['sharpe'], showscale=True, size=7, line_width=0,
            colorscale="Viridis", colorbar=dict(title="Tỷ lệ Sharpe")
        ),
        hovertemplate=(
            "<b>Danh mục Mô phỏng</b><br>"
            "Lợi nhuận: %{y:.2%}<br>Rủi ro: %{x:.2%}<br>Sharpe: %{marker.color:.2f}<extra></extra>"
        ),
        name='Các danh mục mô phỏng'
    ))

    fig.add_trace(go.Scatter(
        x=[max_sharpe_portfolio['volatility']], y=[max_sharpe_portfolio['return']],
        mode='markers', marker=dict(color='red', size=15, symbol='star'), name='Sharpe Tối đa',
        hovertemplate="<b>Sharpe Tối đa</b><br>Lợi nhuận: %{y:.2%}<br>Rủi ro: %{x:.2%}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=[min_vol_portfolio['volatility']], y=[min_vol_portfolio['return']],
        mode='markers', marker=dict(color='green', size=15, symbol='star'), name='Rủi ro Tối thiểu',
        hovertemplate="<b>Rủi ro Tối thiểu</b><br>Lợi nhuận: %{y:.2%}<br>Rủi ro: %{x:.2%}<extra></extra>"
    ))

    fig.update_layout(
        title="Đường biên Hiệu quả & Các Danh mục Mô phỏng",
        xaxis_title="Rủi ro (Độ lệch chuẩn hàng năm)",
        yaxis_title="Lợi nhuận kỳ vọng hàng năm",
        xaxis_tickformat=".2%", yaxis_tickformat=".2%",
        legend_title="Danh mục nổi bật", height=600, template="plotly_white"
    )
    return fig

def plot_portfolio_pie(weights_df: pd.DataFrame, title: str = 'Phân bổ Danh mục') -> go.Figure:
    fig = px.pie(
        weights_df, values='Tỷ trọng', names=weights_df.index, title=title
    )
    fig.update_traces(
        textposition='inside', textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Tỷ trọng: %{percent:.2%}<extra></extra>'
    )
    return fig

def prepare_echarts_sunburst_data(weights_df: pd.DataFrame) -> str:
    """
    Chuẩn bị dữ liệu phân bổ danh mục cho biểu đồ ECharts Nested Pie.
    """
    st.info("Đang lấy dữ liệu ngành cho các cổ phiếu...")
    portfolio_details = []
    progress_bar = st.progress(0)

    if weights_df['Tỷ trọng'].dtype == 'object':
         weights_df['Tỷ trọng'] = weights_df['Tỷ trọng'].str.rstrip('%').astype('float') / 100.0

    for i, (symbol, row) in enumerate(weights_df.iterrows()):
        try:
            company_overview_df = Company(symbol=symbol, source='TCBS').overview()
            industry = 'Ngành khác'

            if not company_overview_df.empty and 'industry' in company_overview_df.columns:
                industry_value = company_overview_df['industry'].iloc[0]

                if pd.notna(industry_value) and industry_value is not None:
                    industry = industry_value

            portfolio_details.append({
                'symbol': symbol,
                'weight': row['Tỷ trọng'],
                'industry': industry
            })
        except Exception as e:
            st.warning(f"Không thể lấy thông tin ngành cho {symbol}: {e}")
            portfolio_details.append({
                'symbol': symbol,
                'weight': row['Tỷ trọng'],
                'industry': 'Ngành khác'
            })
        progress_bar.progress((i + 1) / len(weights_df))

    progress_bar.empty()

    if not portfolio_details:
        return json.dumps({})

    details_df = pd.DataFrame(portfolio_details)

    total_weight = details_df['weight'].sum()
    if total_weight > 0:
        industry_weights_raw = details_df.groupby('industry')['weight'].sum()
        small_industries = industry_weights_raw[industry_weights_raw / total_weight < 0.02].index
        details_df['industry'] = details_df['industry'].apply(lambda x: 'Ngành khác' if x in small_industries else x)

    details_df = details_df.sort_values(by='industry').reset_index(drop=True)

    outer_ring_data = details_df[['weight', 'symbol']].rename(columns={'weight': 'value', 'symbol': 'name'}).to_dict('records')
    industry_weights = details_df.groupby('industry')['weight'].sum().reset_index()
    inner_ring_data = industry_weights.rename(columns={'weight': 'value', 'industry': 'name'}).to_dict('records')
    legend_data = industry_weights['industry'].tolist()

    final_data = {
        "legendData": legend_data,
        "innerRingData": inner_ring_data,
        "outerRingData": outer_ring_data
    }

    return json.dumps(final_data, indent=2, ensure_ascii=False)

# --- CORRECTED FUNCTION ---
def plot_cumulative_returns(performance_df: pd.DataFrame, title: str) -> go.Figure:
    """
    Vẽ biểu đồ đường so sánh hiệu suất tích lũy của danh mục và benchmark.

    Args:
        performance_df (pd.DataFrame): DataFrame có chứa các cột hiệu suất tích lũy.
        title (str): Tiêu đề của biểu đồ.

    Returns:
        go.Figure: Đối tượng biểu đồ Plotly.
    """
    if performance_df.empty or len(performance_df.columns) < 2:
        return go.Figure().update_layout(title="Không có đủ dữ liệu để vẽ biểu đồ hiệu suất.")

    # Sử dụng Plotly Express để vẽ biểu đồ đường
    fig = px.line(
        performance_df,
        x=performance_df.index,
        y=performance_df.columns,
        title=title,  # Use the passed title argument
        labels={'value': 'Hiệu suất Tích lũy', 'index': 'Ngày', 'variable': 'Chỉ số'}
    )

    # Tùy chỉnh layout
    fig.update_layout(
        template="plotly_white",
        legend_title_text='',
        yaxis_tickformat=".2%",
        hovermode="x unified"
    )

    # Tùy chỉnh hovertemplate
    fig.update_traces(
        hovertemplate='<b>%{x|%d-%m-%Y}</b><br>%{data.name}: %{y:.2%}<extra></extra>'
    )

    return fig