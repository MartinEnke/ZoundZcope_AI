## SQLAlchemy

[SQLAlchemy](https://www.sqlalchemy.org/) is the Python SQL toolkit and Object Relational Mapper (ORM) that gives application developers full power and flexibility of SQL.

### Why SQLAlchemy?

- **Robust ORM:** Simplifies interaction with the database by mapping Python classes to tables.
- **Session Management:** Manages database transactions and connections efficiently.
- **Cross-DB Compatibility:** Supports SQLite, PostgreSQL, MySQL, and more.
- **Complex Queries:** Enables expressive query building and relationship management between models.

### How it’s used in this project

SQLAlchemy manages:

- Data models for sessions, tracks, analyses, and chat messages.
- Persistent storage and retrieval of analysis and AI feedback data.
- Relationship handling between sessions and multiple tracks or chat messages.

---
