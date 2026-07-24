from __future__ import annotations

import io
import math
import wave
from array import array

import pygame


def _tone_pcm(
    start_frequency: float,
    end_frequency: float,
    duration_ms: int,
    volume: float,
    sample_rate: int = 22050,
) -> array[int]:
    frame_count = int(sample_rate * (duration_ms / 1000.0))
    data = array("h")
    amplitude = int(32767 * max(0.0, min(volume, 1.0)))
    phase = 0.0
    attack_frames = max(1, int(sample_rate * 0.008))
    release_frames = max(1, int(sample_rate * 0.018))

    for index in range(frame_count):
        progress = index / max(1, frame_count - 1)
        frequency = start_frequency + (end_frequency - start_frequency) * progress
        phase += (2.0 * math.pi * frequency) / sample_rate
        attack = min(1.0, index / attack_frames)
        release = min(1.0, (frame_count - index - 1) / release_frames)
        envelope = max(0.0, min(attack, release))
        waveform = math.sin(phase) + 0.14 * math.sin(phase * 2.0)
        data.append(int(amplitude * envelope * waveform))
    return data


def _build_tone_sound(
    frequency: float,
    duration_ms: int,
    volume: float,
    end_frequency: float | None = None,
) -> pygame.mixer.Sound:
    sample_rate = 22050
    data = _tone_pcm(
        start_frequency=frequency,
        end_frequency=end_frequency if end_frequency is not None else frequency,
        duration_ms=duration_ms,
        volume=volume,
        sample_rate=sample_rate,
    )
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
                "move": _build_tone_sound(420.0, 45, 0.13, 510.0),
                "eat": _build_tone_sound(640.0, 95, 0.23, 920.0),
                "confirm": _build_tone_sound(500.0, 100, 0.20, 680.0),
                "death": _build_tone_sound(260.0, 300, 0.28, 85.0),
                "powerup": _build_tone_sound(540.0, 180, 0.24, 1080.0),
                "stage": _build_tone_sound(460.0, 220, 0.22, 840.0),
                "shield": _build_tone_sound(320.0, 240, 0.25, 960.0),
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
