from __future__ import annotations

import io
import math
import wave
from array import array

import pygame


def _build_tone_sound(frequency: float, duration_ms: int, volume: float) -> pygame.mixer.Sound:
    sample_rate = 22050
    frame_count = int(sample_rate * (duration_ms / 1000.0))
    data = array("h")
    amplitude = int(32767 * max(0.0, min(volume, 1.0)))

    for index in range(frame_count):
        angle = (2.0 * math.pi * frequency * index) / sample_rate
        data.append(int(amplitude * math.sin(angle)))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data.tobytes())
    buffer.seek(0)
    return pygame.mixer.Sound(file=buffer)


class AudioManager:
    def __init__(self, muted: bool) -> None:
        self.muted = muted
        self.available = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.sounds = {
                "move": _build_tone_sound(440.0, 40, 0.15),
                "eat": _build_tone_sound(700.0, 80, 0.25),
                "confirm": _build_tone_sound(560.0, 90, 0.22),
                "death": _build_tone_sound(180.0, 220, 0.30),
            }
            self.available = True
        except pygame.error:
            self.available = False
            self.sounds = {}

    def set_muted(self, muted: bool) -> None:
        self.muted = muted

    def play(self, event_name: str) -> None:
        if self.muted or not self.available:
            return
        sound = self.sounds.get(event_name)
        if sound is not None:
            sound.play()

