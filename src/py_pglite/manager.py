"""Core PGlite process management."""

import json
import logging
import os
import subprocess  # nosec B404 - subprocess needed for npm/node process management
import sys
import tempfile
import time

from pathlib import Path
from textwrap import dedent
from typing import Any

import psutil

from py_pglite import __version__
from py_pglite.config import PGliteConfig
from py_pglite.extensions import SUPPORTED_EXTENSIONS
from py_pglite.utils import find_pglite_modules


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
            # Generate JavaScript for extensions
            ext_requires = []
            ext_configs = []
            if self.config.extensions:
                for ext_name in self.config.extensions:
                    ext_info = SUPPORTED_EXTENSIONS[ext_name]
                    ext_requires.append(
                        f"const {{ {ext_info['name']} }} = require('{ext_info['module']}');"
                    )
                    ext_configs.append(f"    {ext_name}: {ext_info['name']}")

            ext_requires_str = "\n".join(ext_requires)
            ext_configs_str = ",\n".join(ext_configs)
            extensions_obj_str = f"{{\n{ext_configs_str}\n}}" if ext_configs else "{}"

            # Generate JavaScript content based on socket mode
            if self.config.use_tcp:
                js_content = self._generate_tcp_js_content(
                    ext_requires_str, extensions_obj_str
                )
            else:
                js_content = self._generate_unix_js_content(
                    ext_requires_str, extensions_obj_str
                )
            with open(manager_js, "w") as f:
                f.write(js_content)

        return work_dir

    def _generate_unix_js_content(
        self, ext_requires_str: str, extensions_obj_str: str
    ) -> str:
        """Generate JavaScript content for Unix socket mode (original logic)."""
        return dedent(f"""
            const {{ PGlite }} = require('@electric-sql/pglite');
            const {{ PGLiteSocketServer }} = require('@electric-sql/pglite-socket');
            const fs = require('fs');
            const path = require('path');
            const {{ unlink }} = require('fs/promises');
            const {{ existsSync }} = require('fs');
            {ext_requires_str}

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
                    // Create a PGlite instance with extensions
                    const db = new PGlite({{
                        extensions: {extensions_obj_str}
                    }});

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

            startServer();
        """).strip()

    def _generate_tcp_js_content(
        self, ext_requires_str: str, extensions_obj_str: str
    ) -> str:
        """Generate JavaScript content for TCP socket mode."""
        return dedent(f"""
            const {{ PGlite }} = require('@electric-sql/pglite');
            const {{ PGLiteSocketServer }} = require('@electric-sql/pglite-socket');
            const fs = require('fs');
            const path = require('path');
            {ext_requires_str}

            async function startServer() {{
                try {{
                    // Create a PGlite instance with extensions
                    const db = new PGlite({{
                        extensions: {extensions_obj_str}
                    }});

                    // Create and start a TCP server
                    const server = new PGLiteSocketServer({{
                        db,
                        host: '{self.config.tcp_host}',
                        port: {self.config.tcp_port}
                    }});
                    await server.start();
                    console.log(`Server started on TCP {self.config.tcp_host}:{self.config.tcp_port}`);

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

            startServer();
        """).strip()

    def _cleanup_socket(self) -> None:
        """Clean up the PGlite socket file."""
        # Skip cleanup for TCP mode
        if self.config.use_tcp:
            return

        socket_path = Path(self.config.socket_path)
        if socket_path.exists():
            try:
                socket_path.unlink()
                self.logger.info(f"Cleaned up socket at {socket_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up socket: {e}")

    def _kill_existing_processes(self) -> None:
        """Kill any existing PGlite processes that might conflict with this socket."""
        try:
            my_socket_dir = str(Path(self.config.socket_path).parent)
            for proc in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
                if proc.info["cmdline"] and any(
                    "pglite_manager.js" in cmd for cmd in proc.info["cmdline"]
                ):
                    # Only kill processes in the same socket directory to avoid killing other instances
                    try:
                        proc_cwd = proc.info.get("cwd", "")
                        if my_socket_dir in proc_cwd or proc_cwd in my_socket_dir:
                            pid = proc.info["pid"]
                            self.logger.info(f"Killing existing PGlite process: {pid}")
                            proc.kill()
                            proc.wait(timeout=5)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process already gone or can't access it
                        continue
        except Exception as e:
            self.logger.warning(f"Error killing existing PGlite processes: {e}")

    def _kill_all_pglite_processes(self) -> None:
        """Kill all PGlite processes globally (more aggressive cleanup for termination)."""
        try:
            killed_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["cmdline"] and any(
                    "pglite_manager.js" in cmd for cmd in proc.info["cmdline"]
                ):
                    try:
                        pid = proc.info["pid"]
                        self.logger.info(f"Killing PGlite process globally: {pid}")
                        proc.kill()
                        proc.wait(timeout=5)
                        killed_processes.append(pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process already gone or can't access it
                        continue
            
            if killed_processes:
                self.logger.info(f"Killed {len(killed_processes)} PGlite processes: {killed_processes}")
        except Exception as e:
            self.logger.warning(f"Error killing all PGlite processes: {e}")

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

            # Prepare environment for Node.js process
            env = os.environ.copy()
            if self.config.node_options:
                env["NODE_OPTIONS"] = self.config.node_options
                self.logger.info(
                    f"Using custom NODE_OPTIONS: {self.config.node_options}"
                )

            # Ensure Node.js can find the required modules
            node_modules_path = find_pglite_modules(self.work_dir)
            if node_modules_path:
                env["NODE_PATH"] = str(node_modules_path)
                self.logger.info(f"Setting NODE_PATH to: {node_modules_path}")

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
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None,  # Create new process group on Unix
            )

            # Wait for startup with robust monitoring
            start_time = time.time()
            ready_logged = False

            while time.time() - start_time < self.config.timeout:
                # Check if process died
                if self.process.poll() is not None:
                    # Get output with timeout to prevent hanging
                    try:
                        stdout, _ = self.process.communicate(timeout=2)
                        output = (
                            stdout[:1000] if stdout else "No output"
                        )  # Limit output
                    except subprocess.TimeoutExpired:
                        output = "Process output timeout"

                    raise RuntimeError(
                        f"PGlite process died during startup. Output: {output}"
                    )

                # Check readiness based on socket mode
                if self.config.use_tcp:
                    # TCP readiness check
                    if not ready_logged:
                        self.logger.info(
                            f"Waiting for TCP server on {self.config.tcp_host}:{self.config.tcp_port}..."
                        )
                        ready_logged = True

                    try:
                        import socket

                        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_socket.settimeout(1)
                        test_socket.connect(
                            (self.config.tcp_host, self.config.tcp_port)
                        )
                        test_socket.close()
                        self.logger.info(
                            f"PGlite TCP server started successfully on {self.config.tcp_host}:{self.config.tcp_port}"
                        )
                        break
                    except (ImportError, OSError):
                        # TCP port not ready yet, continue waiting
                        pass
                else:
                    # Unix socket readiness check
                    socket_path = Path(self.config.socket_path)
                    if socket_path.exists() and not ready_logged:
                        self.logger.info(
                            "PGlite socket created, server should be ready..."
                        )
                        ready_logged = True

                        # Test basic connectivity to ensure it's really ready
                        try:
                            import socket

                            test_socket = socket.socket(
                                socket.AF_UNIX, socket.SOCK_STREAM
                            )
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
            
            # Try to terminate the entire process group if it exists
            if hasattr(os, 'killpg') and hasattr(self.process, 'pid'):
                try:
                    # Try to kill the process group first (includes child processes)
                    os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM
                    self.logger.debug("Sent SIGTERM to process group")
                except (OSError, ProcessLookupError):
                    # Fall back to single process termination
                    self.process.terminate()
            else:
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
                
                # Try to kill the entire process group first
                if hasattr(os, 'killpg') and hasattr(self.process, 'pid'):
                    try:
                        os.killpg(os.getpgid(self.process.pid), 9)  # SIGKILL
                        self.logger.debug("Sent SIGKILL to process group")
                    except (OSError, ProcessLookupError):
                        # Fall back to single process kill
                        self.process.kill()
                else:
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
            # Additional cleanup: kill any remaining pglite processes
            self._kill_all_pglite_processes()
            if self.config.cleanup_on_exit:
                self._cleanup_socket()

    def is_running(self) -> bool:
        """Check if PGlite process is running."""
        return self.process is not None and self.process.poll() is None

    def get_connection_string(self) -> str:
        """Get the database connection string for framework-agnostic usage.

        Returns:
            PostgreSQL connection string

        Raises:
            RuntimeError: If PGlite server is not running
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        return self.config.get_connection_string()

    def get_dsn(self) -> str:
        """Get the database DSN string for framework-agnostic usage.

        Returns:
            PostgreSQL DSN string
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        return self.config.get_dsn()

    def wait_for_ready_basic(self, max_retries: int = 15, delay: float = 1.0) -> bool:
        """Wait for database to be ready using framework-agnostic connection test.

        Args:
            max_retries: Maximum number of connection attempts
            delay: Delay between attempts in seconds

        Returns:
            True if database becomes ready, False otherwise
        """
        from py_pglite.utils import check_connection

        for attempt in range(max_retries):
            try:
                # Use DSN format for direct psycopg connection testing
                if check_connection(self.config.get_dsn()):
                    self.logger.info(f"Database ready after {attempt + 1} attempts")
                    time.sleep(0.2)  # Small stability delay
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

        return False

    def wait_for_ready(self, max_retries: int = 15, delay: float = 1.0) -> bool:
        """Wait for database to be ready (framework-agnostic).

        This is an alias for wait_for_ready_basic() to maintain API consistency
        across different manager types while keeping the base manager framework-agnostic.

        Args:
            max_retries: Maximum number of connection attempts
            delay: Delay between attempts in seconds

        Returns:
            True if database becomes ready, False otherwise
        """
        return self.wait_for_ready_basic(max_retries=max_retries, delay=delay)

    def restart(self) -> None:
        """Restart the PGlite server.

        Stops the current server if running and starts a new one.
        """
        if self.is_running():
            self.stop()
        self.start()

    def get_psycopg_uri(self) -> str:
        """Get the database URI for psycopg usage.

        Returns:
            PostgreSQL URI string compatible with psycopg

        Raises:
            RuntimeError: If PGlite server is not running
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        return self.config.get_psycopg_uri()

    def get_asyncpg_uri(self) -> str:
        """Get the database URI for asyncpg usage.

        Returns:
            PostgreSQL URI string compatible with asyncpg.connect()

        Raises:
            RuntimeError: If PGlite server is not running
        """
        if not self.is_running():
            raise RuntimeError("PGlite server is not running. Call start() first.")

        return self.config.get_asyncpg_uri()
