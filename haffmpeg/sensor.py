"""For HA camera components."""
from .core import HAFFmpegQue


class SensorNoise(HAFFmpegQue):
    """Implement a noise detection on a autio stream."""

    def __init__(self, ffmpeg_bin):
        """Init CameraMjpeg."""
        HAFFmpegQue.__init__(self, ffmpeg_bin=ffmpeg_bin)

        self._peak = -30
        self._time_period = 2

    @property
    def peak(self, val):
        self._peak = val

    @property
    def time_period(self, val):
        self._time_period = val

    def open_sensor(self, input_source, output_dest=None, extra_cmd=None):
        """Open FFmpeg process as mjpeg video stream."""
        command = [
            "-i",
            input_source,
            "-vn",
            "-c:v",
            "mjpeg",
            "-f",
            "mpjpeg"
        ]

        self.open(cmd=command, output=output_dest, extra_cmd=extra_cmd)
