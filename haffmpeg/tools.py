"""For HA varios tools."""
import logging
import queue
import subprocess
import threading
from time import time

from .core import HAFFmpeg

_LOGGER = logging.getLogger(__name__)

IMAGE_JPEG = 'mjpeg'
IMAGE_PNG = 'png'

IMAGE_MAGIC = {
    IMAGE_JPEG: b'\xFF\xD8\xFF',
    IMAGE_PNG: b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
}


class Test(HAFFmpeg):
    """Test a ffmpeg/mulimedia file/stream."""

    def __init__(self, ffmpeg_bin):
        """Init Test."""
        HAFFmpeg.__init__(self, ffmpeg_bin=ffmpeg_bin)

    def run_test(self, input_source, timeout=15):
        """Start a test and give a TRUE or FALSE."""
        command = [
            "-frames:v",
            "1",
            "-frames:a",
            "1",
        ]

        # Run a short test with input
        self.open(cmd=command, input_source=input_source, stderr_pipe=True,
                  output=None)

        # error after open?
        if self._proc is None:
            return False

        try:
            out, error = self._proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout reading test.")
            self.close()
            return None

        # check error code
        if self._proc.returncode == 0:
            _LOGGER.debug("STD: %s / ERR: %s", out, error)
            return True
        _LOGGER.critical("ReturnCode: %i / STD: %s / ERR: %s",
                         self._proc.returncode, out, error)
        return False


class ImageSingle(HAFFmpeg):
    """Implement a single image caputre from a stream."""

    def __init__(self, ffmpeg_bin):
        """Init ImageSingle."""
        HAFFmpeg.__init__(self, ffmpeg_bin=ffmpeg_bin)

    # pylint: disable=too-many-arguments
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
        self.open(cmd=command, input_source=input_source,
                  output="-f image2pipe -", extra_cmd=extra_cmd)

        # read image
        try:
            # pylint: disable=unused-variable
            image, error = self._proc.communicate(timeout=timeout)
            return image
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout reading image.")
            self.close()
            return None


class ImageStream(HAFFmpeg):
    """Read stream and can put Image to a queue."""

    CLOSE_IMAGE_STREAM = b'!HAFFMPEG_QUEUE_END!'

    def __init__(self, ffmpeg_bin, callback, image_buffer=5):
        """Init ImageStream."""
        HAFFmpeg.__init__(self, ffmpeg_bin=ffmpeg_bin)

        self._callback = callback
        self._que = queue.Queue(maxsize=image_buffer)
        self._que_thread = None
        self._push_event = threading.Event()
        self._push_thread = None

    # pylint: disable=too-many-arguments
    def open_stream(self, input_source, interval, output_format=IMAGE_JPEG,
                    extra_cmd=None):
        """Start a stream and but image in interval to queue -> callback."""
        if self.is_running:
            _LOGGER.error("Image stream is running!")
            return

        command = [
            "-an",
            "-c:v",
            output_format,
        ]

        # open input for image stream
        self.open(cmd=command, input_source=input_source,
                  output="-f image2pipe -", extra_cmd=extra_cmd)

        # init threading
        self._que_thread = threading.Thread(
            target=self._read_stream,
            kwargs={
                'interval': interval,
                'output_format': output_format,
            },
        )
        self._push_thread = threading.Thread(
            target=self._image_callback_handler,
        )

        # start processing
        self._que_thread.start()
        self._push_thread.start()

    def push_image(self):
        """Push a image out of interval to queu."""
        self._push_event.set()

    def _read_stream(self, output_format, interval):
        """Read a stream and extract image data."""
        buff = b''
        next_put = time()

        # read stream
        for chunk in self:
            buff += chunk
            magic_frame = buff.rfind(IMAGE_MAGIC.get(output_format))

            # new frame?
            if magic_frame > 0:
                # time for new image
                if next_put <= time() or self._push_event.is_set():
                    # push new image to queue
                    new_image = buff[:magic_frame-1]
                    try:
                        self._push_event.clear()
                        next_put = time() + interval
                        self._que.put(new_image, block=False)
                        _LOGGER.debug("Put image to queue")
                    except queue.Full:
                        _LOGGER.critical("Image queue is full!")
                # reset
                buff = buff[magic_frame:]

        # end
        self._que.put(self.CLOSE_IMAGE_STREAM)

    def _image_callback_handler(self):
        """Read queue and send it as callback to HA."""
        while True:
            data = self._que.get(block=True)
            if data == self.CLOSE_IMAGE_STREAM:
                return

            _LOGGER.debug("Push image to HA")
            self._callback(data)
