from web_scraper import WebScraper

ws = WebScraper()

if __name__ == "__main__":
    # for item in ws.listing_list:
    #     print(f"URL: {item['url']}")
    print(f"Total number of scraped url: {len(ws.listing_list)}")

    ws.merge_data()

    for item in ws.gathered_info_list:
        print(f'Name: {item["name"]}')
        print(f'Genre: {item["genre"]}')
        print(f'URL: {item["url"]}')
        print('Contact:')
        for key, val in item["cont"].items():
            print(f'{key}: {val}')
