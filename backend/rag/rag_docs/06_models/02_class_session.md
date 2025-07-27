## Class: Session

Represents a user session grouping multiple tracks and chat messages.

### Fields

- `id` (String, Primary Key): Unique session identifier (e.g., UUID or normalized string).  
- `user_id` (Integer, Foreign Key): Reference to the owning `User`.  
- `session_name` (String): Human-readable session name.  
- `created_at` (DateTime): Timestamp of session creation, set automatically.  

### Relationships

- `user`: Many-to-one relationship to `User`.  
- `tracks`: One-to-many relationship to `Track`.  
- `chats`: One-to-many relationship to `ChatMessage`.