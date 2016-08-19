"""Base functionality of ffmpeg HA wrapper."""
import logging
import queue
import re
import shlex
import subprocess
import threading

_LOGGER = logging.getLogger(__name__)

HAFFMPEG_QUEUE_END = '!HAFFMPEG_QUEUE_END!'

class HAFFmpeg(object):
    """Base HA FFmpeg process.

    Object is iterable but only for data streams! For other things use the
    process property to call from Popen object.
    """

    def __init__(self, ffmpeg_bin, chunk_size=1024):
        """Base initialize."""
        self._ffmpeg = ffmpeg_bin
        self._argv = [ffmpeg_bin]
        self._chunk_size = chunk_size
        self._bin_mode = None
        self._proc = None

    # pylint: disable=too-many-arguments
    def open(self, cmd, output="-", extra_cmd=None, text=False,
             stdout_pipe=True, stderr_pipe=False):
        """Start a ffmpeg instance and pipe output."""
        stdout = subprocess.PIPE if stdout_pipe else subprocess.DEVNULL
        stderr = subprocess.PIPE if stderr_pipe else subprocess.DEVNULL

        if self.is_running:
            _LOGGER.critical("FFmpeg is allready running!")
            return

        # add cmds
        self._argv.extend(cmd)

        # exists a extra cmd from customer
        if extra_cmd is not None:
            self._argv.extend(shlex.split(extra_cmd))

        # add output
        if output is None:
            self._argv.extend(['-f', 'null', '-'])

            # output to null / copy audio/audio for muxer
            if '-an' not in self._argv:
                self._argv.extend(['-c:a', 'copy'])
            if '-av' not in self._argv:
                self._argv.extend(['-c:v', 'copy'])
        else:
            self._argv.append(output)

        # start ffmpeg
        _LOGGER.debug("Start FFmpeg with %s.", str(self._argv))
        self._proc = subprocess.Popen(
            self._argv,
            stderr=stderr,
            stdout=stdout,
            stdin=subprocess.PIPE,
            universal_newlines=text
        )

        # save bin/text mode of process
        self._bin_mode = False if text else True

    def close(self, timeout=5):
        """Stop a ffmpeg instance."""
        if not self.is_running:
            _LOGGER.error("FFmpeg isn't running!")
            return

        # set stop command for ffmpeg
        stop = b'q' if self._bin_mode else 'q'

        try:
            # send stop to ffmpeg
            self._proc.communicate(input=stop, timeout=timeout)
            _LOGGER.debug("Close FFmpeg process.")
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout while waiting of FFmpeg.")
            self._proc.kill()
            self._proc.wait()

        # clean ffmpeg cmd
        self._argv = [self._ffmpeg]
        self._proc = None
        self._bin_mode = None

    @property
    def process(self):
        """Return a Popen object or None of not running."""
        return self._proc

    @property
    def is_running(self):
        """Return True if ffmpeg is running."""
        if self._proc is None or self._proc.poll() is not None:
            return False
        return True

    def __iter__(self):
        """Read data from ffmpeg PIPE/STDERR as iter."""
        return self

    def __next__(self):
        """Get next buffer data."""
        if not self.is_running:
            _LOGGER.debug("don't exists data from a process.")
            raise StopIteration

        # check if reading from pipe
        if self._proc.stdout is None:
            _LOGGER.critical("Iterator havn't data to  read from!")
            raise StopIteration

        return self._proc.stdout.read(self._chunk_size)


class HAFFmpegQue(HAFFmpeg):
    """Read FFmpeg STDERR output to QUE."""

    def __init__(self, ffmpeg_bin, chunk_size=1024):
    """Base initialize."""
        super().__init__(ffmpeg_bin, chunk_size)

        self._que = queue.Queue()
        self._queThread = None

    def _readLinesToQue(pattern=None):
        """Read line from STDERR to Que they match with pattern / thread."""
        if pattern is not None:
            cmp = re.compile(pattern)

        # read lines
        while self.is_running:
            line = self._proc.stderr.readline()

            match = True if pattern is None else cmp.serach(line)
            if match:
                try:
                    self._que.put(line, block=False)
                except queue.Full:
                    _LOGGER.warning("Queue is full...")

        # send end to reader of queue
        self._que.put(HAFFMPEG_QUEUE_END)

    def startReadingQue(pattern=None):
        """Read line from STDERR to Que they match with pattern."""
        if self._queThread is not None:
            _LOGGER.critical("Thread is allready running now!")
            return
        if self._bin_mode:
            _LOGGER.critical("ReadingQue not support ob Binmode!")
            return

        self._queThread = threading.Thread(
            target=self._readLinesToQue,
            kwargs={'pattern': pattern}
        )

        self._queThread.start()
        _LOGGER.debug("Start thread. Pattern: %s", pattern)


class HAFFmpegWorker(HAFFmpegQue):
    """Process Que data into a thread."""

    def __init__(self, ffmpeg_bin, chunk_size=1024):
    """Base initialize."""
        super().__init__(ffmpeg_bin, chunk_size)

        self._workerThread = None

    def startWorker(self, command, output=None, extra_cmd=None, pattern=None):
        """Start ffmpeg process with que and process data."""
        if self._workerThread is not None and self._workerThread.is_alive():
            _LOGGER.warning("Can't start worker. It is allready running!")
            return

        # start ffmpeg and reading to queue
        self.open(command=command, output=output, extra_cmd=extra_cmd)
        self.startReadingQue(pattern=pattern)
        self._workerThread = threading.Thread(
            target=self._worker_process
        )

        self._workerThread.start()
        _LOGGER.debug("Start working thread.")

    def _worker_process(self):
        """This function run in thread for process que data."""
        raise NotImplemented
