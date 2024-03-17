import time

from bs4 import BeautifulSoup
import requests
import logging
import concurrent.futures

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

URL = "https://whop.com"
ITEM_CLASS = "hover:bg-whop-hover border-whop-stroke group flex cursor-pointer flex-col items-stretch gap-2 overflow-x-hidden border-0 border-b border-solid p-5 transition md:flex-row md:items-center md:gap-5 md:rounded-lg md:border-b-0 md:p-4"
ITEM_TITLE = "subtitle1 overflow-x-hidden text-ellipsis whitespace-nowrap"
CAT_CLASS = "subtitle3 text-whop-dark-gray hover:text-whop-off-black whitespace-nowrap py-3.5 transition"
LP_CLASS = "subtitle flex h-8 w-8 cursor-pointer select-none items-center justify-center rounded-md border-2 transition border-transparent hover:bg-whop-hover hover:border-whop-hover active:border-whop-hover-press active:bg-whop-hover-press"
ONE_CLASS = "subtitle flex h-8 w-8 cursor-pointer select-none items-center justify-center rounded-md border-2 transition border-black"
THREAD = 15


class WebScraper:
    def __init__(self):
        self.data = self.get_request_data(URL)
        self.listing_list = []
        self.categories = []
        self.cat_page_list = []
        self.gathered_info_list = []
        self.get_html_data()

    @staticmethod
    def get_request_data(req_url):
        success = False
        retries = 0
        while not success and retries < 3:
            try:
                response = requests.get(url=req_url)
                response.raise_for_status()
                logging.info(f'Generating response from get request: {req_url}')
                success = True
                return response.text
            except Exception as e:
                logging.error(f'Request Failed with Exception: {e}')
                logging.error(f'Retrying request...')
                time.sleep(10)
                retries += 1

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

    def scrape_info_in_page(self, url):
        pl_list = []
        it_list = []
        resp = self.get_request_data(req_url=url)
        soup = self.get_soup_data(resp)
        name = soup.find("div", class_="display3 text-whop-black").getText()
        genre = soup.find("div", class_="text-whop-dark-gray text-text3").getText()
        contact_info = soup.find_all("a", class_="text-whop-field-highlight flex cursor-pointer items-center gap-0.5")
        platform = soup.find_all("div", class_="text-whop-gray flex items-center gap-1.5")
        for pl in platform:
            pl_list.append(pl.getText())

        for it in contact_info:
            it_list.append(it.get("href"))

        res = {}
        for key in pl_list:
            for value in it_list:
                res[key] = value
                it_list.remove(value)
                break

        fin_dc = {
            "url": url,
            "name": name,
            "genre": genre,
            "cont": res
        }

        self.gathered_info_list.append(fin_dc)

    def merge_data(self):
        lst = []
        for url in self.listing_list:
            lst.append(url['url'])

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD) as executor:
            executor.map(self.scrape_info_in_page, lst)

    def get_html_data(self):
        page_url_list = []
        soup = self.get_soup_data(self.data)
        categories = soup.find_all("a", class_=CAT_CLASS)
        logging.info(f'Getting all categories in the page')
        for category in categories:
            logging.info(f'Extracting `href` from {category.getText()}')
            self.categories.append(category.get('href'))

        cat_url_list = self.generate_url(self.categories)
        for cat_url in cat_url_list:
            self.scrape_category_data(cat_url)

        logging.info(f'Generating request URL and appending it to URL List')
        for item in self.cat_page_list:
            total_page_count = item["total_page"]
            category = item["category"]
            for page_count in range(1, total_page_count + 1):
                page_url = f"{category}page/{page_count}/"
                logging.info(f'Appending {page_url} to url list')

                page_url_list.append(page_url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD) as executor:
            executor.map(self.scrape_data, page_url_list)

        logging.info(f'Extraction Completed.')
