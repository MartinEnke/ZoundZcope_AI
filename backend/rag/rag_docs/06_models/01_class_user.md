## Class: User

Represents a registered user in the system.

### Fields

- `id` (Integer, Primary Key): Unique identifier for the user.  
- `username` (String, Unique, Not Null): User’s chosen name.  
- `email` (String, Unique, Not Null): User’s email address.  
- `hashed_password` (String, Not Null): Securely stored password hash.  
- `created_at` (DateTime): Timestamp of user creation, set automatically.  

### Relationships

- `sessions`: One-to-many relationship to `Session`. A user can have multiple sessions.