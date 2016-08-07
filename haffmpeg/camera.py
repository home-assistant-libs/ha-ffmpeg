"""For HA camera components."""
from .core import HAFFmpeg


class CameraMjpeg(HAFFmpeg):
    """Implement a camera they convert video stream to MJPEG."""

    def __init__(self, ffmpeg_bin):
        """Init CameraMjpeg."""
        HAFFmpeg.__init__(self, ffmpeg_bin=ffmpeg_bin)

    def open_camera(self, input_source, extra_cmd=None):
        """Open FFmpeg process as mjpeg video stream."""
        command = [
            "-i",
            input_source,
            "-an",
            "-c:v",
            "mjpeg"
        ]

        self.open(cmd=command, extra_cmd=extra_cmd)
