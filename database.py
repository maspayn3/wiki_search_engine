import sqlite3
import threading
import time
from queue import Queue, Empty, Full
from contextlib import contextmanager

def get_db():
    """Opens database connection."""
    db = sqlite3.connect('./var/wiki.sqlite3')

    if not db:
        print("Error connnecting to database")
        exit(1)
    return db


class DatabasePool:
    def __init__(self, database_path: str, max_connections: int = 10, timeout: int = 30):
        self.max_connections = 10
        self.active_connections = 0
        self.connections = Queue(maxsize=max_connections)
        self.database_path = database_path
        self.timeout = timeout
        self._lock = threading.Lock()

    def _create_connection(self):
        """Create new SQLite connection."""
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.timeout, 
            check_same_thread=False)

        conn.execute('PRAGMA journal_mode=WAL') # Improves concurrency
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.row_factory = sqlite3.Row # Dict like access 
        return conn

    def get_connection(self):
        """
        Function attempts these steps in order
        1. Get existing connection from pool (no wait)
        2. Create new connection if under limit
        3. Wait for new connection to be returned to pool via .get()

        Returns:
            sqlite3.Connection: A database connection 
        Raises:
            TimeoutError: If no connection available within timeout period
        """
        try:
            # Get connection w/o waiting if available
            return self.connections.get_nowait()
        except Empty:
            with self._lock:
                if self.active_connections < self.max_connections:
                    # Create and return new connection
                    self.active_connections += 1
                    return self._create_connection()
                try:
                    # At limit, block until new connection is available
                    return self.connections.get(timeout=self.timeout)
                except Empty:
                    raise TimeoutError(
                        f"Could not get connection within {self.timeout} seconds. "
                        f"Active connections: {self.active_connections}"
                    )
                
    def return_connection(self, conn: sqlite3.Connection):
        """Return connection to the pool for reusage or close it if the pool is full"""
        try:
            self.connections.put_nowait(conn)
        except Full:
            conn.close()
            with self._lock:
                self.active_connections -= 1

pool = None

def init_db(app):
    global pool
    if pool is None:
        pool = DatabasePool(
            database_path=app.config.get('DATABASE_PATH', '../var/wiki.sqlite3'),
            max_connections=app.config.get('DATABASE_POOL_SIZE', 10),
            timeout=app.config.get('DATABASE_TIMEOUT', 30)
        )

@contextmanager
def get_db():
    """Get a db connection from the pool"""

    if pool is not None:
        conn = pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            pool.return_connection(conn)
    else:
        conn = sqlite3.connect('./var/wiki.sqlite3')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
