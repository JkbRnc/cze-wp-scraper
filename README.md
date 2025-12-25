# Czech Water Polo Scraper

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Loguru](https://img.shields.io/badge/loguru-0.7.3+-blue.svg)](https://github.com/Delgan/loguru)
[![mypy](https://img.shields.io/badge/mypy-1.19.1+-blue.svg)](https://github.com/python/mypy)
[![pandas](https://img.shields.io/badge/pandas-2.0.0+-blue.svg)](https://pandas.pydata.org)

A Python web scraper for extracting Czech Water Polo match results from [csvp.cz](https://www.csvp.cz). This tool fetches match data including teams, scores, dates, leagues, and match outcomes, and exports them to pandas DataFrames or CSV files.

## Overview

This scraper provides a clean, type-safe interface to extract structured match data from the Czech Water Polo website. It handles HTTP requests, HTML parsing, data validation, and provides convenient batch processing capabilities.

### Features

- 🔍 **Web Scraping**: Fetches match pages from csvp.cz
- 📊 **Data Extraction**: Extracts match details (teams, scores, dates, leagues, winners)
- ✅ **Type Safety**: Uses Pydantic models for data validation
- 💾 **Export Options**: Output to pandas DataFrame or CSV file
- 🛡️ **Error Handling**: Gracefully handles missing or invalid matches
- 🧪 **Well Tested**: Comprehensive unit test coverage

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/JkbRnc/cze-wp-scraper.git
cd cze-wp-scraper
```

2. Install dependencies with uv:
```bash
uv sync
```

### Running the Scraper

The easiest way to scrape matches is using the `run_all_matches.py` script:

#### Basic Usage

Scrape matches from game_id 1 to the default maximum (2425):
```bash
uv run python scripts/run_all_matches.py
```

#### Custom Range

Scrape matches from game_id 1 to a specific maximum:
```bash
uv run python scripts/run_all_matches.py 3000
```

#### Save to CSV

Save results to a CSV file:
```bash
uv run python scripts/run_all_matches.py 3000 -o matches.csv
```

### Programmatic Usage

You can also use the scraper programmatically:

```python
from cze_wp_scraper.scraper.scraper import MatchScraper

# Initialize scraper
scraper = MatchScraper()

# Scrape specific matches
game_ids = [2425, 2424, 2423]
df = scraper.scrape_matches(game_ids)

# Access the data
print(df.head())
print(f"Total matches: {len(df)}")
```

## Project Structure

```
cze-wp-scraper/
├── src/
│   └── cze_wp_scraper/
│       ├── models/          # Pydantic data models
│       ├── scraper/        # Scraping logic (client, parser, scraper)
│       └── utils/          # Utility functions
├── scripts/
│   └── run_all_matches.py  # Batch scraping script
├── tests/                  # Unit tests
└── pyproject.toml          # Project configuration
```

## Data Model

Each match contains the following fields:

- `game_id`: Match identifier
- `home_team`: Home team name
- `away_team`: Away team name
- `match_date`: Match date and time (datetime)
- `league`: Competition name
- `home_score`: Home team score
- `away_score`: Away team score
- `winner`: Winner indicator ("H" for home, "A" for away, "D" for draw)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/cze_wp_scraper --cov-report=html

# Run specific test file
uv run pytest tests/unit/scraper/test_scraper.py
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check .

# Format code
uv run ruff format .

# Type checking with mypy
uv run mypy src/
```

## Dependencies

### Runtime
- `httpx`: Modern HTTP client
- `beautifulsoup4` + `lxml`: HTML parsing
- `pandas`: Data manipulation and export
- `pydantic`: Data validation
- `loguru`: Logging

### Development
- `pytest`: Testing framework
- `ruff`: Linting and formatting
- `mypy`: Type checking
