"""Spoken announcements with Android's built-in TextToSpeech. Silently disabled if unavailable."""
import threading
import time


class Speaker:
    def __init__(self, lang):
        self.lang = lang
        self.tts = None
        self.lock = threading.Lock()
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            self.Locale = autoclass("java.util.Locale")
            self.QUEUE_FLUSH = TextToSpeech.QUEUE_FLUSH
            self.tts = TextToSpeech(PythonActivity.mActivity, None)
        except Exception:
            self.tts = None

    def _speak(self, text, block):
        if self.tts is None:
            return
        with self.lock:
            try:
                self.tts.setLanguage(self.Locale("ar" if self.lang == "ar" else "en"))
                self.tts.setSpeechRate(1.2)
                self.tts.speak(text, self.QUEUE_FLUSH, None, "dicom")
                if block:
                    time.sleep(0.3)
                    end = time.time() + 15
                    while self.tts.isSpeaking() and time.time() < end:
                        time.sleep(0.05)
            except Exception:
                pass

    def say(self, text, block=False):
        if block:
            self._speak(text, True)
        else:
            threading.Thread(target=self._speak, args=(text, False), daemon=True).start()

    def shutdown(self):
        try:
            if self.tts is not None:
                self.tts.shutdown()
        except Exception:
            pass
