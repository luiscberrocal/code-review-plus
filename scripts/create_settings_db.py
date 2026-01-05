"""Script to create SQLite database for vetted settings variables."""

import json
import sqlite3
from pathlib import Path


def create_database(db_path: Path, json_path: Path) -> None:
    """Create database and populate with vetted variables.

    Args:
        db_path: Path to the SQLite database file
        json_path: Path to the vetted_variables.json file
    """
    # Load JSON data
    with open(json_path, 'r') as f:
        vetted_variables = json.load(f)

    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vetted_settings_variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            vetted BOOLEAN NOT NULL DEFAULT 1,
            modules TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert data
    inserted_count = 0
    skipped_count = 0

    for var in vetted_variables:
        # Convert modules list to comma-separated string
        modules_str = ','.join(var['modules'])

        try:
            cursor.execute('''
                INSERT INTO vetted_settings_variables (name, type, vetted, modules)
                VALUES (?, ?, ?, ?)
            ''', (var['name'], var['type'], var['vetted'], modules_str))
            inserted_count += 1
        except sqlite3.IntegrityError:
            # Variable already exists
            skipped_count += 1
            print(f"Skipped duplicate: {var['name']}")

    # Commit changes
    conn.commit()

    # Display summary
    cursor.execute('SELECT COUNT(*) FROM vetted_settings_variables')
    total_count = cursor.fetchone()[0]

    print(f"\nDatabase created successfully at: {db_path}")
    print(f"Total variables in database: {total_count}")
    print(f"Newly inserted: {inserted_count}")
    print(f"Skipped (duplicates): {skipped_count}")

    # Display sample data
    print("\nSample data (first 5 rows):")
    cursor.execute('SELECT * FROM vetted_settings_variables LIMIT 5')
    rows = cursor.fetchall()
    for row in rows:
        print(f"  ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Modules: {row[4]}")

    # Close connection
    conn.close()


def main():
    """Main execution function."""
    # Define paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "code_review.db"
    json_path = project_root / "code_review" / "plugins" / "django" / "vetted_variables.json"

    # Verify JSON file exists
    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}")
        return

    # Create database
    create_database(db_path, json_path)

    print(f"\n✓ Database setup complete!")


if __name__ == "__main__":
    main()

