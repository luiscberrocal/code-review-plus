import click
from typing import List, Optional

from code_review.handlers.display_handlers import display_about_table, show_banner
from code_review.schemas import SeverityLevel
from code_review.handlers.validation_handlers import filter_validation_results, get_summary_stats


@click.group()
def cli() -> None:
    """A simple command-line tool for code review operations."""
    pass


@cli.command()
def about() -> None:
    """About the CLI."""
    show_banner()
    display_about_table()


@cli.command()
@click.option('--min-severity', 
              type=click.Choice(['info', 'warning', 'error', 'critical'], case_sensitive=False),
              help='Minimum severity level to include')
@click.option('--severity', 'severities',
              multiple=True,
              type=click.Choice(['info', 'warning', 'error', 'critical'], case_sensitive=False),
              help='Specific severity levels to include (can be used multiple times)')
@click.option('--violations-only', 
              is_flag=True,
              help='Only show failed validation results')
@click.option('--output-format',
              type=click.Choice(['text', 'json', 'markdown'], case_sensitive=False),
              default='text',
              help='Output format for results')
@click.option('--fail-on-violations',
              is_flag=True,
              help='Exit with non-zero code if violations are found')
def coverage(min_severity: Optional[str],
             severities: List[str],
             violations_only: bool,
             output_format: str,
             fail_on_violations: bool) -> None:
    """Analyze code coverage with optional filtering."""
    
    # Import here to avoid circular imports
    from code_review.plugins.coverage.handlers import validate_coverage_rules
    
    try:
        # For now, use dummy data - in real implementation this would analyze actual coverage
        results = validate_coverage_rules()
        
        # Apply filtering
        filter_kwargs = {}
        
        if min_severity:
            filter_kwargs['min_severity'] = SeverityLevel(min_severity.lower())
        
        if severities:
            filter_kwargs['severities'] = [SeverityLevel(s.lower()) for s in severities]
        
        if violations_only:
            filter_kwargs['violations_only'] = True
        
        if filter_kwargs:
            results = filter_validation_results(results, **filter_kwargs)
        
        # Output results
        if output_format == 'json':
            import json
            output_data = [result.model_dump() for result in results]
            click.echo(json.dumps(output_data, indent=2))
            # Don't show summary for JSON output
        elif output_format == 'markdown':
            click.echo("# Coverage Analysis Results\n")
            for result in results:
                status = "❌" if not result.passed else "✅"
                click.echo(f"## {status} {result.name}")
                click.echo(f"**Category:** {result.category.value}")
                click.echo(f"**Severity:** {result.severity.value}")
                click.echo(f"**Message:** {result.message}")
                if result.details:
                    click.echo(f"**Details:** {result.details}")
                click.echo("")
            
            # Summary statistics for markdown
            if results:
                stats = get_summary_stats(results)
                click.echo(f"## Summary\n- {stats['violations']} violations\n- {stats['blocking_violations']} blocking")
        else:  # text format
            if not results:
                click.echo("No results found matching the specified criteria.")
                return
            
            click.echo(f"Found {len(results)} result(s):\n")
            for result in results:
                status = "FAIL" if not result.passed else "PASS"
                click.echo(f"[{status}] {result.name} ({result.severity.value.upper()})")
                click.echo(f"  Category: {result.category.value}")
                click.echo(f"  Message: {result.message}")
                if result.details:
                    click.echo(f"  Details: {result.details}")
                click.echo("")
            
            # Summary statistics for text output
            if results:
                stats = get_summary_stats(results)
                click.echo(f"Summary: {stats['violations']} violations, {stats['blocking_violations']} blocking")
        
        # Exit with error code if violations found and requested
        if fail_on_violations and violations_only and results:
            exit(1)
        
    except Exception as e:
        click.echo(f"Error analyzing coverage: {e}", err=True)
        exit(1)
