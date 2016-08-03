"""
Base functionality of ffmpeg HA wrapper.
"""
import logger
import shlex
import subprocess

_LOGGER = logging.getLogger(__name__)

HAFFmpeg(object):
    """Base HA FFmpeg object."""

    def __init__(self, ffmpeg_bin):
        """Base initialize."""
        self._ffmpeg = ffmpeg_bin
        self._argv = [ffmpeg_bin]
        self._popen = None

    def _start(self, cmd, output="-", extra_cmd=None, text=False,
               stdout_pipe=True, stderr_pipe=False):
        """Start a ffmpeg instance and pipe output."""
        stdout = subprocess.PIPE if stdout_pipe else subprocess.DEVNULL
        stderr = subprocess.PIPE if stderr_pipe else subprocess.DEVNULL

        if self._popen is not None:
            _LOGGER.critical("FFmpeg is allready running!")
            return

        # add cmds
        self._argv.append(cmd)

        # exists a extra cmd from customer
        if extra_cmd is not None:
            self._argv.extend(shlex.split(extra_cmd))

        # add output
        self._argv.append(output)

        # start ffmpeg
        self._popen = subprocess.Popen(
            self._argv,
            stderr=stderr,
            stdout=stdout,
            universal_newlines=text
        )

    def _stop(self, timeout=15):
        """Stop a ffmpeg instance."""

        if self._popen is None:
            _LOGGER.error("FFmpeg isn't running!")
            return

        # send stop to ffmpeg
        self._popen.terminate()

        try:
            self._popen.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout while waiting of FFmpeg.")

        # clean ffmpeg cmd
        self._argv = [self._ffmpeg]
