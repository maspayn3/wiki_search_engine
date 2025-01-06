# Wikipedia Search Engine

A full-stack application that scrapes Wikipedia articles, builds a search index using MapReduce, and provides a modern search interface. Features include TF-IDF ranking, title boosting, and a React-based UI.

## Features

- **Wikipedia Scraper**: Multi-threaded crawler that collects article text and metadata
- **Search Engine**: Vector space model with cosine similarity scoring
- **MapReduce Pipeline**: Distributed index building using Hadoop
- **Modern UI**: React-based frontend with auto-complete and real-time search
- **Connection Pooling**: Optimized database access
- **Performance Metrics**: Built-in tracking of search and system performance

## Demo

![Search Engine Demo](docs/assets/demo.gif)

## Prerequisites

- Python 3.11+
- Node.js 20+
- Hadoop 3.4.0 (for index building)
- Java 8 or 11 (required by Hadoop)
- SQLite3

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd wikipedia_scraper
```

2. Set up Python environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

3. Initialize the database:
```bash
chmod +x bin/wikidb
./bin/wikidb create
```

4. Install frontend dependencies:
```bash
cd client
npm install
```

5. Start the application:
```bash
# Terminal 1 - Backend
python run.py

# Terminal 2 - Frontend
cd client
npm run dev
```

The application will be available at http://localhost:3000

## Data Collection and Indexing

### Prerequisites

- Hadoop 3.4.0
- Java 8 or 11
- Python 3.11+

### 1. Configure Hadoop

1. Verify your Hadoop installation:
```bash
hadoop version  # Should show 3.4.0
hdfs dfs -ls /  # Should show root directory
```

2. Set up HDFS directories:
```bash
# Create required directories
hdfs dfs -mkdir -p /user/$USER/inverted_index/input
hdfs dfs -mkdir -p /user/$USER/inverted_index/output
```

### 2. Collect Wikipedia Articles

1. Initialize the SQLite database:
```bash
./bin/wikidb create
```

2. Run the multi-threaded scraper:
```bash
# Basic usage (starts from Dune article)
python wiki_scraper.py

# Start from a specific article
python wiki_scraper.py -s "Computer_science"
```

The scraper will generate:
- `data.csv`: Contains document IDs, titles, and article contents
- SQLite database (`var/wiki.sqlite3`): Stores article metadata and content
- Console output showing progress and article count

The scraper can be stopped safely at any time using Ctrl+C. It will resume from where it left off on the next run.

### 3. Build the Search Index

1. Prepare the input data:
```bash
# Copy data to HDFS
hdfs dfs -put data.csv /user/$USER/inverted_index/input/

# Verify the data is in HDFS
hdfs dfs -ls /user/$USER/inverted_index/input
```

2. Run the MapReduce pipeline:
```bash
cd inverted_index
./pipeline.sh
```

The pipeline runs several MapReduce jobs to:
- Clean and tokenize the text
- Remove stopwords
- Calculate term frequencies
- Compute TF-IDF scores
- Build the final inverted index

3. Export the results:
```bash
# Create data directory if it doesn't exist
mkdir -p ../data

# Copy the three index parts
hdfs dfs -get /user/$USER/inverted_index/output5/part-0000* ../data/

# Copy stopwords
cp inverted_index/stopwords.txt ../data/
```

## Components

### Web Scraper

The scraper is multi-threaded and features:
- Rate limiting to respect Wikipedia's servers
- Duplicate detection
- Proper error handling
- Automatic resumption from previous runs

### Search Index Building

The search index uses a 6-stage MapReduce pipeline:
1. Document parsing and term extraction
2. Stopword removal
3. Term frequency calculation
4. Document frequency aggregation
5. TF-IDF computation
6. Final index partitioning

### Server Management

Control the search server instances:

```bash
# Start server (single instance)
./bin/server start

# Start multiple instances
./bin/server start --multi

# Check server status
./bin/server status

# Stop all instances
./bin/server stop
```

## Project Structure

```
wikipedia_scraper/
├── client/                 # React frontend
├── wikipedia_search/       # Flask backend
│   ├── api/               # API endpoints
│   ├── search/            # Search engine implementation
│   └── views/             # Web routes
├── data/                  # Index files
├── inverted_index/        # MapReduce implementation
└── var/                   # Runtime data (SQLite DB, logs)
```

## API Endpoints

- `GET /api/v1/hits/?q=<query>&k=<num_results>`: Search endpoint
- `GET /api/v1/stats`: Index statistics
- `GET /api/v1/word/<word>/`: Individual word lookup

## Performance Considerations

- Multi-threaded scraping with configurable worker count
- Connection pooling enabled by default (pool size: 10)
- Search results are cached using LRU cache
- The frontend implements debounced search for better performance
- Multiple server instances can be run to handle different index partitions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Flask and React
- Uses shadcn/ui components