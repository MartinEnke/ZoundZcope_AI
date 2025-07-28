# 10. Suggested Gaps / Limitations

## Security and Privacy

- No user accounts or authentication yet.  
- Uploaded audio and feedback data are deleted automatically after 2 days.  
- Focus is on AI integration; privacy/security is minimal currently.

## Performance & Scalability

- Supports MP3, WAV, AIFF up to 48kHz/24bit.  
- Intended for single tracks, not full mixes or albums.  
- No concurrency optimization implemented.  
- No length limit, but performance may degrade with very long audio.

## Extensibility

- Fixed roles and profiles; no UI or config for adding new ones.  
- Changes require backend code modification.  
- AI model integration currently tied to OpenAI API.

## User Interface Customization

- Follow-up question chips are pre-selected based on audio type, genre, and profile.  
- No user customization for questions or UI elements.  
- Future improvements could add config/admin options.
