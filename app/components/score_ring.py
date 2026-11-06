"""
FoodLens AI — Score Ring Gauge Component
Uses Plotly indicator gauge with vector status icons to display category-aware FoodLens Score.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional
from app.components.icons import get_icon_svg


def render_score_ring(score: Optional[int], band: str, color_hex: str, version: str = "1.0.0"):
    """
    Renders a circular gauge for the 0-100 score.
    If score is None, renders an informative 'Insufficient Data' card with vector alert icon.
    """
    if score is None:
        alert_svg = get_icon_svg("alert", size=32, color="#F59E0B")
        st.markdown(
            f"""
            <div style="text-align: center; padding: 26px 20px; background: #FFFBEB; border-radius: 18px; border: 1.5px dashed #FCD34D; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.08);">
                <div style="margin-bottom: 8px;">{alert_svg}</div>
                <div style="font-size: 18px; font-weight: 800; color: #92400E; margin-top: 4px;">{band}</div>
                <div style="font-size: 12.5px; color: #B45309; margin-top: 4px;">Score v{version} • Missing > 2 core label values</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>{band}</b><br><span style='font-size:12px;color:#64748B'>Score v{version}</span>", 'font': {'size': 16, 'family': 'Plus Jakarta Sans', 'color': '#0F172A'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1.5, 'tickcolor': "#94A3B8"},
            'bar': {'color': color_hex, 'thickness': 0.8},
            'bgcolor': "#F1F5F9",
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

    st.plotly_chart(fig, width='stretch')
