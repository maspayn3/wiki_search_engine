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


class SearchEngine:
    def __init__(self, index: SearchIndex):
        self.search_index = index
        self.stopwords = set()
        self.doc_lengths = {}
        self.total_docs = 0
        self.metrics = SearchMetrics()

        logging.basicConfig(
            filename='search_engine.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger(__name__)


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
    
    @lru_cache(maxsize=500)
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
        try:
            self.metrics.total_searches += 1
            cleaned_query_terms = self.clean_query(query)
            
            if not cleaned_query_terms:
                return []

            # find if terms are in the index
            found_terms = [term for term in query
                           if term in self.search_index.inverted_index]

            if not found_terms:
                return []

            if strict_match:
                # get docs which contain all the search terms
                found_docs = self._find_intersection(found_terms)
                if not found_docs:
                    return []
            else:
                # get all docs containing any query term
                found_docs = self._find_union(found_terms)
            
            query_vector = self._calc_query_vector(found_terms)
            results = self._calculate_scores(found_docs, found_terms, query_vector)

            # Return top k results
            return sorted(results.items(), key=lambda x: x[1], reverse=True)[:k]

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise

    def _find_intersection(self, terms):
        doc_sets = []

        for term in terms:
            if term in self.search_index.inverted_index:
                doc_ids = {int(doc_entry["doc_id"])
                           for doc_entry in self.search_index.inverted_index[term]["doc_id"]}
                doc_sets.append(doc_ids)
        
        if not doc_sets:
            return set()
        
        # find intersection of all the sets in document
        return set.intersection(*doc_sets)

    def _find_union(self, terms):
        docs_union = set()

        for term in terms:
            if term in self.search_index.inverted_index:
                # add doc IDs for this term
                docs = {int(doc_entry["doc_id"]) 
                       for doc_entry in self.index.inverted_index[term]["documents"]}
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

    def _calculate_scores(self, 
                          result_docs: Set[int], 
                          terms: List[str], 
                          query_vector: Dict[str, float]):
        """
        Calculate cosine similarity scores for term matching documents.
        
        Args:
            matching_docs: Set of document IDs to score
            query_terms: List of query terms
            query_vector: Query term weights
            
        Returns:
            Dictionary mapping document IDs to scores
        """

        scores = {}

        query_magnitude = math.sqrt(sum(weight * weight)
                                    for weight in query_vector.values())
        
        if query_magnitude == 0:
            return {}

        for doc_id in result_docs:
            # calc doc vector and dot product
            dot_product = 0
            doc_magnitude = 0

            for term in terms:
                if term in self.search_index.inverted_index:
                   doc_entry = next(
                        (entry for entry in self.search_index.inverted_index[term]["documents"]
                         if int(entry["doc_id"]) == doc_id),
                        None
                    )
                   
                   if doc_entry:
                        # calc term weight
                        doc_weight = doc_entry["tfk"] * self.search_index.inverted_index[term]["idf"]
                        dot_product += query_vector[term] * doc_weight
                        doc_magnitude += doc_weight * doc_weight

            if doc_magnitude > 0:
                doc_magnitude = math.sqrt(doc_magnitude)
                scores[doc_id] = dot_product / (query_magnitude * doc_magnitude)

            return scores
        
class SearchMetrics:
    """Track search engine performance metrics."""
    def __init__(self):
        self.search_times = []
        self.total_searches = 0
        self.cache_hits = 0
        self.last_load_time = 0.0

    def record_search_time(self, time: float) -> None:
        self.search_times.append(time)
        self.total_searches += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_load_time(self, time: float) -> None:
        self.last_load_time = time

    def average_search_time(self) -> float:
        if not self.search_times:
            return 0.0
        return sum(self.search_times) / len(self.search_times)