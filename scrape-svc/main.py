# main.py

import os
from flask import Flask, send_file, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary  # Adds chromedriver binary to path
import json
import logging
from google.cloud import bigquery


app = Flask(__name__)

# The following options are required to make headless Chrome
# work in a Docker container
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")
# Initialize a new browser
browser = webdriver.Chrome(chrome_options=chrome_options)
base_url = "https://fr.wikipedia.org/w/index.php?fulltext=1&search="

# Initialize BQ client
PROJECT_ID = os.getenv('GCP_PROJECT')
BQ_DATASET = 'meae_dataset'
BQ_TABLE = 'meae_wsreqs_table'
BQ = bigquery.Client()
table_id = BQ.dataset(BQ_DATASET).table(BQ_TABLE)

def add_to_db(search, res):
    row = [
        {u"search": str(search), u"res": int(res)}
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

@app.route("/stroccurences", methods=["POST"])
def stroccurences():
    request_data = request.get_json()
    if request_data:
        #if 'calling_task' in request_data:
        #    calling_task = request_data['calling_task']
        #else:
        #    calling_task = "unspecified"
        if 'query' in request_data:
            query = request_data['query']
            req = base_url + query
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
                    print("Weird Error: query: " + query + " - No res found or not found!")
                    pass
                else:
                    nbres = "0"
                    noresult = False
            if noresult == False:
                error = add_to_db(query, nbres)
                if error == 0:
                    print("Success: query: " + query + " - Res found and inserted in BQ!")
                    return nbres, 200
                else:
                    print("Error: query: " + query + "Res found but Not Inserted in BQ!")
                    return "Res found but Not Inserted in BQ\n", 404
        else:
            print("Error: no query string in request data!") 
            return "no query in request data\n", 402
    else:
        print("Error: no request data!")
        return "no request data\n", 401


'''
    browser.get(req)
    try:
        res = browser.find_element_by_class_name('results-info')
        return res.get_attribute("data-mw-num-results-total")
    except:
        browser.find_element_by_class_name('mw-search-nonefound')
        return 0
'''
'''
            query = request_data['query']
            req = base_url + query
            browser.get(req)
            res = browser.find_elements_by_class_name('results-info')
            if len(res) > 0:
                nbres = int(res[0].get_attribute("data-mw-num-results-total"))
            else:
                if browser.find_element_by_class_name('mw-search-nonefound'):
                    nbres = 0
                else:
                    print("Weird Error Task: " + calling_task + " query: " + query + " no res found or not found!")
                    nbres = 0
            error = add_to_db(query, nbres)
            if error == 0:
                print()
                return str(nbres), 200
            else:
                print("Error Task: " + calling_task + " query: " + query + "Res found but Not Inserted in BQ!")
                return "Res found but Not Inserted in BQ\n", 404
'''
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))