"""For HA camera components."""
import asyncio

from .core import HAFFmpeg


class CameraMjpeg(HAFFmpeg):
    """Implement a camera they convert video stream to MJPEG."""

    @asyncio.coroutine
    def open_camera(self, input_source, extra_cmd=None):
        """Open FFmpeg process as mjpeg video stream."""
        command = [
            "-an",
            "-c:v",
            "mjpeg",
        ]

        yield from self.open(
            cmd=command, input_source=input_source, output="-f mpjpeg -",
            extra_cmd=extra_cmd)
