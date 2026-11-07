"""
FoodLens Browser Speech Provider
Leverages standard HTML5 Web Speech API (window.speechSynthesis) inside the user's browser.
Ensures zero data transmission to external servers, absolute privacy, and instant playback.
"""

from foodlens.tts.base import TTSProvider, TTSResult


class BrowserSpeechProvider(TTSProvider):
    """
    Browser-native speech synthesis using standard window.speechSynthesis.
    """
    def synthesize(self, text: str, language: str = "en") -> TTSResult:
        # Browser speech is executed directly on the client side via JavaScript
        return TTSResult(
            audio_bytes=None,
            provider_type="browser_speech_synthesis",
            cached=False,
        )

    def generate_html_player(
        self,
        text: str,
        language: str = "en",
        speed: float = 1.0,
        player_id: str = "tts_player",
    ) -> str:
        """
        Generates an accessible, keyboard-operable Web Speech API audio widget.
        Checks for hi-IN voice support when Hindi is chosen and notifies if absent.
        """
        lang_code = "hi-IN" if language == "hi" else "en-US"
        safe_text = text.replace('"', '\\"').replace("\n", " ").replace("'", "\\'")

        return f"""
        <div id="{player_id}_container" style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin: 10px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">🔊</span>
                    <span style="font-weight: 700; color: #0F172A; font-size: 14px;">Audio Narration ({'Hindi' if language == 'hi' else 'English'})</span>
                </div>
                <div id="{player_id}_status" style="font-size: 12px; color: #64748B;">Ready to play</div>
            </div>

            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                <button id="{player_id}_play" onclick="speakText_{player_id}()" 
                    style="background: #1B5E3F; color: white; border: none; border-radius: 8px; padding: 6px 14px; font-weight: 700; font-size: 13px; cursor: pointer;"
                    aria-label="Play narration">▶ Play</button>
                <button id="{player_id}_pause" onclick="pauseText_{player_id}()" 
                    style="background: #E2E8F0; color: #334155; border: none; border-radius: 8px; padding: 6px 12px; font-weight: 600; font-size: 13px; cursor: pointer;"
                    aria-label="Pause narration">⏸ Pause</button>
                <button id="{player_id}_stop" onclick="stopText_{player_id}()" 
                    style="background: #E2E8F0; color: #334155; border: none; border-radius: 8px; padding: 6px 12px; font-weight: 600; font-size: 13px; cursor: pointer;"
                    aria-label="Stop narration">⏹ Stop</button>
            </div>

            <div id="{player_id}_voice_warning" style="display: none; background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #92400E; margin-top: 6px;">
                ⚠️ Hindi voice not detected in your device browser. Speaking with fallback synthesizer.
            </div>

            <script>
                var synth_{player_id} = window.speechSynthesis;
                var utterance_{player_id} = null;

                function checkVoices_{player_id}() {{
                    if (!synth_{player_id}) return;
                    var voices = synth_{player_id}.getVoices();
                    var hasHi = voices.some(v => v.lang.includes('hi') || v.lang.includes('HI'));
                    var warn = document.getElementById('{player_id}_voice_warning');
                    if ('{language}' === 'hi' && !hasHi && warn) {{
                        warn.style.display = 'block';
                    }}
                }}

                if (window.speechSynthesis) {{
                    window.speechSynthesis.onvoiceschanged = checkVoices_{player_id};
                    checkVoices_{player_id}();
                }}

                function speakText_{player_id}() {{
                    if (!synth_{player_id}) {{
                        alert('Browser speech synthesis is not supported on this device.');
                        return;
                    }}
                    if (synth_{player_id}.paused) {{
                        synth_{player_id}.resume();
                        document.getElementById('{player_id}_status').innerText = 'Playing...';
                        return;
                    }}
                    synth_{player_id}.cancel();

                    utterance_{player_id} = new SpeechSynthesisUtterance("{safe_text}");
                    utterance_{player_id}.lang = "{lang_code}";
                    utterance_{player_id}.rate = {speed};

                    var voices = synth_{player_id}.getVoices();
                    var targetVoice = voices.find(v => v.lang.replace('_', '-').toLowerCase() === '{lang_code}'.toLowerCase());
                    if (targetVoice) {{
                        utterance_{player_id}.voice = targetVoice;
                    }}

                    utterance_{player_id}.onstart = function() {{
                        document.getElementById('{player_id}_status').innerText = 'Speaking...';
                    }};
                    utterance_{player_id}.onend = function() {{
                        document.getElementById('{player_id}_status').innerText = 'Finished';
                    }};
                    utterance_{player_id}.onerror = function(e) {{
                        document.getElementById('{player_id}_status').innerText = 'Stopped';
                    }};

                    synth_{player_id}.speak(utterance_{player_id});
                }}

                function pauseText_{player_id}() {{
                    if (synth_{player_id} && synth_{player_id}.speaking) {{
                        synth_{player_id}.pause();
                        document.getElementById('{player_id}_status').innerText = 'Paused';
                    }}
                }}

                function stopText_{player_id}() {{
                    if (synth_{player_id}) {{
                        synth_{player_id}.cancel();
                        document.getElementById('{player_id}_status').innerText = 'Stopped';
                    }}
                }}
            </script>
        </div>
        """
