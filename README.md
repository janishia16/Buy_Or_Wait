# Buy Or Wait

A book price tracking system that scrapes prices from Amazon India and Flipkart, stores historical data, and provides insights through a Databricks dashboard to help you decide whether to buy now or wait for a better deal.


## Overview

This project automates the collection of book prices from major Indian e-commerce platforms and visualizes price trends to help make informed purchasing decisions.

## Features

- Web scraping from Amazon India and Flipkart
- Daily price data collection and storage
- Historical price tracking
- Interactive Databricks dashboard for price analysis
- Price comparison across platforms

## Project Structure

```
Buy_Or_Wait/
├── files/                              # Data files and exports
├── notebook/                           # Databricks notebooks for analysis
├── scrapping_data_local_machine/       # Local scraping scripts (run on local/EC2)
├── Master Dashboard for Book price.lvdash.json  # Databricks dashboard config
└── README.md
```

## Tech Stack

- **Python** - Web scraping and data processing
- **Playwright** - Browser automation for scraping
- **Databricks** - Data processing, notebooks, and dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           WORKFLOW                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   LOCAL MACHINE / EC2                      DATABRICKS                │
│   ┌─────────────────────┐                 ┌─────────────────────┐   │
│   │                     │                 │                     │   │
│   │  1. Run Scraper     │  ──── CSV ────► │  2. Process Data    │   │
│   │     (Python +       │                 │     (Notebooks)     │   │
│   │      Playwright)    │                 │                     │   │
│   │                     │                 │  3. Visualize       │   │
│   │  scrapping_data_    │                 │     (Dashboard)     │   │
│   │  local_machine/     │                 │                     │   │
│   └─────────────────────┘                 └─────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Guide

### Step 1: Run Scraper(scrapping_data_local_machine/) (Local Machine or EC2)

> **Note:** Run the scraping scripts on your **local machine** or **EC2 server**. Databricks cannot run browser automation.

#### 1.1 Clone the repository

```bash
git clone https://github.com/janishia16/Buy_Or_Wait.git
cd Buy_Or_Wait
```

#### 1.2 Install dependencies

```bash
pip install playwright pandas
playwright install firefox
playwright install-deps
```

#### 1.3 Add books to track

Edit the input CSV file with book names and product URLs:

```csv
book_name,flipkart_link,amazon_link
Atomic Habits,https://www.flipkart.com/...,https://www.amazon.in/...
Project Hail Mary,https://www.flipkart.com/...,https://www.amazon.in/...
```

#### 1.4 Run the scraper

```bash
cd scrapping_data_local_machine
python scraper.py
```

#### 1.5 Upload scraped data to Databricks

After scraping, upload the output CSV file to your Databricks workspace:

**Option A: Using Databricks UI**
- Go to Databricks → Data → Add Data → Upload File
- Upload the CSV file to DBFS

**Option B: Using Databricks CLI**
```bash
databricks fs cp book_daily.csv dbfs:/FileStore/book_data/
```

**Option C: Manually edit the CSV**
- Open `daily.csv` and paste/edit the scraped data directly
- Useful for combining data from multiple scraping sessions

---

### Step 2: Process Data in Databricks

> The Databricks job pipeline is already configured and ready to use!

#### Pipeline Overview

![Databricks Pipeline](https://raw.githubusercontent.com/janishia16/Images/main/databricks.png)

The pipeline consists of 4 automated tasks:

| Task | Notebook | Description |
|------|----------|-------------|
| **Scraping** | `Book_Scrapping` | Loads raw scraped data |
| **Cleaning** | `Cleaning the Data` | Cleans and transforms data |
| **Training** | `Model Training` | Trains price prediction model |
| **Predicting** | `Predictions` | Generates price predictions |

#### Pipeline Configuration

- **Trigger**: Table update on `layers.bronze.book_daily_raw`
- **Compute**: Serverless
- **Execution**: Automatic when new data is uploaded

#### 2.1 Import notebooks (if not already imported)

1. Go to Databricks → Workspace → Import
2. Upload notebooks from the `notebook/` folder
3. Attach notebooks to a cluster

#### 2.2 Run the pipeline

The pipeline runs automatically when new data arrives, or you can:
- Click **Run now** to execute manually
- Edit triggers via **Edit trigger** button

---

### Step 3: View Dashboard in Databricks

> Use the pre-built dashboard to visualize price trends and comparisons

#### Dashboard Preview

![Book Price Dashboard](https://raw.githubusercontent.com/janishia16/Images/main/image.png)

#### 3.1 Import the dashboard

1. Go to Databricks → SQL → Dashboards
2. Click **Import** and select `Master Dashboard for Book price.lvdash.json`

#### 3.2 Connect data source

1. Update the dashboard queries to point to your data tables
2. Refresh the dashboard to load data

#### 3.3 Explore insights

- Compare prices across Amazon and Flipkart
- Track price changes over time
- Identify the best time to buy

---

## Data Schema

| Field | Description |
|-------|-------------|
| ISBN | Book identifier (ISBN-10 or ISBN-13) |
| Book Name | Title of the book |
| Author | Author name |
| Source | Platform (Amazon/Flipkart) |
| Price | Current price in INR (₹) |
| Scrape Timestamp | Date and time of data collection |
| URL | Product page link |

## Use Cases

- Track prices of books on your wishlist
- Find the best platform to purchase from
- Identify price drops and deals
- Analyze price patterns over time

## Roadmap

- [ ] **AWS EC2 Automation** - Set up scheduled scraping on EC2 with cron jobs
- [ ] **Automated Data Pipeline** - Auto-upload scraped data to Databricks
- [ ] **Email Alerts** - Notify when prices drop below threshold
- [ ] **More Retailers** - Add support for additional bookstores

### Planned Architecture (EC2 Automation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUTOMATED PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   AWS EC2                                  DATABRICKS                │
│   ┌─────────────────────┐                 ┌─────────────────────┐   │
│   │  Cron Job           │                 │                     │   │
│   │  (Daily @ 8 AM)     │                 │  Auto-refresh       │   │
│   │         │           │                 │  Dashboard          │   │
│   │         ▼           │                 │                     │   │
│   │  Run Scraper        │  ── S3/DBFS ──► │  Process Data       │   │
│   │         │           │                 │                     │   │
│   │         ▼           │                 │                     │   │
│   │  Upload to Cloud    │                 │                     │   │
│   └─────────────────────┘                 └─────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

[janishia16](https://github.com/janishia16)
