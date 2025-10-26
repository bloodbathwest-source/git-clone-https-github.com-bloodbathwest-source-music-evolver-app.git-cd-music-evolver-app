import streamlit as st
import numpy as np
import pretty_midi
import tempfile
import os
import matplotlib.pyplot as plt
from io import BytesIO

# --- Helper functions ---

# Map genres to chord progressions (basic example)
GENRE_PROGRESSIONS = {
    "Pop": [["I", "V", "vi", "IV"], ["I", "vi", "IV", "V"]],
    "Jazz": [["ii", "V", "I", "vi"]],
    "Rock": [["I", "IV", "V", "I"], ["I", "bVII", "IV", "I"]],
    "Classical": [["I", "IV", "V", "I"], ["I", "V", "vi", "iii", "IV", "I"]],
}

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MODES = ["Major", "Minor"]
EMOTIONS = ["Happy", "Sad", "Mysterious", "Excited"]

def chord_to_notes(chord, key, mode):
    # Map Roman numeral to scale degree
    scale_degrees_major = {'I': 0, 'ii': 2, 'iii': 4, 'IV': 5, 'V': 7, 'vi': 9, 'bVII': 10}
    scale_degrees_minor = {'i': 0, 'ii': 2, 'III': 3, 'iv': 5, 'v': 7, 'VI': 8, 'bVII': 10}
    if mode == "Major":
        scale = scale_degrees_major
        intervals = [0, 4, 7]
        root_pitch = pretty_midi.note_name_to_number(key + "4")
    else:
        scale = scale_degrees_minor
        intervals = [0, 3, 7]
        root_pitch = pretty_midi.note_name_to_number(key + "4")
    deg = chord if chord in scale else 'I'
    root = (root_pitch + scale.get(deg, 0)) % 128
    notes = [root + interval for interval in intervals]
    return notes

def emotion_tempo(emotion):
    return {
        "Happy": 120,
        "Sad": 70,
        "Mysterious": 90,
        "Excited": 140
    }.get(emotion, 100)

def evolve_melody(prev, scale_notes, length=8):
    # Evolve melody by random walk with scale constraints.
    melody = []
    prev_note = prev[-1] if prev else np.random.choice(scale_notes)
    for _ in range(length):
        step = np.random.choice([-2, -1, 0, 1, 2])
        idx = scale_notes.index(prev_note) if prev_note in scale_notes else 0
        next_idx = min(max(idx + step, 0), len(scale_notes)-1)
        next_note = scale_notes[next_idx]
        melody.append(next_note)
        prev_note = next_note
    return melody

def make_scale(key, mode):
    # Basic major/minor scale
    major_intervals = [0, 2, 4, 5, 7, 9, 11]
    minor_intervals = [0, 2, 3, 5, 7, 8, 10]
    base = pretty_midi.note_name_to_number(key + "4")
    intervals = major_intervals if mode == "Major" else minor_intervals
    return [(base + i) % 128 for i in intervals]

def generate_music(genre, key, mode, emotion, generations):
    tempo = emotion_tempo(emotion)
    scale_notes = make_scale(key, mode)
    chord_prog = GENRE_PROGRESSIONS.get(genre, [["I", "IV", "V", "I"]])[0]
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    inst = pretty_midi.Instrument(program=0)
    time = 0.0
    melody = [np.random.choice(scale_notes)]
    notes_plot = []
    for gen in range(generations):
        for chord in chord_prog:
            chord_notes = chord_to_notes(chord, key, mode)
            # Add chord
            for n in chord_notes:
                note = pretty_midi.Note(velocity=70, pitch=int(n), start=time, end=time+0.9)
                inst.notes.append(note)
            # Evolve melody
            melody = evolve_melody(melody, scale_notes, length=4)
            for idx, n in enumerate(melody):
                note = pretty_midi.Note(velocity=100, pitch=int(n), start=time+idx*0.25, end=time+idx*0.25+0.2)
                inst.notes.append(note)
                notes_plot.append((time+idx*0.25, n))
            time += 1
    midi.instruments.append(inst)
    return midi, notes_plot, tempo

def plot_notes(notes_plot):
    times = [t[0] for t in notes_plot]
    pitches = [t[1] for t in notes_plot]
    plt.figure(figsize=(8, 3))
    plt.scatter(times, pitches, c='blue')
    plt.xlabel("Time (s)")
    plt.ylabel("MIDI Pitch")
    plt.title("Melody Notes Over Time")
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def midi_to_bytes(midi):
    midibytes = BytesIO()
    midi.write(midibytes)
    return midibytes.getvalue()

# --- Streamlit UI ---

st.title("🎶 Music-Evolving AI Web App")

st.markdown("Generate evolving music by selecting your favorite genre, key, mode, and emotion! Download MIDI or visualize the melody.")

col1, col2 = st.columns(2)
with col1:
    genre = st.selectbox("Genre", list(GENRE_PROGRESSIONS.keys()))
    key = st.selectbox("Key", KEYS)
    mode = st.selectbox("Mode", MODES)
with col2:
    emotion = st.selectbox("Emotion", EMOTIONS)
    generations = st.slider("Number of Generations", 1, 12, 4)

if st.button("Generate Music"):
    with st.spinner("Composing..."):
        midi, notes_plot, tempo = generate_music(genre, key, mode, emotion, generations)
        st.success(f"Music generated at {tempo} bpm!")
        # MIDI download
        midibytes = midi_to_bytes(midi)
        st.download_button(
            label="Download MIDI",
            data=midibytes,
            file_name="generated_music.mid",
            mime="audio/midi"
        )
        # Melody plot
        buf = plot_notes(notes_plot)
        st.image(buf, caption="Melody Visualization", use_column_width=True)
        # Optionally, you can use audio playback with a synth package or MIDI-to-audio conversion if desired.
        st.info("Tip: Open the MIDI in your favorite DAW, MuseScore, or online player to listen!")

st.markdown("---")
st.caption("Built with ❤️ and Streamlit. Powered by pretty_midi, numpy, matplotlib.")
