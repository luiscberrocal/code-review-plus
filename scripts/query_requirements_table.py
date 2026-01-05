"""Script to query and display information from the vetted_requirements table."""

import sqlite3
from pathlib import Path


def display_requirements_info(db_path: Path) -> None:
    """Display information about the vetted_requirements table.

    Args:
        db_path: Path to the SQLite database file
    """
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table schema
    print("=" * 80)
    print("TABLE SCHEMA: vetted_requirements")
    print("=" * 80)
    cursor.execute("PRAGMA table_info(vetted_requirements)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  Column: {col[1]:<25} Type: {col[2]:<10} NotNull: {col[3]} PK: {col[5]}")

    # Get total count
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    cursor.execute('SELECT COUNT(*) FROM vetted_requirements')
    total_count = cursor.fetchone()[0]
    print(f"Total requirements: {total_count}")

    # Count by environment
    print("\nRequirements by environment:")
    cursor.execute('''
        SELECT environment, COUNT(*) as count 
        FROM vetted_requirements 
        GROUP BY environment 
        ORDER BY environment
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} : {row[1]:>3} requirements")

    # Count by specifier
    print("\nRequirements by specifier:")
    cursor.execute('''
        SELECT specifier, COUNT(*) as count 
        FROM vetted_requirements 
        GROUP BY specifier 
        ORDER BY count DESC
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} : {row[1]:>3} requirements")

    # Django packages
    print("\n" + "=" * 80)
    print("DJANGO PACKAGES")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier, environment
        FROM vetted_requirements 
        WHERE name LIKE 'django%'
        ORDER BY name
    ''')
    django_reqs = cursor.fetchall()
    print(f"Total Django packages: {len(django_reqs)}")
    for row in django_reqs[:10]:  # Show first 10
        print(f"  {row[0]:<40} {row[2]} {row[1]:<12} ({row[3]})")
    if len(django_reqs) > 10:
        print(f"  ... and {len(django_reqs) - 10} more")

    # BASE requirements
    print("\n" + "=" * 80)
    print("BASE REQUIREMENTS (first 15)")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier
        FROM vetted_requirements 
        WHERE environment = 'BASE'
        ORDER BY name
        LIMIT 15
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[2]} {row[1]}")

    # PRODUCTION requirements
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
    print(f"Total: {len(prod_reqs)}")
    for row in prod_reqs:
        print(f"  {row[0]:<40} {row[2]} {row[1]}")

    # DEVELOPMENT requirements
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
    print(f"Total: {len(dev_reqs)}")
    for row in dev_reqs:
        print(f"  {row[0]:<40} {row[2]} {row[1]}")

    # GIT-based requirements
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
    print(f"Total: {len(git_reqs)}")
    for row in git_reqs:
        print(f"  {row[0]:<40} v{row[1]:<10} ({row[3]})")
        if row[2]:
            print(f"    → {row[2]}")

    # Testing packages
    print("\n" + "=" * 80)
    print("TESTING PACKAGES (pytest, coverage, etc.)")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier, environment
        FROM vetted_requirements 
        WHERE name LIKE 'pytest%' OR name LIKE 'coverage%' OR name = 'hypothesis' OR name = 'factory-boy'
        ORDER BY name
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[2]} {row[1]:<12} ({row[3]})")

    # Celery related
    print("\n" + "=" * 80)
    print("CELERY RELATED PACKAGES")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier, environment
        FROM vetted_requirements 
        WHERE name LIKE '%celery%'
        ORDER BY name
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[2]} {row[1]:<12} ({row[3]})")

    # Linting/formatting packages
    print("\n" + "=" * 80)
    print("LINTING/FORMATTING PACKAGES")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier, environment
        FROM vetted_requirements 
        WHERE name LIKE 'pylint%' OR name LIKE '%lint%' OR name = 'pre-commit'
        ORDER BY name
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[2]} {row[1]:<12} ({row[3]})")

    # Database drivers
    print("\n" + "=" * 80)
    print("DATABASE DRIVERS")
    print("=" * 80)
    cursor.execute('''
        SELECT name, version, specifier, environment
        FROM vetted_requirements 
        WHERE name LIKE 'psycopg%' OR name = 'mysqlclient' OR name = 'redis'
        ORDER BY name
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[2]} {row[1]:<12} ({row[3]})")

    conn.close()
    print("\n" + "=" * 80)


def query_requirement(db_path: Path, requirement_name: str) -> None:
    """Query a specific requirement by name.

    Args:
        db_path: Path to the SQLite database file
        requirement_name: Name of the requirement to query
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM vetted_requirements WHERE name = ?
    ''', (requirement_name,))

    rows = cursor.fetchall()
    if rows:
        print(f"\n{'='*80}")
        print(f"REQUIREMENT: {requirement_name}")
        print('='*80)
        for row in rows:
            print(f"  ID: {row[0]}")
            print(f"  Name: {row[1]}")
            print(f"  Version: {row[3]} {row[2]}")
            if row[4]:
                print(f"  Source: {row[4]}")
            print(f"  Environment: {row[5]}")
            print(f"  Created: {row[6]}")
            print()
    else:
        print(f"\nRequirement '{requirement_name}' not found in database.")

    conn.close()


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "code_review.db"

    # Display database info
    display_requirements_info(db_path)

    # Query some specific requirements
    print("\n" + "=" * 80)
    print("SPECIFIC REQUIREMENT QUERIES")
    print("=" * 80)
    for req_name in ["django", "celery", "pytest", "pydantic"]:
        query_requirement(db_path, req_name)


if __name__ == "__main__":
    main()

