"""
Unit tests for app.components.page_header
"""

import pytest
from unittest.mock import patch, MagicMock
from app.components.page_header import render_page_header


def test_render_page_header_executes_cleanly():
    """Verify render_page_header constructs valid HTML and calls st.html."""
    with patch("streamlit.html") as mock_st_html:
        render_page_header(
            title="Test Title",
            subtitle="Test Subtitle",
            icon_name="camera",
            overline="TEST OVERLINE",
            action_pills=[
                {"icon": "camera", "text": "Batch"},
                {"icon": "shield", "text": "Protected"}
            ]
        )

        assert mock_st_html.called
        html_arg = mock_st_html.call_args[0][0]
        assert "foodlens-page-banner" in html_arg
        assert "Test Title" in html_arg
        assert "Test Subtitle" in html_arg
        assert "TEST OVERLINE" in html_arg
        assert "Batch" in html_arg
        assert "Protected" in html_arg
        assert "linear-gradient(135deg, #144730 0%, #1B5E3F 60%, #2E7D56 100%)" in html_arg


def test_render_page_header_without_optionals():
    """Verify render_page_header works when subtitle and action_pills are omitted."""
    with patch("streamlit.html") as mock_st_html:
        render_page_header(title="Minimal Title")

        assert mock_st_html.called
        html_arg = mock_st_html.call_args[0][0]
        assert "Minimal Title" in html_arg
        assert "foodlens-page-banner" in html_arg
