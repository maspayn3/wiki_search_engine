# Wikipedia Based Search Engine + Wikipedia Scraper
## Wikipedia Scraper:
Usage: `$ python3 wiki_scraper.py -r -c -s {STARTING_SEARCH}`  
    -r: [OPTIONAL] randomizes wiki selection in set of wikis to be scraped  
    -c: [OPTIONAL] cleans the text of any non-alphanumerics, case sensitivity and common stopwords  
    -s [/wiki/{starting_wiki}]: [OPTIONAL] choose a starting wiki for scraper to use, default is Dune_(novel), /wiki/ must be included and starting_wiki must match URL exactly  

Description: Uses starting wiki as a launch point to collect all the text and links to other wiki articles found in the starting wiki. Then all the connected wiki articles will be scraped for text and links as well, leading to a cycle of scraping wiki articles.

Questionable implementation: To counteract possibly visited the same article twice, after every script run, upon a keyboard interrupt (CTRL + C), a database is populated in /var/wiki.sqlite3 with every wiki page scraped in this script run. Once the script runs again, it will check for this database and bring the list of visited articles into memory for this run.  

!!! MUST RUN `$ ./bin/wikidb` create to initialize database before any script runs !!!  

Use `$ chmod +x /bin/wikidb` to add executable bit to db script

#### TODO: speed up search with multi-threading

## Wikipedia Search Engine:
### Hosted at: 
Uses Hadoop to create an inverted index. Which is used by a Flask program and HTML/CSS frontend to replicate a small scale search engine
#### TODO: implement frontend
