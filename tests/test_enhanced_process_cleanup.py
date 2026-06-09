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
            # Global cleanup should NOT be called for graceful termination
            mock_cleanup.assert_not_called()

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
            # Global cleanup should NOT be called if the final wait succeeds
            mock_cleanup.assert_not_called()

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
            # Global cleanup should NOT be called for graceful termination
            mock_cleanup.assert_not_called()

    def test_stop_without_killpg(self):
        """Test stop behavior when killpg is not available."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.wait.return_value = None
        manager.process = mock_process

        # Temporarily remove killpg from os module to simulate it not being available
        original_killpg = getattr(os, "killpg", None)
        if hasattr(os, "killpg"):
            delattr(os, "killpg")

        try:
            with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
                manager.stop()

                # Should use single process termination
                mock_process.terminate.assert_called_once()
                mock_process.wait.assert_called_once_with(timeout=5)
                # Global cleanup should NOT be called for graceful termination
                mock_cleanup.assert_not_called()
        finally:
            # Restore killpg if it existed
            if original_killpg is not None:
                os.killpg = original_killpg

    def test_stop_calls_global_cleanup_on_termination_failure(self):
        """Test that global cleanup is called when process termination fails."""
        manager = PGliteManager()

        mock_process = Mock()
        mock_process.pid = 1234
        # Simulate both graceful and force termination failing
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired("cmd", 5),  # First wait (graceful) fails
            subprocess.TimeoutExpired("cmd", 2),  # Second wait (force) fails
        ]
        manager.process = mock_process

        with patch.object(manager, "_kill_all_pglite_processes") as mock_cleanup:
            manager.stop()

            # Should try terminate, then kill, then call global cleanup
            mock_process.terminate.assert_called_once()
            mock_process.kill.assert_called_once()
            # Global cleanup should be called when final wait fails
            mock_cleanup.assert_called_once()


class TestTempDirCleanup:
    """Test cleanup of temporary directories during stop()."""

    def test_cleanup_temp_dirs_removes_socket_and_work_dirs(self):
        """Test that _cleanup_temp_dirs removes both socket and work directories."""
        import shutil
        from pathlib import Path

        manager = PGliteManager()

        socket_dir = Path(manager.config.socket_path).parent
        work_dir = tempfile.mkdtemp(prefix="py-pglite-test-")

        manager.work_dir = Path(work_dir)
        manager._auto_work_dir = True

        assert socket_dir.exists()
        assert manager.work_dir.exists()

        manager._cleanup_temp_dirs()

        assert not socket_dir.exists()
        assert not manager.work_dir.exists()

    def test_cleanup_temp_dirs_socket_dir_not_empty(self):
        """Test _cleanup_temp_dirs when socket directory is not empty."""
        from pathlib import Path

        manager = PGliteManager()

        socket_dir = Path(manager.config.socket_path).parent
        # Create a file inside the socket dir so rmdir fails
        extra_file = socket_dir / "extra_file.txt"
        extra_file.write_text("blocking removal")

        manager._cleanup_temp_dirs()

        # Socket directory should still exist because it wasn't empty
        assert socket_dir.exists()
        # Clean up our test artifact
        extra_file.unlink()
        socket_dir.rmdir()

    def test_cleanup_temp_dirs_no_auto_work_dir(self):
        """Test _cleanup_temp_dirs does not remove user-specified work dir."""
        import shutil
        from pathlib import Path

        manager = PGliteManager()
        work_dir = tempfile.mkdtemp(prefix="py-pglite-test-")
        manager.work_dir = Path(work_dir)
        manager._auto_work_dir = False

        assert manager.work_dir.exists()

        manager._cleanup_temp_dirs()

        # User-specified work dir should NOT be removed
        assert manager.work_dir.exists()
        shutil.rmtree(work_dir)

    def test_cleanup_temp_dirs_work_dir_already_gone(self):
        """Test _cleanup_temp_dirs handles work dir already deleted."""
        import shutil
        from pathlib import Path

        manager = PGliteManager()
        work_dir = tempfile.mkdtemp(prefix="py-pglite-test-")
        manager.work_dir = Path(work_dir)
        manager._auto_work_dir = True

        shutil.rmtree(work_dir)

        # Should not raise
        manager._cleanup_temp_dirs()

    def test_cleanup_temp_dirs_socket_dir_already_gone(self):
        """Test _cleanup_temp_dirs handles socket dir already deleted."""
        from pathlib import Path

        manager = PGliteManager()

        socket_dir = Path(manager.config.socket_path).parent
        socket_dir.rmdir()

        # Should not raise
        manager._cleanup_temp_dirs()

    def test_stop_calls_cleanup_temp_dirs_when_cleanup_on_exit(self):
        """Test stop() calls _cleanup_temp_dirs when cleanup_on_exit is True."""
        config = PGliteConfig(cleanup_on_exit=True)
        manager = PGliteManager(config)
        manager.process = Mock()
        manager.process.pid = 1234
        manager.process.wait.return_value = None

        with (
            patch.object(manager, "_cleanup_socket") as mock_socket,
            patch.object(manager, "_cleanup_temp_dirs") as mock_temp_dirs,
        ):
            manager.stop()

            mock_socket.assert_called_once()
            mock_temp_dirs.assert_called_once()

    def test_stop_skips_cleanup_temp_dirs_when_cleanup_on_exit_false(self):
        """Test stop() does NOT call _cleanup_temp_dirs when cleanup_on_exit is False."""
        config = PGliteConfig(cleanup_on_exit=False)
        manager = PGliteManager(config)
        manager.process = Mock()
        manager.process.pid = 1234
        manager.process.wait.return_value = None

        with (
            patch.object(manager, "_cleanup_socket") as mock_socket,
            patch.object(manager, "_cleanup_temp_dirs") as mock_temp_dirs,
        ):
            manager.stop()

            mock_socket.assert_not_called()
            mock_temp_dirs.assert_not_called()

    def test_full_stop_cycle_cleans_up_real_temp_dirs(self):
        """End-to-end test: start/stop leaves no temp directories behind."""
        from pathlib import Path

        manager = PGliteManager()

        manager.start()
        assert manager.is_running()

        socket_dir = Path(manager.config.socket_path).parent
        work_dir = manager.work_dir

        assert socket_dir.exists()
        assert work_dir is not None
        assert work_dir.exists()

        manager.stop()
        assert not manager.is_running()

        # Both temp directories should be gone
        assert not socket_dir.exists(), f"Socket dir still exists: {socket_dir}"
        assert not work_dir.exists(), f"Work dir still exists: {work_dir}"

    def test_stop_terminates_process_and_cleans_up(self):
        """End-to-end test: stop() kills the OS process and removes temp dirs."""
        from pathlib import Path

        import psutil

        manager = PGliteManager()
        manager.start()
        assert manager.is_running()
        assert manager.process is not None

        pid = manager.process.pid
        socket_dir = Path(manager.config.socket_path).parent
        work_dir = manager.work_dir
        assert work_dir is not None

        manager.stop()

        # Manager should report stopped
        assert not manager.is_running()
        assert manager.process is None

        # Process should no longer exist at the OS level
        assert not psutil.pid_exists(pid), f"Process {pid} still running"

        # No PGlite processes should remain
        for proc in psutil.process_iter(["cmdline"]):
            if proc.info["cmdline"]:
                assert not any(
                    "pglite_manager.js" in cmd for cmd in proc.info["cmdline"]
                ), f"PGlite process still running: {proc.info['cmdline']}"

        # Temp directories should be gone
        assert not socket_dir.exists(), f"Socket dir still exists: {socket_dir}"
        assert not work_dir.exists(), f"Work dir still exists: {work_dir}"
