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
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from . import __version__
from .config import PGliteConfig


class PGliteManager:
    """Manages PGlite process lifecycle for testing.

    Handles starting, stopping, and health monitoring of PGlite server processes.
    Provides SQLAlchemy engines connected to the PGlite instance.
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
            await server.stop();
            await db.close();
            console.log('Server stopped and database closed');
            process.exit(0);
        }});

        process.on('SIGTERM', async () => {{
            await server.stop();
            await db.close();
            console.log('Server stopped and database closed');
            process.exit(0);
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

            # Start PGlite process
            self.logger.info("Starting PGlite server...")
            # nosec B603,B607 - node with fixed script, safe for testing library
            self.process = subprocess.Popen(
                ["node", "pglite_manager.js"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Wait for startup with real-time output monitoring
            start_time = time.time()
            socket_path = Path(self.config.socket_path)

            while time.time() - start_time < self.config.timeout:
                # Check if process died
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    raise RuntimeError(
                        f"PGlite process died: stdout={stdout}, stderr={stderr}"
                    )

                # Check if socket exists - simpler approach like working version
                if socket_path.exists():
                    self.logger.info("PGlite socket created, server should be ready...")
                    # Give it a moment to be fully ready
                    time.sleep(2)
                    self.logger.info("PGlite server started successfully")
                    break

                time.sleep(1.0)  # Check less frequently
            else:
                # Timeout
                if self.process.poll() is None:
                    self.process.kill()
                stdout, stderr = self.process.communicate()
                raise RuntimeError(
                    f"PGlite server failed to start within {self.config.timeout} "
                    f"seconds: stdout={stdout}, stderr={stderr}"
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
            # Send SIGTERM first
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill
                self.process.kill()
                self.process.wait()

            self.logger.info("PGlite server stopped")

        except Exception as e:
            self.logger.warning(f"Error stopping PGlite: {e}")
        finally:
            self.process = None
            if self.config.cleanup_on_exit:
                self._cleanup_socket()

    def is_running(self) -> bool:
        """Check if PGlite process is running."""
        return self.process is not None and self.process.poll() is None

    def wait_for_ready(self, max_retries: int = 15, delay: float = 1.0) -> bool:
        """Wait for database to be ready and responsive."""
        # Create engine once and reuse it
        engine = self.get_engine()

        for attempt in range(max_retries):
            try:
                with engine.connect() as conn:
                    # Test basic connectivity
                    result = conn.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row is not None and row[0] == 1:
                        self.logger.info(f"Database ready after {attempt + 1} attempts")
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

    def get_engine(self, **engine_kwargs: Any) -> Engine:
        """Get SQLAlchemy engine connected to PGlite.

        Args:
            **engine_kwargs: Additional arguments for create_engine

        Returns:
            SQLAlchemy Engine connected to PGlite
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        default_kwargs = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_timeout": 30,
            "connect_args": {"connect_timeout": 10, "application_name": "py-pglite"},
        }
        default_kwargs.update(engine_kwargs)

        return create_engine(self.config.get_connection_string(), **default_kwargs)
