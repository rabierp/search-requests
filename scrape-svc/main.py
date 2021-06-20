# main.py

import os
from flask import Flask, send_file, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary  # Adds chromedriver binary to path
import json
import re
import logging as log
import google.cloud.logging
from google.cloud import bigquery
import urllib.parse


app = Flask(__name__)

# The following options are required to make headless Chrome
# work in a Docker container
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1024,768")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--incognito")
# Initialize a new browser
browser = webdriver.Chrome(chrome_options=chrome_options)
wbase_url = "https://fr.wikipedia.org/w/index.php?fulltext=1&search="
gbase_url = "https://www.google.com/search?hl=fr&q="

# Initialize BQ client
PROJECT_ID = os.getenv('GCP_PROJECT')
BQ_DATASET = 'meae_dataset'
BQ_TABLE = 'meae_wsreqs_table'
BQ = bigquery.Client()
table_id = BQ.dataset(BQ_DATASET).table(BQ_TABLE)

# init logging
logclient = google.cloud.logging.Client()
logclient.get_default_handler()
logclient.setup_logging()

# compile regexp for results extraction
extract = re.compile('Environ ([\d\s]+)&nbsp')

def add_to_db(lexique, categorie, res):
    row = [
        {u"lexique": str(lexique), u"categorie": str(categorie), u"res": int(res)}
    ]

    errors = BQ.insert_rows_json(
        table_id, json_rows=row, row_ids=[None] * len(row)
    )  # Make an API request.
    if errors == []:
        return 0
    else:
        return 1

@app.route("/")
def hello_world():
    browser.get("https://google.com")
    file_name = 'test.png'
    browser.save_screenshot(file_name)
    return send_file(file_name)

@app.route("/gstroccurences", methods=["POST"])
def gstroccurences():
    request_data = request.get_json()
    if request_data:
        if 'query' in request_data:
            search_string = request_data['query']
            lex = request_data['lexique']
            cat = request_data['categorie']
            log.info("received request for string: " + search_string + " = lex: " + lex + " + cat: " + cat)
            query = urllib.parse.quote_plus(search_string)
            req = gbase_url + query
            log.info("Scraping URL: " + req)
            browser.get(req)
            file_name = 'test.png'
            browser.save_screenshot(file_name)
            try:
                button = browser.find_element_by_id('L2AGLb')
            except NoSuchElementException:
                log.info("Exception: query: " + query + " - cannot find button")
    
            try:
                button.click()
            except:
                log.info("Exception: query: " + query + " - cannot click")
    
            try:
                res = browser.find_element_by_id('result-stats')
            except:
                log.info("Exception: query: " + query + " - cannot find result-stats")

            try:
                nbres_sentence = res.get_attribute("innerHTML")
            except:
                nbres_sentence = None
                log.info("Exception: query: " + query + " - Cannot get inner HTML")
    
            try:
                nbres_numonly = extract.findall(nbres_sentence)
            except:
                print("Exception: Cannot Extract numbers")

            if nbres_numonly:
                nbres = "".join(nbres_numonly[0].split())
            else:
                nbres = "0"

            nbresint = int(nbres)

            error = add_to_db(lex, cat, nbresint)
            if error == 0:
                log.info("Success: query: " + query + " - Res inserted in BQ!")
                return nbres, 200
            else:
                log.error("Error: query: " + query + "Res Not Inserted in BQ!")
                return "Res Not Inserted in BQ\n", 404
        else:
            log.error("Error: no query string in request data!") 
            return "no query in request data\n", 402
    else:
        log.error("Error: no request data!")
        return "no request data\n", 401
    
@app.route("/stroccurences", methods=["POST"])
def stroccurences():
    request_data = request.get_json()
    if request_data:
        if 'query' in request_data:
            search_string = request_data['query']
            lex = request_data['lexique']
            cat = request_data['categorie']
            log.info("received request for string: " + search_string + " = lex: " + lex + " + cat: " + cat)
            query = urllib.parse.quote_plus(search_string)
            req = base_url + query
            log.info("Scraping URL: " + req)
            browser.get(req)
            noresult = False
            try:
                res = browser.find_element_by_class_name('results-info')
            except NoSuchElementException:
                noresult = True
                pass
            else:
                nbres = res.get_attribute("data-mw-num-results-total")
            if noresult:
                try:
                    browser.find_element_by_class_name('mw-search-nonefound')
                except NoSuchElementException:
                    noresult = True
                    log.warning("Weird Error: query: " + query + " - No res found or not found!")
                    pass
                else:
                    nbres = "0"
                    noresult = False
            if noresult == False:
                error = add_to_db(lex, cat, nbres)
                if error == 0:
                    log.info("Success: query: " + query + " - Res found and inserted in BQ!")
                    return nbres, 200
                else:
                    log.error("Error: query: " + query + "Res found but Not Inserted in BQ!")
                    return "Res found but Not Inserted in BQ\n", 404
        else:
            log.error("Error: no query string in request data!") 
            return "no query in request data\n", 402
    else:
        log.error("Error: no request data!")
        return "no request data\n", 401


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
