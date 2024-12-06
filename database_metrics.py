"""Performance metrics collection and comparison for database implementations."""
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
import json
import logging
from contextlib import contextmanager
import sqlite3
import database  # Our database module with pool
import os
from flask import Flask


# Set up logging
logging.basicConfig(
    filename='performance_metrics.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def init_test_app():
    """Create and configure a test Flask app for database initialization."""
    logging.info("Initializing test Flask app and database pool...")
    
    # Get absolute path to database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join('.', 'var', 'wiki.sqlite3')
    
    # Verify database file exists
    if not os.path.exists(db_path):
        logging.error(f"Database file not found at: {db_path}")
        raise FileNotFoundError(f"Database file not found at: {db_path}")

    app = Flask(__name__)
    app.config.update({
        'DATABASE_PATH': './var/wiki.sqlite3',
        'DATABASE_POOL_SIZE': 10,
        'DATABASE_TIMEOUT': 30
    })
    database.init_db(app)
    return app


@dataclass
class PerformanceMetrics:
    """Track performance metrics for database operations."""
    implementation: str
    query_times: List[float] = field(default_factory=list)
    total_queries: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    def add_measurement(self, query_time: float) -> None:
        """Add a new query time measurement."""
        self.query_times.append(query_time)
        self.total_queries += 1

    def get_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics from collected metrics."""
        if not self.query_times:
            return {"error": "No measurements recorded"}

        try:
            return {
                "implementation": self.implementation,
                "total_queries": self.total_queries,
                "total_errors": self.errors,
                "error_rate": (self.errors / self.total_queries) if self.total_queries > 0 else 0,
                "avg_query_time_ms": statistics.mean(self.query_times) * 1000,
                "median_query_time_ms": statistics.median(self.query_times) * 1000,
                "p95_query_time_ms": statistics.quantiles(self.query_times, n=20)[-1] * 1000,
                "min_query_time_ms": min(self.query_times) * 1000,
                "max_query_time_ms": max(self.query_times) * 1000,
                "total_duration_seconds": (datetime.now() - self.start_time).total_seconds()
            }
        except Exception as e:
            logging.error(f"Error calculating statistics: {e}")
            return {"error": f"Failed to calculate statistics: {str(e)}"}

@contextmanager
def get_simple_connection():
    """Context manager for non-pooled database connection."""
    db_path = os.path.join('.', 'var', 'wiki.sqlite3')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def test_implementation(implementation: str, num_queries: int, test_doc_ids: List[int], 
                       use_pool: bool = True) -> Dict[str, Any]:
    """Test database implementation performance.
    
    Args:
        implementation: Name of implementation being tested
        num_queries: Number of queries to run
        test_doc_ids: List of document IDs to query
        use_pool: Whether to use connection pool or simple connection
        
    Returns:
        Dictionary containing performance statistics
    """
    metrics = PerformanceMetrics(implementation)
    total_operations = num_queries * len(test_doc_ids)
    
    logging.info(f"\nStarting {implementation} test:")
    logging.info(f"Target operations: {total_operations}")

    start_time = time.time()
    successful_queries = 0
    failed_queries = 0
    last_log_time = start_time
    
    for query_num in range(num_queries):
        for doc_id in test_doc_ids:
            try:
                query_start = time.time()

                if use_pool:
                    with database.get_db() as conn:
                        cur = conn.execute(
                            "SELECT summary FROM documents WHERE doc_id = ?",
                            (doc_id,)
                        )
                        summary = cur.fetchone()
                        tmp = summary['summary']
                else:
                    with get_simple_connection() as conn:
                        cur = conn.execute(
                            "SELECT summary FROM documents WHERE doc_id = ?",
                            (doc_id,)
                        )
                        summary = cur.fetchone()
                        tmp = summary['summary']
                        
                query_time = time.time() - query_start
                metrics.add_measurement(query_time)
                successful_queries += 1

                current_time = time.time()
                if current_time - last_log_time >= 5:
                    elapsed = current_time - start_time
                    success_rate = successful_queries / elapsed
                    progress = (successful_queries / total_operations) * 100
                
                    logging.info(
                        f"{implementation} Status:"
                        f"\n  Progress: {progress:.1f}%"
                        f"\n  Successful queries: {successful_queries}"
                        f"\n  Failed queries: {failed_queries}"
                        f"\n  Query rate: {success_rate:.1f}/sec"
                        f"\n  Elapsed time: {elapsed:.1f}s"
                    )
                    last_log_time = current_time


            except Exception as e:
                failed_queries += 1
                metrics.errors += 1

                # Log errors, but don't spam the log file
                if failed_queries % 10 == 0:  # Log every 10th error
                    logging.error(
                        f"Error in {implementation} test:"
                        f"\n  Error: {str(e)}"
                        f"\n  Failed queries: {failed_queries}"
                        f"\n  Successful queries: {successful_queries}"
                    )
    
    return metrics.get_stats()

def run_performance_comparison(num_queries: int = 100) -> Dict[str, Any]:
    """Run complete performance comparison between implementations.
    
    Args:
        num_queries: Number of queries to run per implementation
        
    Returns:
        Dictionary containing comparison results and statistics
    """
    try:
        # Ensure database pool is initialized
        if database.pool is None:
            raise RuntimeError("Database pool not initialized")
            
        # Generate test document IDs
        test_doc_ids = list(range(1, 11))  # Test with first 10 doc IDs
        
        # Test both implementations
        pooled_results = test_implementation(
            "connection_pool",
            num_queries,
            test_doc_ids,
            use_pool=True
        )
        
        non_pooled_results = test_implementation(
            "simple_connection",
            num_queries,
            test_doc_ids,
            use_pool=False
        )
        
        # Calculate improvements
        if non_pooled_results.get("avg_query_time_ms") and pooled_results.get("avg_query_time_ms"):
            improvement = {
                "avg_query_time_percent": (
                    (non_pooled_results["avg_query_time_ms"] - 
                     pooled_results["avg_query_time_ms"]) /
                    non_pooled_results["avg_query_time_ms"] * 100
                ),
                "error_rate_percent": (
                    (non_pooled_results["error_rate"] - 
                     pooled_results["error_rate"]) /
                    (non_pooled_results["error_rate"] if non_pooled_results["error_rate"] > 0 else 1) * 100
                )
            }
        else:
            improvement = {"error": "Could not calculate improvements"}

        results = {
            "pooled": pooled_results,
            "non_pooled": non_pooled_results,
            "improvement": improvement,
            "pool_info": {
                "max_connections": database.pool.max_connections,
                "active_connections": database.pool.active_connections
            },
            "test_info": {
                "queries_per_implementation": num_queries,
                "timestamp": datetime.now().isoformat(),
                "doc_ids_tested": test_doc_ids
            }
        }

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'performance_comparison_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
        logging.info(f"Performance comparison completed and saved to {filename}")
        return results

    except Exception as e:
        error_msg = f"Performance comparison failed: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

if __name__ == "__main__":
    # Example usage
    print("Initializing database pool...")
    test_app = init_test_app()
    print("Database initialized!")
    try:
        print("Running tests...")
        # Run comparisons with different loads
        light_load = run_performance_comparison(100)
        medium_load = run_performance_comparison(500)
        heavy_load = run_performance_comparison(1000)

        print("\nLight Load Improvement:")
        print(f"Average Query Time: {light_load['improvement']['avg_query_time_percent']:.2f}%")
        
        print("\nMedium Load Improvement:")
        print(f"Average Query Time: {medium_load['improvement']['avg_query_time_percent']:.2f}%")
        
        print("\nHeavy Load Improvement:")
        print(f"Average Query Time: {heavy_load['improvement']['avg_query_time_percent']:.2f}%")

    except Exception as e:
        print(f"Error running performance tests: {e}")
        logging.error(f"Performance test error: {e}")