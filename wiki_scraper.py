import argparse
import requests
import re
import time
import csv
import random
import sqlite3
from bs4 import BeautifulSoup

import database

parser = argparse.ArgumentParser()

# -r -s INITIAL_WIKI
parser.add_argument("-r", '--randomize_search', action='store_true')
parser.add_argument('-s', '--search', action='store')

args = parser.parse_args()

def get_wiki_text(soup: BeautifulSoup):
    """Extracts body of text from a wikipedia article."""
    body = soup.find(id='bodyContent')
    unclean_text = body.find_all(['p', 'h2'])

    final_text = []

    pattern = r'\[[^\]]*\]'
    compiled_pattern = re.compile(pattern)
    for text in unclean_text:
        # clean text of [] and \n
        cleaned_text = compiled_pattern.sub('', text.get_text()).rstrip()
        cleaned_text = cleaned_text.replace("\n", '')
        final_text.append(cleaned_text)
        
    return ''.join(final_text)


def get_wiki_title(soup: BeautifulSoup):
    title = soup.find(id="firstHeading").get_text()
    return title


def get_links_from_article(soup: BeautifulSoup):
    """Collects all links to other wikipedia articles from a single wiki article."""
    body = soup.find(id="bodyContent")
    links = body.find_all('a', href=True)

    wiki_links_list = []
    wiki_links_set = set()

    # need to clean the links for only other wiki articles
    for link in links:
        # link here is a Tag class object and [] is the access operator
        if not link['href'].startswith("/wiki/"):
            continue

        # Considering skipping files, but some contain useful things
        temp = link['href'].split('/')[2]

        if temp.startswith("File:"):
            continue

        elif temp.startswith("Category:"):
            continue
        
        elif temp.startswith("User:"):
            continue
        
        elif temp.startswith("Special:BookSources"):
            continue

        elif temp.startswith("Editing"):
            continue

        elif temp.startswith("Template"):
            continue

        wiki_links_list.append(link['href'])
    wiki_links_set.update(wiki_links_list)

    return wiki_links_set


def get_article(article_link):
    response = requests.get(url=f"https://en.wikipedia.org/{article_link}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    
    else:
        print(f"Status code: {response.status_code}")
        return None


def download_wiki_text(randomize_list: bool):
    """Scapes initial wiki article for text and links to branch and build data.csv."""
    # planned to keep track of origin article and all 
    # linked articles to create a graph
    
    # initialize set pair meant to track previously visited wikis
    # and wikis visited this script run
    prev_visited_wikis = set(get_visited_wikis())
    curr_visited_wiki_names = set()
    curr_visited_wikis = []

    if args.search == None:
        # to_be_scraped = set(['/wiki/Dune_(novel)'])
        to_be_scraped = set(['/wiki/Isaac_Asimov'])
    
    else:
        to_be_scraped = set([args.search])

    token = get_wiki_token()

    try:
        while to_be_scraped:
            if randomize_list is True:
                random_wiki = random.choice(list(to_be_scraped))
                soup = get_article(random_wiki)
                to_be_scraped.remove(random_wiki)

            else:
                soup = get_article(to_be_scraped.pop())

            if soup == None:
                continue

            # check if current wiki has already been scraped
            title = get_wiki_title(soup)
            if title in curr_visited_wiki_names or title in prev_visited_wikis:
                print(f"Already visited {title}")
                print(f"Trying again...")
                continue
            
            text = get_wiki_text(soup)
            store_wiki_summary(token, text)

            to_be_scraped.update(get_links_from_article(soup))
            wiki_data_entry = [(token, title, text)]

            print(f"Visting... {title}")
            with open("data.csv", mode='a', newline='\n', encoding='utf-8') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_ALL)
                writer.writerows(wiki_data_entry)

            curr_visited_wikis.append((token, title))
            curr_visited_wiki_names.add(title)
            token += 1

            # time.sleep(5)

    except KeyboardInterrupt:
        print("Ending search")
        store_visited_wikis(curr_visited_wikis)


def get_wiki_token():
    con = database.get_db()
    cur = con.execute(
        "SELECT doc_id FROM visited_wikis "
        "ORDER BY doc_id DESC LIMIT 1"
    )
    token = cur.fetchone()

    if token == None:
        return 0

    return token[0] + 1


def store_wiki_summary(wiki_id, text):
    summary = text[:200]

    con = database.get_db()
    cur = con.execute(
        "INSERT INTO wiki_summaries (doc_id, summary) "
        "VALUES (?, ?) ",
        (wiki_id, summary, )
    )
    con.commit()


def store_visited_wikis(visited_wikis: set):
    """Stores ids and names of all visited wikis during execution."""

    # Establish database connection
    con = database.get_db()
    for wiki in visited_wikis:
        cur = con.execute(
            "INSERT INTO visited_wikis (doc_id, title) "
            "VALUES (?, ?) ",
            (wiki[0], wiki[1], )
        )
    con.commit()
    con.close()


def get_visited_wikis():
    """Queries database for all previously visited wikis."""    
    visited_wikis = []
    con = database.get_db()
    cur = con.cursor()

    cur.execute(
        "SELECT title "
        "FROM visited_wikis"
    )
    temp = cur.fetchall()

    for title in temp:
        visited_wikis.append(title[0])

    return visited_wikis


if __name__ == "__main__":
    print("Press ctrl + c to end search")

    start_time = time.time()
    download_wiki_text(randomize_list=args.randomize_search)
    end_time = time.time()

    print("Elapsed time:", end_time - start_time, "seconds")