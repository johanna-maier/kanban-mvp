# Database Schema

SQLite database created at runtime (`data/kanban.db`). Created automatically on first backend startup if it does not exist.

## Tables

### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL, UNIQUE |
| password_hash | TEXT | NOT NULL |

### boards

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, REFERENCES users(id) |
| title | TEXT | NOT NULL, DEFAULT 'My Board' |

### columns

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| board_id | INTEGER | NOT NULL, REFERENCES boards(id) |
| title | TEXT | NOT NULL |
| position | INTEGER | NOT NULL |

### cards

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| column_id | INTEGER | NOT NULL, REFERENCES columns(id) |
| title | TEXT | NOT NULL |
| details | TEXT | NOT NULL, DEFAULT '' |
| position | INTEGER | NOT NULL |

## Design decisions

- Integer auto-increment IDs. The backend owns identity; frontend receives IDs from the API.
- `position` integer on columns and cards controls ordering. Reindexed on move.
- `password_hash` stores a hashed password, never plaintext.
- Foreign keys enforce data integrity.
- No migrations framework for MVP. Tables created on first run.
- One board per user for MVP. Schema supports multiple boards per user for future expansion.
