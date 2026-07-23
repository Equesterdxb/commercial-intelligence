"""Tests for database module."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from database.db import Database


class TestDatabase:
    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            yield db

    def test_database_initialization(self, temp_db):
        """Test database initialization."""
        assert temp_db.db_path.exists()

    def test_get_connection(self, temp_db):
        """Test getting database connection."""
        conn = temp_db.get_connection()
        assert conn is not None
        conn.close()

    def test_execute_query(self, temp_db):
        """Test executing a query."""
        cursor = temp_db.execute(
            "INSERT INTO pipeline_log (id, source_name, records_fetched, records_inserted, status) "
            "VALUES (?, ?, ?, ?, ?)",
            ("log1", "test", 10, 5, "success")
        )
        assert cursor is not None

    def test_fetch_all(self, temp_db):
        """Test fetching all results."""
        temp_db.execute(
            "INSERT INTO pipeline_log (id, source_name, records_fetched, records_inserted, status) "
            "VALUES (?, ?, ?, ?, ?)",
            ("log1", "test", 10, 5, "success")
        )
        results = temp_db.fetch_all("SELECT * FROM pipeline_log")
        assert len(results) == 1
        assert results[0]["source_name"] == "test"

    def test_fetch_one(self, temp_db):
        """Test fetching single result."""
        temp_db.execute(
            "INSERT INTO pipeline_log (id, source_name, records_fetched, records_inserted, status) "
            "VALUES (?, ?, ?, ?, ?)",
            ("log1", "test", 10, 5, "success")
        )
        result = temp_db.fetch_one("SELECT * FROM pipeline_log WHERE source_name = ?", ("test",))
        assert result is not None
        assert result["source_name"] == "test"

    def test_insert_dataframe_empty(self, temp_db):
        """Test inserting empty dataframe."""
        df = pd.DataFrame()
        result = temp_db.insert_dataframe(df, "bookings")
        assert result == 0

    def test_insert_dataframe_with_data(self, temp_db):
        """Test inserting dataframe with data."""
        df = pd.DataFrame({
            "id": ["1"],
            "guest_name": ["John"],
            "booking_source": ["app"],
            "booking_status": ["confirmed"],
        })
        result = temp_db.insert_dataframe(df, "bookings")
        assert result == 1

    def test_get_last_fetch(self, temp_db):
        """Test getting last fetch timestamp."""
        last_fetch = temp_db.get_last_fetch("bookings")
        # Should return None or timestamp for new database
        assert last_fetch is None or isinstance(last_fetch, str)

    def test_log_pipeline_execution(self, temp_db):
        """Test logging pipeline execution."""
        log_id = temp_db.log_pipeline_execution("test_source", 100, 50, "success")
        assert log_id is not None

        result = temp_db.fetch_one("SELECT * FROM pipeline_log WHERE id = ?", (log_id,))
        assert result is not None
        assert result["source_name"] == "test_source"
        assert result["records_fetched"] == 100
        assert result["records_inserted"] == 50

    def test_get_pipeline_stats(self, temp_db):
        """Test getting pipeline statistics."""
        temp_db.log_pipeline_execution("test1", 100, 50, "success")
        temp_db.log_pipeline_execution("test2", 200, 150, "success")

        stats = temp_db.get_pipeline_stats(days=7)
        assert len(stats) >= 2

    def test_cleanup_old_records(self, temp_db):
        """Test cleaning up old records."""
        # Insert test data
        df = pd.DataFrame({
            "id": ["1"],
            "guest_name": ["John"],
            "booking_source": ["app"],
            "booking_status": ["confirmed"],
        })
        temp_db.insert_dataframe(df, "bookings")

        # Cleanup should not remove recent data
        temp_db.cleanup_old_records(retention_days=365)
        results = temp_db.fetch_all("SELECT * FROM bookings")
        assert len(results) == 1
