# Book Price Scraper

A Python scraper that fetches book prices from **Amazon India** and **Flipkart** using Playwright.

## Features

- Scrapes prices from both Amazon India and Flipkart
- Extracts book details: ISBN, author, price, and URL
- Uses direct product URLs (no search needed)
- Outputs results to CSV for tracking price history

## Requirements

- Python 3.8+
- Firefox browser (installed automatically by Playwright)

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install firefox
   playwright install-deps
   ```

## File Structure

```
book-price-scrapper/
├── scraper/
│   ├── scraper.py       # Main scraper script
│   ├── book_list.csv    # Input: books to scrape (you edit this)
│   └── book_daily.csv   # Output: scraped results
├── requirements.txt
└── README.md
```

## Usage

### Step 1: Add Books to `book_list.csv`

Edit `scraper/book_list.csv` with the books you want to track:

```csv
book_name,flipkart_link,amazon_link
Atomic Habits,https://www.flipkart.com/atomic-habits.../p/itmXXX,https://www.amazon.in/Atomic-Habits.../dp/XXXXXXXXXX
Project Hail Mary,https://www.flipkart.com/project-hail-mary.../p/itmXXX,https://www.amazon.in/Project-Hail-Mary.../dp/XXXXXXXXXX
```

**Tips for finding links:**
- **Amazon**: Search for the book, click the product, copy the URL
- **Flipkart**: Search for the book, click the product, copy the URL
- You can leave a link empty to skip that source

### Step 2: Run the Scraper

```bash
cd scraper
python3 scraper.py
```

The scraper will:
1. Read books from `book_list.csv`
2. Open a headless Firefox browser
3. Scrape each book from Amazon and Flipkart
4. Save results to `book_daily.csv`

### Step 3: View Results

Results are saved to `scraper/book_daily.csv`:

| book_id | isbn | book_name | author | source | price | scrape_ts | url |
|---------|------|-----------|--------|--------|-------|-----------|-----|
| 1 | 1847941834 | Atomic Habits | James Clear | Amazon | 497 | 2026-01-30 08:56:21 | https://... |
| 2 | 9781847941831 | Atomic Habits | | Flipkart | 259 | 2026-01-30 08:56:31 | https://... |

## Output Format

| Column | Description |
|--------|-------------|
| `book_id` | Unique identifier |
| `isbn` | ISBN-10 or ISBN-13 |
| `book_name` | Name of the book |
| `author` | Author (extracted from Amazon) |
| `source` | Amazon or Flipkart |
| `price` | Price in INR (₹) |
| `scrape_ts` | Timestamp of scrape |
| `url` | Product URL |

## Configuration

You can modify these settings at the top of `scraper.py`:

```python
CSV_INPUT_PATH = "book_list.csv"   # Input file
CSV_OUTPUT_PATH = "book_daily.csv" # Output file
MAX_BOOKS = 10                      # Max books per run
```

## Troubleshooting

### "playwright install" fails
```bash
# Try installing system dependencies first
playwright install-deps
playwright install firefox
```

### Browser crashes or times out
- Ensure you have enough RAM (at least 2GB free)
- Try running one book at a time
- Check your internet connection

### Prices not found
- The website layout may have changed
- Try updating the URL in `book_list.csv`
- Check if the product page loads correctly in a regular browser

### "command not found: python"
```bash
# Use python3 instead
python3 scraper.py
```

## Notes

- The scraper runs in **headless mode** (no browser window)
- Each scrape takes ~10 seconds per book per source
- Results are **appended** to `book_daily.csv` (not overwritten)
- Maximum 5 books per run to avoid rate limiting

## License

MIT
