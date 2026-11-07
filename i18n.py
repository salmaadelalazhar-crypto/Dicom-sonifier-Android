"""Language: Arabic if the Android system language is Arabic, otherwise English."""
import os
STRINGS = {
    "en": {
        "title": "DICOM Sonifier",
        "open": "Open DICOM file",
        "play": "Play / Pause (Space)",
        "prev": "Previous row (Left)",
        "next": "Next row (Right)",
        "back10": "Previous part (Up)",
        "fwd10": "Next part (Down)",
        "parts": "Number of parts per slice",
        "replay": "Repeat current row (R)",
        "where": "Where am I? (W)",
        "part_status": "Part {p} of {np}.",
        "prev_slice": "Previous slice (Page Up)",
        "next_slice": "Next slice (Page Down)",
        "export": "Export WAV (Ctrl+S)",
        "settings": "Settings",
        "fmin": "Lowest frequency (Hz)",
        "fmax": "Highest frequency (Hz)",
        "vmin": "Lowest density",
        "vmax": "Highest density",
        "tone_ms": "Tone duration per pixel (ms)",
        "step": "Pixel step",
        "apply": "Apply",
        "no_file": "No file loaded. Tap Open DICOM file.",
        "loaded": "Loaded: {name}. {rows} rows, {slices} slices.",
        "status": "Slice {s} of {ns}. Row {r} of {nr}.",
        "playing": "Playing",
        "paused": "Paused",
        "end": "End of slice reached.",
        "saved": "Saved: {path}",
        "error": "Error",
        "audio_err": "Audio playback failed: {e}",
        "help": "Tap the buttons, or with a Bluetooth/USB keyboard: Ctrl+O open, Space play/pause, Left/Right previous/next row, Up/Down previous/next part, R repeat row, W where am I, Home/End first/last row, Page Up/Down change slice, Ctrl+S export WAV.",
    },
    "ar": {
        "title": "محوّل الأشعة إلى صوت",
        "open": "فتح ملف أشعة",
        "play": "تشغيل / إيقاف (مسافة)",
        "prev": "الصف السابق (يسار)",
        "next": "الصف التالي (يمين)",
        "back10": "الجزء السابق (أعلى)",
        "fwd10": "الجزء التالي (أسفل)",
        "parts": "عدد أجزاء الشريحة",
        "replay": "إعادة الصف الحالي (R)",
        "where": "أين أنا؟ (W)",
        "part_status": "الجزء {p} من {np}.",
        "prev_slice": "الشريحة السابقة (Page Up)",
        "next_slice": "الشريحة التالية (Page Down)",
        "export": "تصدير WAV (Ctrl+S)",
        "settings": "الإعدادات",
        "fmin": "أدنى تردد (هرتز)",
        "fmax": "أعلى تردد (هرتز)",
        "vmin": "أدنى كثافة",
        "vmax": "أعلى كثافة",
        "tone_ms": "مدة نغمة كل نقطة (مللي ثانية)",
        "step": "خطوة النقاط",
        "apply": "تطبيق",
        "no_file": "لا يوجد ملف. اضغط زر فتح ملف أشعة.",
        "loaded": "تم التحميل: {name}. {rows} صف، {slices} شريحة.",
        "status": "الشريحة {s} من {ns}. الصف {r} من {nr}.",
        "playing": "جارٍ التشغيل",
        "paused": "متوقف",
        "end": "انتهت الشريحة.",
        "saved": "تم الحفظ: {path}",
        "error": "خطأ",
        "audio_err": "تعذّر تشغيل الصوت: {e}",
        "help": "استخدم الأزرار، أو مع لوحة مفاتيح بلوتوث/USB: Ctrl+O فتح، المسافة تشغيل/إيقاف، يمين/يسار الصف التالي/السابق، أعلى/أسفل الجزء السابق/التالي، R إعادة الصف، W أين أنا، Home/End أول/آخر صف، Page Up/Down تغيير الشريحة، Ctrl+S تصدير.",
    },
}


def detect_language() -> str:
    try:
        from jnius import autoclass
        lang = autoclass("java.util.Locale").getDefault().getLanguage()
        return "ar" if str(lang).lower().startswith("ar") else "en"
    except Exception:
        return "ar" if os.environ.get("LANG", "").lower().startswith("ar") else "en"


LANG = detect_language()

# Arabic needs a font with Arabic glyphs; Android ships one under /system/fonts.
FONT = None
if LANG == "ar":
    for f in ("/system/fonts/NotoNaskhArabic-Regular.ttf", "/system/fonts/NotoNaskhArabicUI-Regular.ttf",
              "/system/fonts/NotoSansArabic-Regular.ttf", "/system/fonts/DroidNaskh-Regular.ttf",
              "/system/fonts/DroidSansArabic.ttf"):
        if os.path.isfile(f):
            FONT = f
            break


def shape(text: str) -> str:
    """Kivy draws text left-to-right without joining letters; reshape Arabic for correct display."""
    if LANG != "ar":
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def t(key: str, **kw) -> str:
    return STRINGS[LANG][key].format(**kw)
