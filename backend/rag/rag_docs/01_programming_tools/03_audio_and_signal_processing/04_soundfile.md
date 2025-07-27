# SoundFile

[SoundFile](https://pysoundfile.readthedocs.io/en/latest/) is a library to read and write sound files in various formats using libsndfile.

### Why SoundFile?

- **File Format Support:** Handles reading and writing of many audio formats like WAV, FLAC, AIFF.
- **Accurate Audio Data Access:** Provides precise sample data needed for analysis.
- **Dependency for Librosa:** Librosa depends on SoundFile for audio I/O.

### How it's used in this project

- Reads user-uploaded audio files for processing and analysis.
- Provides audio data buffers consumed by Librosa and other analysis functions.
