"""Install the APK on the running Android emulator, launch it, and pass if it is still running after 30 s."""
import subprocess
import sys
import time

apk = sys.argv[1]
pkg = sys.argv[2] if len(sys.argv) > 2 else "org.dicomsonifier.dicomsonifier"


def adb(*args, check=True):
    return subprocess.run(["adb", *args], capture_output=True, text=True, check=check)


adb("install", "-r", apk)
adb("logcat", "-c", check=False)
adb("shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1")
for _ in range(30):
    time.sleep(1)
    if not adb("shell", "pidof", pkg, check=False).stdout.strip():
        break
log = adb("logcat", "-d", check=False).stdout
open("logcat.txt", "w", encoding="utf-8").write(log)
alive = bool(adb("shell", "pidof", pkg, check=False).stdout.strip())
crashed = "FATAL EXCEPTION" in log or ("python" in log.lower() and "Traceback" in log)
if not alive or crashed:
    print("FAIL: app closed or crashed before 30 seconds")
    print("\n".join(log.splitlines()[-200:]))
    sys.exit(1)
print("PASS: app ran for 30 seconds without closing")
adb("shell", "am", "force-stop", pkg, check=False)
