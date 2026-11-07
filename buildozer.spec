[app]
title = DICOM Sonifier
package.name = dicomsonifier
package.domain = org.dicomsonifier
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.exclude_dirs = .github,scripts,bin,.buildozer
version = 2.0
requirements = python3,kivy==2.3.0,numpy,pydicom,pyjnius,android,arabic_reshaper,python-bidi==0.4.2,six
orientation = portrait
fullscreen = 0

# Android 5.0 (API 21) and newer, built against Android 14 (API 34)
android.api = 34
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a, x86_64
android.accept_sdk_license = True
android.allow_backup = True
# No permissions needed: files are opened/saved through the system file picker.
android.permissions =

[buildozer]
log_level = 2
warn_on_root = 0
