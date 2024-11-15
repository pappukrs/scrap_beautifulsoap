import requests
from bs4 import BeautifulSoup
import schedule
import time
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


POST_URL = "https://script.google.com/macros/s/AKfycbyhuR4yYKO7uCZpLxX5xrAojBlAa83vhnDrtFo85BD8oJQX9ugkN2N23Snqu48uCbvcBQ/exec"


current_page = 2
base_url = "http://quotes.toscrape.com/page/"

def scrape_and_post():
    global current_page

    logging.info(f"Starting the scraping process for page {current_page}...")

    url = f"{base_url}{current_page}/"
    try:
        # Fetch the webpage
        logging.info(f"Sending GET request to {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            logging.info(f"Successfully fetched page {current_page}.")
        elif response.status_code == 404:
            logging.info(f"Reached the last page. Stopping the scraper.")
            schedule.clear()  # Stop further scheduling
            return
        else:
            logging.error(f"Failed to fetch page {current_page}. Status code: {response.status_code}")
            return

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info(f"Parsed the content of page {current_page}.")

        # Find all quotes
        quotes = soup.find_all('div', class_='quote')
        if not quotes:
            logging.info(f"No quotes found on page {current_page}. Stopping the scraper.")
            schedule.clear()  # Stop further scheduling
            return

        logging.info(f"Found {len(quotes)} quotes on page {current_page}.")

        # Prepare data for Google Sheets API
        data_to_post = {"quotes": []}
        for quote in quotes:
            text = quote.find('span', class_='text').text.strip()
            author = quote.find('small', class_='author').text.strip()
            data_to_post["quotes"].append({"quote": text, "author": author})
            logging.info(f"Prepared quote: '{text}' by {author}")

        # Send data to Google Sheets API
        logging.info("Sending data to Google Sheets API...")
        post_response = requests.post(POST_URL, json=data_to_post)

        if post_response.status_code == 200:
            logging.info("Data successfully inserted into Google Sheets.")
        else:
            logging.error(f"Failed to insert data. API response: {post_response.status_code} - {post_response.text}")

        # Increment the page number for the next run
        current_page += 1
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Schedule the scraper to run every 5 minutes
schedule.every(5).minutes.do(scrape_and_post)

if __name__ == "__main__":
    logging.info("Starting the scheduled task...")
    scrape_and_post()  
    while True:
        schedule.run_pending()
        time.sleep(1)
