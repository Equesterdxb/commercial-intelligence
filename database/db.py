"""SQLite database management for commercial intelligence."""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List


class Database:
    def __init__(self, db_path: str = "equester_commercial.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize database schema from schema.sql."""
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            with open(schema_file, "r") as f:
                schema = f.read()
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema)
                conn.commit()

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, query: str, params: tuple = ()):
        """Execute a single query."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def execute_many(self, query: str, params_list: List[tuple]):
        """Execute multiple queries with different parameters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[dict]:
        """Fetch all results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Fetch single result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = "append"):
        """Insert pandas DataFrame into table."""
        if df.empty:
            return 0

        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            conn.commit()
        return len(df)

    def get_last_fetch(self, table_name: str) -> Optional[str]:
        """Get timestamp of last successful fetch for a table."""
        query = f"SELECT MAX(fetched_at) as last_fetch FROM {table_name}"
        result = self.fetch_one(query)
        return result.get("last_fetch") if result else None

    def log_pipeline_execution(self, source_name: str, records_fetched: int,
                               records_inserted: int, status: str, error: str = None,
                               execution_time: float = 0):
        """Log pipeline execution details."""
        import uuid
        log_id = str(uuid.uuid4())
        query = """
            INSERT INTO pipeline_log (id, source_name, records_fetched, records_inserted, status, error_message, execution_time_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (log_id, source_name, records_fetched, records_inserted, status, error, execution_time)
        self.execute(query, params)
        return log_id

    def get_pipeline_stats(self, days: int = 7) -> pd.DataFrame:
        """Get pipeline execution statistics."""
        query = """
            SELECT source_name, COUNT(*) as executions, SUM(records_inserted) as total_inserted,
                   AVG(execution_time_seconds) as avg_time, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM pipeline_log
            WHERE execution_date >= datetime('now', '-' || ? || ' days')
            GROUP BY source_name
        """
        return pd.read_sql_query(query, self.get_connection(), params=(days,))

    def cleanup_old_records(self, retention_days: int = 365):
        """Remove records older than retention period."""
        tables = [
            "bookings", "meta_ads_performance", "instagram_organic", "facebook_organic",
            "google_ads_performance", "ga4_website", "tiktok_organic"
        ]
        for table in tables:
            query = f"DELETE FROM {table} WHERE fetched_at < datetime('now', '-' || ? || ' days')"
            try:
                self.execute(query, (retention_days,))
            except sqlite3.OperationalError:
                pass
