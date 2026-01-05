"""Script to create and populate vetted_requirements table in the database."""

import sqlite3
from pathlib import Path

# Import the DEFAULT_CONFIG from config.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_review.config import DEFAULT_CONFIG


def create_vetted_requirements_table(db_path: Path) -> None:
    """Create the vetted_requirements table and populate it with data.

    Args:
        db_path: Path to the SQLite database file
    """
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vetted_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            specifier TEXT NOT NULL,
            source TEXT,
            environment TEXT NOT NULL DEFAULT 'BASE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, environment)
        )
    ''')

    print("✓ Table 'vetted_requirements' created successfully")

    # Get services data from DEFAULT_CONFIG
    vetted_reqs = DEFAULT_CONFIG.get("vetted_requirements", {})
    if isinstance(vetted_reqs, dict):
        services = vetted_reqs.get("services", [])
    else:
        services = []

    if not services:
        print("⚠ No services found in DEFAULT_CONFIG")
        conn.close()
        return

    # Insert data
    inserted_count = 0
    skipped_count = 0
    updated_count = 0

    for service in services:
        name = service.get("name")
        version = service.get("version")
        specifier = service.get("specifier")
        source = service.get("source")
        environment = service.get("environment", "BASE")  # Default to BASE if not specified

        if not name or not version or not specifier:
            print(f"⚠ Skipping incomplete service entry: {service}")
            skipped_count += 1
            continue

        try:
            cursor.execute('''
                INSERT INTO vetted_requirements (name, version, specifier, source, environment)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, version, specifier, source, environment))
            inserted_count += 1
            print(f"  ✓ Inserted: {name} {specifier} {version} (Environment: {environment})")
        except sqlite3.IntegrityError:
            # Entry already exists, try to update it
            try:
                cursor.execute('''
                    UPDATE vetted_requirements 
                    SET version = ?, specifier = ?, source = ?
                    WHERE name = ? AND environment = ?
                ''', (version, specifier, source, name, environment))
                updated_count += 1
                print(f"  ↻ Updated: {name} {specifier} {version} (Environment: {environment})")
            except Exception as e:
                print(f"  ✗ Error updating {name}: {e}")
                skipped_count += 1

    # Commit changes
    conn.commit()

    # Display summary
    cursor.execute('SELECT COUNT(*) FROM vetted_requirements')
    total_count = cursor.fetchone()[0]

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total requirements in database: {total_count}")
    print(f"Newly inserted: {inserted_count}")
    print(f"Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")

    # Display statistics by environment
    print("\n" + "=" * 80)
    print("REQUIREMENTS BY ENVIRONMENT")
    print("=" * 80)
    cursor.execute('''
        SELECT environment, COUNT(*) 
        FROM vetted_requirements 
        GROUP BY environment 
        ORDER BY environment
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} : {row[1]:>3} requirements")

    # Display some sample data
    print("\n" + "=" * 80)
    print("SAMPLE DATA (first 10 requirements)")
    print("=" * 80)
    cursor.execute('''
        SELECT id, name, version, specifier, environment 
        FROM vetted_requirements 
        ORDER BY name
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"  [{row[0]:>3}] {row[1]:<40} {row[3]} {row[2]:<12} ({row[4]})")

    # Display production requirements
    print("\n" + "=" * 80)
    print("PRODUCTION REQUIREMENTS")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier 
        FROM vetted_requirements 
        WHERE environment = 'PRODUCTION'
        ORDER BY name
    ''')
    prod_reqs = cursor.fetchall()
    if prod_reqs:
        for row in prod_reqs:
            print(f"  {row[0]:<40} {row[2]} {row[1]}")
    else:
        print("  No production-specific requirements found")

    # Display development requirements
    print("\n" + "=" * 80)
    print("DEVELOPMENT REQUIREMENTS")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier 
        FROM vetted_requirements 
        WHERE environment = 'DEVELOPMENT'
        ORDER BY name
    ''')
    dev_reqs = cursor.fetchall()
    if dev_reqs:
        for row in dev_reqs:
            print(f"  {row[0]:<40} {row[2]} {row[1]}")
    else:
        print("  No development-specific requirements found")

    # Display git-based requirements
    print("\n" + "=" * 80)
    print("GIT-BASED REQUIREMENTS (@ specifier)")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, source, environment
        FROM vetted_requirements 
        WHERE specifier = '@'
        ORDER BY name
    ''')
    git_reqs = cursor.fetchall()
    if git_reqs:
        for row in git_reqs:
            print(f"  {row[0]:<40} v{row[1]:<10} ({row[3]})")
            if row[2]:
                print(f"    Source: {row[2]}")
    else:
        print("  No git-based requirements found")

    # Close connection
    conn.close()
    print("\n" + "=" * 80)


def main():
    """Main execution function."""
    # Define paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "code_review.db"

    # Verify database exists
    if not db_path.exists():
        print(f"⚠ Database not found at {db_path}")
        print("Creating new database...")

    # Create table and populate
    create_vetted_requirements_table(db_path)

    print(f"\n✓ Database setup complete!")
    print(f"Database location: {db_path}")


if __name__ == "__main__":
    main()

