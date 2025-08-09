"""
Database optimization service for Quote Master Pro.
Implements query optimization, connection pooling, and performance monitoring.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import Engine, event, text
from sqlalchemy.engine.events import PoolEvents
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from src.core.config import get_settings
from src.services.cache.response_optimizer import DatabaseQueryOptimizer

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryType(str, Enum):
    """Database query types for optimization"""

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    COMPLEX = "complex"


@dataclass
class QueryStats:
    """Statistics for database queries"""

    query_type: QueryType
    table_name: str
    execution_time: float
    rows_affected: int
    cache_hit: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DatabaseOptimizer:
    """
    Advanced database optimization and monitoring service.
    """

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.query_stats: List[QueryStats] = []
        self.connection_pool_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0,
        }
        self.slow_query_threshold = 1.0  # 1 second

    async def initialize(self):
        """Initialize optimized database engine"""
        try:
            # Create engine with optimization settings
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                # Connection pool optimization
                poolclass=QueuePool,
                pool_size=20,  # Base number of connections
                max_overflow=30,  # Additional connections when needed
                pool_timeout=30,  # Timeout waiting for connection
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True,  # Validate connections before use
                # Performance settings
                echo=False,  # Disable query logging in production
                echo_pool=False,
                query_cache_size=1200,  # SQL compilation cache
                # Connection settings for better performance
                connect_args={
                    "server_settings": {
                        "application_name": "quote_master_pro",
                        "jit": "off",  # Disable JIT for predictable performance
                    }
                }
                if "postgresql" in settings.DATABASE_URL
                else {},
            )

            # Set up session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Set up event listeners for monitoring
            self._setup_event_listeners()

            logger.info("Database optimizer initialized successfully")

        except Exception as e:
            logger.error(f"Database optimizer initialization failed: {e}")
            raise

    def _setup_event_listeners(self):
        """Set up database event listeners for monitoring"""

        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Monitor database connections"""
            self.connection_pool_stats["total_connections"] += 1
            logger.debug("New database connection established")

        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Monitor connection checkout"""
            self.connection_pool_stats["checked_out"] += 1

        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Monitor connection checkin"""
            self.connection_pool_stats["checked_out"] = max(
                0, self.connection_pool_stats["checked_out"] - 1
            )

    @asynccontextmanager
    async def get_session(self):
        """Get optimized database session with monitoring"""
        if not self.session_factory:
            raise RuntimeError("Database optimizer not initialized")

        session = self.session_factory()
        start_time = time.time()

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

            # Track session duration
            session_duration = time.time() - start_time
            if session_duration > self.slow_query_threshold:
                logger.warning(f"Slow database session: {session_duration:.3f}s")

    async def execute_optimized_query(
        self,
        query: str,
        params: Dict[str, Any] = None,
        query_type: QueryType = QueryType.SELECT,
        table_name: str = "unknown",
        use_cache: bool = True,
    ) -> Any:
        """Execute database query with optimization and caching"""

        # Try cache first for SELECT queries
        if use_cache and query_type == QueryType.SELECT:
            cache_key = f"query_{table_name}"
            cached_result = await DatabaseQueryOptimizer.get_cached_query_result(
                cache_key, query=query, params=params
            )
            if cached_result is not None:
                self._log_query_stats(
                    QueryStats(
                        query_type=query_type,
                        table_name=table_name,
                        execution_time=0.001,  # Cache hit is very fast
                        rows_affected=len(cached_result)
                        if isinstance(cached_result, list)
                        else 1,
                        cache_hit=True,
                    )
                )
                return cached_result

        # Execute query with timing
        start_time = time.time()

        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), params or {})

                if query_type == QueryType.SELECT:
                    data = result.fetchall()
                    rows_affected = len(data)
                else:
                    data = result.rowcount
                    rows_affected = result.rowcount or 0

                execution_time = time.time() - start_time

                # Log query statistics
                self._log_query_stats(
                    QueryStats(
                        query_type=query_type,
                        table_name=table_name,
                        execution_time=execution_time,
                        rows_affected=rows_affected,
                        cache_hit=False,
                    )
                )

                # Cache SELECT results
                if use_cache and query_type == QueryType.SELECT and data:
                    cache_key = f"query_{table_name}"
                    await DatabaseQueryOptimizer.cache_query_result(
                        cache_key, data, query=query, params=params
                    )

                return data

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Query execution failed ({execution_time:.3f}s): {e}")
                raise

    async def bulk_insert_optimized(
        self, table_name: str, records: List[Dict[str, Any]], batch_size: int = 1000
    ) -> int:
        """Optimized bulk insert operation"""
        if not records:
            return 0

        start_time = time.time()
        total_inserted = 0

        async with self.get_session() as session:
            try:
                # Process records in batches for memory efficiency
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]

                    # Create parameterized insert query
                    columns = list(batch[0].keys())
                    placeholders = ", ".join([f":{col}" for col in columns])
                    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                    # Execute batch insert
                    result = await session.execute(text(query), batch)
                    total_inserted += len(batch)

                    # Commit periodically to avoid long-running transactions
                    if i % (batch_size * 5) == 0:
                        await session.commit()

                execution_time = time.time() - start_time

                self._log_query_stats(
                    QueryStats(
                        query_type=QueryType.INSERT,
                        table_name=table_name,
                        execution_time=execution_time,
                        rows_affected=total_inserted,
                    )
                )

                logger.info(
                    f"Bulk insert completed: {total_inserted} records in {execution_time:.3f}s"
                )
                return total_inserted

            except Exception as e:
                logger.error(f"Bulk insert failed: {e}")
                raise

    async def optimize_table(self, table_name: str):
        """Optimize specific table (database-specific operations)"""
        try:
            async with self.get_session() as session:
                if "postgresql" in settings.DATABASE_URL:
                    # PostgreSQL optimization
                    await session.execute(text(f"ANALYZE {table_name}"))
                    await session.execute(text(f"VACUUM ANALYZE {table_name}"))
                elif "sqlite" in settings.DATABASE_URL:
                    # SQLite optimization
                    await session.execute(text(f"ANALYZE {table_name}"))
                    await session.execute(text("PRAGMA optimize"))

                logger.info(f"Table {table_name} optimized successfully")

        except Exception as e:
            logger.error(f"Table optimization failed for {table_name}: {e}")

    def _log_query_stats(self, stats: QueryStats):
        """Log query statistics"""
        self.query_stats.append(stats)

        # Keep only recent stats (last 1000 queries)
        if len(self.query_stats) > 1000:
            self.query_stats = self.query_stats[-1000:]

        # Log slow queries
        if stats.execution_time > self.slow_query_threshold and not stats.cache_hit:
            logger.warning(
                f"Slow query detected: {stats.query_type} on {stats.table_name} "
                f"took {stats.execution_time:.3f}s"
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        if not self.query_stats:
            return {"message": "No query statistics available"}

        # Calculate statistics
        recent_stats = [
            s
            for s in self.query_stats
            if s.timestamp > datetime.now() - timedelta(minutes=30)
        ]

        if not recent_stats:
            return {"message": "No recent query statistics"}

        execution_times = [s.execution_time for s in recent_stats if not s.cache_hit]
        cache_hits = len([s for s in recent_stats if s.cache_hit])
        total_queries = len(recent_stats)

        query_type_counts = {}
        table_counts = {}

        for stat in recent_stats:
            query_type_counts[stat.query_type] = (
                query_type_counts.get(stat.query_type, 0) + 1
            )
            table_counts[stat.table_name] = table_counts.get(stat.table_name, 0) + 1

        return {
            "total_queries_30min": total_queries,
            "cache_hit_rate": round((cache_hits / total_queries) * 100, 2)
            if total_queries > 0
            else 0,
            "average_execution_time": round(
                sum(execution_times) / len(execution_times), 3
            )
            if execution_times
            else 0,
            "slowest_query_time": round(max(execution_times), 3)
            if execution_times
            else 0,
            "query_types": query_type_counts,
            "table_activity": table_counts,
            "connection_pool": self.connection_pool_stats,
            "slow_queries_count": len(
                [
                    s
                    for s in recent_stats
                    if s.execution_time > self.slow_query_threshold
                ]
            ),
        }

    async def run_maintenance(self):
        """Run database maintenance tasks"""
        try:
            logger.info("Starting database maintenance")

            # Analyze all tables for better query planning
            table_names = [
                "users",
                "quotes",
                "service_quotes",
                "quote_generations",
                "voice_recordings",
            ]

            for table_name in table_names:
                await self.optimize_table(table_name)
                await asyncio.sleep(1)  # Prevent overwhelming the database

            # Clear old statistics
            cutoff_time = datetime.now() - timedelta(days=7)
            self.query_stats = [
                s for s in self.query_stats if s.timestamp > cutoff_time
            ]

            logger.info("Database maintenance completed")

        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")

    async def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            # Quote performance indexes
            "CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_created_at ON quotes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_service_type ON quotes(service_type)",
            "CREATE INDEX IF NOT EXISTS idx_quotes_suburb ON quotes(suburb)",
            # Service quote indexes
            "CREATE INDEX IF NOT EXISTS idx_service_quotes_user_id ON service_quotes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_service_quotes_created_at ON service_quotes(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_service_quotes_status ON service_quotes(status)",
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            # Voice recording indexes
            "CREATE INDEX IF NOT EXISTS idx_voice_recordings_user_id ON voice_recordings(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_voice_recordings_created_at ON voice_recordings(created_at)",
        ]

        async with self.get_session() as session:
            for index_sql in indexes:
                try:
                    await session.execute(text(index_sql))
                    logger.debug(f"Created index: {index_sql.split(' ')[-1]}")
                except Exception as e:
                    logger.warning(f"Index creation failed or already exists: {e}")

        logger.info("Database indexes created/verified")


# Global instance
_database_optimizer = None


async def get_database_optimizer() -> DatabaseOptimizer:
    """Get global database optimizer instance"""
    global _database_optimizer
    if _database_optimizer is None:
        _database_optimizer = DatabaseOptimizer()
        await _database_optimizer.initialize()
    return _database_optimizer


# Utility functions for common operations
async def get_optimized_user_quotes(
    user_id: int, limit: int = 50
) -> List[Dict[str, Any]]:
    """Get user quotes with optimization"""
    optimizer = await get_database_optimizer()

    query = """
    SELECT id, service_type, suburb, final_price, status, created_at
    FROM quotes
    WHERE user_id = :user_id
    ORDER BY created_at DESC
    LIMIT :limit
    """

    return await optimizer.execute_optimized_query(
        query=query,
        params={"user_id": user_id, "limit": limit},
        query_type=QueryType.SELECT,
        table_name="quotes",
        use_cache=True,
    )


async def get_quote_analytics(days: int = 30) -> Dict[str, Any]:
    """Get quote analytics with caching"""
    optimizer = await get_database_optimizer()

    query = """
    SELECT
        service_type,
        COUNT(*) as count,
        AVG(final_price) as avg_price,
        MAX(final_price) as max_price,
        MIN(final_price) as min_price
    FROM quotes
    WHERE created_at >= NOW() - INTERVAL :days DAY
    GROUP BY service_type
    ORDER BY count DESC
    """

    return await optimizer.execute_optimized_query(
        query=query,
        params={"days": days},
        query_type=QueryType.SELECT,
        table_name="quotes",
        use_cache=True,
    )


async def cleanup_old_data(days: int = 90):
    """Clean up old data to maintain performance"""
    optimizer = await get_database_optimizer()

    # Clean up old quote generations
    cleanup_query = """
    DELETE FROM quote_generations
    WHERE created_at < :cutoff_date
    """

    cutoff_date = datetime.now() - timedelta(days=days)

    result = await optimizer.execute_optimized_query(
        query=cleanup_query,
        params={"cutoff_date": cutoff_date},
        query_type=QueryType.DELETE,
        table_name="quote_generations",
        use_cache=False,
    )

    logger.info(f"Cleaned up {result} old quote generations")
    return result
