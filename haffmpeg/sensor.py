"""For HA camera components."""
import logging
import queue
import re

from .core import HAFFmpegWorker, HAFFMPEG_QUEUE_END

_LOGGER = logging.getLogger(__name__)


class SensorNoise(HAFFmpegWorker):
    """Implement a noise detection on a autio stream."""

    STATE_NONE = 0
    STATE_NOISE = 1
    STATE_END = 2
    STATE_DETECT = 3

    def __init__(self, ffmpeg_bin, callback):
        """Init noise sensor."""
        super().__init__(self, ffmpeg_bin)

        self._callback = callback
        self._peak = -30
        self._time_duration = 1
        self._time_reset = 2

    @property
    def peak(self, val):
        self._peak = val

    def set_options(self, time_duration=1, time_reset=2):
        """Set option parameter for noise sensor."""
        self._time_duration = time_duration
        self._time_reset = time_reset

    def open_sensor(self, input_source, output_dest=None, extra_cmd=None):
        """Open FFmpeg process as mjpeg video stream."""
        command = [
            "-i",
            input_source,
            "-vn",
            "-filter:a",
            "silencedetect=n={}dB:d=1".format(self._peak)
        ]

        # run ffmpeg, read output
        self.start_worker(cmd=command, output=output_dest, extra_cmd=extra_cmd,
                          pattern="silent")

    def _worker_process(self):
        """This function run in thread for process que data."""
        state = self.STATE_NONE
        timeout = None

        re_start = re.compile("silent_start")
        re_end = re.compile("silent_end")

        # process queue data
        while True:
            try:
                _LOGGER.debug("Reading State: %d, timeout: %s", state, timeout)
                data = self._que.get(block=True, timeout=timeout)
                timeout = None
                if data == HAFFMPEG_QUEUE_END:
                    return
            except queue.Empty:
                _LOGGER.debug("Blocking timeout")
                # noise
                if state == self.STATE_DETECT:
                    # noise detected
                    self._callback(True)
                    state = self.STATE_NOISE

                elif state == self.STATE_END:
                    # no noise
                    self._callback(False)
                    state = self.STATE_NONE

                timeout = None
                continue

            if re_start.search(data):
                if state == self.STATE_NOISE:
                    # stop noise detection
                    state = self.STATE_END
                    timeout = self._time_reset
                if state == self.STATE_DETECT:
                    # reset if only a peak
                    state = self.STATE_NONE
                continue

            if re_end.search(data):
                if state == self.STATE_NONE:
                    # detect noise begin
                    state = self.STATE_DETECT
                    timeout = self._time_duration
                continue

        _LOGGER.warning("Unknown data from queue!")
