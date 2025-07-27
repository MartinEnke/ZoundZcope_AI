# audioread

[audioread](https://github.com/beetbox/audioread) is a cross-library (GStreamer, Core Audio, MAD, FFmpeg) audio decoding library for Python.

### Why audioread?

- **Broad Audio Support:** Decodes many audio formats reliably across platforms.
- **Fallback Decoder:** Used as a fallback for audio file reading in Librosa.
- **Cross-Platform:** Works on Windows, macOS, and Linux.

### How it's used in this project

- Supports audio decoding for analysis pipelines when SoundFile cannot handle certain formats.
- Enables flexibility in the audio input formats accepted by the system.
