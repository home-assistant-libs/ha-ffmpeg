"""For HA camera components."""
import re

from .core import HAFFmpegWorker, HAFFMPEG_QUEUE_END


class SensorNoise(HAFFmpegWorker):
    """Implement a noise detection on a autio stream."""

    def __init__(self, ffmpeg_bin, callback):
        """Init CameraMjpeg."""
        super().__init__(self, ffmpeg_bin=ffmpeg_bin)

        self._callback = callback
        self._peak = -30
        self._time_duration = 1
        self._time_reset = 2

    @property
    def peak(self, val):
        self._peak = val

    @time_duration.setter
    def time_duration(self, val):
        self._time_duration = val

    @time_reset.setter
    def time_reset(self, val):
        self._time_reset = val

    def open_sensor(self, input_source, output_dest=None, extra_cmd=None):
        """Open FFmpeg process as mjpeg video stream."""
        command = [
            "-i",
            input_source,
            "-vn",
            "-af",
            "silencedetect=n={}dB:d=1".format(self._peak)
        ]

        # run ffmpeg, read output
        self.startWorker(cmd=command, output=output_dest, extra_cmd=extra_cmd,
                         pattern="silent")

    def _worker_process(self):
        """This function run in thread for process que data."""
        noise_detect = False
        detect_time = None

        re_start = re.compile("")
        re_end = re.compile("")

        while True:
            data = self._que.get()

            # program close?
            if data == HAFFMPEG_QUEUE_END:
                return
