import argparse
import requests
import re
import time
import csv
import random
import sqlite3
from bs4 import BeautifulSoup
from collections import deque

import database

class WikiScraper:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.seen_links = set()
        self.visited_titles = set()

    
    def get_wiki_text(self, soup: BeautifulSoup):
        """Extracts body of text from a wikipedia article."""
        body = soup.find(id='bodyContent')
        if not body:
            return "", ""
        
        found_text = body.find_all(['p', 'h2', 'h3'])

        final_text = []
        pattern = re.compile(r'\[[^\]]*\]')
        for text in found_text:
            # clean text of [] and \n
            element = text.get_text()
            cleaned_text = pattern.sub('', element)
            # Clean whitespace
            cleaned_text = ' '.join(cleaned_text.split())
            if cleaned_text:
                final_text.append(cleaned_text)

        full_text = ' '.join(final_text)
        summary = full_text[:250] if full_text else ""
        return full_text, summary

    def store_article(self, doc_id, title, url, content, summary) -> bool:
        """Store article data in var/wiki.sqlite3."""
        with database.get_db() as conn:
            try:
                # store document metadata
                conn.execute(
                    "INSERT INTO documents (doc_id, title, url, summary) "
                    "VALUES (?, ?, ?, ?)", (doc_id, title, url, summary)
                )

                # store document body text
                conn.execute(
                    "INSERT INTO document_content (doc_id, content) "
                    "VALUES (?, ?)", (doc_id, content)
                )
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error storing article: {e}")
                conn.rollback()
                return False

    def get_links_from_article(self, soup: BeautifulSoup):
        """Collects all links to other wikipedia articles from a single wiki article."""
        body = soup.find(id="bodyContent")
        if not body:
            return []
        
        skip_prefixes = {
            "File:", "Category:", "Help:", "Template:",
            "Wikipedia:", "Portal:", "Talk:", "Special:",
            "User:", "Special:BookSources", "Editing"
        }
        links = []
        for link in body.find_all('a', href=True):
            href = link['href']
            if not href.startswith("/wiki/"):
                continue

            page_name = href.split('/wiki/', 1)[1]
            if any(page_name.startswith(prefix) for prefix in skip_prefixes):
                continue
            
            links.append(href)

        return links

    def load_visited_titles(self):
        with database.get_db() as conn:
            cur = conn.execute(
                "SELECT title FROM documents"
            )
            self.visited_titles = {row['title'] for row in cur.fetchall()}

    def scrape_wikipedia(self,start_url: str="/wiki/Dune_(novel)", randomize: bool=False):
        """Scapes initial wiki article for text and links to branch and build data.csv."""
        # planned to keep track of origin article and all 
        # linked articles to create a graph
        
        # initialize set pair meant to track previously visited wikis
        # and wikis visited this script run
        self.load_visited_titles()
        to_be_scraped = deque([start_url])
        articles_scraped = 0
        token = self.get_wiki_token()

        try:
            while to_be_scraped:
                if randomize:
                    random_index = random.randint(0, len(to_be_scraped) - 1)
                    curr_wiki = to_be_scraped[random_index]
                    del to_be_scraped[random_index]

                else:
                    curr_wiki = to_be_scraped.popleft()

                soup = self.get_article(curr_wiki)

                if soup == None:
                    continue

                # check if current wiki has already been scraped
                title = soup.find(id="firstHeading").get_text()
                if title in self.visited_titles:
                    print(f"Skipping already visited: {title}")
                    print(f"Trying again...")
                    continue
                
                content, summary = self.get_wiki_text(soup)
                if not content:
                    continue
                
                if self.store_article(token, title, curr_wiki, content, summary):
                    # Store document content and metadata in wiki.sqlite 3 and data.csv
                    wiki_data_entry = [(token, title, content)]

                    token += 1
                    articles_scraped += 1

                    self.visited_titles.add(title)
                    new_links = self.get_links_from_article(soup)

                    to_be_scraped.extend(link for link in new_links
                                         if link not in self.seen_links)
                    self.seen_links.update(new_links)
                
                    print(f"Visting... {title}")
                    with open("data.csv", mode='a', newline='\n', encoding='utf-8') as file:
                        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
                        writer.writerows(wiki_data_entry)

                # politeness delay 
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nScraping interrupted by user")
        except Exception as e:
            print(f"\nError during scraping: {e}")
        finally:
            print(f"\nScraped {articles_scraped} articles")
    
    def get_article(self, url):
        try:
            response = requests.get(f"https://en.wikipedia.org{url}")
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            print(f"Failed to fetch {url}: {response.status_code}")
            return None
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}")
            return None

    def add_new_links(self, new_links, seen_links: set):
        unseen_links = [link for link in new_links if link not in seen_links]
        seen_links.update(new_links)

        return unseen_links

    def get_wiki_token(self):
        """Get next available document ID."""
        with database.get_db() as conn:
            cur = conn.execute(
                "SELECT MAX(doc_id) FROM documents "
                )
            max_id = cur.fetchone()[0]
        return (max_id or 0) + 1


parser = argparse.ArgumentParser()

# -r -s INITIAL_WIKI
parser.add_argument("-r", '--randomize', action='store_true')
parser.add_argument('-s', '--search', action='store')

args = parser.parse_args()


if __name__ == "__main__":
    print("Press ctrl + c to end search")

    scraper = WikiScraper("./var/wiki.sqlite3")

    if not args.search:
        args.search = "Dune_(novel)"

    start_time = time.time()
    scraper.scrape_wikipedia(
        f"/wiki/{args.search}",
        randomize=args.randomize,
    )
    end_time = time.time()

    print("Elapsed time:", end_time - start_time, "seconds")