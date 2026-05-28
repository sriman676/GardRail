"""Database connection pooling and optimization utilities."""
import sqlite3
import logging
import threading
from typing import Optional, Any
from queue import Queue
import os

logger = logging.getLogger("guardrail.db_pool")


class SQLiteConnectionPool:
    """Thread-safe SQLite connection pool for improved concurrency."""
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: int = 10):
        """
        Initialize connection pool.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Maximum number of pooled connections
            timeout: Connection timeout in seconds
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialized = False
        self._init_pool()
    
    def _init_pool(self):
        """Initialize the connection pool."""
        parent = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(parent, exist_ok=True)
        
        # Pre-create pool connections
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self.pool.put(conn, block=False)
            except Exception as e:
                logger.warning(f"Could not create pooled connection: {e}")
        
        self._initialized = True
        logger.info(f"Initialized connection pool with up to {self.pool_size} connections")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.timeout,
            isolation_level=None  # autocommit mode
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection from the pool.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        try:
            # Try to get from pool first
            conn = self.pool.get(block=False)
            return conn
        except:
            # If pool is empty, create a new connection
            return self._create_connection()
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        Return a connection to the pool.
        
        Args:
            conn: Database connection to return
        """
        try:
            self.pool.put(conn, block=False)
        except:
            # Pool is full, close this connection
            try:
                conn.close()
            except:
                pass
    
    def close_all(self):
        """Close all connections in the pool."""
        while True:
            try:
                conn = self.pool.get(block=False)
                conn.close()
            except:
                break
        logger.info("Closed all pooled connections")


class DatabaseConnection:
    """Context manager for database connections from the pool."""
    
    def __init__(self, pool: SQLiteConnectionPool):
        self.pool = pool
        self.conn: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        self.conn = self.pool.get_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                # Rollback on exception
                try:
                    self.conn.rollback()
                except:
                    pass
            self.pool.return_connection(self.conn)


def create_connection_pool(db_path: str, pool_size: int = 5) -> SQLiteConnectionPool:
    """Factory function to create a connection pool."""
    return SQLiteConnectionPool(db_path, pool_size=pool_size)
