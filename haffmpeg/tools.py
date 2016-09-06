"""For HA varios tools."""
import logging
import subprocess

from .core import HAFFmpeg

_LOGGER = logging.getLogger(__name__)

IMAGE_JPEG = 'mjpeg'
IMAGE_PNG = 'png'


class ImageSingle(HAFFmpeg):
    """Implement a single image caputre from a stream."""

    def __init__(self, ffmpeg_bin):
        """Init ImageSingle."""
        HAFFmpeg.__init__(self, ffmpeg_bin=ffmpeg_bin)

    # pylint: disable=too-many-arguments
    def get_image(self, input_source, output_format, extra_cmd=None,
                  timeout=15):
        """Open FFmpeg process as capture 1 frame."""
        command = [
            "-an",
            "-frame:v",
            "1",
            "-c:v",
            output_format,
        ]

        # open input for capture 1 frame
        self.open(cmd=command, input_source=input_source, output="-f image2 -",
                  extra_cmd=extra_cmd)

        # read image
        try:
            image, error = self._proc.communicate(timeout=timeout)
            return image
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout reading image.")
            self.close()
            return None
