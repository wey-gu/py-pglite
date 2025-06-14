"""Configuration for PGlite testing."""

import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .extensions import SUPPORTED_EXTENSIONS


def _get_secure_socket_path() -> str:
    """Generate a secure socket path in user's temp directory."""
    temp_dir = Path(tempfile.gettempdir()) / f"py-pglite-{os.getpid()}"
    temp_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    # Use PostgreSQL's standard socket naming convention
    return str(temp_dir / ".s.PGSQL.5432")


@dataclass
class PGliteConfig:
    """Configuration for PGlite test database.

    Args:
        timeout: Timeout in seconds for PGlite startup (default: 30)
        cleanup_on_exit: Whether to cleanup socket/process on exit (default: True)
        log_level: Logging level for PGlite operations (default: "INFO")
        socket_path: Custom socket path (default: secure temp directory)
        work_dir: Working directory for PGlite files (default: None, uses temp)
        node_modules_check: Whether to verify node_modules exists (default: True)
        auto_install_deps: Whether to auto-install npm dependencies (default: True)
        extensions: List of PGlite extensions to enable (e.g., ["pgvector"])
    """

    timeout: int = 30
    cleanup_on_exit: bool = True
    log_level: str = "INFO"
    socket_path: str = field(default_factory=_get_secure_socket_path)
    work_dir: Path | None = None
    node_modules_check: bool = True
    auto_install_deps: bool = True
    extensions: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log_level: {self.log_level}")

        if self.extensions:
            for ext in self.extensions:
                if ext not in SUPPORTED_EXTENSIONS:
                    raise ValueError(
                        f"Unsupported extension: '{ext}'. "
                        f"Available extensions: {list(SUPPORTED_EXTENSIONS.keys())}"
                    )

        if self.work_dir is not None:
            self.work_dir = Path(self.work_dir).resolve()

    @property
    def log_level_int(self) -> int:
        """Get logging level as integer."""
        level_value = getattr(logging, self.log_level)
        return int(level_value)

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string for PGlite."""
        # For psycopg with Unix domain sockets, we need to specify the directory
        # and use the standard PostgreSQL socket naming convention
        socket_dir = str(Path(self.socket_path).parent)

        # Use the socket directory as host - psycopg will look for .s.PGSQL.5432
        connection_string = (
            f"postgresql+psycopg://postgres:postgres@/postgres?host={socket_dir}"
        )

        return connection_string

    def get_dsn(self) -> str:
        """Get PostgreSQL DSN connection string for direct psycopg usage."""
        socket_dir = str(Path(self.socket_path).parent)
        # Use key-value format for psycopg DSN, including password
        return f"host={socket_dir} dbname=postgres user=postgres password=postgres"
