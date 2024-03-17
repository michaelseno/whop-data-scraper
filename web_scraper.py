from bs4 import BeautifulSoup
import requests
import logging
import concurrent.futures

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

URL = "https://whop.com"
ITEM_CLASS = "hover:bg-whop-hover border-whop-stroke group flex cursor-pointer flex-col items-stretch gap-2 overflow-x-hidden border-0 border-b border-solid p-5 transition md:flex-row md:items-center md:gap-5 md:rounded-lg md:border-b-0 md:p-4"
ITEM_TITLE = "subtitle1 overflow-x-hidden text-ellipsis whitespace-nowrap"
CAT_CLASS = "subtitle3 text-whop-dark-gray hover:text-whop-off-black whitespace-nowrap py-3.5 transition"
LP_CLASS = "subtitle flex h-8 w-8 cursor-pointer select-none items-center justify-center rounded-md border-2 transition border-transparent hover:bg-whop-hover hover:border-whop-hover active:border-whop-hover-press active:bg-whop-hover-press"
ONE_CLASS = "subtitle flex h-8 w-8 cursor-pointer select-none items-center justify-center rounded-md border-2 transition border-black"
THREAD = 10


class WebScraper:
    def __init__(self):
        self.data = self.get_request_data(URL)
        self.listing_list = []
        self.categories = []
        self.cat_page_list = []
        self.get_html_data()

    @staticmethod
    def get_request_data(req_url):
        response = requests.get(url=req_url)
        logging.info(f'Generating response from get request: {req_url}')
        return response.text

    @staticmethod
    def get_soup_data(data):
        logging.info(f'Parsing data in BeautifulSoup')
        return BeautifulSoup(data, "html.parser")

    @staticmethod
    def get_total_pages_count(pages):
        num_of_pages = []
        for page in pages:
            page_number = page.getText()
            num_of_pages.append(page_number)
            return num_of_pages[-1]

    @staticmethod
    def get_title(tag):
        item_name = (tag.getText())
        logging.info(f'Extracted `title` {item_name}')
        return item_name

    @staticmethod
    def get_href(tag):
        item_url = (tag.get("href"))
        logging.info(f'Extracted `href` {item_url}')
        return item_url

    def scrape_data(self, url):
        logging.info(f'Initiating GET request to : {url}')
        by_category = self.get_request_data(req_url=url)
        by_cat_soup = self.get_soup_data(by_category)
        logging.info(f'Getting all the listing in the page for URL: {url}')
        listings = by_cat_soup.find_all("a", class_=ITEM_CLASS)
        logging.info(f'Iterating each listing to get the `href` and `title`')
        for listing in listings:
            item_url = self.get_href(listing)
            dc = {
                "url": f"{URL}{item_url}",
            }
            logging.info(f'Appending data extracted to listing list.')
            self.listing_list.append(dc)

    def scrape_category_data(self, url):
        global tot_page
        by_cat = self.get_request_data(req_url=url)
        cat_soup = self.get_soup_data(by_cat)
        pages = cat_soup.find_all("a", class_=LP_CLASS)
        logging.info(f'Getting total number of pages')
        try:
            if len(pages) > 2:
                tot_page = int(pages[2].getText())
            else:
                tot_page = int(pages[0].getText())
        except IndexError:
            sing_page = cat_soup.find("a", class_=ONE_CLASS)
            tot_page = int(sing_page.getText())

        dc = {
            "category": url,
            "total_page": tot_page
        }
        logging.info(f'Appending category: {url} and total page: {tot_page} in category page list')
        self.cat_page_list.append(dc)

    @staticmethod
    def generate_url(cat_list):
        list_url = []
        for cat in cat_list:
            list_url.append(f"{URL}{cat}")
        return list_url

    def get_html_data(self):
        soup = self.get_soup_data(self.data)
        categories = soup.find_all("a", class_=CAT_CLASS)
        logging.info(f'Getting all categories in the page')
        for category in categories:
            logging.info(f'Extracting `href` from {category.getText()}')
            self.categories.append(category.get('href'))

        url_list = self.generate_url(self.categories)

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD) as executor:
            executor.map(self.scrape_category_data, url_list)

        logging.info(f'Generating request URL and appending it to URL List')
        for item in self.cat_page_list:
            total_page_count = item["total_page"]
            category = item["category"]
            for page_count in range(1, total_page_count + 1):
                url = f"{URL}{category}page/{page_count}/"
                logging.info(f'Appending {url} to url list')

                url_list.append(url)

        print(f"URL_LIST_COUNT: {len(url_list)}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD) as executor:
            executor.map(self.scrape_data, url_list)

        logging.info(f'Extraction Completed.')
