"""For HA varios tools."""
import functools
import logging
import re
import subprocess
from typing import Optional

from .core import HAFFmpeg

_LOGGER = logging.getLogger(__name__)

IMAGE_JPEG = "mjpeg"
IMAGE_PNG = "png"


class ImageFrame(HAFFmpeg):
    """Implement a single image capture from a stream."""

    async def get_image(
        self,
        input_source: str,
        output_format: str = IMAGE_JPEG,
        extra_cmd: Optional[str] = None,
        timeout: int = 15,
    ) -> Optional[bytes]:
        """Open FFmpeg process as capture 1 frame."""
        command = ["-an", "-frames:v", "1", "-c:v", output_format]

        # open input for capture 1 frame
        is_open = await self.open(
            cmd=command,
            input_source=input_source,
            output="-f image2pipe -",
            extra_cmd=extra_cmd,
        )

        # error after open?
        if not is_open:
            _LOGGER.warning("Error starting FFmpeg.")
            return None

        # read image
        try:
            proc_func = functools.partial(self._proc.communicate, timeout=timeout)
            image, _ = await self._loop.run_in_executor(None, proc_func)
            return image

        except (subprocess.TimeoutExpired, ValueError):
            _LOGGER.warning("Timeout reading image.")
            self.kill()
            return None


class FFVersion(HAFFmpeg):
    """Retrieve FFmpeg version information."""

    async def get_version(self, timeout: int = 15) -> Optional[str]:
        """Execute FFmpeg process and parse the version information.

        Return full FFmpeg version string. Such as 3.4.2-tessus
        """
        command = ["-version"]
        # open input for capture 1 frame

        is_open = await self.open(cmd=command, input_source=None, output="")

        # error after open?
        if not is_open:
            _LOGGER.warning("Error starting FFmpeg.")
            return

        # read output
        try:
            proc_func = functools.partial(self._proc.communicate, timeout=timeout)
            output, _ = await self._loop.run_in_executor(None, proc_func)

            result = re.search(r"ffmpeg version (\S*)", output.decode())
            if result is not None:
                return result.group(1)

        except (subprocess.TimeoutExpired, ValueError):
            _LOGGER.warning("Timeout reading stdout.")
            self.kill()

        return None
