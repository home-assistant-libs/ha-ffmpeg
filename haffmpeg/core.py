"""Base functionality of ffmpeg HA wrapper."""
import logging
import queue
import re
import shlex
import subprocess
import threading

_LOGGER = logging.getLogger(__name__)

HAFFMPEG_QUEUE_END = '!HAFFMPEG_QUEUE_END!'

FFMPEG_STDERR = 'stderr'
FFMPEG_STDOUT = 'stdout'


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
    def open(self, cmd, input_source, output="-", extra_cmd=None, text=False,
             stdout_pipe=True, stderr_pipe=False):
        """Start a ffmpeg instance and pipe output."""
        stdout = subprocess.PIPE if stdout_pipe else subprocess.DEVNULL
        stderr = subprocess.PIPE if stderr_pipe else subprocess.DEVNULL

        if self.is_running:
            _LOGGER.critical("FFmpeg is allready running!")
            return

        # set input
        input_cmd = shlex.split(input_source)
        if len(input_cmd) > 1:
            self._argv.extend(input_cmd)
        else:
            self._argv.extend(['-i', input_source])

        # add cmds
        self._argv.extend(cmd)

        # exists a extra cmd from customer
        if extra_cmd is not None:
            self._argv.extend(shlex.split(extra_cmd))

        # cleanup filters
        for opts in (['-filter:a', '-af'], ['-filter:v', '-vf']):
            filter_list = []
            new_argv = []
            cmd_iter = iter(self._argv)
            for element in cmd_iter:
                if element in opts:
                    filter_list.insert(0, next(cmd_iter))
                else:
                    new_argv.append(element)

            # update argv if changes
            if filter_list:
                new_argv.extend([opts[0], ",".join(filter_list)])
                self._argv = new_argv.copy()

        # add output
        if output is None:
            self._argv.extend(['-f', 'null', '-'])
        else:
            output_cmd = shlex.split(output)
            if len(output_cmd) > 1:
                self._argv.extend(output_cmd)
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
        super().__init__(ffmpeg_bin, chunk_size=chunk_size)

        self._que = queue.Queue()
        self._que_thread = None
        self._reading = None

    def _read_lines_to_que(self, pattern=None):
        """Read line from pipe to Que they match with pattern / thread."""
        if pattern is not None:
            cmp = re.compile(pattern)

        # read lines
        while self.is_running:
            try:
                line = self._reading.readline()
            # pylint: disable=broad-except
            except Exception:
                break

            match = True if pattern is None else cmp.search(line)
            if match:
                try:
                    _LOGGER.debug("Put do que: %s", line)
                    self._que.put(line, block=False)
                except queue.Full:
                    _LOGGER.warning("Queue is full...")

        # send end to reader of queue
        _LOGGER.debug("Close read ffmpeg output to que.")
        self._que.put(HAFFMPEG_QUEUE_END)

    def start_reading_que(self, pattern=None, reading=FFMPEG_STDERR):
        """Read line from STDERR to Que they match with pattern."""
        if self._que_thread is not None:
            _LOGGER.critical("Thread is allready running now!")
            return False
        elif self._bin_mode:
            _LOGGER.critical("ReadingQue not support ob Binmode!")
            return False

        # create thread
        self._que_thread = threading.Thread(
            target=self._read_lines_to_que,
            kwargs={'pattern': pattern}
        )

        # set reading from
        if reading == FFMPEG_STDOUT:
            self._reading = self._proc.stdout
        else:
            self._reading = self._proc.stderr

        # process data
        self._que_thread.start()
        _LOGGER.debug("Start thread from %s. Pattern: %s", reading, pattern)
        return True


class HAFFmpegWorker(HAFFmpegQue):
    """Process Que data into a thread."""

    def __init__(self, ffmpeg_bin, chunk_size=1024):
        """Base initialize."""
        super().__init__(ffmpeg_bin, chunk_size)

        self._worker_thread = None

    # pylint: disable=too-many-arguments
    def start_worker(self, cmd, input_source, output=None, extra_cmd=None,
                     pattern=None, reading=FFMPEG_STDERR):
        """Start ffmpeg process with que and process data."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            _LOGGER.warning("Can't start worker. It is allready running!")
            return

        # set PIPE configs
        if reading == FFMPEG_STDERR:
            pip_std = False
            pip_err = True
        else:
            pip_std = True
            pip_err = False

        # start ffmpeg and reading to queue
        self.open(cmd=cmd, input_source=input_source, output=output,
                  extra_cmd=extra_cmd, stdout_pipe=pip_std,
                  stderr_pipe=pip_err, text=True)
        if not self.start_reading_que(pattern=pattern, reading=reading):
            _LOGGER.warning("Can't start worker if queue is not running!")
            return

        self._worker_thread = threading.Thread(target=self._worker_process)
        self._worker_thread.start()
        _LOGGER.debug("Start working thread.")

    def _worker_process(self):
        """Function run in thread for process que data."""
        raise NotImplementedError
