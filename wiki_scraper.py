import argparse
import requests
import re
import time
import csv
import random
import sqlite3
from bs4 import BeautifulSoup
from collections import deque
from queue import Empty, Queue
import threading
from concurrent.futures import ThreadPoolExecutor

import database

class WikiScraper:
    def __init__(self, db_path: str, max_workers: int = 25):
        self.db_path = db_path
        self.seen_links = set()
        self.queued_links = set()
        self.links_queue = Queue()
        self.seen_titles = set()
        self.max_workers = max_workers

        # Locks for separate resources to reduce blocking
        self.article_lock = threading.Lock()
        self.rate_limit_lock = threading.Lock()
        self.file_lock = threading.Lock()
        self.title_lock = threading.Lock()

        self.request_times = deque(maxlen=50)
        self.min_delay = 0.05

        self.headers = {
            'User-Agent': 'WikipediaSearchBot/1.0 Educational Project',
            'Accept': 'text/html,application/xhtml+xml'
        }

    def _rate_limit(self):
        """Thread-safe rate limiting."""
        sleep_duration = 0
        with self.rate_limit_lock:
            now = time.time()
            if len(self.request_times) > 0:
                elapsed = now - self.request_times[-1]
                if elapsed < 0.02:
                    sleep_duration = 0.02 - elapsed
            self.request_times.append(now)

        if sleep_duration > 0:
            time.sleep(sleep_duration)
            
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

    def store_article(self, title, url, content, summary) -> bool:
        """Store article data in var/wiki.sqlite3."""
        with database.get_db() as conn:
            try:
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")

                cur = conn.execute(
                    "SELECT 1 FROM documents WHERE url = ?", (url,)
                )
                if cur.fetchone():
                    conn.rollback()
                    return False

                # store document metadata
                cur = conn.execute(
                    "INSERT INTO documents (title, url, summary) "
                    "VALUES (?, ?, ?)", (title, url, summary)
                )

                doc_id = cur.lastrowid

                # store document body text
                conn.execute(
                    "INSERT INTO document_content (doc_id, content) "
                    "VALUES (?, ?)", (doc_id, content)
                )
                conn.commit()
                return doc_id
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

            base_url = href.split('#')[0]
            page_name = base_url.split('/wiki/', 1)[1]
            if any(page_name.startswith(prefix) for prefix in skip_prefixes):
                continue
            
            links.append(href)

        return links

    def load_visited_titles(self):
        with database.get_db() as conn:
            cur = conn.execute(
                "SELECT url FROM documents"
            )
            results = cur.fetchall()
            self.seen_links = {row['url'] for row in results}
            self.seen_titles = {row['url'] for row in results}

    def _process_article(self, url: str) -> bool:
        """Process single article."""
        with self.article_lock:
            if url in self.seen_links:
                return False    
            self.seen_links.add(url)
        
        try:
            soup = self.get_article(url)
            if not soup:
                return False
        
            title = soup.find(id="firstHeading").get_text()
            if not title:
                return False
            
            with self.title_lock:
                if title in self.seen_titles:
                    print(f"Skipping dup article: {title}")
                    return False
                self.seen_titles.add(title)

            content, summary = self.get_wiki_text(soup)
            if not content:
                return False
            
            with self.article_lock:
                doc_id = self.store_article(title, url, content, summary)
                if not doc_id:
                    return False

            new_links = self.get_links_from_article(soup)
            
            with self.article_lock:
                unseen_links = [link for link in new_links
                                if link not in self.seen_links
                                and link not in self.queued_links]

                for link in unseen_links:
                    self.links_queue.put(link)
                    self.queued_links.add(link)

            print(f"Visiting... {title}")

            with self.file_lock:
                with open("data.csv", mode='a', newline='\n', encoding='utf-8') as file:
                    wiki_data_entry = [(doc_id, title, content)]
                    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
                    writer.writerows(wiki_data_entry)
            return True

        except Exception as e:
            print(f"Error processing article {url}: {e}")
        return False

    def scrape_wikipedia(self,start_url: str="/wiki/Dune_(novel)"):
        """Scapes initial wiki article for text and links to branch and build data.csv."""
        # planned to keep track of origin article and all 
        # linked articles to create a graph
        
        # initialize set pair meant to track previously visited wikis
        # and wikis visited this script run
        self.load_visited_titles()
        self.links_queue.put(start_url)
        self.queued_links.add(start_url)
        articles_scraped = 0
        running = True

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = set()

                while running:
                    if self.links_queue.empty() and not futures:
                        break

                    # process completed futures before getting new work
                    done = {f for f in futures if f.done()}
                    for f in done:
                        try:
                            if f.result():
                                articles_scraped += 1
                        except Exception as e:
                            print(f"Error in future: {e}")
                        futures.remove(f)

                    if self.links_queue.empty():
                        continue

                    try:
                        curr_wiki = self.links_queue.get(block=False)
                        if curr_wiki in self.seen_links:
                            continue
                        future = executor.submit(self._process_article, curr_wiki)
                        futures.add(future)
                    except Exception as e:
                        continue

        except KeyboardInterrupt:
            running = False

            for future in futures: 
                future.cancel()

            while not self.links_queue.empty():
                try:
                    self.links_queue.get_nowait()
                except Empty:
                    break

            executor._threads.clear()
            executor._shutdown = True
            executor._broken = True

            print("\nScraping interrupted by user")
            
        except Exception as e:
            print(f"\nError during scraping: {e}")
        finally:
            print(f"\nScraped {articles_scraped} articles")
    
    def get_article(self, url):
        self._rate_limit()
        try:
            response = requests.get(f"https://en.wikipedia.org{url}",
                                    headers=self.headers)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            print(f"Failed to fetch {url}: {response.status_code}")
            return None
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}")
            return None
    
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
        f"/wiki/{args.search}"
    )
    end_time = time.time()

    print("Elapsed time:", end_time - start_time, "seconds")