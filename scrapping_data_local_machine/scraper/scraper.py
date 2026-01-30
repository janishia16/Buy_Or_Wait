"""
Book Price Scraper using Playwright
Scrapes from Amazon India and Flipkart using direct URLs from CSV

Install:
    pip install playwright pandas
    playwright install firefox
    playwright install-deps

Usage (Interactive):
    python scraper.py
    
Usage (Automated - EC2):
    python scraper.py --auto

CSV Input Format: book_name,flipkart_link,amazon_link
CSV Output: book_daily.csv
"""
# !pip install playwright pandas
# !playwright install firefox
# !playwright install-deps

import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import re
import os
import sys


# ============================================
# CONFIGURATION
# ============================================
CSV_INPUT_PATH = "book_list.csv"
CSV_OUTPUT_PATH = "book_daily.csv"
MAX_BOOKS = 10
# ============================================


def extract_isbn(text):
    """Extract ISBN from text."""
    if not text:
        return None
    # Try ISBN-13 first (978 or 979 prefix)
    isbn13 = re.search(r'(?:978|979)\d{10}', str(text))
    if isbn13:
        return int(isbn13.group())
    return None

def extract_isbn_from_amazon_url(url):
    """Extract ISBN/ASIN from Amazon URL (dp/XXXXXXXXXX)."""
    if not url:
        return None
    # Amazon URLs have format: /dp/XXXXXXXXXX or /product/XXXXXXXXXX
    match = re.search(r'/dp/(\d{10})', str(url))
    if match:
        return match.group(1)  # Return as string (ISBN-10)
    return None

def clean_price(price_text):
    """Extract numeric price."""
    if not price_text:
        return None
    numbers = re.findall(r'[\d,]+', str(price_text).replace(',', ''))
    if numbers:
        return int(numbers[0].replace(',', ''))
    return None

def extract_author_flipkart(title):
    """Extract author from Flipkart title."""
    if not title:
        return None
    match = re.search(r'\((?:Paperback|Hardcover|Papeprback)?,?\s*([A-Za-z\s\.]+)\)\s*$', str(title))
    if match:
        author = match.group(1).strip()
        for word in ['Paperback', 'Papeprback', 'Hardcover', 'English']:
            author = re.sub(rf'\b{word}\b', '', author, flags=re.IGNORECASE)
        author = re.sub(r'^\s*,\s*', '', author).strip()
        if ',' in author:
            author = author.split(',')[0].strip()
        return author if author else None
    return None


def scrape_amazon_url(page, book_name, book_id, url):
    """Scrape book from Amazon India using direct URL."""
    result = {
        'book_id': book_id,
        'isbn': None,
        'book_name': book_name,
        'author': None,
        'source': 'Amazon',
        'price': None,
        'scrape_ts': datetime.now(),
        'url': url
    }
    
    try:
        page.goto(url, wait_until="load", timeout=60000)
        time.sleep(4)
        
        result['url'] = page.url
        print(f"    Amazon URL: {result['url'][:60]}...")
        
        # Author - try multiple selectors
        try:
            author_selectors = [
                "#bylineInfo .author a",
                "#bylineInfo a.contributorNameID",
                "#bylineInfo a",
                ".author a",
                "a.a-link-normal.contributorNameID",
                "#bylineInfo span.author a"
            ]
            for sel in author_selectors:
                elem = page.query_selector(sel)
                if elem:
                    text = elem.text_content()
                    if text and len(text.strip()) > 1:
                        result['author'] = text.strip()
                        print(f"    Author found: {result['author']}")
                        break
        except Exception as e:
            print(f"    Author extraction error: {str(e)[:30]}")
        
        # Price
        try:
            for sel in ["span.a-price-whole", "#corePrice_feature_div span.a-price-whole", ".a-price .a-offscreen"]:
                elem = page.query_selector(sel)
                if elem:
                    text = elem.text_content()
                    price = clean_price(text)
                    if price:
                        result['price'] = price
                        break
        except:
            pass
        
        # ISBN - look in product details table
        try:
            # First try to find ISBN in product details
            isbn_found = None
            detail_rows = page.query_selector_all("#detailBullets_feature_div li, #productDetails_detailBullets_sections1 tr, .detail-bullet-list span")
            for row in detail_rows:
                text = row.text_content() or ""
                if 'ISBN-13' in text or 'ISBN-10' in text or 'ISBN' in text:
                    isbn_found = extract_isbn(text)
                    if isbn_found:
                        result['isbn'] = isbn_found
                        print(f"    ISBN found: {result['isbn']}")
                        break
            
            # Fallback 1: search entire page content for ISBN-13
            if not isbn_found:
                content = page.content()
                result['isbn'] = extract_isbn(content)
                if result['isbn']:
                    print(f"    ISBN found (page): {result['isbn']}")
                    isbn_found = True
            
            # Fallback 2: extract from Amazon URL (ISBN-10/ASIN)
            if not isbn_found:
                url_isbn = extract_isbn_from_amazon_url(url)
                if url_isbn:
                    result['isbn'] = url_isbn
                    print(f"    ISBN from URL: {result['isbn']}")
        except Exception as e:
            print(f"    ISBN extraction error: {str(e)[:30]}")
        
    except Exception as e:
        print(f"    Amazon error: {str(e)[:40]}")
        
    return result


def scrape_flipkart_url(page, book_name, book_id, url):
    """Scrape book from Flipkart using direct URL."""
    result = {
        'book_id': book_id,
        'isbn': None,
        'book_name': book_name,
        'author': None,
        'source': 'Flipkart',
        'price': None,
        'scrape_ts': datetime.now(),
        'url': url
    }
    
    try:
        page.goto(url, wait_until="load", timeout=60000)
        time.sleep(4)
        
        # Close popup if present
        try:
            popup = page.query_selector("button._2KpZ6l._2doB4z, span._30XB9F")
            if popup:
                popup.click()
                time.sleep(1)
        except:
            pass
        
        result['url'] = page.url
        print(f"    Flipkart URL: {result['url'][:60]}...")
        
        # Author - try multiple methods
        try:
            # Method 1: Look for author in product details/specifications
            author_selectors = [
                "//div[contains(text(), 'Author')]/following-sibling::div",
                "//td[contains(text(), 'Author')]/following-sibling::td",
                "//span[contains(text(), 'Author')]/parent::div/following-sibling::div"
            ]
            
            # Try CSS selectors first
            spec_rows = page.query_selector_all("div._3k-BhJ div, table._14cfVK tr, div.row div")
            for row in spec_rows:
                text = row.text_content() or ""
                if 'Author' in text and ':' in text:
                    parts = text.split(':')
                    if len(parts) >= 2:
                        author = parts[1].strip().split('\n')[0].strip()
                        if author and len(author) > 1:
                            result['author'] = author
                            print(f"    Author found: {result['author']}")
                            break
            
            # Method 2: Extract from title if not found
            if not result['author']:
                title_elem = page.query_selector("h1 span, span.B_NuCI, h1.yhB1nd")
                if title_elem:
                    full_title = title_elem.text_content() or ""
                    result['author'] = extract_author_flipkart(full_title)
                    if result['author']:
                        print(f"    Author from title: {result['author']}")
        except Exception as e:
            print(f"    Author extraction error: {str(e)[:30]}")
        
        # Price
        try:
            for sel in ["div.hZ3P6w", "div.Nx9bqj", "div.CEmiEU div.Nx9bqj", "div._30jeq3"]:
                elem = page.query_selector(sel)
                if elem:
                    text = elem.text_content()
                    price = clean_price(text)
                    if price:
                        result['price'] = price
                        break
        except:
            pass
        
        # ISBN - look in specifications
        try:
            isbn_found = None
            # Look in product specifications
            spec_rows = page.query_selector_all("div._3k-BhJ div, table._14cfVK tr, div.row")
            for row in spec_rows:
                text = row.text_content() or ""
                if 'ISBN' in text:
                    isbn_found = extract_isbn(text)
                    if isbn_found:
                        result['isbn'] = isbn_found
                        print(f"    ISBN found: {result['isbn']}")
                        break
            
            # Fallback: search URL for ISBN (Flipkart often has ISBN in URL/pid)
            if not isbn_found:
                # Try to get from pid parameter or URL path
                url_isbn = extract_isbn(url)
                if url_isbn:
                    result['isbn'] = url_isbn
                    print(f"    ISBN from URL: {result['isbn']}")
                    isbn_found = True
            
            # Also try the final page URL (after redirect)
            if not isbn_found:
                final_url_isbn = extract_isbn(result['url'])
                if final_url_isbn:
                    result['isbn'] = final_url_isbn
                    print(f"    ISBN from final URL: {result['isbn']}")
            
            # Final fallback: search page content
            if not result['isbn']:
                content = page.content()
                result['isbn'] = extract_isbn(content)
                if result['isbn']:
                    print(f"    ISBN found (fallback): {result['isbn']}")
        except Exception as e:
            print(f"    ISBN extraction error: {str(e)[:30]}")
        
    except Exception as e:
        print(f"    Flipkart error: {str(e)[:40]}")
        
    return result


def get_next_book_id(daily_path):
    """Get next book_id from daily file."""
    try:
        if os.path.exists(daily_path) and os.path.getsize(daily_path) > 0:
            df = pd.read_csv(daily_path)
            if len(df) > 0:
                return int(df['book_id'].max()) + 1
    except:
        pass
    return 1


def create_empty_result(book_id, book_name, source, url):
    """Create an empty result dict."""
    return {
        'book_id': book_id,
        'isbn': None,
        'book_name': book_name,
        'author': None,
        'source': source,
        'price': None,
        'scrape_ts': datetime.now(),
        'url': url
    }


def launch_browser(p):
    """Launch Firefox browser (more stable with anti-bot sites)."""
    browser = p.firefox.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    return browser, context


def get_books_from_csv():
    """Get book details from CSV file."""
    print("\n" + "="*60)
    print("BOOK PRICE SCRAPER")
    print("="*60)
    print("\nCSV Format: book_name,flipkart_link,amazon_link")
    print("Max 5 books per run")
    print("Leave link empty to skip that source\n")
    
    # Default to book_list.csv in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "book_list.csv")
    print(f"Using CSV file: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return []
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
    
    # Check required columns
    required_cols = ['book_name']
    for col in required_cols:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            print(f"Found columns: {list(df.columns)}")
            return []
    
    # Check for at least one link column
    if 'flipkart_link' not in df.columns and 'amazon_link' not in df.columns:
        print("CSV must have at least one of: flipkart_link, amazon_link")
        return []
    
    books = []
    for idx, row in df.head(5).iterrows():  # Max 5 books
        book_name = str(row.get('book_name', '')).strip()
        if not book_name or book_name == 'nan':
            continue
        
        flipkart_link = str(row.get('flipkart_link', '')).strip()
        amazon_link = str(row.get('amazon_link', '')).strip()
        
        # Clean up nan values
        if flipkart_link == 'nan':
            flipkart_link = ''
        if amazon_link == 'nan':
            amazon_link = ''
        
        if not flipkart_link and not amazon_link:
            print(f"Skipping '{book_name}' - no links provided")
            continue
        
        books.append({
            'book_name': book_name,
            'flipkart_link': flipkart_link,
            'amazon_link': amazon_link
        })
    
    return books


def main():
    daily_path = "book_daily.csv"
    
    # Get books from CSV
    books = get_books_from_csv()
    
    if not books:
        print("\nNo books to scrape. Exiting.")
        return None
    
    print(f"\n\nBooks to scrape: {len(books)}")
    for b in books:
        sources = []
        if b['amazon_link']:
            sources.append('Amazon')
        if b['flipkart_link']:
            sources.append('Flipkart')
        print(f"  - {b['book_name']} ({', '.join(sources)})")
    
    book_id = get_next_book_id(daily_path)
    all_results = []
    
    print("\nStarting Playwright...")
    
    with sync_playwright() as p:
        browser, context = launch_browser(p)
        
        print("Browser started!\n")
        
        for book in books:
            book_name = book['book_name']
            amazon_link = book['amazon_link']
            flipkart_link = book['flipkart_link']
            
            print(f"\n=== Scraping: {book_name} ===")
            
            # Scrape Amazon if link provided
            if amazon_link:
                try:
                    page = context.new_page()
                    result = scrape_amazon_url(page, book_name, book_id, amazon_link)
                    all_results.append(result)
                    print(f"  Amazon: Price={result['price']}, Author={result['author']}")
                    book_id += 1
                    page.close()
                except Exception as e:
                    print(f"  Amazon error: {str(e)[:50]}")
                    all_results.append(create_empty_result(book_id, book_name, 'Amazon', amazon_link))
                    book_id += 1
                
                time.sleep(3)
            
            # Scrape Flipkart if link provided
            if flipkart_link:
                try:
                    page = context.new_page()
                    result = scrape_flipkart_url(page, book_name, book_id, flipkart_link)
                    all_results.append(result)
                    print(f"  Flipkart: Price={result['price']}, Author={result['author']}")
                    book_id += 1
                    page.close()
                except Exception as e:
                    print(f"  Flipkart error: {str(e)[:50]}")
                    all_results.append(create_empty_result(book_id, book_name, 'Flipkart', flipkart_link))
                    book_id += 1
                
                time.sleep(3)
        
        try:
            browser.close()
        except:
            pass
    
    if not all_results:
        print("\nNo results to save.")
        return None
    
    # Save results to daily
    df = pd.DataFrame(all_results)
    cols = ['book_id', 'isbn', 'book_name', 'author', 'source', 'price', 'scrape_ts', 'url']
    df = df[cols]
    
    # Append to existing daily file or create new
    try:
        if os.path.exists(daily_path) and os.path.getsize(daily_path) > 0:
            existing = pd.read_csv(daily_path)
            df = pd.concat([existing, df], ignore_index=True)
    except:
        pass
    
    df.to_csv(daily_path, index=False)
    print(f"\nSaved {len(all_results)} new records to {daily_path}")
    print(f"Total records in {daily_path}: {len(df)}")
    
    return df


if __name__ == "__main__":
    results = main()
    print("\nDone!")
