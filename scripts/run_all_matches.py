from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cze_wp_scraper.scraper.scraper import MatchScraper


def main() -> None:
    """Scrape all matches from game_id 1 to max_game_id."""
    parser = argparse.ArgumentParser(description="Scrape Czech Water Polo matches from game_id 1 to max_game_id")
    parser.add_argument(
        "max_game_id",
        type=int,
        nargs="?",
        default=2425,
        help="Maximum game ID to scrape (default: 2500)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output CSV file path (optional). If not provided, prints to stdout.",
    )

    args = parser.parse_args()

    if args.max_game_id < 1:
        print("Error: max_game_id must be at least 1", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("Czech Water Polo Scraper - Batch Scraping")
    print("=" * 80)
    print(f"Scraping matches from game_id 1 to {args.max_game_id}")
    print(f"Total matches to attempt: {args.max_game_id}")
    print()

    # Generate list of game IDs
    game_ids = list(range(1, args.max_game_id + 1))

    # Scrape matches
    scraper = MatchScraper()
    df = scraper.scrape_matches(game_ids)

    # Display results
    print("=" * 80)
    print("Scraping completed!")
    print("=" * 80)
    print(f"Successfully scraped: {len(df)} matches")
    print(f"Failed/Skipped: {len(game_ids) - len(df)} matches")
    print()

    if len(df) > 0:
        print("Sample of scraped data:")
        print(df.head(10).to_string())
        print()

        # Save to file if output path provided
        if args.output:
            output_path = Path(args.output)
            df.to_csv(output_path, index=False)
            print(f"Results saved to: {output_path}")
        else:
            print("Full results:")
            print(df.to_string())
    else:
        print("No matches were successfully scraped.")
        print("This could mean:")
        print("  - All game IDs in the range don't exist")
        print("  - Network errors occurred")
        print("  - Parsing errors occurred")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
