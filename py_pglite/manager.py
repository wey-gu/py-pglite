"""Core PGlite process management."""

import json
import logging
import os
import subprocess  # nosec B404 - subprocess needed for npm/node process management
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

from . import __version__
from .config import PGliteConfig


class PGliteManager:
    """Manages PGlite process lifecycle for testing.

    Framework-agnostic PGlite process manager. Provides database connections
    through framework-specific methods that require their respective dependencies.
    """

    def __init__(self, config: PGliteConfig | None = None):
        """Initialize PGlite manager.

        Args:
            config: Configuration for PGlite. If None, uses defaults.
        """
        self.config = config or PGliteConfig()
        self.process: subprocess.Popen[str] | None = None
        self.work_dir: Path | None = None
        self._original_cwd: str | None = None
        self._shared_engine: Any | None = None

        # Set up logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.config.log_level_int)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(self.config.log_level_int)

    def __enter__(self) -> "PGliteManager":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()

    def _setup_work_dir(self) -> Path:
        """Setup working directory for PGlite files."""
        if self.config.work_dir:
            work_dir = self.config.work_dir
            work_dir.mkdir(parents=True, exist_ok=True)
        else:
            work_dir = Path(tempfile.mkdtemp(prefix="py-pglite-"))

        # Create package.json if it doesn't exist
        package_json = work_dir / "package.json"
        if not package_json.exists():
            package_content = {
                "name": "py-pglite-env",
                "version": __version__,
                "description": "PGlite test environment for py-pglite",
                "scripts": {"start": "node pglite_manager.js"},
                "dependencies": {
                    "@electric-sql/pglite": "^0.3.0",
                    "@electric-sql/pglite-socket": "^0.0.8",
                },
            }
            with open(package_json, "w") as f:
                json.dump(package_content, f, indent=2)

        # Create pglite_manager.js if it doesn't exist
        manager_js = work_dir / "pglite_manager.js"
        if not manager_js.exists():
            js_content = f"""const {{ PGlite }} = require('@electric-sql/pglite');
const {{ PGLiteSocketServer }} = require('@electric-sql/pglite-socket');
const fs = require('fs');
const path = require('path');
const {{ unlink }} = require('fs/promises');
const {{ existsSync }} = require('fs');

const SOCKET_PATH = '{self.config.socket_path}';

async function cleanup() {{
    if (existsSync(SOCKET_PATH)) {{
        try {{
            await unlink(SOCKET_PATH);
            console.log(`Removed old socket at ${{SOCKET_PATH}}`);
        }} catch (err) {{
            // Ignore errors during cleanup
        }}
    }}
}}

async function startServer() {{
    try {{
        // Create a PGlite instance
        const db = await PGlite.create();

        // Clean up any existing socket
        await cleanup();

        // Create and start a socket server
        const server = new PGLiteSocketServer({{
            db,
            path: SOCKET_PATH,
        }});
        await server.start();
        console.log(`Server started on socket ${{SOCKET_PATH}}`);

        // Handle graceful shutdown
        process.on('SIGINT', async () => {{
            console.log('Received SIGINT, shutting down gracefully...');
            try {{
                await server.stop();
                await db.close();
                console.log('Server stopped and database closed');
            }} catch (err) {{
                console.error('Error during shutdown:', err);
            }}
            process.exit(0);
        }});

        process.on('SIGTERM', async () => {{
            console.log('Received SIGTERM, shutting down gracefully...');
            try {{
                await server.stop();
                await db.close();
                console.log('Server stopped and database closed');
            }} catch (err) {{
                console.error('Error during shutdown:', err);
            }}
            process.exit(0);
        }});

        // Keep the process alive
        process.on('exit', () => {{
            console.log('Process exiting...');
        }});

    }} catch (err) {{
        console.error('Failed to start PGlite server:', err);
        process.exit(1);
    }}
}}

startServer();"""
            with open(manager_js, "w") as f:
                f.write(js_content)

        return work_dir

    def _cleanup_socket(self) -> None:
        """Clean up the PGlite socket file."""
        socket_path = Path(self.config.socket_path)
        if socket_path.exists():
            try:
                socket_path.unlink()
                self.logger.info(f"Cleaned up socket at {socket_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up socket: {e}")

    def _kill_existing_processes(self) -> None:
        """Kill any existing PGlite processes."""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["cmdline"] and any(
                    "pglite_manager.js" in cmd for cmd in proc.info["cmdline"]
                ):
                    pid = proc.info["pid"]
                    self.logger.info(f"Killing existing PGlite process: {pid}")
                    proc.kill()
                    proc.wait(timeout=5)
        except Exception as e:
            self.logger.warning(f"Error killing existing PGlite processes: {e}")

    def _install_dependencies(self, work_dir: Path) -> None:
        """Install npm dependencies if needed."""
        if not self.config.auto_install_deps:
            return

        node_modules = work_dir / "node_modules"
        if self.config.node_modules_check and not node_modules.exists():
            self.logger.info("Installing npm dependencies...")
            # nosec B603,B607 - npm install with fixed args, safe for testing library
            result = subprocess.run(
                ["npm", "install"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,  # Add timeout for npm install
            )
            self.logger.info(f"npm install completed: {result.stdout}")

    def start(self) -> None:
        """Start the PGlite server."""
        if self.process is not None:
            self.logger.warning("PGlite process already running")
            return

        # Setup
        self._kill_existing_processes()
        self._cleanup_socket()

        # Setup work directory
        self.work_dir = self._setup_work_dir()
        self._original_cwd = os.getcwd()
        os.chdir(self.work_dir)

        try:
            # Install dependencies
            self._install_dependencies(self.work_dir)

            # Start PGlite process with limited output buffering
            self.logger.info("Starting PGlite server...")
            # nosec B603,B607 - node with fixed script, safe for testing library
            self.process = subprocess.Popen(
                ["node", "pglite_manager.js"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=0,  # Unbuffered for real-time monitoring
                universal_newlines=True,
            )

            # Wait for startup with robust monitoring
            start_time = time.time()
            socket_path = Path(self.config.socket_path)
            ready_logged = False

            while time.time() - start_time < self.config.timeout:
                # Check if process died
                if self.process.poll() is not None:
                    # Get output with timeout to prevent hanging
                    try:
                        stdout, stderr = self.process.communicate(timeout=2)
                        output = (
                            stdout[:1000] if stdout else "No output"
                        )  # Limit output
                    except subprocess.TimeoutExpired:
                        output = "Process output timeout"

                    raise RuntimeError(
                        f"PGlite process died during startup. Output: {output}"
                    )

                # Check if socket exists and log ready message once
                if socket_path.exists() and not ready_logged:
                    self.logger.info("PGlite socket created, server should be ready...")
                    ready_logged = True

                    # Test basic connectivity to ensure it's really ready
                    try:
                        import socket

                        test_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        test_socket.settimeout(1)
                        test_socket.connect(str(socket_path))
                        test_socket.close()
                        self.logger.info("PGlite server started successfully")
                        break
                    except (ImportError, OSError):
                        # Socket exists but not ready yet, continue waiting
                        pass

                time.sleep(0.5)  # Check more frequently for better responsiveness
            else:
                # Timeout - cleanup and raise error
                if self.process and self.process.poll() is None:
                    self.logger.warning("PGlite server startup timeout, terminating...")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Force killing PGlite process...")
                        self.process.kill()
                        self.process.wait()

                raise RuntimeError(
                    f"PGlite server failed to start within {self.config.timeout} seconds"
                )

        finally:
            # Restore working directory
            if self._original_cwd:
                os.chdir(self._original_cwd)

    def stop(self) -> None:
        """Stop the PGlite server."""
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
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.logger.warning(
                    "PGlite process didn't stop gracefully, force killing..."
                )
                self.process.kill()
                try:
                    self.process.wait(timeout=2)
                    self.logger.info("PGlite server stopped forcefully")
                except subprocess.TimeoutExpired:
                    self.logger.error("Failed to kill PGlite process!")

        except Exception as e:
            self.logger.warning(f"Error stopping PGlite: {e}")
        finally:
            self.process = None
            # Clean up shared engine properly
            if hasattr(self, "_shared_engine") and self._shared_engine is not None:
                try:
                    self._shared_engine.dispose()
                except Exception as e:
                    self.logger.warning(f"Error disposing engine: {e}")
                finally:
                    self._shared_engine = None
            if self.config.cleanup_on_exit:
                self._cleanup_socket()

    def is_running(self) -> bool:
        """Check if PGlite process is running."""
        return self.process is not None and self.process.poll() is None

    def get_engine(self, **engine_kwargs: Any) -> Any:
        """Get SQLAlchemy engine connected to PGlite.

        NOTE: This method requires SQLAlchemy to be installed.

        IMPORTANT: Returns a shared engine instance to prevent connection timeouts.
        PGlite's socket server can only handle 1 connection at a time, so multiple
        engines would cause psycopg.errors.ConnectionTimeout. The shared engine
        architecture ensures all database operations use the same connection.

        Args:
            **engine_kwargs: Additional arguments for create_engine

        Returns:
            SQLAlchemy Engine connected to PGlite (shared instance)

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
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool, StaticPool
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
                "prepare_threshold": None,  # Disable prepared statements for test stability
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
        self._shared_engine = create_engine(
            self.config.get_connection_string(), **final_kwargs
        )
        return self._shared_engine

    def wait_for_ready(self, max_retries: int = 15, delay: float = 1.0) -> bool:
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
                with engine.connect() as conn:
                    # Test basic connectivity
                    result = conn.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row is not None and row[0] == 1:
                        # Additional check: try to create a temporary table to ensure DDL works
                        try:
                            conn.execute(
                                text("CREATE TEMP TABLE readiness_test (id INTEGER)")
                            )
                            conn.execute(text("DROP TABLE readiness_test"))
                            conn.commit()  # Ensure transaction completes
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
