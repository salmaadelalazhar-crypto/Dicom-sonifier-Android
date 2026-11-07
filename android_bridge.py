"""Android-only helpers (pyjnius): file open/save through the system picker and audio playback.

Uses the Storage Access Framework, so no storage permission is needed on any Android version.
"""
import os
import time

from kivy.clock import Clock
from jnius import autoclass, cast
from android import activity

import sonify

PythonActivity = autoclass("org.kivy.android.PythonActivity")
Intent = autoclass("android.content.Intent")
MediaPlayer = autoclass("android.media.MediaPlayer")

REQ_OPEN, REQ_SAVE = 4201, 4202
RESULT_OK = -1

on_open_result = None   # callback(path, display_name)
on_save_result = None   # callback(write_fn(bytes), display_name)


def _act():
    return PythonActivity.mActivity


def cache_dir():
    return _act().getCacheDir().getAbsolutePath()


def detach_thread():
    try:
        from jnius import detach
        detach()
    except Exception:
        pass


def _name(uri):
    try:
        seg = uri.getLastPathSegment() or "file"
        return seg.split("/")[-1].split(":")[-1]
    except Exception:
        return "file"


def _on_result(request, result, intent):
    if result != RESULT_OK or intent is None:
        return
    uri = intent.getData()
    if uri is None:
        return
    resolver = _act().getContentResolver()
    if request == REQ_OPEN:
        pfd = resolver.openFileDescriptor(uri, "r")
        dst = os.path.join(cache_dir(), "opened.dcm")
        with os.fdopen(pfd.detachFd(), "rb") as src, open(dst, "wb") as out:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        name = _name(uri)
        if on_open_result:
            Clock.schedule_once(lambda *_: on_open_result(dst, name))
    elif request == REQ_SAVE:
        name = _name(uri)

        def write(data):
            pfd = _act().getContentResolver().openFileDescriptor(uri, "wt")
            with os.fdopen(pfd.detachFd(), "wb") as f:
                f.write(data)

        if on_save_result:
            Clock.schedule_once(lambda *_: on_save_result(write, name))


activity.bind(on_activity_result=_on_result)


def pick_file():
    try:
        it = Intent(Intent.ACTION_OPEN_DOCUMENT)
        it.addCategory(Intent.CATEGORY_OPENABLE)
        it.setType("*/*")
        _act().startActivityForResult(it, REQ_OPEN)
        return True
    except Exception:
        return False


def pick_save(filename):
    try:
        it = Intent(Intent.ACTION_CREATE_DOCUMENT)
        it.addCategory(Intent.CATEGORY_OPENABLE)
        it.setType("audio/wav")
        it.putExtra(Intent.EXTRA_TITLE, filename)
        _act().startActivityForResult(it, REQ_SAVE)
        return True
    except Exception:
        return False


class RowPlayer:
    """Plays one row of audio at a time with Android MediaPlayer."""

    def __init__(self):
        self.mp = None
        self.flip = 0

    def _file(self, audio):
        self.flip ^= 1
        path = os.path.join(cache_dir(), "row%d.wav" % self.flip)
        with open(path, "wb") as f:
            f.write(sonify.wav_bytes(audio, bits=16))
        return path

    def stop(self):
        mp, self.mp = self.mp, None
        if mp is not None:
            try:
                mp.stop()
            except Exception:
                pass
            try:
                mp.release()
            except Exception:
                pass

    release = stop

    def play(self, audio, wait=False, cancelled=lambda: False):
        self.stop()
        path = self._file(audio)
        mp = MediaPlayer()
        mp.setDataSource(path)
        mp.prepare()
        mp.start()
        self.mp = mp
        if not wait:
            return
        end = time.time() + len(audio) / float(sonify.SAMPLE_RATE) + 0.3
        while time.time() < end and not cancelled():
            time.sleep(0.02)
        if self.mp is mp:
            self.stop()
