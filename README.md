# DICOM Sonifier (Android)
Android app that turns DICOM images into sound, row by row, for blind users.
Low density = low pitch, high density = high pitch (30 Hz - 14 kHz, log scale, 48 kHz / 24-bit WAV export).
Language follows the phone: Arabic if Android is set to Arabic, otherwise English. Spoken feedback uses Android's text-to-speech.
Works on Android 5.0 and newer (including Android 11+). Use the on-screen buttons or a Bluetooth/USB keyboard.

Build: push to GitHub; the workflow builds the APK with Buildozer, runs it on an Android emulator for 30 s, and uploads the APK as an artifact.
Note: compressed (JPEG / JPEG 2000) DICOM files are not supported on Android; uncompressed DICOM works.
