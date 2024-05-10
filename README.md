# Wikipedia Based Search Engine + Wikipedia Scraper
## Wikipedia Scraper
Usage: `$ python3 wiki_scraper.py -r -c -s {STARTING_SEARCH}`  
    `-r, --randomize`: [OPTIONAL] randomizes wiki selection in set of wikis to be scraped   
    `-s, --search [/wiki/{starting_wiki}]`: [OPTIONAL] choose a starting wiki for scraper to use, default is Dune_(novel), /wiki/ must be included and starting_wiki must match URL exactly  

Output: Wiki_id, Title, Body of text -> data.csv  

Description: Uses starting wiki as a launch point to collect all the text and links to other wiki articles found in the starting wiki. Then all the connected wiki articles will be scraped for text and links as well, leading to a cycle of scraping wiki articles.

Questionable implementation: To counteract possibly visited the same article twice, after every script run, upon a keyboard interrupt (CTRL + C), a database is populated in /var/wiki.sqlite3 with every wiki page scraped in this script run. Once the script runs again, it will check for this database and bring the list of visited articles into memory for this run.  

!!! MUST RUN `$ ./bin/wikidb create` to initialize database before any script runs !!!  

Use `$ chmod +x /bin/wikidb` to add executable bit to db script

## sqlite3 Database  
  Use `$ ./bin/wiki (create|destroy|reset)` to perform actions related to the database
  !!! MUST use wikidb create prior to running web scraping script !!!  
    
Database has two tables, visited_wikis and wiki_summaries to store both the titles and 
summaries of the scraped wiki articles.  

Script will automatically keep track of visited wikis and store them in this database so long as a keyboard interrupt CTRL + C is used to terminate the program

#### TODO: speed up search with multi-threading

## Wikipedia Search Engine
### Hosted at: 
Uses Hadoop to create an inverted index. Which is used by a Flask program and HTML/CSS frontend to replicate a small scale search engine
#### TODO: implement frontend
