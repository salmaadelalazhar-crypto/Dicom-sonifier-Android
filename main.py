"""DICOM Sonifier - Android app for blind users. Row-by-row playback of DICOM images as sound.

Works with touch buttons and with an external (Bluetooth/USB) keyboard.
"""
import os
import threading

import numpy as np
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import android_bridge as ab
import sonify
from i18n import LANG, FONT, t, shape
from speech import Speaker

DEFAULTS = {"fmin": 30, "fmax": 14000, "vmin": -1000, "vmax": 3000, "tone_ms": 15, "step": 2, "parts": 10}

# Kivy keycodes
K_SPACE, K_LEFT, K_RIGHT, K_UP, K_DOWN = 32, 276, 275, 273, 274
K_HOME, K_END, K_PGUP, K_PGDN = 278, 279, 280, 281


def _font_kw():
    return {"font_name": FONT} if FONT else {}


class SonifierApp(App):
    title = "DICOM Sonifier"

    # ---------- UI ----------
    def build(self):
        self.vol = None
        self.slice = 0
        self.row = 0
        self.playing = False
        self.play_id = 0
        self.speaker = Speaker(LANG)
        self.player = ab.RowPlayer()
        halign = "right" if LANG == "ar" else "left"

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        self.status = Label(text=shape(t("no_file")), font_size=sp(18), halign=halign,
                            valign="middle", size_hint_y=None, **_font_kw())
        self.status.bind(width=lambda w, v: setattr(w, "text_size", (v, None)),
                         texture_size=lambda w, v: setattr(w, "height", max(dp(70), v[1] + dp(10))))
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        col.bind(minimum_height=col.setter("height"))

        for key, cmd in [("open", self.open_file), ("play", self.toggle_play),
                         ("prev", lambda: self.move(-1)), ("next", lambda: self.move(1)),
                         ("back10", lambda: self.move_part(-1)), ("fwd10", lambda: self.move_part(1)),
                         ("replay", self.play_row_once), ("where", self.announce),
                         ("prev_slice", lambda: self.change_slice(-1)),
                         ("next_slice", lambda: self.change_slice(1)), ("export", self.export)]:
            b = Button(text=shape(t(key)), size_hint_y=None, height=dp(58), font_size=sp(17), **_font_kw())
            b.bind(on_release=lambda _b, f=cmd: f())
            col.add_widget(b)

        col.add_widget(Label(text=shape(t("settings")), size_hint_y=None, height=dp(40),
                             font_size=sp(18), bold=True, **_font_kw()))
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(4), row_default_height=dp(48),
                          row_force_default=True)
        grid.bind(minimum_height=grid.setter("height"))
        self.inputs = {}
        for k, v in DEFAULTS.items():
            lab = Label(text=shape(t(k)), halign=halign, valign="middle", font_size=sp(15), **_font_kw())
            lab.bind(size=lambda w, s: setattr(w, "text_size", s))
            ti = TextInput(text=str(v), multiline=False, input_filter="float", font_size=sp(17),
                           input_type="number")
            self.inputs[k] = ti
            pair = (ti, lab) if LANG == "ar" else (lab, ti)
            for w in pair:
                grid.add_widget(w)
        col.add_widget(grid)
        ab_btn = Button(text=shape(t("apply")), size_hint_y=None, height=dp(56), font_size=sp(17), **_font_kw())
        ab_btn.bind(on_release=lambda *_: self.apply())
        col.add_widget(ab_btn)

        helpl = Label(text=shape(t("help")), size_hint_y=None, halign=halign, font_size=sp(14), **_font_kw())
        helpl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)),
                   texture_size=lambda w, v: setattr(w, "height", v[1] + dp(10)))
        col.add_widget(helpl)

        scroll.add_widget(col)
        root.add_widget(scroll)

        Window.bind(on_keyboard=self.on_key)
        ab.on_open_result = self.load
        ab.on_save_result = self._do_export
        return root

    def on_start(self):
        Clock.schedule_once(lambda *_: self.speaker.say(t("no_file")), 1.5)

    def on_pause(self):
        self.stop()
        return True

    def on_stop(self):
        self.stop()
        self.player.release()
        self.speaker.shutdown()

    def on_key(self, _win, key, _scan, codepoint, modifiers):
        if key == 27:  # Android back button -> let system handle
            return False
        if any(ti.focus for ti in self.inputs.values()):
            return False
        ctrl = "ctrl" in modifiers
        actions = {
            K_SPACE: self.toggle_play, K_LEFT: lambda: self.move(-1), K_RIGHT: lambda: self.move(1),
            K_UP: lambda: self.move_part(-1), K_DOWN: lambda: self.move_part(1),
            K_HOME: lambda: self.goto(0), K_END: lambda: self.goto(10 ** 9),
            K_PGUP: lambda: self.change_slice(-1), K_PGDN: lambda: self.change_slice(1),
        }
        if ctrl and codepoint == "o":
            self.open_file()
        elif ctrl and codepoint == "s":
            self.export()
        elif codepoint == "r" and not ctrl:
            self.play_row_once()
        elif codepoint == "w" and not ctrl:
            self.announce()
        elif key in actions:
            actions[key]()
        else:
            return False
        return True

    @mainthread
    def set_status(self, text):
        self.status.text = shape(text)

    # ---------- settings ----------
    def params(self):
        try:
            p = {k: float(ti.text) for k, ti in self.inputs.items()}
        except ValueError:
            p = {k: float(v) for k, v in DEFAULTS.items()}
        p["fmin"] = max(20.0, p["fmin"])
        p["fmax"] = max(p["fmin"] + 1, min(20000.0, p["fmax"]))
        p["tone_ms"] = max(1.0, p["tone_ms"])
        p["step"] = max(1, int(p["step"]))
        p["parts"] = max(1, int(p["parts"]))
        return p

    def apply(self):
        self.update_status()

    # ---------- file ----------
    def open_file(self):
        if not ab.pick_file():
            self.set_status(t("error") + ": file picker")

    def load(self, path, name):
        try:
            self.stop()
            self.vol = sonify.load_dicom(path)
            self.slice = self.vol.shape[0] // 2
            self.row = 0
            lo, hi = np.percentile(self.vol, [0.5, 99.5])
            self.inputs["vmin"].text = f"{lo:.0f}"
            self.inputs["vmax"].text = f"{hi:.0f}"
            msg = t("loaded", name=name, rows=self.vol.shape[1], slices=self.vol.shape[0])
            self.set_status(msg)
            self.speaker.say(msg)
        except Exception as e:
            msg = f"{t('error')}: {e}"
            self.set_status(msg)
            self.speaker.say(t("error"))

    # ---------- navigation ----------
    def update_status(self, extra=""):
        if self.vol is None:
            return
        self.set_status(f"{self.position_text()} {extra}".strip())

    def part_bounds(self):
        n = min(self.params()["parts"], self.vol.shape[1])
        return [int(round(i * self.vol.shape[1] / n)) for i in range(n)]

    def current_part(self):
        starts = self.part_bounds()
        return max(i for i, st in enumerate(starts) if st <= self.row), len(starts)

    def position_text(self):
        p, n = self.current_part()
        return (t("status", s=self.slice + 1, ns=self.vol.shape[0], r=self.row + 1, nr=self.vol.shape[1])
                + " " + t("part_status", p=p + 1, np=n))

    def announce(self):
        if self.vol is not None:
            self.speaker.say(self.position_text())

    def move_part(self, d):
        if self.vol is None:
            return
        starts = self.part_bounds()
        p, n = self.current_part()
        p = int(np.clip(p + d, 0, n - 1))
        self.goto(starts[p], speak=t("part_status", p=p + 1, np=n))

    def goto(self, r, speak=None):
        if self.vol is None:
            return
        self.row = int(np.clip(r, 0, self.vol.shape[1] - 1))
        was = self.playing
        self.stop()

        def after_speech():
            if speak:
                self.speaker.say(speak, block=True)
            if was:
                Clock.schedule_once(lambda *_: self.start())
            else:
                self.update_status()
                self.play_row_once()

        threading.Thread(target=after_speech, daemon=True).start()

    def move(self, d):
        if self.vol is not None:
            self.goto(self.row + d)

    def change_slice(self, d):
        if self.vol is None:
            return
        self.slice = int(np.clip(self.slice + d, 0, self.vol.shape[0] - 1))
        self.goto(self.row, speak=t("status", s=self.slice + 1, ns=self.vol.shape[0],
                                    r=self.row + 1, nr=self.vol.shape[1]))

    # ---------- audio ----------
    def row_audio(self, r):
        p = self.params()
        return sonify.row_to_audio(self.vol[self.slice, r], p["vmin"], p["vmax"],
                                   p["fmin"], p["fmax"], p["tone_ms"], p["step"])

    def play_row_once(self):
        if self.vol is None:
            return
        try:
            self.player.play(self.row_audio(self.row), wait=False)
        except Exception as e:
            self.set_status(t("audio_err", e=e))

    def toggle_play(self):
        if self.vol is None:
            return
        self.stop() if self.playing else self.start()

    def start(self):
        if self.vol is None:
            return
        self.playing = True
        self.play_id += 1
        threading.Thread(target=self._loop, args=(self.play_id,), daemon=True).start()

    def _loop(self, my_id):
        try:
            while self.playing and my_id == self.play_id:
                self.update_status(t("playing"))
                try:
                    self.player.play(self.row_audio(self.row), wait=True,
                                     cancelled=lambda: not self.playing or my_id != self.play_id)
                except Exception as e:
                    self.set_status(t("audio_err", e=e))
                    self.playing = False
                    return
                if not self.playing or my_id != self.play_id:
                    return
                if self.row >= self.vol.shape[1] - 1:
                    self.playing = False
                    self.update_status(t("end"))
                    self.speaker.say(t("end"))
                    return
                self.row += 1
        finally:
            ab.detach_thread()

    def stop(self):
        self.playing = False
        self.play_id += 1
        try:
            self.player.stop()
        except Exception:
            pass
        self.update_status(t("paused"))

    # ---------- export ----------
    def export(self):
        if self.vol is None:
            return
        if not ab.pick_save("dicom_slice_%d.wav" % (self.slice + 1)):
            self.set_status(t("error") + ": save")

    def _do_export(self, write_fn, name):
        def work():
            try:
                audio = np.concatenate([self.row_audio(r) for r in range(self.vol.shape[1])])
                write_fn(sonify.wav_bytes(audio, bits=24))
                self.set_status(t("saved", path=name))
                self.speaker.say(t("saved", path=name))
            except Exception as e:
                self.set_status(f"{t('error')}: {e}")
            finally:
                ab.detach_thread()

        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    SonifierApp().run()
