## Class: ChatMessage

Represents a message in the chat history between user and AI assistant.

### Fields

- `id` (Integer, Primary Key): Unique identifier.  
- `session_id` (String, Foreign Key): Reference to the related `Session`.  
- `track_id` (String, Foreign Key): Reference to the related `Track`.  
- `sender` (String): Message sender, e.g., "user" or "assistant".  
- `message` (Text): The message content.  
- `timestamp` (DateTime): When the message was sent, set automatically.  
- `feedback_profile` (String, Nullable): Feedback detail level context (e.g., "simple", "pro").  
- `followup_group` (Integer, Nullable, Default=0): Grouping index for threaded follow-up conversations.

### Relationships

- `session`: Many-to-one relationship to `Session`.