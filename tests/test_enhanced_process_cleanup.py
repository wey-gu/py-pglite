"""Tests for enhanced process cleanup functionality."""

import os
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


class TestEnhancedProcessCleanup:
    """Test enhanced process cleanup functionality."""

    def test_kill_all_pglite_processes_success(self):
        """Test killing all PGlite processes globally."""
        manager = PGliteManager()

        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            "pid": 1234,
            "name": "node",
            "cmdline": ["node", "pglite_manager.js"],
        }

        mock_proc2 = Mock()
        mock_proc2.info = {
            "pid": 5678,
            "name": "node",
            "cmdline": ["node", "other_script.js"],
        }

        mock_proc3 = Mock()
        mock_proc3.info = {
            "pid": 9999,
            "name": "node",
            "cmdline": ["node", "pglite_manager.js", "--port", "5433"],
        }

        with patch(
            "psutil.process_iter", return_value=[mock_proc1, mock_proc2, mock_proc3]
        ):
            manager._kill_all_pglite_processes()

            # Should kill processes 1 and 3 (containing pglite_manager.js) but not 2
            mock_proc1.kill.assert_called_once()
            mock_proc1.wait.assert_called_once_with(timeout=5)

            mock_proc2.kill.assert_not_called()

            mock_proc3.kill.assert_called_once()
            mock_proc3.wait.assert_called_once_with(timeout=5)

    def test_kill_all_pglite_processes_with_exception(self):
        """Test handling exceptions during global process cleanup."""
        manager = PGliteManager()

        mock_proc1 = Mock()
        mock_proc1.info = {
            "pid": 1234,
            "name": "node",
            "cmdline": ["node", "pglite_manager.js"],
        }
        mock_proc1.kill.side_effect = psutil.NoSuchProcess(1234)

        mock_proc2 = Mock()
        mock_proc2.info = {
            "pid": 5678,
            "name": "node",
            "cmdline": ["node", "pglite_manager.js"],
        }

        with patch("psutil.process_iter", return_value=[mock_proc1, mock_proc2]):
            manager._kill_all_pglite_processes()

            # Should attempt to kill both processes
            mock_proc1.kill.assert_called_once()
            mock_proc1.wait.assert_not_called()  # Exception prevents wait

            mock_proc2.kill.assert_called_once()
            mock_proc2.wait.assert_called_once_with(timeout=5)

    def test_kill_all_pglite_processes_no_processes(self):
        """Test global cleanup when no PGlite processes exist."""
        manager = PGliteManager()

        mock_proc = Mock()
        mock_proc.info = {
            "pid": 1234,
            "name": "python",
            "cmdline": ["python", "test.py"],
        }

        with patch("psutil.process_iter", return_value=[mock_proc]):
            manager._kill_all_pglite_processes()

            # Should not kill any processes
            mock_proc.kill.assert_not_called()

    def test_kill_all_pglite_processes_exception_handling(self):
        """Test exception handling in global process cleanup."""
        manager = PGliteManager()

        with patch("psutil.process_iter", side_effect=Exception("psutil error")):
            # Should not raise exception
            manager._kill_all_pglite_processes()

    @patch("os.setsid")
    def test_start_with_process_group(self, mock_setsid):
        """Test that process starts with process group on Unix systems."""
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
            patch("subprocess.Popen", return_value=mock_process) as mock_popen,
            patch("pathlib.Path.exists", return_value=True),
            patch("socket.socket") as mock_socket_class,
            patch("time.sleep"),
            patch("os.setsid", mock_setsid),
        ):
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket

            manager.start()

            # Check that subprocess.Popen was called with preexec_fn
            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert "preexec_fn" in call_kwargs
            assert call_kwargs["preexec_fn"] is not None

    def test_start_without_setsid(self):
        """Test that process starts without process group when setsid not available."""
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
            patch("subprocess.Popen", return_value=mock_process) as mock_popen,
            patch("pathlib.Path.exists", return_value=True),
            patch("socket.socket") as mock_socket_class,
            patch("time.sleep"),
            patch("os.setsid", None),  # Simulate setsid not available
        ):
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket

            manager.start()

            # Check that subprocess.Popen was called with preexec_fn=None
            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs.get("preexec_fn") is None


class TestEnhancedStopMethod:
    """Test enhanced stop method with process group handling."""

    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_with_process_group_graceful(self, mock_getpgid, mock_killpg):
        """Test graceful stop with process group termination."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.return_value = None  # Graceful termination
        manager.process = mock_process

        mock_getpgid.return_value = 1234

        with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
            manager.stop()

            # Should use process group termination
            mock_getpgid.assert_called_once_with(1234)
            mock_killpg.assert_called_once_with(1234, 15)  # SIGTERM
            mock_process.wait.assert_called_once_with(timeout=5)
            mock_cleanup.assert_called_once()

    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_with_process_group_force_kill(self, mock_getpgid, mock_killpg):
        """Test force kill with process group termination."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]
        manager.process = mock_process

        mock_getpgid.return_value = 1234

        with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
            manager.stop()

            # Should use process group termination for both SIGTERM and SIGKILL
            mock_getpgid.assert_has_calls([call(1234), call(1234)])
            mock_killpg.assert_has_calls(
                [call(1234, 15), call(1234, 9)]
            )  # SIGTERM, then SIGKILL
            mock_cleanup.assert_called_once()

    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_fallback_to_single_process(self, mock_getpgid, mock_killpg):
        """Test fallback to single process termination when process group fails."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.return_value = None
        manager.process = mock_process

        # Simulate process group operations failing
        mock_getpgid.side_effect = OSError("No such process")

        with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
            manager.stop()

            # Should fall back to single process termination
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once_with(timeout=5)
            mock_cleanup.assert_called_once()

    def test_stop_without_killpg(self):
        """Test stop behavior when killpg is not available."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.return_value = None
        manager.process = mock_process

        # Temporarily remove killpg from os module to simulate it not being available
        original_killpg = getattr(os, 'killpg', None)
        if hasattr(os, 'killpg'):
            delattr(os, 'killpg')

        try:
            with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
                manager.stop()

                # Should use single process termination
                mock_process.terminate.assert_called_once()
                mock_process.wait.assert_called_once_with(timeout=5)
                mock_cleanup.assert_called_once()
        finally:
            # Restore killpg if it existed
            if original_killpg is not None:
                setattr(os, 'killpg', original_killpg)
