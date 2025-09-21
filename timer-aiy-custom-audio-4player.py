#!/usr/bin/env python3
# Pi 3 + Google AIY Voice Kit v1 (Voice HAT)
# Four-player turn timer using the HAT's button, button LED, and speaker.
# Requires the AIY Python libs (aiy.board, aiy.voice.audio).

import io, math, struct, wave, time, os, tempfile
from aiy.board import Board, Led
from aiy.voice import audio as aiy_audio  # play_wav(path)

# ---- CONFIG ----
TURN_SECONDS = 10
WARN_YELLOW = 4
WARN_RED = 2
PLAYER_COUNT = 4  # number of players in rotation

# Base path to audio/ directory relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(SCRIPT_DIR, "audio")

# Audio file paths
WELCOME_WAV   = os.path.join(AUDIO_DIR, "welcome.wav")
START_P1_WAV  = os.path.join(AUDIO_DIR, "start_p1.wav")
START_P2_WAV  = os.path.join(AUDIO_DIR, "start_p2.wav")
START_P3_WAV  = os.path.join(AUDIO_DIR, "start_p3.wav")
START_P4_WAV  = os.path.join(AUDIO_DIR, "start_p4.wav")
TIMEOUT_WAV   = os.path.join(AUDIO_DIR, "timeout.wav")

# Optional per-player fallback beep patterns if custom WAVs are missing
START_BEEP_PATTERNS = {
    1: [1200, 1200],
    2: [1000, 1000, 1000],
    3: [900, 1100, 900],
    4: [700, 700, 1000, 700],
}
TIMEOUT_BEEP_PATTERN = [1200, 1000, 800, 600, 400]

# ---- Tone/WAV helpers ----
def make_tone_wav_bytes(freq_hz=1000, ms=120, volume=0.5, sample_rate=44100):
    """Return stereo 16-bit PCM WAV bytes for a sine tone."""
    n = int(sample_rate * ms / 1000.0)
    frames = bytearray()
    amp = int(32767 * max(0.0, min(1.0, volume)))
    for i in range(n):
        s = int(amp * math.sin(2 * math.pi * freq_hz * i / sample_rate))
        frames += struct.pack('<h', s) * 2  # stereo L+R
    b = io.BytesIO()
    with wave.open(b, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)
    return b.getvalue()

def play_wav_bytes(wav_bytes):
    """Write bytes to a temp WAV and play with aiy.voice.audio.play_wav(path)."""
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    try:
        tmp.write(wav_bytes)
        tmp.flush()
        tmp.close()
        aiy_audio.play_wav(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

def beep(freq=1000, ms=100, vol=0.5):
    play_wav_bytes(make_tone_wav_bytes(freq, ms, vol))

# ---- Custom sound helpers ----
def play_custom_or_beep(path, fallback_freqs, beep_ms=120, pause_s=0.04, vol=0.7):
    """Try to play a custom wav; if missing, play a sequence of beeps."""
    if os.path.exists(path):
        aiy_audio.play_wav(path)
    else:
        for f in fallback_freqs:
            play_wav_bytes(make_tone_wav_bytes(f, beep_ms, vol))
            time.sleep(pause_s)

# ---- LED helpers ----
def led_pattern_for_remaining(r):
    """
    Map remaining seconds to an LED pattern that most AIY builds support.
    Uses BEACON when safe, BLINK when critical. Falls back to ON if unknown.
    """
    try:
        if r > WARN_YELLOW:
            return Led.BEACON
        elif r <= WARN_RED:
            return Led.BLINK
        else:
            return Led.BEACON_DARK
    except AttributeError:
        return Led.ON if r > WARN_RED else Led.BLINK

# ---- Player rotation ----
def next_in_sequence(p):
    return (p % PLAYER_COUNT) + 1

# ---- State machine ----
state = "IDLE"   # IDLE, P1_RUNNING, P2_RUNNING, P3_RUNNING, P4_RUNNING, TIMEOUT
active_player = 1
deadline = 0.0

def state_for_player(player):
    return {1: "P1_RUNNING", 2: "P2_RUNNING", 3: "P3_RUNNING", 4: "P4_RUNNING"}[player]

def start_sound(player):
    path = {
        1: START_P1_WAV,
        2: START_P2_WAV,
        3: START_P3_WAV,
        4: START_P4_WAV,
    }[player]
    play_custom_or_beep(path, START_BEEP_PATTERNS.get(player, [1000, 1000]))

def timeout_alarm():
    play_custom_or_beep(TIMEOUT_WAV, TIMEOUT_BEEP_PATTERN)

def start_turn(player):
    global state, active_player, deadline
    active_player = player
    deadline = time.monotonic() + TURN_SECONDS
    state = state_for_player(player)
    start_sound(player)

def next_player():
    start_turn(next_in_sequence(active_player))

def remaining():
    return max(0, int(round(deadline - time.monotonic())))

# ---- Startup audio ----
try:
    if os.path.exists(WELCOME_WAV):
        aiy_audio.play_wav(WELCOME_WAV)
    else:
        print("Welcome WAV not found - playing test clip instead.")
        aiy_audio.play_wav('/usr/share/sounds/alsa/Front_Center.wav')
except Exception as e:
    print('Startup audio failed:', e)

# ---- Main ----
print("AIY Timer: press the big button to start Player 1. Ctrl+C to exit.")
with Board() as board:
    board.led.state = Led.OFF
    try:
        while True:
            pressed = board.button.wait_for_press(timeout=0.05)
            if pressed:
                if state in ("IDLE", "TIMEOUT"):
                    # From IDLE, start Player 1. From TIMEOUT, advance to next in sequence.
                    player_to_start = 1 if state == "IDLE" else next_in_sequence(active_player)
                    start_turn(player_to_start)
                else:
                    next_player()

            if state in ("P1_RUNNING", "P2_RUNNING", "P3_RUNNING", "P4_RUNNING"):
                r = remaining()
                board.led.state = led_pattern_for_remaining(r)
                if r <= 0:
                    state = "TIMEOUT"
                    try:
                        board.led.state = Led.BLINK_3
                    except AttributeError:
                        board.led.state = Led.BLINK
                    timeout_alarm()
            else:
                if state == "IDLE":
                    board.led.state = Led.OFF
                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        board.led.state = Led.OFF
