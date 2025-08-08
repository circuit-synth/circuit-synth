#!/usr/bin/env python3
"""
Fast JLCPCB Search CLI

Command-line interface for the optimized JLCPCB component search.
Provides fast, token-free searching with immediate results.
"""

import json
import time
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from circuit_synth.manufacturing.jlcpcb import (
    fast_jlc_search,
    find_cheapest_jlc,
    find_most_available_jlc,
    get_fast_searcher,
)

console = Console()


@click.group()
def cli():
    """Fast JLCPCB component search - no agents, instant results."""
    pass


@cli.command()
@click.argument("query")
@click.option("--min-stock", "-s", default=0, help="Minimum stock required")
@click.option("--max-results", "-n", default=10, help="Maximum results to show")
@click.option(
    "--sort",
    "-o",
    type=click.Choice(["relevance", "price", "stock"]),
    default="relevance",
)
@click.option("--basic-only", "-b", is_flag=True, help="Show only basic parts")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def search(
    query: str,
    min_stock: int,
    max_results: int,
    sort: str,
    basic_only: bool,
    output_json: bool,
):
    """
    Search for JLCPCB components.

    Examples:
        jlc-fast search STM32G4
        jlc-fast search "0.1uF 0603" --min-stock 1000
        jlc-fast search LM358 --sort price
    """
    start_time = time.time()

    if not output_json:
        console.print(f"\n🔍 Searching JLCPCB for: [bold blue]{query}[/bold blue]\n")

    # Perform search
    results = fast_jlc_search(
        query=query,
        min_stock=min_stock,
        max_results=max_results,
        sort_by=sort,
        prefer_basic=basic_only,
    )

    elapsed = time.time() - start_time

    if output_json:
        # JSON output for scripting
        output = {
            "query": query,
            "elapsed_seconds": elapsed,
            "result_count": len(results),
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))
    else:
        # Rich console output
        if not results:
            console.print("[red]No results found[/red]")
            return

        # Create results table
        table = Table(title=f"Found {len(results)} components in {elapsed:.2f}s")
        table.add_column("Part #", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Stock", justify="right", style="green")
        table.add_column("Price", justify="right", style="yellow")
        table.add_column("Package", style="magenta")
        table.add_column("Type", style="blue")
        table.add_column("Score", justify="right", style="dim")

        for result in results:
            stock_str = f"{result.stock:,}" if result.stock > 0 else "OOS"
            price_str = f"${result.price:.4f}" if result.price > 0 else "-"
            type_str = "Basic" if result.basic_part else "Ext"
            score_str = f"{result.match_score:.2f}"

            # Truncate long descriptions
            desc = result.description
            if len(desc) > 40:
                desc = desc[:37] + "..."

            table.add_row(
                result.part_number,
                desc,
                stock_str,
                price_str,
                result.package,
                type_str,
                score_str,
            )

        console.print(table)


@cli.command()
@click.argument("query")
@click.option("--min-stock", "-s", default=100, help="Minimum stock required")
def cheapest(query: str, min_stock: int):
    """
    Find the cheapest component matching the query.

    Example:
        jlc-fast cheapest "10uF 0805"
    """
    start_time = time.time()
    console.print(f"\n💰 Finding cheapest: [bold blue]{query}[/bold blue]\n")

    result = find_cheapest_jlc(query, min_stock)
    elapsed = time.time() - start_time

    if result:
        panel = Panel(
            f"[bold]{result.part_number}[/bold]\n"
            f"{result.description}\n\n"
            f"Price: [yellow]${result.price:.4f}[/yellow]\n"
            f"Stock: [green]{result.stock:,}[/green]\n"
            f"Package: [magenta]{result.package}[/magenta]\n"
            f"Type: [blue]{'Basic' if result.basic_part else 'Extended'}[/blue]",
            title=f"Cheapest Match (found in {elapsed:.2f}s)",
            border_style="green",
        )
        console.print(panel)
    else:
        console.print(f"[red]No components found with minimum stock {min_stock}[/red]")


@cli.command()
@click.argument("query")
def most_available(query: str):
    """
    Find the component with the highest stock.

    Example:
        jlc-fast most-available STM32F103
    """
    start_time = time.time()
    console.print(f"\n📦 Finding most available: [bold blue]{query}[/bold blue]\n")

    result = find_most_available_jlc(query)
    elapsed = time.time() - start_time

    if result:
        panel = Panel(
            f"[bold]{result.part_number}[/bold]\n"
            f"{result.description}\n\n"
            f"Stock: [green]{result.stock:,}[/green]\n"
            f"Price: [yellow]${result.price:.4f}[/yellow]\n"
            f"Package: [magenta]{result.package}[/magenta]\n"
            f"Type: [blue]{'Basic' if result.basic_part else 'Extended'}[/blue]",
            title=f"Highest Stock (found in {elapsed:.2f}s)",
            border_style="green",
        )
        console.print(panel)
    else:
        console.print("[red]No components found[/red]")


@cli.command()
@click.argument("part_number")
@click.option("--max-results", "-n", default=5, help="Maximum alternatives to show")
def alternatives(part_number: str, max_results: int):
    """
    Find alternative components for a given part.

    Example:
        jlc-fast alternatives C123456
    """
    start_time = time.time()
    console.print(
        f"\n🔄 Finding alternatives for: [bold blue]{part_number}[/bold blue]\n"
    )

    searcher = get_fast_searcher()
    results = searcher.find_alternatives(part_number, max_results)
    elapsed = time.time() - start_time

    if not results:
        console.print("[red]No alternatives found[/red]")
        return

    # Create results table
    table = Table(title=f"Found {len(results)} alternatives in {elapsed:.2f}s")
    table.add_column("Part #", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Stock", justify="right", style="green")
    table.add_column("Price", justify="right", style="yellow")
    table.add_column("Package", style="magenta")

    for result in results:
        stock_str = f"{result.stock:,}" if result.stock > 0 else "OOS"
        price_str = f"${result.price:.4f}" if result.price > 0 else "-"

        # Truncate long descriptions
        desc = result.description
        if len(desc) > 45:
            desc = desc[:42] + "..."

        table.add_row(result.part_number, desc, stock_str, price_str, result.package)

    console.print(table)


@cli.command()
def benchmark():
    """
    Benchmark search performance vs agent-based search.

    Shows the performance improvement of direct search.
    """
    console.print("\n⏱️  [bold]Performance Benchmark[/bold]\n")

    test_queries = ["STM32G4", "0.1uF 0603", "LM358", "USB-C connector", "10k resistor"]

    total_time = 0
    for query in test_queries:
        start = time.time()
        results = fast_jlc_search(query, max_results=5)
        elapsed = time.time() - start
        total_time += elapsed

        status = "✅" if results else "❌"
        console.print(f"{status} '{query}': {elapsed:.3f}s ({len(results)} results)")

    avg_time = total_time / len(test_queries)

    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Average search time: [green]{avg_time:.3f}s[/green]")
    console.print(f"  Total time: [green]{total_time:.3f}s[/green]")
    console.print(f"  vs Agent estimate: [red]~30s per search[/red]")
    console.print(
        f"  [bold green]Speed improvement: {30/avg_time:.1f}x faster![/bold green]"
    )
    console.print(f"  [bold blue]Token usage: 0 (vs ~500 per agent search)[/bold blue]")


@cli.command()
def clear_cache():
    """Clear the JLCPCB search cache."""
    cache_dir = Path.home() / ".circuit-synth" / "cache" / "jlcpcb"

    if cache_dir.exists():
        count = 0
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        console.print(f"[green]Cleared {count} cached searches[/green]")
    else:
        console.print("[yellow]No cache to clear[/yellow]")


if __name__ == "__main__":
    cli()
