"""
Audio for Open-Mon: a thin, failure-proof wrapper around pygame.mixer.

Sounds are synthesised (square-wave chiptune) so no audio assets are needed.
If the mixer can't start (CI, no device) every call is a silent no-op.
"""

import array
import contextlib

import pygame

RATE = 22050
VOLUME = 0.25

# name -> list of (frequency Hz, seconds); frequency 0 is a rest
SFX = {
    "move": [(880, 0.03)],
    "confirm": [(660, 0.04), (990, 0.06)],
    "hit": [(220, 0.04), (110, 0.08)],
    "faint": [(440, 0.1), (330, 0.1), (220, 0.1), (110, 0.25)],
    "levelup": [(523, 0.07), (659, 0.07), (784, 0.07), (1047, 0.07), (1319, 0.2)],
    "capture": [(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.2)],
}

_C, _D, _E, _F, _G, _A = 262, 294, 330, 349, 392, 440
MUSIC = {
    "title": [
        *[(_C, 0.3), (_E, 0.3), (_G, 0.3), (_E, 0.3), (_D, 0.3), (_F, 0.3)],
        *[(_A, 0.3), (_F, 0.3)],
    ],
    "overworld": [
        *[(_E, 0.25), (_G, 0.25), (_E, 0.25), (_C, 0.25), (0, 0.25)],
        *[(_D, 0.25), (_F, 0.25), (_D, 0.25), (_G, 0.5), (0, 0.25)],
    ],
    "battle": [
        *[(_A, 0.12), (_A, 0.12), (_E, 0.12), (_A, 0.12), (_G, 0.12)],
        *[(_G, 0.12), (_D, 0.12), (_G, 0.12)] * 2,
    ],
}

muted = False
current_music = None  # name of the requested track, even when silent
played = []  # log of requested SFX names (handy for tests)

_ready = None  # None = not tried yet
_cache = {}
_music_channel = None


def _init():
    """Start the mixer once; return whether audio is usable."""
    global _ready
    if _ready is None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            _ready = True
        except pygame.error:
            _ready = False
    return _ready


def _synth(notes):
    samples = array.array("h")
    amp = int(32767 * VOLUME)
    for freq, secs in notes:
        n = int(RATE * secs)
        period = RATE / freq if freq else 0
        for i in range(n):
            if not period:
                samples.append(0)
                continue
            level = int(amp * min(1.0, (n - i) / 200))  # fade out: no clicks
            samples.append(level if (i % period) < period / 2 else -level)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def _sound(kind, name):
    key = (kind, name)
    if key not in _cache:
        _cache[key] = _synth((SFX if kind == "sfx" else MUSIC)[name])
    return _cache[key]


def set_muted(value):
    global muted
    muted = bool(value)
    with contextlib.suppress(pygame.error):
        if _music_channel is not None:
            _music_channel.set_volume(0 if muted else 1)


def toggle_mute():
    set_muted(not muted)
    return muted


def play_sfx(name):
    played.append(name)
    if muted or name not in SFX or not _init():
        return
    with contextlib.suppress(pygame.error):
        _sound("sfx", name).play()


def play_music(name):
    """Loop the named track; asking for the track already playing is a no-op."""
    global current_music, _music_channel
    if name == current_music:
        return
    current_music = name
    if not _init():
        return
    with contextlib.suppress(pygame.error):
        if _music_channel is not None:
            _music_channel.stop()
            _music_channel = None
        if name in MUSIC:
            _music_channel = _sound("music", name).play(loops=-1)
            if _music_channel is not None:
                _music_channel.set_volume(0 if muted else 1)


def stop_music():
    global current_music
    current_music = None
    with contextlib.suppress(pygame.error):
        if _music_channel is not None:
            _music_channel.stop()
