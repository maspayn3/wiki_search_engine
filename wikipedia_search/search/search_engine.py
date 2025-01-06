"""
Search engine implementation with focus on clean code, performance and testability.
Features TF-IDF ranking, result caching, and performance monitoring.
"""
import re
import math
import time
import logging
from typing import Dict, List, Set, Tuple, Optional
from functools import lru_cache
from wikipedia_search.search.index_loader import SearchIndex
from collections import defaultdict
import database


class SearchEngine:
    def __init__(self, index: SearchIndex):
        self.search_index = index
        self.stopwords = set()
        self._doc_magnitudes = {}
        self.metrics = SearchMetrics()

        # doc id -> title
        self.title_index = {}

        # term -> doc_ids
        self.term_title_index = defaultdict(set)

        logging.basicConfig(
            filename='var/log/search_engine.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger(__name__)        
        self.search_index.on_index_loaded = self._init_doc_magnitudes

        print(f"Number of documents with magnitudes: {len(self._doc_magnitudes)}")


    def _init_doc_magnitudes(self):
        """Pre-calculate document magnitudes for fast scoring"""
        self._load_titles()

        for term, term_data in self.search_index.inverted_index.items():
            for doc in term_data["documents"]:
                doc_id = int(doc["doc_id"])
                if doc_id not in self._doc_magnitudes:
                    self._doc_magnitudes[doc_id] = 0.0
                weight = float(doc["tfk"]) * float(term_data["idf"])
                self._doc_magnitudes[doc_id] += weight * weight
        
        for doc_id in self._doc_magnitudes:
            self._doc_magnitudes[doc_id] = math.sqrt(self._doc_magnitudes[doc_id])
        
        print(f"init doc maginitudes finished, size: {len(self._doc_magnitudes)}")

    def _load_titles(self):
        try:
            with database.get_db() as conn:
                cur = conn.execute(
                    "SELECT doc_id, title FROM documents"
                )
                for row in cur:
                    doc_id = int(row['doc_id'])
                    title = row['title']

                    self.title_index[doc_id] = title
                    clean_terms = self.clean_query(title)
                    for term in clean_terms:
                        self.term_title_index[term].add(doc_id)

            self.logger.info(f"Loaded {len(self.title_index)} document titles")

        except Exception as e:
            self.logger.error(f"Title loading failed: {str(e)}")
            raise

    def _is_term_in_title(self, doc_id, term):
        return doc_id in self.term_title_index.get(term, set())

    def clean_query(self, query):
        """
        Clean and turn search query into a list.

        Args:
            query: query request string 

        Returns:
            list of cleaned terms in query
        """
        # regex notes:
        # r means "raw string" (treats backslashes literally)
        # [] defines a character set
        # ^ inside [] means "NOT these characters"
        # a-z means any lowercase letter
        # A-Z means any uppercase letter
        # 0-9 means any digit
        #   (space) is also allowed
        # + means "one or more occurrences" 
        query = re.sub(r"[^a-zA-Z0-9 ]", "", query)

        # convert to lowercase and split
        query = query.casefold()
        query_terms = query.split()

        # remove stop words
        cleaned_terms = [term for term in query_terms 
                         if term not in self.search_index.stopwords]
        return cleaned_terms
    
    @lru_cache(maxsize=1000)
    def search(self, query: str, k: int = 10, strict_match: bool = True):
        """
        Search query using vector space model with cosine similarity 
        (https://en.wikipedia.org/wiki/Cosine_similarity)

        cosine_sim = S_c(A,B) := cos(theta) = A * B / (||A||||B||) 
                   = sum(A_i*B_i)/sqrt(sum(A_i^2)) * sqrt(sum(B_i^2))

                   A will be the document verctor
                   B will bbe the query vector

        Args:
            query: Search string
            k: Number of results requested to return
            strict_match: Requires all query terms to be present if True

        Returns:
            List of (doc_id, score) pairs
        """
        cache_info = self.search.cache_info()
        if cache_info.hits > self.metrics.cache_hits:
            self.metrics.record_cache_hit()

        start_time = time.time()
        try:
            cleaned_query_terms = self.clean_query(query)
            
            if not cleaned_query_terms:
                return []

            # find which terms if any are in the index
            found_terms = [term for term in cleaned_query_terms
                           if term in self.search_index.inverted_index]

            if not found_terms:
                return []

            print(found_terms)

            if strict_match:
                # get docs which contain all the search terms
                found_docs = self._find_intersection(found_terms)
            else:
                # get all docs containing any query term
                found_docs = self._find_union(found_terms)
            
            if not found_docs:
                return []
            
            query_vector = self._calc_query_vector(found_terms)
            query_magnitude = math.sqrt(sum(w * w for w in query_vector.values()))
            print(f"Query vector: {query_vector}")  # Debug
            print(f"Query magnitude: {query_magnitude}")  # Debug

            if query_magnitude == 0:
                return []

            results = self._calculate_scores(found_docs, found_terms, query_vector, query_magnitude)

            # Return top k results
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[:k]

            search_time = time.time() - start_time
            self.metrics.record_search_time(search_time, len(sorted_results))

            return sorted_results

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise

    def _find_intersection(self, terms):
        """More efficient intersection by starting with shortest posting list"""
        # Get posting lists with lengths
        term_docs = [(term, {int(doc["doc_id"]) 
                    for doc in self.search_index.inverted_index[term]["documents"]})
                    for term in terms]
        
        # Sort by posting list length
        term_docs.sort(key=lambda x: len(x[1]))
        
        if not term_docs:
            return set()
            
        result = term_docs[0][1]
        for _, docs in term_docs[1:]:
            result &= docs
            if not result:  # Early exit if empty
                break
                
        return result

    def _find_union(self, terms):
        docs_union = set()

        for term in terms:
            # add doc IDs for this term
            docs = {int(doc_entry["doc_id"]) 
                    for doc_entry in self.search_index.inverted_index[term]["documents"]}
            docs_union.update(docs)

        return docs_union

    def _calc_query_vector(self, query_terms: List[str]):
        """
        Calculate query vector with term frequencies and IDF weights.
        
        Args:
            query_terms: List of query terms
            
        Returns:
            Dictionary mapping terms to their weights
        """
        query_vector = {}

        for term in query_terms:
            # get term frequency and idf 
            tf = query_terms.count(term)
            idf = self.search_index.inverted_index[term]["idf"]

            # calc term weight
            query_vector[term] = tf * idf

        return query_vector


    def _calculate_scores(self, result_docs, found_terms, query_vector, query_magnitude):
        """More efficient batch scoring"""
        try:
            scores = {doc_id: 0.0 for doc_id in result_docs}
            title_exact_boost = 10
            title_boost = 2
            
            # Pre-calculate title matches
            title_matches = {
                doc_id: set(term for term in found_terms 
                        if self._is_term_in_title(doc_id, term))
                for doc_id in result_docs
            }
            
            # Calculate dot products in batch
            for term in found_terms:
                term_data = self.search_index.inverted_index[term]
                query_weight = query_vector[term]
                
                for doc_entry in term_data["documents"]:
                    doc_id = int(doc_entry["doc_id"])
                    if doc_id in result_docs:
                        weight = float(doc_entry["tfk"]) * float(term_data["idf"])
                        scores[doc_id] += query_weight * weight
                        print(f"Score update for doc {doc_id}: {scores[doc_id]}")  # Debug
            
            # Normalize and apply boosts
            final_scores = {}
            for doc_id, score in scores.items():
                if score > 0:
                    # Use pre-calculated magnitude
                    base_score = score / (query_magnitude * self._doc_magnitudes[doc_id])
                    
                    # Apply title boost
                    title_matching_terms = title_matches[doc_id]
                    if len(title_matching_terms) == len(found_terms):
                        final_score = base_score * title_exact_boost
                    elif title_matching_terms:
                        final_score = base_score * title_boost
                    else:
                        final_score = base_score
                        
                    final_scores[doc_id] = float((math.tanh(final_score) + 1) / 2)
                    print(f"Final score for doc {doc_id}: {final_scores[doc_id]}")
            
            return final_scores
        except Exception as e:
            print(f"Scoring error: {str(e)}")
            raise


class SearchMetrics:
    """Track search engine performance metrics."""
    def __init__(self):
        self.search_times = []  # Store time taken for each search
        self.total_searches = 0  # Total number of searches performed
        self.cache_hits = 0      # Number of cache hits
        self.last_load_time = 0.0  # Time taken to load index
        self.result_counts = []  # Number of results per search
        self.most_recent_search_time = 0.0
        
    def record_search_time(self, time_taken: float, num_results: int) -> None:
        """Record the time taken for a search and number of results."""
        self.search_times.append(time_taken)
        self.total_searches += 1
        self.result_counts.append(num_results)
        self.most_recent_search_time = time_taken

    def record_cache_hit(self) -> None:
        """Record when a search result comes from cache."""
        self.cache_hits += 1

    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.search_times:
            return {
                "total_searches": 0,
                "avg_search_time": 0,
                "cache_hit_rate": 0,
                "avg_results": 0
            }
            
        return {
            "total_searches": self.total_searches,
            "avg_search_time": sum(self.search_times) / len(self.search_times),
            "cache_hit_rate": self.cache_hits / self.total_searches,
            "avg_results": sum(self.result_counts) / len(self.result_counts)
        }