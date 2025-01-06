# Wikipedia Search Engine

A full-stack application that scrapes Wikipedia articles, builds a search index using MapReduce, and provides a modern search interface. Features include TF-IDF ranking, title boosting, and a React-based UI.

## Demo

![Search Engine Demo](docs/assets/demo.gif)

## Features

- **Wikipedia Scraper**: Recursive crawler that collects article text and metadata
- **Search Engine**: Vector space model with cosine similarity scoring
- **MapReduce Pipeline**: Distributed index building using Hadoop
- **Modern UI**: React-based frontend with auto-complete and real-time search
- **Connection Pooling**: Optimized database access
- **Performance Metrics**: Built-in tracking of search and system performance

## Prerequisites

- Python 3.11+
- Node.js 20+
- Hadoop 3.4.0 (for index building)
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

## Components

### Web Scraper

The scraper collects Wikipedia articles starting from a seed article and following links recursively.

```bash
python wiki_scraper.py [-r] [-s STARTING_ARTICLE]

Options:
  -r, --randomize        Randomize article selection
  -s, --search ARTICLE   Starting article (default: Dune_(novel))
```

### Search Index Building

The search index is built using a MapReduce pipeline in Hadoop:

1. Set up Hadoop configuration:
```bash
# Verify Hadoop installation
hadoop version

# Start Hadoop services
start-all.sh
```

2. Run the indexing pipeline:
```bash
cd inverted_index
./pipeline.sh
```

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
└── var/                   # Runtime data
```

## API Endpoints

- `GET /api/v1/hits/?q=<query>&k=<num_results>`: Search endpoint
- `GET /api/v1/stats`: Index statistics
- `GET /api/v1/word/<word>/`: Individual word lookup


## Performance Considerations

- Connection pooling is enabled by default with a pool size of 10
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