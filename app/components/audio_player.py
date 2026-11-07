"""
FoodLens UI Component: Read-Aloud Audio Player
Provides an accessible, interactive spoken audio player with speed and language controls.
"""

from typing import Dict, Any
import streamlit as st
import streamlit.components.v1 as components

from foodlens.narration import generate_narration_script, NarrationMode
from foodlens.tts.browser import BrowserSpeechProvider

browser_tts = BrowserSpeechProvider()


def render_audio_narration_player(
    product_data: Dict[str, Any],
    default_lang: str = "en",
    key_suffix: str = "main",
):
    """
    Renders the Read-Aloud speech player with speed, language, and mode controls.
    """
    with st.expander("🔊 Listen to Summary (Hindi / English Read-Aloud)", expanded=False):
        c_lang, c_mode, c_spd = st.columns([1.2, 1.2, 1.2])

        with c_lang:
            lang_choice = st.selectbox(
                "Language",
                options=["en", "hi"],
                index=0 if default_lang == "en" else 1,
                format_func=lambda x: "English (EN)" if x == "en" else "हिंदी (HI)",
                key=f"audio_lang_{key_suffix}"
            )

        with c_mode:
            mode_choice = st.selectbox(
                "Detail Level",
                options=[NarrationMode.DETAILED, NarrationMode.SHORT],
                index=0,
                format_func=lambda x: "Detailed (<45s)" if x == NarrationMode.DETAILED else "Short (<20s)",
                key=f"audio_mode_{key_suffix}"
            )

        with c_spd:
            speed_choice = st.selectbox(
                "Speed",
                options=[0.75, 1.0, 1.25],
                index=1,
                format_func=lambda x: f"{x}x",
                key=f"audio_spd_{key_suffix}"
            )

        # Generate deterministic script
        script = generate_narration_script(product_data, language=lang_choice, mode=mode_choice)

        # Render Browser Web Speech API player in clean component container
        player_html = browser_tts.generate_html_player(
            text=script.text,
            language=lang_choice,
            speed=speed_choice,
            player_id=f"player_{key_suffix}",
        )
        components.html(player_html, height=135)

        # Transcript Drawer
        with st.expander("📄 Spoken Transcript (Text)", expanded=False):
            st.markdown(
                f"""
                <div style="font-size: 13.5px; color: #334155; line-height: 1.6; background: #FFFFFF; padding: 12px; border-radius: 8px; border: 1px solid #CBD5E1;">
                    {script.text}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.caption(f"Estimated duration: ~{script.duration_seconds}s • {script.word_count} words • 100% deterministic (no LLM translation)")
