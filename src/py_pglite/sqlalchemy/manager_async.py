"""SQLAlchemy-specific manager for py-pglite.

Extends the core PGliteManager with SQLAlchemy-specific functionality.
"""

import time

from typing import Any

from py_pglite.manager import PGliteManager


class SQLAlchemyAsyncPGliteManager(PGliteManager):
    """PGlite manager with SQLAlchemy-specific functionality.

    Extends the core PGliteManager with methods that require SQLAlchemy.
    Use this manager when you need SQLAlchemy integration.
    """

    async def __aenter__(self) -> "SQLAlchemyAsyncPGliteManager":
        """Override to return correct type for type checking."""
        super().__enter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()

    def __enter__(self):
        raise TypeError(
            "'SQLAlchemyAsyncPGliteManager'  does not support the context manager protocol"
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise TypeError(
            "'SQLAlchemyAsyncPGliteManager'  does not support the context manager protocol"
        )

    def get_engine(self, **engine_kwargs: Any) -> Any:
        """Get SQLAlchemy async engine connected to PGlite.

        NOTE: This method requires SQLAlchemy to be installed.

        IMPORTANT: Returns a shared async engine instance to prevent connection timeouts.
        PGlite's socket server can only handle 1 connection at a time, so multiple
        engines would cause psycopg.errors.ConnectionTimeout. The shared engine
        architecture ensures all database operations use the same connection.

        Args:
            **engine_kwargs: Additional arguments for create_async_engine

        Returns:
            SQLAlchemy Async Engine connected to PGlite (shared instance)

        Raises:
            ImportError: If SQLAlchemy is not installed
            RuntimeError: If PGlite server is not running
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        # Always return shared engine to avoid connection conflicts
        # PGlite socket server can only handle one connection at a time
        if hasattr(self, "_shared_engine") and self._shared_engine is not None:
            return self._shared_engine

        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy.pool import NullPool
            from sqlalchemy.pool import StaticPool
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy is required for get_engine(). "
                "Install with: pip install py-pglite[sqlalchemy]"
            ) from e

        # Default configuration optimized for testing with PGlite
        default_kwargs = {
            "echo": False,
            "pool_pre_ping": False,  # Disable pre-ping for Unix sockets
            "pool_recycle": 3600,  # Longer recycle time for testing
            "connect_args": {
                "connect_timeout": 60,  # Much longer timeout for table creation
                "application_name": "py-pglite",
                "sslmode": "disable",  # Disable SSL for Unix sockets
                "prepare_threshold": None,  # Disable prepared states for test stability
                "keepalives_idle": 600,  # Keep connection alive longer
                "keepalives_interval": 30,  # Check every 30 seconds
                "keepalives_count": 3,  # Allow 3 failed keepalive probes
            },
        }

        # Check if user specified a poolclass
        poolclass = engine_kwargs.get("poolclass")

        if poolclass is None:
            # Default to StaticPool for testing - single persistent connection
            default_kwargs["poolclass"] = StaticPool
        elif poolclass.__name__ in ("StaticPool", "NullPool"):
            # StaticPool and NullPool don't accept pool_size/max_overflow parameters
            pass
        else:
            # User chose a different pool, add timeout and size settings
            default_kwargs["pool_timeout"] = 30
            default_kwargs["pool_size"] = 5
            default_kwargs["max_overflow"] = 10

        # Merge user kwargs with defaults (user kwargs take precedence)
        final_kwargs = {**default_kwargs, **engine_kwargs}

        # Create and store the shared engine
        self._shared_engine = create_async_engine(
            self.config.get_connection_string(), **final_kwargs
        )
        return self._shared_engine

    async def wait_for_ready(self, max_retries: int = 15, delay: float = 1.0) -> bool:
        """Wait for database to be ready and responsive.

        NOTE: This method requires SQLAlchemy to be installed.

        Args:
            max_retries: Maximum number of connection attempts
            delay: Delay between attempts in seconds

        Returns:
            True if database becomes ready, False otherwise

        Raises:
            ImportError: If SQLAlchemy is not installed
        """
        try:
            from sqlalchemy import text
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy is required for wait_for_ready(). "
                "Install with: pip install py-pglite[sqlalchemy]"
            ) from e

        # Use the shared engine that get_engine() creates
        engine = self.get_engine(pool_pre_ping=False)

        for attempt in range(max_retries):
            try:
                async with engine.begin() as conn:
                    # Test basic connectivity
                    result = await conn.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row is not None and row[0] == 1:
                        # Additional check:
                        # try to create a temporary table to ensure DDL works
                        try:
                            await conn.execute(
                                text("CREATE TEMP TABLE readiness_test (id INTEGER)")
                            )
                            await conn.execute(text("DROP TABLE readiness_test"))
                            await conn.commit()  # Ensure transaction completes
                        except Exception as ddl_error:
                            # If DDL fails, continue retrying
                            self.logger.warning(
                                f"DDL test failed (attempt {attempt + 1}): {ddl_error}"
                            )
                            if attempt < max_retries - 1:
                                time.sleep(delay)
                                continue
                            else:
                                raise

                        self.logger.info(f"Database ready after {attempt + 1} attempts")

                        # Give a small additional delay to ensure stability
                        time.sleep(0.2)
                        return True

            except Exception as e:
                self.logger.warning(
                    f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Database failed to become ready after {max_retries} attempts"
                    )
                    raise
        return False

    async def stop(self) -> None:
        """Stop the PGlite server with proper SQLAlchemy cleanup."""
        if self.process is None:
            return

        try:
            # Send SIGTERM first for graceful shutdown
            self.logger.debug("Sending SIGTERM to PGlite process...")
            self.process.terminate()

            # Wait for graceful shutdown with timeout
            try:
                self.process.wait(timeout=5)
                self.logger.info("PGlite server stopped gracefully")
            except Exception:
                # Force kill if graceful shutdown fails
                self.logger.warning(
                    "PGlite process didn't stop gracefully, force killing..."
                )
                self.process.kill()
                try:
                    self.process.wait(timeout=2)
                    self.logger.info("PGlite server stopped forcefully")
                except Exception:
                    self.logger.error("Failed to kill PGlite process!")

        except Exception as e:
            self.logger.warning(f"Error stopping PGlite: {e}")
        finally:
            self.process = None
            # Clean up shared engine properly
            if hasattr(self, "_shared_engine") and self._shared_engine is not None:
                try:
                    await self._shared_engine.dispose()
                except Exception as e:
                    self.logger.warning(f"Error disposing engine: {e}")
                finally:
                    self._shared_engine = None
            if self.config.cleanup_on_exit:
                self._cleanup_socket()


__all__ = ["SQLAlchemyAsyncPGliteManager"]
