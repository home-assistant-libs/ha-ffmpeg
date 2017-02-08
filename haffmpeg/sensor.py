"""For HA sensor components."""
import asyncio
import logging
import re
from time import time

import async_timeout

from .core import HAFFmpegWorker, FFMPEG_STDOUT

_LOGGER = logging.getLogger(__name__)


class SensorNoise(HAFFmpegWorker):
    """Implement a noise detection on a autio stream."""

    STATE_NONE = 0
    STATE_NOISE = 1
    STATE_END = 2
    STATE_DETECT = 3

    def __init__(self, ffmpeg_bin, loop, callback):
        """Init noise sensor."""
        super().__init__(ffmpeg_bin, loop)

        self._callback = callback
        self._peak = -30
        self._time_duration = 1
        self._time_reset = 2

    def set_options(self, time_duration=1, time_reset=2, peak=-30):
        """Set option parameter for noise sensor."""
        self._time_duration = time_duration
        self._time_reset = time_reset
        self._peak = peak

    @asyncio.coroutine
    def open_sensor(self, input_source, output_dest=None, extra_cmd=None):
        """Open FFmpeg process for read autio stream."""
        command = [
            "-vn",
            "-filter:a",
            "silencedetect=n={}dB:d=1".format(self._peak)
        ]

        # run ffmpeg, read output
        yield from self.start_worker(
            cmd=command, input_source=input_source, output=output_dest,
            extra_cmd=extra_cmd, pattern="silence")

    @asyncio.coroutine
    def _worker_process(self):
        """This function processing data."""
        state = self.STATE_DETECT
        timeout = self._time_duration

        re_start = re.compile("silence_start")
        re_end = re.compile("silence_end")

        # process queue data
        while True:
            try:
                _LOGGER.debug("Reading State: %d, timeout: %s", state, timeout)
                with async_timeout.timeout(timeout, loop=self._loop):
                    data = yield from self._que.get()
                timeout = None
                if data is None:
                    self._loop.call_later(2, self._callback, None)
                    return
            except asyncio.TimeoutError:
                _LOGGER.debug("Blocking timeout")
                # noise
                if state == self.STATE_DETECT:
                    # noise detected
                    self._loop.call_soon(self._callback, True)
                    state = self.STATE_NOISE

                elif state == self.STATE_END:
                    # no noise
                    self._loop.call_soon(self._callback, False)
                    state = self.STATE_NONE

                timeout = None
                continue

            if re_start.search(data):
                if state == self.STATE_NOISE:
                    # stop noise detection
                    state = self.STATE_END
                    timeout = self._time_reset
                elif state == self.STATE_DETECT:
                    # reset if only a peak
                    state = self.STATE_NONE
                continue

            if re_end.search(data):
                if state == self.STATE_NONE:
                    # detect noise begin
                    state = self.STATE_DETECT
                    timeout = self._time_duration
                elif state == self.STATE_END:
                    # back to noise status
                    state = self.STATE_NOISE
                continue

            _LOGGER.warning("Unknown data from queue!")


class SensorMotion(HAFFmpegWorker):
    """Implement motion detection with ffmpeg scene detection."""

    STATE_NONE = 0
    STATE_REPEAT = 1
    STATE_MOTION = 2

    MATCH = r"\d,.*\d,.*\d,.*\d,.*\d,.*\w"

    def __init__(self, ffmpeg_bin, loop, callback):
        """Init motion sensor."""
        super().__init__(ffmpeg_bin, loop)

        self._callback = callback
        self._changes = 10
        self._time_reset = 60
        self._time_repeat = 0
        self._repeat = 0

    def set_options(self, time_reset=60, time_repeat=0, repeat=0,
                    changes=10):
        """Set option parameter for noise sensor."""
        self._time_reset = time_reset
        self._time_repeat = time_repeat
        self._repeat = repeat
        self._changes = changes

    @asyncio.coroutine
    def open_sensor(self, input_source, extra_cmd=None):
        """Open FFmpeg process a video stream for motion detection."""
        command = [
            "-an",
            "-filter:v",
            "select=gt(scene\\,{0})".format(self._changes / 100),
        ]

        # run ffmpeg, read output
        yield from self.start_worker(
            cmd=command, input_source=input_source, output="-f framemd5 -",
            extra_cmd=extra_cmd, pattern=self.MATCH, reading=FFMPEG_STDOUT)

    @asyncio.coroutine
    def _worker_process(self):
        """This function processing data."""
        state = self.STATE_NONE
        timeout = None

        # for repeat feature
        re_frame = 0
        re_time = 0

        re_data = re.compile(self.MATCH)

        # process queue data
        while True:
            try:
                _LOGGER.debug("Reading State: %d, timeout: %s", state, timeout)
                with async_timeout.timeout(timeout, loop=self._loop):
                    data = yield from self._que.get()
                if data is None:
                    self._loop.call_later(2, self._callback, None)
                    return
            except asyncio.TimeoutError:
                _LOGGER.debug("Blocking timeout")
                # reset motion detection
                if state == self.STATE_MOTION:
                    state = self.STATE_NONE
                    self._loop.call_soon(self._callback, False)
                    timeout = None
                # reset repeate state
                if state == self.STATE_REPEAT:
                    state = self.STATE_NONE
                    timeout = None
                continue

            frames = re_data.search(data)
            if frames:
                # repeat not used
                if self._repeat == 0 and state == self.STATE_NONE:
                    state = self.STATE_MOTION
                    self._loop.call_soon(self._callback, True)
                    timeout = self._time_reset

                # repeat feature is on / first motion
                if state == self.STATE_NONE:
                    state = self.STATE_REPEAT
                    timeout = self._time_repeat
                    re_frame = 0
                    re_time = time()

                elif state == self.STATE_REPEAT:
                    re_frame += 1

                    # REPEAT ready?
                    if re_frame >= self._repeat:
                        state = self.STATE_MOTION
                        self._loop.call_soon(self._callback, True)
                        timeout = self._time_reset
                    else:
                        past = time() - re_time
                        timeout -= past

                    # REPEAT time down
                    if timeout <= 0:
                        _LOGGER.debug("Reset repeat to none")
                        state = self.STATE_NONE
                        timeout = None

                continue

            _LOGGER.warning("Unknown data from queue!")
