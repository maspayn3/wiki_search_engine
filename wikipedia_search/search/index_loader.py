"""Load and manage inverted index."""
import os
import logging

class SearchIndex:
    def __init__(self):
        self.inverted_index = {}
        self.stopwords = set()
        self.doc_lengths = {}
        self.total_docs = 0
        self.on_index_loaded = None

        logging.basicConfig(
            filename='var/log/index_loader.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_index(self, index_path, stopwords_path):
        """
        Load three-part inverted index and stopwords.
        
        Args:
            index_path: Base path to index files
            stopwords_path: Path to stopwords file
        
        Raises:
            FileNotFoundError: If index or stopwords files not found
            ValueError: If index files are malformed
        """
        try:
            self._load_stopwords(stopwords_path)

            for i in range(3):
                part = os.path.join(index_path, f'part-0000{i}')
                if not os.path.exists(part):
                    raise FileNotFoundError(f"Index part not found: {part}")
                self._load_index_part(part)

            if self.on_index_loaded:
                self.on_index_loaded()

        except Exception as e:
            self.logger.error(f"Error loading index: {str(e)}")
            raise


    def _load_stopwords(self, stopwords_path):
        if not os.path.exists(stopwords_path):
            raise FileNotFoundError(f"Stopwords file not found: {stopwords_path}")
        
        with open(stopwords_path, mode='r', encoding='utf-8') as file:
            self.stopwords = {line.strip() for line in file}

        self.logger.info(f"Loaded {len(self.stopwords)} stopwords")


    def _load_index_part(self, file_path):
        """
        Load single part of inverted index.
        
        Args:
            file_path: Path to index part file
            
        Raises:
            ValueError: If index file data is malformed
        """
        with open(file_path, mode='r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                try:
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
                        
                        doc_id  = int(data[i])
                        tfk = float(data[i + 1])
                        norm_factor = float(data[i + 2])

                        doc_entry = {
                            "doc_id": doc_id,
                            "tfk": tfk,
                            "norm_factor": norm_factor
                        }
                        self.inverted_index[word]["documents"].append(doc_entry)

                        # update doc tracking
                        self.doc_lengths[doc_id] = norm_factor
                        self.total_docs = max(self.total_docs, doc_id + 1)

                except (ValueError, IndexError) as e:
                    self.logger.error(
                        f"Error parsing line {line_num} in {file_path}: {str(e)}"
                    )
                    raise ValueError(
                        f"Malformed index entry at {line_num}"
                    ) from e
 

