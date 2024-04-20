import argparse
import requests
import re
import time
import csv
import random
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()

# -r -c -s INITIAL_WIKI
parser.add_argument("-r", '--randomize_search', action='store_true')
parser.add_argument('-c', '--clean_text', action='store_true')
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

        # elif temp.startswith("Category:"):
        #     continue
        
        elif temp.startswith("User:"):
            continue
        
        elif temp.startswith("Special:BookSources"):
            continue

        elif temp.startswith("Editing"):
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
        exit(1)


def download_wiki_text(randomize_list: bool, clean_text_flag: bool):
    """Scapes initial wiki article for text and links to branch and build data.csv."""
    # planned to keep track of origin article and all 
    # linked articles to create a graph

    if args.search == None:
        to_be_scraped = set(['/wiki/Category:Dark matter'])
    
    else:
        to_be_scraped = set([args.search])
    with open('wiki_num_token.txt', mode='r') as file:
        token = int(file.readline())

    try:
        while to_be_scraped:
            if randomize_list is True:
                soup = get_article(random.choice(list(to_be_scraped)))
            else:
                soup = get_article(to_be_scraped.pop())

            title = get_wiki_title(soup)
            text = get_wiki_text(soup)

            # clean text for usage in inverted index
            if clean_text_flag is True:
                text = clean_text(text)

            to_be_scraped.update(get_links_from_article(soup))
            wiki_data_entry = [(token, title, text)]

            print(f"Visting... {title}")
            with open("data.csv", mode='a', newline='\n', encoding='utf-8') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_ALL)
                writer.writerows(wiki_data_entry)

                token += 1

            # time.sleep(5)

    except KeyboardInterrupt:
        print("Ending search")

        with open("wiki_num_token.txt", mode='w') as file:
            file.write(str(token))


def clean_text(text):
    """Prepares text for usage in an inverted index."""
    # removes non alphanumerics and case sensitivity
    text = re.sub (r"[^a-zA-Z0-9 ]+", "", text)
    text = text.casefold()

    # split text into list of whitespace-deliminated words
    text = text.split()

    stop_words = []
    with open("stop_words.txt", mode='r') as file:
        # generator expression, reads file line by line and 
        # does not read entire file into memory
        for word in (line.strip() for line in file):
            stop_words.append(word)

    for word in text:
        if word in stop_words:
            text.remove(word)
            print(f"removed {word}")

    return text


if __name__ == "__main__":
    print("Press ctrl + c to end search")

    start_time = time.time()
    print(args.randomize_search, args.clean_text, args.search)
    download_wiki_text(randomize_list=args.randomize_search, clean_text_flag=args.clean_text)
    end_time = time.time()

    print("Elapsed time:", end_time - start_time, "seconds")