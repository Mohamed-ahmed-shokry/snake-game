from snake_game.audio import _tone_pcm


def test_tone_pcm_uses_envelope_and_frequency_sweep() -> None:
    samples = _tone_pcm(
        start_frequency=320.0,
        end_frequency=960.0,
        duration_ms=120,
        volume=0.25,
        sample_rate=8000,
    )

    assert len(samples) == 960
    assert samples[0] == 0
    assert samples[-1] == 0
    assert max(abs(sample) for sample in samples) > 1000
    assert len(set(samples[100:200])) > 50
