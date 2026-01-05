"""Database interface for vetted requirements."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VettedRequirementDB(BaseModel):
    """Schema for a vetted requirement from the database."""

    id: int = Field(description="Database ID")
    name: str = Field(description="Package name")
    version: str = Field(description="Package version")
    specifier: str = Field(description="Version specifier (==, >=, @, etc.)")
    source: Optional[str] = Field(default=None, description="Source URL for git-based packages")
    environment: str = Field(default="BASE", description="Environment (BASE, DEVELOPMENT, PRODUCTION)")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")

    @classmethod
    def from_db_row(cls, row: tuple) -> "VettedRequirementDB":
        """Create instance from database row.

        Args:
            row: Tuple from database query

        Returns:
            VettedRequirementDB instance
        """
        return cls(
            id=row[0],
            name=row[1],
            version=row[2],
            specifier=row[3],
            source=row[4],
            environment=row[5],
            created_at=row[6] if len(row) > 6 else None,
        )

    def to_requirement_string(self) -> str:
        """Convert to pip requirement string format.

        Returns:
            Formatted requirement string
        """
        if self.specifier == "@" and self.source:
            return self.source
        else:
            return f"{self.name}{self.specifier}{self.version}"


class VettedRequirementsDatabase:
    """Interface for querying vetted requirements database."""

    def __init__(self, db_path: Path):
        """Initialize database interface.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def get_all_requirements(self) -> list[VettedRequirementDB]:
        """Get all vetted requirements from database.

        Returns:
            List of VettedRequirementDB objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vetted_requirements ORDER BY name')
        rows = cursor.fetchall()
        conn.close()

        return [VettedRequirementDB.from_db_row(row) for row in rows]

    def get_requirement_by_name(self, name: str, environment: Optional[str] = None) -> Optional[VettedRequirementDB]:
        """Get a specific requirement by name.

        Args:
            name: Package name
            environment: Optional environment filter

        Returns:
            VettedRequirementDB object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if environment:
            cursor.execute(
                'SELECT * FROM vetted_requirements WHERE name = ? AND environment = ?',
                (name, environment)
            )
        else:
            cursor.execute('SELECT * FROM vetted_requirements WHERE name = ? LIMIT 1', (name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return VettedRequirementDB.from_db_row(row)
        return None

    def get_requirements_by_environment(self, environment: str) -> list[VettedRequirementDB]:
        """Get all requirements for a specific environment.

        Args:
            environment: Environment name (BASE, DEVELOPMENT, PRODUCTION)

        Returns:
            List of VettedRequirementDB objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vetted_requirements 
            WHERE environment = ?
            ORDER BY name
        ''', (environment,))
        rows = cursor.fetchall()
        conn.close()

        return [VettedRequirementDB.from_db_row(row) for row in rows]

    def get_git_based_requirements(self) -> list[VettedRequirementDB]:
        """Get all git-based requirements (with @ specifier).

        Returns:
            List of VettedRequirementDB objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vetted_requirements 
            WHERE specifier = '@'
            ORDER BY name
        ''')
        rows = cursor.fetchall()
        conn.close()

        return [VettedRequirementDB.from_db_row(row) for row in rows]

    def search_requirements(self, pattern: str) -> list[VettedRequirementDB]:
        """Search requirements by name pattern.

        Args:
            pattern: SQL LIKE pattern (e.g., 'django%', '%celery%')

        Returns:
            List of VettedRequirementDB objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vetted_requirements 
            WHERE name LIKE ?
            ORDER BY name
        ''', (pattern,))
        rows = cursor.fetchall()
        conn.close()

        return [VettedRequirementDB.from_db_row(row) for row in rows]

    def get_statistics(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total count
        cursor.execute('SELECT COUNT(*) FROM vetted_requirements')
        total_count = cursor.fetchone()[0]

        # Count by environment
        cursor.execute('''
            SELECT environment, COUNT(*) 
            FROM vetted_requirements 
            GROUP BY environment 
            ORDER BY environment
        ''')
        by_environment = {row[0]: row[1] for row in cursor.fetchall()}

        # Count git-based
        cursor.execute('''
            SELECT COUNT(*) 
            FROM vetted_requirements 
            WHERE specifier = '@'
        ''')
        git_based_count = cursor.fetchone()[0]

        # Count Django packages
        cursor.execute('''
            SELECT COUNT(*) 
            FROM vetted_requirements 
            WHERE name LIKE 'django%'
        ''')
        django_count = cursor.fetchone()[0]

        conn.close()

        return {
            'total_requirements': total_count,
            'by_environment': by_environment,
            'git_based_count': git_based_count,
            'django_count': django_count,
        }

    def requirement_exists(self, name: str, environment: Optional[str] = None) -> bool:
        """Check if a requirement exists in the database.

        Args:
            name: Package name
            environment: Optional environment filter

        Returns:
            True if requirement exists, False otherwise
        """
        return self.get_requirement_by_name(name, environment) is not None

    def get_requirements_dict(self, environment: Optional[str] = None) -> dict[str, VettedRequirementDB]:
        """Get requirements as a dictionary keyed by name.

        Args:
            environment: Optional environment filter

        Returns:
            Dictionary of package name to VettedRequirementDB object
        """
        if environment:
            requirements = self.get_requirements_by_environment(environment)
        else:
            requirements = self.get_all_requirements()

        return {req.name: req for req in requirements}

    def generate_requirements_file(
        self,
        environments: list[str],
        output_path: Optional[Path] = None
    ) -> str:
        """Generate a requirements.txt file content for specified environments.

        Args:
            environments: List of environments to include (e.g., ['BASE', 'DEVELOPMENT'])
            output_path: Optional path to write the requirements file

        Returns:
            Requirements file content as string
        """
        requirements = []

        for env in environments:
            reqs = self.get_requirements_by_environment(env)
            requirements.extend(reqs)

        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_reqs = []
        for req in requirements:
            if req.name not in seen:
                seen.add(req.name)
                unique_reqs.append(req)

        # Generate content
        lines = [f"# Generated requirements file for environments: {', '.join(environments)}\n"]

        for env in environments:
            env_reqs = [r for r in unique_reqs if r.environment == env]
            if env_reqs:
                lines.append(f"\n# {env} requirements\n")
                for req in sorted(env_reqs, key=lambda x: x.name):
                    lines.append(req.to_requirement_string() + "\n")

        content = "".join(lines)

        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(content)
            logger.info(f"Requirements file written to {output_path}")

        return content


def example_usage():
    """Example usage of the requirements database interface."""
    # Initialize database interface
    db_path = Path(__file__).parent.parent.parent / "code_review.db"
    db = VettedRequirementsDatabase(db_path)

    # Get all requirements
    print("Total requirements:", len(db.get_all_requirements()))

    # Get specific requirement
    django_req = db.get_requirement_by_name("django")
    if django_req:
        print(f"\nDjango requirement:")
        print(f"  Version: {django_req.specifier} {django_req.version}")
        print(f"  Environment: {django_req.environment}")

    # Get production requirements
    prod_reqs = db.get_requirements_by_environment("PRODUCTION")
    print(f"\nProduction requirements: {len(prod_reqs)}")

    # Get development requirements
    dev_reqs = db.get_requirements_by_environment("DEVELOPMENT")
    print(f"Development requirements: {len(dev_reqs)}")

    # Get git-based packages
    git_reqs = db.get_git_based_requirements()
    print(f"\nGit-based packages: {len(git_reqs)}")
    print("  Examples:", ", ".join([r.name for r in git_reqs[:3]]))

    # Search for Django packages
    django_pkgs = db.search_requirements("django%")
    print(f"\nDjango packages: {len(django_pkgs)}")

    # Get statistics
    stats = db.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total: {stats['total_requirements']}")
    print(f"  Git-based: {stats['git_based_count']}")
    print(f"  Django packages: {stats['django_count']}")
    print(f"  By environment: {stats['by_environment']}")

    # Generate requirements file
    print("\n" + "="*60)
    print("Sample requirements.txt for BASE + DEVELOPMENT:")
    print("="*60)
    content = db.generate_requirements_file(['BASE', 'DEVELOPMENT'])
    print(content[:500] + "...")


if __name__ == "__main__":
    example_usage()

