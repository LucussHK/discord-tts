"""
Discord TTS App

A desktop application that allows users to convert text to speech and route it to Discord voice channels.
This application uses Microsoft Edge TTS to generate speech and routes the audio to Discord through
a virtual audio device.

Author: LucusHK
License: MIT
"""

import os
import sys
import threading

# Import subprocess wrapper before any other modules that might use subprocess
if sys.platform == "win32":
    # Preload the subprocess wrapper to hide all console windows
    try:
        import subprocess_wrapper
    except ImportError:
        # Handle case where the wrapper is not available
        pass

import asyncio
import tempfile
import json
from datetime import datetime
import re
import hashlib
from functools import lru_cache

import customtkinter as ctk
import pyaudio
import sounddevice as sd
import soundfile as sf
import edge_tts
from pydub import AudioSegment
from CTkToolTip import CTkToolTip
from CTkMessagebox import CTkMessagebox as MessageBox
import numpy as np

# Create a cache directory for temporary audio files
CACHE_DIR = os.path.join(tempfile.gettempdir(), "discord_tts_temp")
os.makedirs(CACHE_DIR, exist_ok=True)

# Clear old cache files on startup
for f in os.listdir(CACHE_DIR):
    if f.endswith('.wav') or f.endswith('.mp3'):
        try:
            os.unlink(os.path.join(CACHE_DIR, f))
        except:
            pass

# ─── HIDE FFmpeg CONSOLES ON WINDOWS ─────────────────────────────────
if sys.platform == "win32":
    import pydub.utils
    import subprocess
    _orig_popen = pydub.utils.Popen
    def _no_console_popen(*args, **kwargs):
        """
        Patched Popen for pydub to hide console windows on Windows
        """
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs.setdefault("startupinfo", si)
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        return _orig_popen(*args, **kwargs)
    pydub.utils.Popen = _no_console_popen
    
    # Also patch regular subprocess.Popen as a fallback
    _orig_subprocess_popen = subprocess.Popen
    def _no_console_subprocess_popen(*args, **kwargs):
        """
        Patched Popen for subprocess to hide console windows on Windows
        """
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs.setdefault("startupinfo", si)
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        return _orig_subprocess_popen(*args, **kwargs)
    # Apply the patch
    subprocess.Popen = _no_console_subprocess_popen

# ─── BUNDLE-AWARE FFmpeg PATHS ─────────────────────────────────
# Set ffmpeg paths to work both when running as script and as a PyInstaller bundle
if getattr(sys, '_MEIPASS', None):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
AudioSegment.converter = os.path.join(base_path, 'ffmpeg.exe')
AudioSegment.ffprobe   = os.path.join(base_path, 'ffprobe.exe')

# ─── EDGE-TTS ASYNC FUNCTIONS ────────────────────────────────
async def _get_voices() -> list:
    """
    Retrieve all available voices from Edge TTS API and group them by language
    
    Returns:
        dict: A dictionary of voice groups organized by locale
    """
    voices = await edge_tts.list_voices()
    # Group voices by language
    voice_groups = {}
    for v in voices:
        locale = v.get('Locale', '')
        if locale not in voice_groups:
            voice_groups[locale] = []
        voice_groups[locale].append({
            'name': v['ShortName'],
            'gender': v.get('Gender', 'Unknown'),
            'display': f"{v['ShortName']} ({v.get('Gender', 'Unknown')})"
        })
    return voice_groups

# Cache for TTS generation - avoid regenerating the same text/voice
# Format: { hash(text+voice+rate): wav_path }
TTS_CACHE = {}
TTS_CACHE_LOCK = threading.Lock()

def get_tts_key(text, voice, rate):
    """
    Generate a unique key for the TTS combination to use in caching
    
    Args:
        text (str): The text to convert to speech
        voice (str): The voice name to use
        rate (str): The speaking rate
        
    Returns:
        str: A hash that uniquely identifies this TTS request
    """
    return hashlib.md5(f"{text}|{voice}|{rate}".encode('utf-8')).hexdigest()

async def _tts_edge(text: str, voice: str, rate: str = "+0%") -> str:
    """
    Generate speech from text using Edge TTS API
    
    Args:
        text (str): The text to convert to speech
        voice (str): The voice name to use
        rate (str): The speaking rate adjustment (e.g., "+10%", "-5%")
        
    Returns:
        str: Path to the generated WAV file
        
    Raises:
        RuntimeError: If speech generation fails
    """
    # Check if we already generated this exact audio
    cache_key = get_tts_key(text, voice, rate)
    
    with TTS_CACHE_LOCK:
        if cache_key in TTS_CACHE and os.path.exists(TTS_CACHE[cache_key]):
            return TTS_CACHE[cache_key]
    
    # Create temporary files with predictable names
    mp3_path = os.path.join(CACHE_DIR, f"{cache_key}.mp3")
    wav_path = os.path.join(CACHE_DIR, f"{cache_key}.wav")
    
    try:
        # Generate speech with edge-tts
        # Force subprocess creation flags if on Windows
        if sys.platform == 'win32':
            # Set process creation flags to suppress console window
            import edge_tts.constants as constants
            if hasattr(constants, 'Process'):
                # Ensure subprocess creationflags are set on Windows
                orig_flags = constants.Process.CREATION_FLAGS
                constants.Process.CREATION_FLAGS = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                
        # Generate the audio
        comm = edge_tts.Communicate(text, voice, rate=rate)
        await comm.save(mp3_path)
        
        # Restore original flags
        if sys.platform == 'win32' and hasattr(constants, 'Process'):
            constants.Process.CREATION_FLAGS = orig_flags
            
        # Convert to WAV at 48kHz (required for Discord)
        audio = AudioSegment.from_file(mp3_path, format='mp3')
        audio = audio.set_frame_rate(48000)
        audio.export(wav_path, format='wav')
        
        # Add to cache
        with TTS_CACHE_LOCK:
            TTS_CACHE[cache_key] = wav_path
        
        # Clean up mp3 file
        try:
            os.unlink(mp3_path)
        except:
            pass
            
        return wav_path
    except Exception as e:
        # Clean up in case of error
        for path in [mp3_path, wav_path]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass
        raise RuntimeError(f'Edge-tts failed: {e}')

class VirtualMicrophoneApp:
    """
    Main application class for the Discord TTS app
    
    This class handles the GUI and all functionality related to:
    - Text-to-speech generation
    - Audio playback to virtual devices
    - Settings management
    - UI controls and interactions
    """
    def __init__(self, root):
        """
        Initialize the application
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title('Discord TTS (Made by LucussHK)')
        self.root.geometry('850x750')  # Increased height to accommodate new UI elements
        self.root.minsize(850, 750)    # Increased minimum height too
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set theme
        ctk.set_appearance_mode('system')  # Use system theme (dark/light)
        ctk.set_default_color_theme('blue')

        # Settings and history
        self.config_file = os.path.join(os.path.expanduser("~"), "discord_tts_config.json")
        self.history_file = os.path.join(os.path.expanduser("~"), "discord_tts_history.json")
        self.settings = self.load_settings()
        self.message_history = self.load_history()
        self.current_history_index = -1
        
        # UI Language support (English/Chinese)
        self.ui_language = self.settings.get("ui_language", "en")  # Default to English
        self.translations = {
            "en": {
                # App title
                "app_title": "Discord TTS",
                "app_subtitle": "Text-to-Speech for Discord",
                # Audio settings
                "audio_settings": "Audio Device Settings",
                "discord_output": "Discord Output:",
                "monitor_output": "Monitor Output:",
                "discord_reminder": "Make sure to select Cable Output in Discord",
                # Voice settings
                "voice_settings": "Voice Settings",
                "language": "Language:",
                "voice": "Voice:",
                "speed": "Speed:",
                # Interface settings
                "interface_settings": "Interface Settings",
                "ui_language": "Interface Language:",
                # Buttons
                "save_settings": "Save Settings",
                "speak": "Speak in Discord (Ctrl+Enter)",
                "stop": "Stop (Esc)",
                "clear": "Clear",
                "save_wav": "Save as WAV",
                # History
                "message_history": "Message History",
                "type_message": "Type your message:",
                # Status and messages
                "ready": "Ready",
                "generating": "Generating speech...",
                "speaking": "Speaking...",
                "stopped": "Stopped",
                "cleared": "Cleared text and history",
                "settings_saved": "Settings saved",
                "loading_voices": "Loading voices...",
                # Languages display names
                "all_languages": "All Languages",
                "chinese_mainland": "Chinese (Mainland)",
                "chinese_taiwan": "Chinese (Taiwan)",
                "cantonese": "Cantonese (Hong Kong)",
                "english_us": "English (US)",
                "english_uk": "English (UK)",
                # Confirmations
                "clear_confirm": "Are you sure you want to clear all text and history?",
                "exit_confirm": "Are you sure you want to exit?",
                # Errors
                "error_loading_voices": "Error loading voices: ",
                "error_tts": "TTS Error",
                "error_playback": "Playback Error",
                "error_save": "Save Error",
                "error_settings": "Settings Error",
                "force_overlap": "Force overlap (stop current playback)",
                "preview": "Preview",
                "previewing": "Previewing...",
                "error_voice_selection": "Invalid voice selection",
                # Tooltips
                "tooltip_speed": "Adjust voice speed (-50% to +50%)",
                "tooltip_speak": "Send TTS to Discord (Ctrl+Enter)",
                "tooltip_stop": "Stop playback (Esc)",
                "tooltip_clear": "Clear text input and history",
                "tooltip_cable": "For Discord to receive the audio, set the Voice Input device to 'Cable Output'",
                "tooltip_overlap": "When checked, new playback will stop any currently playing audio",
                "tooltip_preview": "Play a short sample of the selected voice",
                "tooltip_history": "Double-click to select a previous message"
            },
            "zh": {
                # App title
                "app_title": "Discord文字轉語音",
                "app_subtitle": "Discord文字轉語音工具",
                # Audio settings
                "audio_settings": "音頻設備設置",
                "discord_output": "Discord輸出設備:",
                "monitor_output": "監聽輸出設備:",
                "discord_reminder": "請確保在Discord中選擇Cable Output",
                # Voice settings
                "voice_settings": "語音設置",
                "language": "語言:",
                "voice": "語音:",
                "speed": "語速:",
                # Interface settings
                "interface_settings": "介面設置",
                "ui_language": "介面語言:",
                # Buttons
                "save_settings": "保存設置",
                "speak": "發送語音 (Ctrl+Enter)",
                "stop": "停止 (Esc)",
                "clear": "清除",
                "save_wav": "保存為WAV",
                # History
                "message_history": "消息歷史",
                "type_message": "輸入您的消息:",
                # Status and messages
                "ready": "✅",
                "generating": "❌",
                "speaking": "❌",
                "stopped": "✅",
                "cleared": "✅",
                "settings_saved": "✅",
                "loading_voices": "❌",
                # Languages display names
                "all_languages": "所有語言",
                "chinese_mainland": "中文 (中國大陸)",
                "chinese_taiwan": "中文 (台灣)",
                "cantonese": "粵語 (香港)",
                "english_us": "英語 (美國)",
                "english_uk": "英語 (英國)",
                # Confirmations
                "clear_confirm": "確定要清除所有文本和歷史記錄嗎？",
                "exit_confirm": "確定要退出嗎？",
                # Errors
                "error_loading_voices": "加載語音失敗: ",
                "error_tts": "語音轉換錯誤",
                "error_playback": "播放錯誤",
                "error_save": "保存錯誤",
                "error_settings": "設置錯誤",
                "force_overlap": "強制覆蓋 (停止當前播放)",
                "preview": "預覽",
                "previewing": "預覽中...",
                "error_voice_selection": "無效的語音選擇",
                # Tooltips
                "tooltip_speed": "調整語音速度 (-50% 到 +50%)",
                "tooltip_speak": "發送語音到 Discord (Ctrl+Enter)",
                "tooltip_stop": "停止播放 (Esc)",
                "tooltip_clear": "清除文字輸入和歷史記錄",
                "tooltip_cable": "為了讓 Discord 接收音頻，請在 Discord 中將語音輸入設備設置為 'Cable Output'",
                "tooltip_overlap": "勾選時，新的播放會停止當前正在播放的音頻",
                "tooltip_preview": "播放所選語音的簡短示例",
                "tooltip_history": "雙擊選擇以前的消息"
            }
        }
        
        # Asyncio event loop for TTS
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        # Audio devices
        self.pyaudio_inst = pyaudio.PyAudio()
        self.audio_devices = self._get_audio_devices()
        self.default_monitor_idx = sd.default.device[1]

        # Initialize UI variables
        self.is_generating = False
        self.is_playing = False
        self.voice_groups = {}
        self.all_voices = []
        self.filtered_voices = []
        
        # Build UI
        self._build_ui()
        
        # Fetch voices (async)
        self.status_var.set(self.get_text("loading_voices"))
        threading.Thread(target=self.fetch_voices, daemon=True).start()
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-Return>", lambda e: self.speak_text())
        self.root.bind("<Escape>", lambda e: self.stop_speaking())
        self.text_input.bind("<Up>", self.navigate_history_up)
        self.text_input.bind("<Down>", self.navigate_history_down)
    

    def get_text(self, key):
        """Get translated text based on current UI language"""
        return self.translations.get(self.ui_language, self.translations["en"]).get(key, key)

    def fetch_voices(self):
        try:
            self.voice_groups = asyncio.run_coroutine_threadsafe(_get_voices(), self.loop).result()
            
            # Filter to keep only requested languages (Chinese, Cantonese, English US/UK)
            filtered_groups = {}
            supported_locales = ['zh-CN', 'zh-TW', 'zh-HK', 'en-US', 'en-GB']
            for locale, voices in self.voice_groups.items():
                if locale in supported_locales:
                    filtered_groups[locale] = voices
            
            self.voice_groups = filtered_groups
            self.all_voices = []
            for locale, voices in self.voice_groups.items():
                for voice in voices:
                    voice['locale'] = locale
                    self.all_voices.append(voice)
            
            # Update language filter dropdown
            languages = sorted(self.voice_groups.keys())
            language_display_names = {
                'zh-CN': self.get_text("chinese_mainland"),
                'zh-TW': self.get_text("chinese_taiwan"),
                'zh-HK': self.get_text("cantonese"),
                'en-US': self.get_text("english_us"),
                'en-GB': self.get_text("english_uk")
            }
            
            language_options = [self.get_text("all_languages")] + [language_display_names[lang] for lang in languages]
            
            # Create mappings between display names and language codes
            self.language_mapping = {language_display_names[lang]: lang for lang in languages}
            self.language_mapping[self.get_text("all_languages")] = "All Languages"
            
            # Create reverse mapping (code -> display name) for settings loading
            self.reverse_language_mapping = {"All Languages": self.get_text("all_languages")}
            for code, name in language_display_names.items():
                self.reverse_language_mapping[code] = name
                
            # Update the language filter combobox with available options
            self.language_filter.configure(values=language_options)
            
            # First set filtered_voices to all voices so that when we try to find a specific voice,
            # we have the complete list available
            self.filtered_voices = self.all_voices
            
            # Get saved language from settings
            saved_language = self.settings.get("language", "All Languages")
            print(f"Raw saved language from settings: {saved_language}")
            
            # Figure out if saved_language is a language code or display name
            selected_language_display = self.get_text("all_languages")  # Default
            
            # Case 1: It's a language code like "zh-CN"
            if saved_language in self.reverse_language_mapping:
                selected_language_display = self.reverse_language_mapping[saved_language]
                print(f"Found language code in mapping: {saved_language} -> {selected_language_display}")
            # Case 2: It might be a display name directly
            elif saved_language in self.language_mapping:
                selected_language_display = saved_language
                print(f"Found display name directly: {saved_language}")
            # Case 3: It might be the Chinese display name, try to match part of it
            elif "中文" in saved_language:
                if "大陸" in saved_language or "中国" in saved_language:
                    selected_language_display = self.get_text("chinese_mainland")
                    print(f"Matched Chinese (Mainland) from: {saved_language}")
                elif "台灣" in saved_language or "台湾" in saved_language:
                    selected_language_display = self.get_text("chinese_taiwan")
                    print(f"Matched Chinese (Taiwan) from: {saved_language}")
            elif "粵語" in saved_language or "粤语" in saved_language or "香港" in saved_language:
                selected_language_display = self.get_text("cantonese")
                print(f"Matched Cantonese from: {saved_language}")
            elif "英語" in saved_language or "英语" in saved_language:
                if "美國" in saved_language or "美国" in saved_language:
                    selected_language_display = self.get_text("english_us")
                    print(f"Matched English (US) from: {saved_language}")
                elif "英國" in saved_language or "英国" in saved_language:
                    selected_language_display = self.get_text("english_uk")
                    print(f"Matched English (UK) from: {saved_language}")
            else:
                # Default to All Languages if no match
                print(f"No match found for language: {saved_language}, defaulting to All Languages")
                selected_language_display = self.get_text("all_languages")
                
            # Set the language filter dropdown
            self.language_filter.set(selected_language_display)
            print(f"Setting language filter to: {selected_language_display}")
            
            # Now filter voices based on the selected language
            selected_language = self.language_filter.get()
            if selected_language in self.language_mapping:
                locale = self.language_mapping[selected_language]
                # If the language is not "All Languages", filter the voices
                if locale != "All Languages":
                    print(f"Filtering voices by locale: {locale}")
                    self.filtered_voices = [v for v in self.all_voices if v['locale'] == locale]
            
            # Update the voice dropdown with filtered voices
            voice_display_list = [v['display'] for v in self.filtered_voices]
            self.voice_cb.configure(values=voice_display_list)
            
            # Try to restore selected voice from settings
            saved_voice = self.settings.get("voice")
            print(f"Saved voice from settings: {saved_voice}")
            voice_was_set = False
            
            if saved_voice:
                # Find the voice in filtered voices
                for i, v in enumerate(self.filtered_voices):
                    if v['name'] == saved_voice:
                        print(f"Found matching voice: {saved_voice} -> {v['display']}")
                        self.voice_cb.set(v['display'])
                        voice_was_set = True
                        break
            
            # If voice wasn't set, use default
            if not voice_was_set and voice_display_list:
                chinese_voices = [v for v in self.filtered_voices if v['locale'].startswith(('zh-CN', 'zh-TW'))]
                if chinese_voices:
                    print(f"Setting default Chinese voice: {chinese_voices[0]['display']}")
                    self.voice_cb.set(chinese_voices[0]['display'])
                else:
                    print(f"Setting first available voice: {voice_display_list[0]}")
                    self.voice_cb.set(voice_display_list[0])
            
            self.status_var.set(self.get_text("ready"))
            
            # Clean up any old settings that might be causing issues
            self._clean_settings()
            
            # After loading the settings, register change callbacks to auto-save
            self._register_auto_save_callbacks()
            
        except Exception as e:
            self.status_var.set(f'{self.get_text("error_loading_voices")}{str(e)}')
            print(f"Error loading voices: {e}")
            MessageBox(
                title=self.get_text("error_tts"),
                message=str(e),
                icon="cancel"
            )
            
    def _clean_settings(self):
        """Fix any settings format issues to ensure clean state for next save"""
        # Make sure we have the current selected language code, not display name
        selected_language_display = self.language_filter.get()
        if selected_language_display in self.language_mapping:
            language_code = self.language_mapping[selected_language_display]
            self.settings["language"] = language_code
            print(f"Cleaned up settings: {selected_language_display} -> {language_code}")
            
        # Make sure voice is stored by name, not display
        selected_display = self.voice_cb.get()
        selected_voice = next((v['name'] for v in self.filtered_voices if v['display'] == selected_display), None)
        if selected_voice:
            self.settings["voice"] = selected_voice
            print(f"Cleaned up voice setting: {selected_display} -> {selected_voice}")
            
        # Save the cleaned settings
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error cleaning settings: {e}")
            
    def _register_auto_save_callbacks(self):
        """Register callbacks for auto-saving settings when they change"""
        # For comboboxes, add a callback for when they lose focus or Enter is pressed
        self.language_filter.bind("<FocusOut>", lambda e: self.auto_save_settings())
        self.voice_cb.bind("<FocusOut>", lambda e: self.auto_save_settings())
        self.cable_cb.bind("<FocusOut>", lambda e: self.auto_save_settings())
        self.mon_cb.bind("<FocusOut>", lambda e: self.auto_save_settings())
        self.ui_lang_cb.bind("<FocusOut>", lambda e: self.auto_save_settings())
        
        # Track variable changes for checkboxes/sliders
        self.force_overlap_var.trace_add("write", lambda *args: self.auto_save_settings())
        self.speed_slider.configure(command=self.on_speed_change)
        
    def on_speed_change(self, value):
        """Handle speed changes with visual feedback and auto-save"""
        self.update_speed_label(value)
        self.auto_save_settings()
        
    def filter_voices(self, selected_language=None):
        """Filter available voices based on selected language"""
        if not selected_language:
            selected_language = self.language_filter.get()
            
        if selected_language == self.get_text("all_languages"):
            self.filtered_voices = self.all_voices
        else:
            # Use the mapping to get the actual locale code
            locale = self.language_mapping.get(selected_language)
            self.filtered_voices = [v for v in self.all_voices if v['locale'] == locale]
        
        voice_display_list = [v['display'] for v in self.filtered_voices]
        self.voice_cb.configure(values=voice_display_list)
        
        if voice_display_list:
            self.voice_cb.set(voice_display_list[0])
            
        # Auto save when language filter changes
        self.auto_save_settings()
            
    def auto_save_settings(self):
        """Save settings automatically when they change"""
        # Small delay to avoid saving multiple times in quick succession
        if hasattr(self, '_save_after_id'):
            self.root.after_cancel(self._save_after_id)
        
        self._save_after_id = self.root.after(500, self._do_save_settings)
    
    def _do_save_settings(self):
        """Actually perform the settings save operation"""
        # Get selected voice object
        selected_display = self.voice_cb.get()
        selected_voice = next((v['name'] for v in self.filtered_voices if v['display'] == selected_display), None)
        
        # Get selected language display name
        selected_language_display = self.language_filter.get()
        
        # Convert display name to language code
        if selected_language_display in self.language_mapping:
            language_code = self.language_mapping[selected_language_display]
        else:
            language_code = "All Languages"  # Default
            
        print(f"Saving language: {selected_language_display} -> {language_code}")
        
        settings = {
            "output_device": self.cable_cb.get(),
            "monitor_device": self.mon_cb.get(),
            "voice": selected_voice,
            "speed": int(self.speed_slider.get()),
            "language": language_code,  # Store language code not display name
            "ui_language": self.ui_language,
            "force_overlap": self.force_overlap_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            self.status_var.set(self.get_text("settings_saved"))
            # Clear status after 2 seconds
            self.root.after(2000, lambda: self.status_var.set(self.get_text("ready")))
        except Exception as e:
            print(f"Error saving settings: {e}")
            MessageBox(
                title=self.get_text("error_settings"),
                message=f"Could not save settings: {str(e)}",
                icon="cancel"
            )

    def _get_audio_devices(self) -> dict:
        devs = {}
        for i in range(self.pyaudio_inst.get_device_count()):
            info = self.pyaudio_inst.get_device_info_by_index(i)
            if info.get('maxOutputChannels',0) > 0:
                devs[info['name']] = i
        return devs

    def _build_ui(self):
        # Create main frames
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # App title in sidebar
        self.logo_label = ctk.CTkLabel(self.sidebar, text=self.get_text("app_title"), 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10))
        
        self.subtitle = ctk.CTkLabel(self.sidebar, text=self.get_text("app_subtitle"))
        self.subtitle.pack(padx=20, pady=(0, 20))
        
        # Sidebar sections
        self.sidebar_audio = ctk.CTkFrame(self.sidebar)
        self.sidebar_audio.pack(fill=tk.X, padx=10, pady=5)
        
        # Audio device section
        ctk.CTkLabel(self.sidebar_audio, text=self.get_text("audio_settings"), 
                    font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(5, 10))
        
        # Discord output
        ctk.CTkLabel(self.sidebar_audio, text=self.get_text("discord_output")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.cable_cb = ctk.CTkComboBox(self.sidebar_audio, values=list(self.audio_devices), width=180)
        self.cable_cb.pack(padx=10, pady=(0, 5))
        
        # Discord reminder - Cable output notice
        self.cable_reminder = ctk.CTkLabel(self.sidebar_audio, text=self.get_text("discord_reminder"),
                                          text_color=("gray50", "gray70"), font=ctk.CTkFont(size=10))
        self.cable_reminder.pack(padx=10, pady=(0, 5))
        
        # Set output devices from settings or defaults
        saved_output = self.settings.get("output_device")
        if saved_output and saved_output in self.audio_devices:
            self.cable_cb.set(saved_output)
        else:
            # Try to find "Cable" device as default
            cable_device = next((dev for dev in self.audio_devices if "cable" in dev.lower()), None)
            if cable_device:
                self.cable_cb.set(cable_device)
            else:
                self.cable_cb.set(list(self.audio_devices)[0])
            
        # Monitor output
        ctk.CTkLabel(self.sidebar_audio, text=self.get_text("monitor_output")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.mon_cb = ctk.CTkComboBox(self.sidebar_audio, values=list(self.audio_devices), width=180)
        self.mon_cb.pack(padx=10, pady=(0, 5))
        
        # Set monitor device from settings or default
        saved_monitor = self.settings.get("monitor_device")
        if saved_monitor and saved_monitor in self.audio_devices:
            self.mon_cb.set(saved_monitor)
        else:
            # Try to use system default
            default_name = next((n for n,i in self.audio_devices.items() if i == self.default_monitor_idx), None)
            if default_name:
                self.mon_cb.set(default_name)
            else:
                self.mon_cb.set(list(self.audio_devices)[0])
            
        # Voice settings section
        self.sidebar_voice = ctk.CTkFrame(self.sidebar)
        self.sidebar_voice.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(self.sidebar_voice, text=self.get_text("voice_settings"), 
                    font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(5, 10))
                    
        # Language filter
        ctk.CTkLabel(self.sidebar_voice, text=self.get_text("language")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.language_filter = ctk.CTkComboBox(self.sidebar_voice, values=["Loading..."], width=180,
                                              command=self.filter_voices)
        self.language_filter.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        # Voice model with preview button
        ctk.CTkLabel(self.sidebar_voice, text=self.get_text("voice")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Create a frame for voice selection and preview button
        voice_selection_frame = ctk.CTkFrame(self.sidebar_voice, fg_color="transparent")
        voice_selection_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Voice dropdown
        self.voice_cb = ctk.CTkComboBox(voice_selection_frame, values=["Loading..."], width=140)
        self.voice_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Preview button
        self.preview_btn = ctk.CTkButton(voice_selection_frame, text=self.get_text("preview"), 
                                           width=60, height=28,
                                           command=self.preview_voice)
        self.preview_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Voice speed
        ctk.CTkLabel(self.sidebar_voice, text=self.get_text("speed")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.speed_frame = ctk.CTkFrame(self.sidebar_voice, fg_color="transparent")
        self.speed_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.speed_var = tk.StringVar(value="0")
        self.speed_slider = ctk.CTkSlider(self.speed_frame, from_=-50, to=50, number_of_steps=20,
                                         command=self.update_speed_label)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(0, 5))
        self.speed_slider.set(self.settings.get("speed", 0))
        
        self.speed_label = ctk.CTkLabel(self.speed_frame, text="×1.0", width=40)
        self.speed_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(0, 5))
        self.update_speed_label()  # Update the label immediately
        
        # Interface settings section
        self.sidebar_interface = ctk.CTkFrame(self.sidebar)
        self.sidebar_interface.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(self.sidebar_interface, text=self.get_text("interface_settings"), 
                    font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(5, 10))
        
        # UI Language selection
        ctk.CTkLabel(self.sidebar_interface, text=self.get_text("ui_language")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ui_lang_cb = ctk.CTkComboBox(self.sidebar_interface, values=["English", "中文"], width=180,
                                          command=self.change_ui_language)
        self.ui_lang_cb.pack(padx=10, pady=(0, 5))
        
        # Set UI language from settings
        self.ui_lang_cb.set("English" if self.ui_language == "en" else "中文")
        
        # Main content area
        # Message history
        self.history_label = ctk.CTkLabel(self.main_frame, text=self.get_text("message_history"),
                                        anchor="w", font=ctk.CTkFont(weight="bold"))
        self.history_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.history_frame = ctk.CTkFrame(self.main_frame, height=120)
        self.history_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        self.history_frame.pack_propagate(False)
        
        self.history_list = ctk.CTkTextbox(self.history_frame, height=120, wrap="word")
        self.history_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_list.configure(state="disabled")
        self.update_history_display()
        
        # Text input area
        self.text_label = ctk.CTkLabel(self.main_frame, text=self.get_text("type_message"),
                                     anchor="w", font=ctk.CTkFont(weight="bold"))
        self.text_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.text_input = ctk.CTkTextbox(self.main_frame, height=200, wrap="word")
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        self.text_input.focus_set()
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.speak_btn = ctk.CTkButton(self.button_frame, text=self.get_text("speak"), 
                                      command=self.speak_text,
                                      font=ctk.CTkFont(weight="bold"))
        self.speak_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(self.button_frame, text=self.get_text("stop"), 
                                     command=self.stop_speaking,
                                     fg_color="#D35B58", hover_color="#C77C78")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ctk.CTkButton(self.button_frame, text=self.get_text("clear"), 
                                     command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Force overlap checkbox (below buttons)
        self.overlap_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.overlap_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.force_overlap_var = tk.BooleanVar(value=self.settings.get("force_overlap", False))
        self.force_overlap_cb = ctk.CTkCheckBox(self.overlap_frame, 
                                               text=self.get_text("force_overlap"),
                                               variable=self.force_overlap_var,
                                               onvalue=True, offvalue=False)
        self.force_overlap_cb.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.statusbar_frame = ctk.CTkFrame(self.root, height=25, fg_color=("gray85", "gray25"))
        self.statusbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value=self.get_text("ready"))
        self.statusbar = ctk.CTkLabel(self.statusbar_frame, textvariable=self.status_var,
                                    anchor="w")
        self.statusbar.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=2)
        
        # Add tooltips
        CTkToolTip(self.speed_slider, message=self.get_text("tooltip_speed"))
        CTkToolTip(self.speak_btn, message=self.get_text("tooltip_speak"))
        CTkToolTip(self.stop_btn, message=self.get_text("tooltip_stop"))
        CTkToolTip(self.clear_btn, message=self.get_text("tooltip_clear"))
        CTkToolTip(self.cable_reminder, message=self.get_text("tooltip_cable"))
        CTkToolTip(self.force_overlap_cb, message=self.get_text("tooltip_overlap"))
        CTkToolTip(self.preview_btn, message=self.get_text("tooltip_preview"))
        CTkToolTip(self.history_list, message=self.get_text("tooltip_history"))
        
        # Configure history list double click event
        self.history_list.bind("<Double-Button-1>", self.select_history_item)

        # Bind text change event for auto language detection
        self.text_input.bind("<KeyRelease>", self.on_text_change)

    def update_speed_label(self, value=None):
        speed = self.speed_slider.get()
        if speed < 0:
            factor = 1 + (speed / 100)  # -50 -> 0.5, 0 -> 1.0
        else:
            factor = 1 + (speed / 100)  # 0 -> 1.0, 50 -> 1.5
        self.speed_label.configure(text=f"×{factor:.1f}")
        return f"{int(speed):+d}%"

    def generate_tts(self, text: str) -> str:
        """Generate TTS with performance optimizations"""
        # Get selected voice object
        selected_display = self.voice_cb.get()
        selected_voice = next((v['name'] for v in self.filtered_voices if v['display'] == selected_display), None)
        
        if not selected_voice:
            MessageBox(
                title=self.get_text("error_tts"),
                message=self.get_text("error_voice_selection"),
                icon="cancel"
            )
            return None
            
        # Get speech rate
        rate = self.update_speed_label()
        
        # Pre-calculate the cache key to avoid regenerating the same audio
        cache_key = get_tts_key(text, selected_voice, rate)
        with TTS_CACHE_LOCK:
            if cache_key in TTS_CACHE and os.path.exists(TTS_CACHE[cache_key]):
                return TTS_CACHE[cache_key]
        
        # Generate TTS if not in cache
        future = asyncio.run_coroutine_threadsafe(_tts_edge(text, selected_voice, rate), self.loop)
        try:
            return future.result()
        except Exception as e:
            MessageBox(
                title=self.get_text("error_tts"),
                message=str(e),
                icon="cancel"
            )
            return None

    def play_audio(self, path: str):
        """Play a WAV, but first tear down any existing streams immediately."""
        # 1) Stop any existing playback and mark new playback as active
        self.stop_speaking()
        self.is_playing = True

        # 2) Load the audio file
        try:
            data, fs = sf.read(path, dtype='float32')
            chans = data.shape[1] if data.ndim > 1 else 1
        except Exception as e:
            MessageBox(
                title=self.get_text("error_playback"),
                message=f'WAV read failed: {e}',
                icon="cancel"
            )
            self.status_var.set(self.get_text("ready"))
            return

        # 3) Resolve audio devices
        cidx = self.audio_devices.get(self.cable_cb.get())
        midx = self.audio_devices.get(self.mon_cb.get())
        if cidx is None or midx is None:
            MessageBox(
                title=self.get_text("error_playback"),
                message='Invalid audio device',
                icon="cancel"
            )
            self.status_var.set(self.get_text("ready"))
            return

        # 4) Spawn playback threads, tracking each stream so we can abort if needed
        self._active_streams = []

        def stream_to(idx):
            try:
                stream = sd.OutputStream(
                    device=idx,
                    samplerate=fs,
                    channels=chans,
                    dtype='float32',
                    blocksize=2048,
                    latency='low'
                )
                self._active_streams.append(stream)
                stream.start()

                chunk = 2048
                if chans > 1:
                    pad = np.zeros((chunk, chans), dtype=np.float32)
                else:
                    pad = np.zeros(chunk, dtype=np.float32)

                for i in range(0, len(data), chunk):
                    if not self.is_playing:
                        break
                    block = data[i:i+chunk]
                    if len(block) < chunk:
                        # Pad the final block
                        if chans > 1:
                            block = np.vstack((block, pad[:chunk - len(block)]))
                        else:
                            block = np.concatenate((block, pad[:chunk - len(block)]))
                    stream.write(block)
            except Exception as e:
                if self.is_playing:
                    self.root.after(0, lambda: self.status_var.set(f'Playback error: {e}'))
            finally:
                try:
                    stream.close()
                except:
                    pass

        for idx in (cidx, midx):
            threading.Thread(target=stream_to, args=(idx,), daemon=True).start()

        # 5) Schedule a single "playback finished" callback for this audio
        playback_ms = int(len(data) / fs * 1000 + 200)  # duration + 200ms buffer
        if hasattr(self, '_cleanup_after_id'):
            try:
                self.root.after_cancel(self._cleanup_after_id)
            except:
                pass
        self._cleanup_after_id = self.root.after(playback_ms, self._playback_finished)

    def _playback_finished(self):
        """Called when the scheduled finish timer fires."""
        self.is_playing = False
        self.status_var.set(self.get_text("ready"))
        # Also ensure Speak is re-enabled if it somehow wasn't
        self._on_playback_ready()

            
    def speak_text(self):
        """Called by Ctrl+Enter or Speak button."""
        # If we're already generating or playing (and not forced overlap), ignore spamming
        if self.is_generating or (self.is_playing and not self.force_overlap_var.get()):
            return

        text = self.text_input.get('1.0', tk.END).strip()
        if not text:
            return

        # Mark as generating, disable the button
        self.is_generating = True
        self.speak_btn.configure(state="disabled")
        self.status_var.set(self.get_text("generating"))

        # Spawn background thread to generate + play
        threading.Thread(
            target=self._continue_speak_text,
            args=(text,),
            daemon=True
        ).start()

    def _continue_speak_text(self, text):
        try:
            # Stop any existing playback immediately
            self.stop_speaking()

            # Generate TTS (this may raise)
            wav_path = self.generate_tts(text)
            if not wav_path:
                return

            # Mark playing
            self.is_playing = True
            self.status_var.set(self.get_text("speaking"))
            self.add_to_history(text)

            # Play the audio
            self.play_audio(wav_path)

        except Exception as e:
            # Show error on UI thread
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            # Re-enable Speak button once generation is done
            self.root.after(0, self._on_playback_ready)
    def _on_playback_ready(self):
        """Called after generation/thread-launch to re-enable Speak."""
        self.is_generating = False
        self.speak_btn.configure(state="normal")
    def save_settings(self):
        # Get selected voice object
        selected_display = self.voice_cb.get()
        selected_voice = next((v['name'] for v in self.filtered_voices if v['display'] == selected_display), None)
        
        # Get selected language (convert display name back to code if needed)
        selected_language = self.language_filter.get()
        
        settings = {
            "output_device": self.cable_cb.get(),
            "monitor_device": self.mon_cb.get(),
            "voice": selected_voice,
            "speed": int(self.speed_slider.get()),
            "language": selected_language,
            "ui_language": self.ui_language,
            "force_overlap": self.force_overlap_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            self.status_var.set(self.get_text("settings_saved"))
        except Exception as e:
            MessageBox(
                title=self.get_text("error_settings"),
                message=f"Could not save settings: {str(e)}",
                icon="cancel"
            )

    def stop_speaking(self):
        """Stop all audio immediately and clean up."""
        if not self.is_playing:
            return
        self.is_playing = False

        # Abort each stream
        if hasattr(self, '_active_streams'):
            for stream in self._active_streams:
                try: stream.abort()
                except: pass
            self._active_streams = []

        # Also call sounddevice.stop just in case
        sd.stop()

        # Cancel any pending finish callback
        if hasattr(self, '_cleanup_after_id'):
            try: self.root.after_cancel(self._cleanup_after_id)
            except: pass

        # Update UI
        self.root.after(100, lambda: self.status_var.set(self.get_text("stopped")))

    def add_to_history(self, text):
        # Add to history (with timestamp)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_history.append({
            "text": text,
            "timestamp": timestamp,
            "voice": self.voice_cb.get(),
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Keep only last 50 messages
        if len(self.message_history) > 50:
            self.message_history = self.message_history[-50:]
            
        # Save history
        self.save_history()
        
        # Update display
        self.update_history_display()
        
        # Reset history navigation
        self.current_history_index = -1

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
            
        return []

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.message_history, f, indent=2)
        except Exception as e:
            # Just log error but don't show to user
            print(f"Could not save history: {str(e)}")

    def clear_all(self):
        # Ask for confirmation if there's text or history
        if (self.text_input.get("1.0", tk.END).strip() or self.message_history):
            confirm = MessageBox(
                title=self.get_text("app_title"),
                message=self.get_text("clear_confirm") if "clear_confirm" in self.translations[self.ui_language] 
                    else "Are you sure you want to clear all text and history?",
                icon="warning",
                option_1="Cancel",
                option_2="Yes"
            )
            
            if confirm.get() != "Yes":
                return
                
        # Clear text input
        self.text_input.delete("1.0", tk.END)
        # Clear history
        self.message_history = []
        self.current_history_index = -1
        self.update_history_display()
        # Save empty history to file
        self.save_history()
        self.status_var.set(self.get_text("cleared"))

    def on_closing(self):
        try:
            # Ask for confirmation before exiting
            confirm = MessageBox(
                title=self.get_text("app_title"),
                message=self.get_text("exit_confirm"),
                icon="question",
                option_1="Cancel",
                option_2="Yes"
            )
            
            if confirm.get() != "Yes":
                return
                
            self.save_settings()
            self.save_history()
            self.root.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            self.root.destroy()

    def change_ui_language(self, selection):
        # Update language based on selection
        self.ui_language = "en" if selection == "English" else "zh"
        
        # Save setting
        self.settings["ui_language"] = self.ui_language
        self.auto_save_settings()
        
        # Update UI (restart needed for complete change)
        message = "Interface language changed. Restart the app for full effect." if self.ui_language == "en" else "界面語言已更改。完全更新需要重啟應用。"
        MessageBox(
            title="Language Changed / 語言已更改",
            message=message,
            icon="info"
        )
        
        # Update visible text elements that can be changed without restart
        self.logo_label.configure(text=self.get_text("app_title"))
        self.subtitle.configure(text=self.get_text("app_subtitle"))
        self.history_label.configure(text=self.get_text("message_history"))
        self.text_label.configure(text=self.get_text("type_message"))
        self.speak_btn.configure(text=self.get_text("speak"))
        self.stop_btn.configure(text=self.get_text("stop"))
        self.clear_btn.configure(text=self.get_text("clear"))
        self.force_overlap_cb.configure(text=self.get_text("force_overlap"))
        self.cable_reminder.configure(text=self.get_text("discord_reminder"))
        self.status_var.set(self.get_text("ready"))

    def detect_language(self, text):
        """Detect probable language from text to suggest appropriate voice"""
        # Simple detection based on character sets
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if chinese_chars > english_chars:
            return "zh"
        else:
            return "en"
            
    def suggest_voice_for_text(self):
        """Suggest appropriate voice based on input text language"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            return
            
        detected_lang = self.detect_language(text)
        
        # Get current language selection
        current_voice_locale = next((v['locale'] for v in self.filtered_voices 
                                 if v['display'] == self.voice_cb.get()), None)
        
        # Only change if there's a mismatch
        if current_voice_locale:
            current_lang_prefix = current_voice_locale.split('-')[0]
            
            if current_lang_prefix != detected_lang:
                # Find appropriate voice for detected language
                if detected_lang == "zh":
                    # Select Chinese voice
                    chinese_voices = [v for v in self.all_voices if v['locale'].startswith(('zh-CN', 'zh-TW'))]
                    if chinese_voices:
                        # Switch UI language filter to show Chinese voices
                        self.language_filter.set(self.get_text("chinese_mainland"))
                        self.filter_voices(self.get_text("chinese_mainland"))
                        # Set a Chinese voice
                        self.voice_cb.set(chinese_voices[0]['display'])
                else:
                    # Select English voice
                    english_voices = [v for v in self.all_voices if v['locale'].startswith('en')]
                    if english_voices:
                        # Switch UI language filter to show English voices
                        self.language_filter.set(self.get_text("english_us"))
                        self.filter_voices(self.get_text("english_us"))
                        # Set an English voice
                        self.voice_cb.set(english_voices[0]['display'])

    def on_text_change(self, event=None):
        """Handle text input changes"""
        # Suggest voice after a short delay when typing stops
        if hasattr(self, '_suggest_after_id'):
            self.root.after_cancel(self._suggest_after_id)
        self._suggest_after_id = self.root.after(1000, self.suggest_voice_for_text)

    def update_history_display(self):
        self.history_list.configure(state="normal")
        self.history_list.delete("1.0", tk.END)
        
        for i, item in enumerate(reversed(self.message_history[-10:])):  # Show last 10 messages
            timestamp = item.get("timestamp", "")
            text = item.get("text", "")
            
            # Truncate long messages
            if len(text) > 50:
                text = text[:47] + "..."
                
            # Remove newlines
            text = text.replace("\n", " ")
            
            self.history_list.insert(tk.END, f"[{timestamp}] {text}\n")
            
        self.history_list.configure(state="disabled")

    def select_history_item(self, event):
        try:
            # Get clicked line
            index = self.history_list.index("@%s,%s" % (event.x, event.y))
            line = int(index.split(".")[0]) - 1
            
            # Reverse index to match history
            history_index = min(9, len(self.message_history) - 1) - line
            if 0 <= history_index < len(self.message_history):
                # Set text to input
                selected_text = self.message_history[history_index]["text"]
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", selected_text)
                
                # Update current index for up/down navigation
                self.current_history_index = history_index
        except Exception:
            pass

    def navigate_history_up(self, event):
        if not self.message_history:
            return "break"
            
        if self.current_history_index < len(self.message_history) - 1:
            self.current_history_index += 1
            
        if 0 <= self.current_history_index < len(self.message_history):
            selected_text = self.message_history[self.current_history_index]["text"]
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", selected_text)
            
        return "break"  # Prevent default behavior

    def navigate_history_down(self, event):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            selected_text = self.message_history[self.current_history_index]["text"]
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", selected_text)
        elif self.current_history_index == 0:
            self.current_history_index = -1
            self.text_input.delete("1.0", tk.END)
            
        return "break"  # Prevent default behavior

    def load_settings(self):
        default_settings = {
            "output_device": None,
            "monitor_device": None,
            "voice": None,
            "speed": 0,
            "language": "All Languages",
            "ui_language": "en",  # Default to English
            "force_overlap": False  # Default to not overlapping playback
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
            
        return default_settings

    def preview_voice(self):
        """Play a short preview of the currently selected voice"""
        # If already playing, don't start another preview
        if self.is_playing:
            return
            
        # Determine appropriate sample text based on the voice locale
        selected_display = self.voice_cb.get()
        selected_voice = next((v for v in self.filtered_voices if v['display'] == selected_display), None)
        
        if not selected_voice:
            return
            
        # Choose sample text based on language
        if selected_voice['locale'].startswith('zh'):
            sample_text = "你好，这是语音示例。"  # Chinese sample
        else:
            sample_text = "Hello, this is a voice sample."  # English sample
            
        # Show previewing status
        original_status = self.status_var.get()
        self.status_var.set(self.get_text("previewing"))
        self.preview_btn.configure(state="disabled")
        
        # Generate preview audio
        preview_thread = threading.Thread(
            target=self._generate_and_play_preview,
            args=(sample_text, selected_voice['name'], original_status),
            daemon=True
        )
        preview_thread.start()
        
    def _generate_and_play_preview(self, text, voice_name, original_status):
        """Background thread to generate and play a voice preview"""
        try:
            # Get speech rate from slider
            rate = self.update_speed_label()
            
            # Generate TTS
            future = asyncio.run_coroutine_threadsafe(_tts_edge(text, voice_name, rate), self.loop)
            wav_path = future.result()
            
            if wav_path:
                # Set playing flag
                self.is_playing = True
                
                # Play the audio
                try:
                    data, fs = sf.read(wav_path, dtype='float32')
                    chans = data.shape[1] if data.ndim > 1 else 1
                    
                    # Play only to monitor device (not to Discord)
                    midx = self.audio_devices.get(self.mon_cb.get())
                    if midx is not None:
                        with sd.OutputStream(device=midx, samplerate=fs,
                                          channels=chans, dtype='float32',
                                          blocksize=1024, latency='low') as s:
                            s.write(data)
                finally:
                    # Clean up
                    self.is_playing = False
                    try:
                        os.unlink(wav_path)
                    except:
                        pass
        except Exception as e:
            print(f"Preview error: {e}")
        finally:
            # Restore UI state
            self.root.after(0, lambda: self.status_var.set(original_status))
            self.root.after(0, lambda: self.preview_btn.configure(state="normal"))

if __name__=='__main__':
    # ─── Startup optimizations ─────────────────────────
    import threading
    import json
    import tkinter as tk
    import numpy as np

    # If bundled by PyInstaller, optimize and detect _MEIPASS
    if hasattr(sys, 'frozen'):
        import os
        os.environ['PYTHONOPTIMIZE'] = '2'
        if sys.platform == 'win32':
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass

    # ─── Locate the icon file ─────────────────────────
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    icon_path = os.path.join(base_path, 'icon.ico')

    # ─── Create the root window and set its icon ───────
    root = ctk.CTk()
    try:
        root.iconbitmap(icon_path)            # Windows .ico
    except Exception:
        img = tk.PhotoImage(file=icon_path)  # fallback (PNG would work too)
        root.iconphoto(True, img)

    # ─── Set process priority (optional) ──────────────
    if sys.platform == 'win32':
        import psutil
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except:
            pass

    # ─── Instantiate and run your app ─────────────────
    app = VirtualMicrophoneApp(root)
    root.mainloop()