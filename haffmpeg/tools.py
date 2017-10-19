"""For HA varios tools."""
import asyncio
import logging

import async_timeout

from .core import HAFFmpeg

_LOGGER = logging.getLogger(__name__)

IMAGE_JPEG = 'mjpeg'
IMAGE_PNG = 'png'


class Test(HAFFmpeg):
    """Test a ffmpeg/mulimedia file/stream."""

    @asyncio.coroutine
    def run_test(self, input_source, timeout=15):
        """Start a test and give a TRUE or FALSE."""
        command = [
            "-frames:v",
            "1",
            "-frames:a",
            "1",
        ]

        # Run a short test with input
        is_open = yield from self.open(
            cmd=command, input_source=input_source, stderr_pipe=True,
            output=None)

        # error after open?
        if not is_open:
            return False

        try:
            with async_timeout.timeout(timeout, loop=self._loop):
                out, error = yield from self._proc.communicate()

        except (OSError, asyncio.TimeoutError, ValueError):
            _LOGGER.warning("Timeout/Error reading test.")
            self._proc.kill()
            return False

        # check error code
        if self._proc.returncode == 0:
            _LOGGER.debug("STD: %s / ERR: %s", out, error)
            return True

        # error state
        _LOGGER.error("ReturnCode: %i / STD: %s / ERR: %s",
                      self._proc.returncode, out, error)
        return False


class ImageFrame(HAFFmpeg):
    """Implement a single image caputre from a stream."""

    @asyncio.coroutine
    def get_image(self, input_source, output_format=IMAGE_JPEG, extra_cmd=None,
                  timeout=15):
        """Open FFmpeg process as capture 1 frame."""
        command = [
            "-an",
            "-frames:v",
            "1",
            "-c:v",
            output_format,
        ]

        # open input for capture 1 frame
        is_open = yield from self.open(
            cmd=command, input_source=input_source, output="-f image2pipe -",
            extra_cmd=extra_cmd)

        # error after open?
        if not is_open:
            _LOGGER.warning("Error starting FFmpeg.")
            return None

        # read image
        try:
            with async_timeout.timeout(timeout, loop=self._loop):
                image, _ = yield from self._proc.communicate()

            return image

        except (asyncio.TimeoutError, ValueError):
            _LOGGER.warning("Timeout reading image.")
            self._proc.kill()
            return None
