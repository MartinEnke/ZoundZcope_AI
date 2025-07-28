# 7. Backend & Prompt Engineering

## Prompt Templates

- `REFERENCE_TRACK_INSTRUCTION`: Controls how feedback incorporates reference track data.  
- Role contexts: `mixdown`, `mastering`, `master` — adjust AI focus accordingly.  
- Profile guidance: `simple`, `detailed`, `pro` — adjusts language complexity.

## Data Flow

- Audio analysis results and metadata sent to OpenAI API for feedback generation.  
- Reference track data included if available for comparison.

## Chat Context & Summarization

- Chat history maintained and updated.  
- Summarization triggers keep token usage efficient.
