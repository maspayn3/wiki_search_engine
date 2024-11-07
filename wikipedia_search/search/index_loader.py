"""Load and manage inverted index."""
import os

class SearchIndex:
    def __init__(self):
        self.inverted_index = {}
        self.stopwords = set()

    def load_index(self, index_path, stopwords_path):
        """Load three-part inverted index."""

        with open(stopwords_path, mode='r', encoding='utf-8') as file:
            self.stopwords = set(line.strip() for line in file)

        for i in range(3):
            part = os.path.join(index_path, f'part-0000{i}')
            self._load_index_part(part)

    def _load_index_part(self, file_path):
        """Load single part of inverted index."""
        with open(file_path, mode='r', encoding='utf-8') as file:
            for line in file:
                data = line.split()
                if len(data) < 2:
                    continue

                word = data[0]
                idf = float(data[1])

                if word not in self.inverted_index:
                    self.inverted_index[word] = {
                        "idf": idf, 
                        "documents": []
                    }

                # process document entries, found after idf and word hence + 2
                for i in range(2, len(data), 3):
                    if i + 2 >= len(data):
                        break
                
                    doc_entry = {
                        "doc_id": data[i],
                        "tfk": float(data[i + 1]),
                        "norm_factor": float(data[i + 2])
                    }
                    self.inverted_index[word]["documents"].append(doc_entry)

search_index = SearchIndex()

def init_app(app):
    """Initialize search index with application config."""
    search_index.load_index(
        app.config['INDEX_PATH'],
        app.config['STOPWORDS_PATH']
    )