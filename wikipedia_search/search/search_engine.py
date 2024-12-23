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
        self.doc_lengths = {}
        self.total_docs = 0
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
        self._load_titles()

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

            # find which terms if any are in the index
            found_terms = [term for term in cleaned_query_terms
                           if term in self.search_index.inverted_index]
            
            print(found_terms)

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
            doc_ids = {int(doc_entry["doc_id"])
                        for doc_entry in self.search_index.inverted_index[term]["documents"]}
            doc_sets.append(doc_ids)
        
        if not doc_sets:
            return set()
        
        # find intersection of all the sets in document
        return set.intersection(*doc_sets)

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


    def _calculate_scores(self, 
                          result_docs: Set[int], 
                          found_terms: List[str], 
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
        title_exact_boost = 10
        title_boost = 2
        
        # Calculate query magnitude once
        query_weights = list(query_vector.values())  # Materialize generator
        query_magnitude = math.sqrt(sum(w * w for w in query_weights))
        
        if query_magnitude == 0:
            return {}
            
        for doc_id in result_docs:
            dot_product = 0.0
            doc_weights = []  # Store weights to calculate magnitude
            
            title_matching_terms = set(
                term for term in found_terms 
                if self._is_term_in_title(doc_id, term)
            )


            # Calculate dot product and collect weights
            for term in found_terms:
                # Find the document entry
                doc_entry = None
                for entry in self.search_index.inverted_index[term]["documents"]:
                    if int(entry["doc_id"]) == doc_id:
                        doc_entry = entry
                        break
                        
                if doc_entry:
                    # Calculate term weights
                    doc_tf = float(doc_entry["tfk"])
                    doc_idf = float(self.search_index.inverted_index[term]["idf"])
                    doc_weight = doc_tf * doc_idf
                    
                    # Store for magnitude calculation
                    doc_weights.append(doc_weight)
                    
                    # Add to dot product
                    dot_product += query_vector[term] * doc_weight
        
            # Calculate document magnitude
            if doc_weights:  # Only if we found matching terms
                doc_magnitude = math.sqrt(sum(w * w for w in doc_weights))
                if doc_magnitude > 0:
                    # Calculate cosine similarity
                    base_score = float(dot_product / (query_magnitude * doc_magnitude))

                    if len(title_matching_terms) == len(found_terms):
                        final_score = base_score * title_exact_boost
                    elif title_matching_terms:
                        final_score = base_score * title_boost
                    else:
                        final_score = base_score

                    normalized_score = math.tanh(final_score)
                    scores[doc_id] = float((normalized_score + 1) / 2)  # Ensure float
        
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