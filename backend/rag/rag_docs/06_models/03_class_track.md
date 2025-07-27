## Class: Track

Represents an uploaded audio track within a session.

### Fields

- `id` (String, Primary Key): Unique identifier (UUID).  
- `session_id` (String, Foreign Key): Reference to the parent `Session`.  
- `track_name` (String): Name of the track.  
- `file_path` (String): Path to the stored audio file.  
- `type` (String): Track type (e.g., "mixdown", "mastering", "reference").  
- `uploaded_at` (DateTime): Timestamp when the track was uploaded, set automatically.  
- `upload_group_id` (String, Not Null): UUID to group related uploads (e.g., original + reference track).

### Relationships

- `session`: Many-to-one relationship to `Session`.  
- `analysis`: One-to-one relationship to `AnalysisResult` containing audio features.