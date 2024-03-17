from web_scraper import WebScraper

ws = WebScraper()

if __name__ == "__main__":
    for item in ws.listing_list:
        print(f"URL: {item['url']}")
    print(f"Total number of scraped url: {len(ws.listing_list)}")
