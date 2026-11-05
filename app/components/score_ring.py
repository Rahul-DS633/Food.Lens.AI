"""
Streamlit Component: Score Ring Gauge
Uses Plotly indicator gauge to display category-aware FoodLens Score.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional


def render_score_ring(score: Optional[int], band: str, color_hex: str, version: str = "1.0.0"):
    """
    Renders a circular gauge for the 0-100 score.
    If score is None, renders an informative 'Insufficient Data' placeholder.
    """
    if score is None:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 24px; background: #F3F4F6; border-radius: 16px; border: 1.5px dashed #CBD5E1;">
                <div style="font-size: 32px;">⚠️</div>
                <div style="font-size: 18px; font-weight: 700; color: #4B5563; margin-top: 8px;">{band}</div>
                <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">Score v{version} • Missing > 2 core label values</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>{band}</b><br><span style='font-size:12px;color:gray'>Score v{version}</span>", 'font': {'size': 16, 'family': 'Plus Jakarta Sans'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#9CA3AF"},
            'bar': {'color': color_hex, 'thickness': 0.8},
            'bgcolor': "#F3F4F6",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 45], 'color': '#FEE2E2'},
                {'range': [45, 70], 'color': '#FEF3C7'},
                {'range': [70, 100], 'color': '#DCFCE7'},
            ],
            'threshold': {
                'line': {'color': color_hex, 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Plus Jakarta Sans'}
    )

    st.plotly_chart(fig, use_container_width=True)
