"""Comprehensive tests for PGlite manager module."""

import subprocess
import tempfile

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import psutil
import pytest

from py_pglite.config import PGliteConfig
from py_pglite.manager import PGliteManager


class TestPGliteManagerInitialization:
    """Test PGliteManager initialization and basic setup."""

    def test_init_with_default_config(self):
        """Test manager initialization with default config."""
        manager = PGliteManager()

        assert isinstance(manager.config, PGliteConfig)
        assert manager.process is None
        assert manager.work_dir is None
        assert manager._original_cwd is None
        assert manager._shared_engine is None
        assert manager.logger is not None

    def test_init_with_custom_config(self):
        """Test manager initialization with custom config."""
        config = PGliteConfig(
            socket_path="/tmp/custom_socket", timeout=30, cleanup_on_exit=False
        )
        manager = PGliteManager(config)

        assert manager.config is config
        assert manager.config.socket_path == "/tmp/custom_socket"
        assert manager.config.timeout == 30
        assert manager.config.cleanup_on_exit is False

    def test_logger_setup(self):
        """Test logger configuration during initialization."""
        config = PGliteConfig(log_level="DEBUG")

        with (
            patch("logging.getLogger") as mock_get_logger,
            patch("logging.StreamHandler") as mock_handler_class,
        ):
            mock_logger = Mock()
            mock_logger.handlers = []  # No existing handlers
            mock_handler = Mock()
            mock_get_logger.return_value = mock_logger
            mock_handler_class.return_value = mock_handler

            manager = PGliteManager(config)  # noqa: F841

            mock_get_logger.assert_called_once_with("py_pglite.manager")
            mock_handler_class.assert_called_once()
            mock_logger.addHandler.assert_called_once_with(mock_handler)


class TestPGliteManagerContextManager:
    """Test PGliteManager context manager functionality."""

    def test_context_manager_enter_exit(self):
        """Test context manager protocol."""
        manager = PGliteManager()

        with (
            patch.object(manager, "start") as mock_start,
            patch.object(manager, "stop") as mock_stop,
        ):
            with manager as ctx_manager:
                assert ctx_manager is manager
                mock_start.assert_called_once()

            mock_stop.assert_called_once()

    def test_context_manager_with_exception(self):
        """Test context manager cleanup when exception occurs."""
        manager = PGliteManager()

        with (
            patch.object(manager, "start") as mock_start,
            patch.object(manager, "stop") as mock_stop,
        ):
            try:
                with manager:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            mock_start.assert_called_once()
            mock_stop.assert_called_once()


class TestWorkingDirectorySetup:
    """Test working directory setup functionality."""

    def test_setup_work_dir_with_provided_dir(self):
        """Test work directory setup when directory is provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_path = Path(temp_dir) / "custom_work"
            config = PGliteConfig(work_dir=work_path)
            manager = PGliteManager(config)

            result = manager._setup_work_dir()

            assert result.resolve() == work_path.resolve()  # Resolve both paths
            assert work_path.exists()
            assert (work_path / "package.json").exists()
            assert (work_path / "pglite_manager.js").exists()

    def test_setup_work_dir_creates_temp_dir(self):
        """Test work directory setup creates temporary directory."""
        manager = PGliteManager()

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/py-pglite-test123"

            with (
                patch("pathlib.Path.exists", return_value=False),
                patch("builtins.open", mock_open_write()) as mock_open,  # noqa: F841
            ):
                result = manager._setup_work_dir()

                assert str(result) == "/tmp/py-pglite-test123"
                mock_mkdtemp.assert_called_once_with(prefix="py-pglite-")

    def test_package_json_creation(self):
        """Test package.json file creation."""
        manager = PGliteManager()

        with (
            patch("tempfile.mkdtemp", return_value="/tmp/test"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", mock_open_write()) as mock_open,
        ):
            manager._setup_work_dir()

            # Check package.json was written
            package_calls = [
                call for call in mock_open.call_args_list if "package.json" in str(call)
            ]
            assert len(package_calls) > 0

    def test_pglite_manager_js_creation_no_extensions(self):
        """Test pglite_manager.js creation without extensions."""
        manager = PGliteManager()

        with (
            patch("tempfile.mkdtemp", return_value="/tmp/test"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", mock_open_write()) as mock_open,
        ):
            manager._setup_work_dir()

            # Check JavaScript file was written
            js_calls = [
                call
                for call in mock_open.call_args_list
                if "pglite_manager.js" in str(call)
            ]
            assert len(js_calls) > 0

    def test_pglite_manager_js_creation_with_extensions(self):
        """Test pglite_manager.js creation with extensions."""
        config = PGliteConfig(extensions=["pgvector"])
        manager = PGliteManager(config)

        with (
            patch("tempfile.mkdtemp", return_value="/tmp/test"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", mock_open_write()) as mock_open,
        ):
            manager._setup_work_dir()

            # Verify JavaScript file creation
            js_calls = [
                call
                for call in mock_open.call_args_list
                if "pglite_manager.js" in str(call)
            ]
            assert len(js_calls) > 0

    def test_existing_files_not_overwritten(self):
        """Test that existing package.json and JS files are not overwritten."""
        manager = PGliteManager()

        with (
            patch("tempfile.mkdtemp", return_value="/tmp/test"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
        ):  # Files exist
            with patch("builtins.open") as mock_open:
                manager._setup_work_dir()

                # Should not have opened files for writing
                mock_open.assert_not_called()


class TestSocketAndProcessManagement:
    """Test socket cleanup and process management."""

    def test_cleanup_socket_success(self):
        """Test successful socket cleanup."""
        manager = PGliteManager()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            manager._cleanup_socket()

            mock_unlink.assert_called_once()

    def test_cleanup_socket_no_file(self):
        """Test socket cleanup when file doesn't exist."""
        manager = PGliteManager()

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            manager._cleanup_socket()

            mock_unlink.assert_not_called()

    def test_cleanup_socket_error_handling(self):
        """Test socket cleanup error handling."""
        manager = PGliteManager()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")),
        ):
            # Should not raise exception
            manager._cleanup_socket()

    def test_kill_existing_processes_success(self):
        """Test killing existing PGlite processes."""
        config = PGliteConfig(socket_path="/tmp/pglite-socket/socket")
        manager = PGliteManager(config)

        mock_proc1 = Mock()
        mock_proc1.info = {
            "pid": 1234,
            "name": "node",
            "cmdline": ["node", "pglite_manager.js"],
            "cwd": "/tmp/pglite-socket",  # Same directory as socket
        }

        mock_proc2 = Mock()
        mock_proc2.info = {
            "pid": 5678,
            "name": "python",
            "cmdline": ["python", "test.py"],
            "cwd": "/home/user",
        }

        with patch("psutil.process_iter", return_value=[mock_proc1, mock_proc2]):
            manager._kill_existing_processes()

            # Should kill the node process but not the python process
            mock_proc1.kill.assert_called_once()
            mock_proc1.wait.assert_called_once_with(timeout=5)
            mock_proc2.kill.assert_not_called()

    def test_kill_existing_processes_exception_handling(self):
        """Test exception handling in process killing."""
        manager = PGliteManager()

        with patch("psutil.process_iter", side_effect=Exception("psutil error")):
            # Should not raise exception
            manager._kill_existing_processes()


class TestDependencyInstallation:
    """Test npm dependency installation."""

    def test_install_dependencies_disabled(self):
        """Test dependency installation when disabled."""
        config = PGliteConfig(auto_install_deps=False)
        manager = PGliteManager(config)

        with patch("subprocess.run") as mock_run:
            manager._install_dependencies(Path("/tmp/test"))

            mock_run.assert_not_called()

    def test_install_dependencies_node_modules_exists(self):
        """Test dependency installation when node_modules exists."""
        config = PGliteConfig(auto_install_deps=True, node_modules_check=True)
        manager = PGliteManager(config)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("subprocess.run") as mock_run,
        ):
            manager._install_dependencies(Path("/tmp/test"))

            mock_run.assert_not_called()

    def test_install_dependencies_success(self):
        """Test successful dependency installation."""
        config = PGliteConfig(auto_install_deps=True, node_modules_check=True)
        manager = PGliteManager(config)

        mock_result = Mock()
        mock_result.stdout = "Dependencies installed successfully"

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            manager._install_dependencies(Path("/tmp/test"))

            mock_run.assert_called_once_with(
                ["npm", "install"],
                cwd=Path("/tmp/test"),
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )

    def test_install_dependencies_no_check(self):
        """Test dependency installation without node_modules check."""
        config = PGliteConfig(auto_install_deps=True, node_modules_check=False)
        manager = PGliteManager(config)

        with patch("subprocess.run") as mock_run:
            manager._install_dependencies(Path("/tmp/test"))

            mock_run.assert_not_called()


class TestProcessLifecycle:
    """Test PGlite process start/stop lifecycle."""

    def test_start_process_already_running(self):
        """Test start when process is already running."""
        manager = PGliteManager()
        manager.process = Mock()  # Simulate running process

        with (
            patch.object(manager, "_kill_existing_processes"),
            patch.object(manager, "_cleanup_socket"),
        ):
            manager.start()

            # Should exit early without starting new process

    def test_start_process_success(self):
        """Test successful process start."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running

        with (
            patch.object(manager, "_kill_existing_processes"),
            patch.object(manager, "_cleanup_socket"),
            patch.object(manager, "_setup_work_dir", return_value=Path("/tmp/test")),
            patch("os.getcwd", return_value="/original/dir"),
            patch("os.chdir"),
            patch.object(manager, "_install_dependencies"),
            patch(
                "py_pglite.utils.find_pglite_modules", return_value="/tmp/node_modules"
            ),
            patch("subprocess.Popen", return_value=mock_process),
            patch("pathlib.Path.exists", return_value=True),
            patch("socket.socket") as mock_socket_class,
            patch("time.sleep"),
        ):
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket

            manager.start()

            assert manager.process is mock_process

    def test_start_process_dies_during_startup(self):
        """Test handling of process death during startup."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process died
        mock_process.communicate.return_value = ("Error output", "")

        with (
            patch.object(manager, "_kill_existing_processes"),
            patch.object(manager, "_cleanup_socket"),
            patch.object(manager, "_setup_work_dir", return_value=Path("/tmp/test")),
            patch("os.getcwd", return_value="/original/dir"),
            patch("os.chdir"),
            patch.object(manager, "_install_dependencies"),
            patch("subprocess.Popen", return_value=mock_process),
            pytest.raises(RuntimeError, match="PGlite process died during startup"),
        ):
            manager.start()

    def test_start_timeout(self):
        """Test start timeout handling."""
        config = PGliteConfig(timeout=1)  # Short timeout
        manager = PGliteManager(config)

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running

        with (
            patch.object(manager, "_kill_existing_processes"),
            patch.object(manager, "_cleanup_socket"),
            patch.object(manager, "_setup_work_dir", return_value=Path("/tmp/test")),
            patch("os.getcwd", return_value="/original/dir"),
            patch("os.chdir"),
            patch.object(manager, "_install_dependencies"),
            patch("subprocess.Popen", return_value=mock_process),
            patch("pathlib.Path.exists", return_value=False),
            patch("time.sleep"),
        ):
            with pytest.raises(RuntimeError, match="failed to start within"):
                manager.start()

            mock_process.terminate.assert_called_once()

    def test_stop_no_process(self):
        """Test stop when no process is running."""
        manager = PGliteManager()

        # Should not raise exception
        manager.stop()

    def test_stop_graceful_shutdown(self):
        """Test graceful process stop."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.wait.return_value = None  # Graceful shutdown
        manager.process = mock_process

        with patch.object(manager, "_cleanup_socket"):
            manager.stop()

            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once_with(timeout=5)
            assert manager.process is None

    def test_stop_force_kill(self):
        """Test force kill when graceful shutdown fails."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]
        manager.process = mock_process

        with patch.object(manager, "_cleanup_socket"):
            manager.stop()

            mock_process.terminate.assert_called_once()
            assert mock_process.wait.call_count == 2  # Graceful then force
            mock_process.kill.assert_called_once()

    def test_stop_error_handling(self):
        """Test error handling in stop method."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.terminate.side_effect = Exception("Process error")
        manager.process = mock_process

        with patch.object(manager, "_cleanup_socket"):
            # Should not raise exception
            manager.stop()

            assert manager.process is None


class TestConnectionAndStatus:
    """Test connection string and status methods."""

    def test_is_running_no_process(self):
        """Test is_running when no process exists."""
        manager = PGliteManager()

        assert not manager.is_running()

    def test_is_running_process_alive(self):
        """Test is_running when process is alive."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process alive
        manager.process = mock_process

        assert manager.is_running()

    def test_is_running_process_dead(self):
        """Test is_running when process is dead."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process dead
        manager.process = mock_process

        assert not manager.is_running()

    def test_get_connection_string_not_running(self):
        """Test get_connection_string when not running."""
        manager = PGliteManager()

        with pytest.raises(RuntimeError, match="PGlite server is not running"):
            manager.get_connection_string()

    def test_get_connection_string_success(self):
        """Test get_connection_string when running."""
        manager = PGliteManager()
        manager.process = Mock()

        with (
            patch.object(manager, "is_running", return_value=True),
            patch.object(
                manager.config,
                "get_connection_string",
                return_value="postgresql://test",
            ),
        ):
            result = manager.get_connection_string()

            assert result == "postgresql://test"

    def test_get_dsn_not_running(self):
        """Test get_dsn when not running."""
        manager = PGliteManager()

        with pytest.raises(RuntimeError, match="PGlite server is not running"):
            manager.get_dsn()

    def test_get_dsn_success(self):
        """Test get_dsn when running."""
        manager = PGliteManager()
        manager.process = Mock()

        with (
            patch.object(manager, "is_running", return_value=True),
            patch.object(manager.config, "get_dsn", return_value="host=/tmp/socket"),
        ):
            result = manager.get_dsn()

            assert result == "host=/tmp/socket"

    def test_get_psycopg_uri_not_running(self):
        """Test get_psycopg_uri when not running."""
        manager = PGliteManager()

        with pytest.raises(RuntimeError, match="PGlite server is not running"):
            manager.get_psycopg_uri()

    def test_get_psycopg_uri_success(self):
        """Test get_psycopg_uri when running."""
        manager = PGliteManager()
        manager.process = Mock()

        with (
            patch.object(manager, "is_running", return_value=True),
            patch.object(
                manager.config, "get_psycopg_uri", return_value="postgresql://uri"
            ),
        ):
            result = manager.get_psycopg_uri()

            assert result == "postgresql://uri"


class TestReadinessWaiting:
    """Test database readiness waiting functionality."""

    def test_wait_for_ready_basic_success(self):
        """Test successful wait_for_ready_basic."""
        manager = PGliteManager()

        with (
            patch("py_pglite.utils.check_connection", return_value=True),
            patch.object(manager.config, "get_dsn", return_value="host=/tmp/socket"),
            patch("time.sleep"),
        ):
            result = manager.wait_for_ready_basic(max_retries=3, delay=0.1)

            assert result is True

    def test_wait_for_ready_basic_failure(self):
        """Test wait_for_ready_basic with connection failures."""
        manager = PGliteManager()

        with (
            patch("py_pglite.utils.check_connection", return_value=False),
            patch.object(manager.config, "get_dsn", return_value="host=/tmp/socket"),
            patch("time.sleep"),
        ):
            result = manager.wait_for_ready_basic(max_retries=2, delay=0.1)

            assert result is False

    def test_wait_for_ready_basic_exception_handling(self):
        """Test wait_for_ready_basic exception handling."""
        manager = PGliteManager()

        with (
            patch(
                "py_pglite.utils.check_connection",
                side_effect=Exception("Connection error"),
            ),
            patch.object(manager.config, "get_dsn", return_value="host=/tmp/socket"),
            patch("time.sleep"),
        ):
            result = manager.wait_for_ready_basic(max_retries=2, delay=0.1)

            assert result is False

    def test_wait_for_ready_alias(self):
        """Test that wait_for_ready is an alias for wait_for_ready_basic."""
        manager = PGliteManager()

        with patch.object(
            manager, "wait_for_ready_basic", return_value=True
        ) as mock_basic:
            result = manager.wait_for_ready(max_retries=5, delay=0.5)

            assert result is True
            mock_basic.assert_called_once_with(max_retries=5, delay=0.5)


class TestRestartFunctionality:
    """Test restart functionality."""

    def test_restart_not_running(self):
        """Test restart when not currently running."""
        manager = PGliteManager()

        with (
            patch.object(manager, "is_running", return_value=False),
            patch.object(manager, "stop") as mock_stop,
            patch.object(manager, "start") as mock_start,
        ):
            manager.restart()

            mock_stop.assert_not_called()
            mock_start.assert_called_once()

    def test_restart_currently_running(self):
        """Test restart when currently running."""
        manager = PGliteManager()

        with (
            patch.object(manager, "is_running", return_value=True),
            patch.object(manager, "stop") as mock_stop,
            patch.object(manager, "start") as mock_start,
        ):
            manager.restart()

            mock_stop.assert_called_once()
            mock_start.assert_called_once()


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_node_options_environment(self):
        """Test NODE_OPTIONS environment variable setting."""
        config = PGliteConfig(node_options="--max-old-space-size=4096")
        manager = PGliteManager(config)

        mock_process = Mock()
        mock_process.poll.return_value = None

        with (
            patch.object(manager, "_kill_existing_processes"),
            patch.object(manager, "_cleanup_socket"),
            patch.object(manager, "_setup_work_dir", return_value=Path("/tmp/test")),
            patch("os.getcwd", return_value="/original/dir"),
            patch("os.chdir"),
            patch.object(manager, "_install_dependencies"),
            patch("py_pglite.utils.find_pglite_modules", return_value=None),
            patch("subprocess.Popen", return_value=mock_process) as mock_popen,
            patch("pathlib.Path.exists", return_value=True),
            patch("socket.socket"),
            patch("time.sleep"),
        ):
            manager.start()

            # Check that NODE_OPTIONS was set in environment
            call_args = mock_popen.call_args
            env = call_args[1]["env"]
            assert env["NODE_OPTIONS"] == "--max-old-space-size=4096"


def mock_open_write():
    """Helper to create a mock for file writing operations."""
    mock = Mock()
    mock.return_value.__enter__ = Mock()
    mock.return_value.__exit__ = Mock()
    return mock
