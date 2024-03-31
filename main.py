import requests
import re
import time
import csv
import random
from bs4 import BeautifulSoup


def get_wiki_text(soup: BeautifulSoup):
    """Extracts all text from a wiki's body."""
    body = soup.find(id="bodyContent")
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
    body = soup.find(id="bodyContent")
    links = body.find_all('a', href=True)

    wiki_links_list = []

    # Need to clean the links for only other wiki articles
    for link in links:
        # link here is a Tag class object and [] is the access operator
        if not link['href'].startswith("/wiki/"):
            continue

        # Considering skipping files, but some contain useful things
        temp = link['href'].split('/')[2]

        if temp.startswith("File:", 0, 5):
            continue

        elif temp.startswith("Category:", 0, 8):
            continue
        
        elif temp.startswith('User:', 0, 5):
            continue
        
        wiki_links_list.append(link['href'])
    
    # Convert to a set to remove duplicates, hopefully avoiding unecessary
    unique_wiki_set = set(wiki_links_list)
    return list(unique_wiki_set)


def get_article(article_link):
    response = requests.get(url=f"https://en.wikipedia.org/{article_link}")
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def build_wiki_graph():
    """Fills up to_be_scraped queue with wiki articles."""
    # planned to keep track of origin article and all linked articles to create a graph
    to_be_scraped = ["/wiki/Dune_(novel)"]

    while to_be_scraped:
        soup = get_article(to_be_scraped[0])
        title = get_wiki_title(soup)
        text = get_wiki_text(soup)
        text = clean_text(text)
        to_be_scraped.extend(get_links_from_article(soup))

        wiki_data_entry = [(title, text)]

        time.sleep(0.5)
        print(f"Visting... {title}")

        with open("data.csv", mode='a', newline='\n', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(wiki_data_entry)

        to_be_scraped.pop(0)

def clean_text(text):
    """Prepares text for usage in an inverted index."""
    text = re.sub (r"[^a-zA-Z0-9 ]+", "", text)
    text = text.casefold()

    return text


if __name__ == "__main__":
    start_time = time.time()
    build_wiki_graph()
    end_time = time.time()

    print("Elapsed time:", end_time - start_time, "seconds")