"""Base functionality of ffmpeg HA wrapper."""
import asyncio
import logging
import re
import shlex

import async_timeout

_LOGGER = logging.getLogger(__name__)

FFMPEG_STDOUT = 'stdout'
FFMPEG_STDERR = 'stderr'


class HAFFmpeg:
    """HA FFmpeg process async.

    Object is iterable or use the process property to call from Popen object.
    """

    def __init__(self, ffmpeg_bin, loop):
        """Base initialize."""
        self._loop = loop
        self._ffmpeg = ffmpeg_bin
        self._argv = None
        self._proc = None

    @property
    def process(self):
        """Return a Popen object or None of not running."""
        return self._proc

    def _generate_ffmpeg_cmd(self, cmd, input_source, output, extra_cmd=None):
        """Generate ffmpeg command line."""
        self._argv = [self._ffmpeg]

        # start command init
        if input_source is not None:
            self._put_input(input_source)
        self._argv.extend(cmd)

        # exists a extra cmd from customer
        if extra_cmd is not None:
            self._argv.extend(shlex.split(extra_cmd))

        self._merge_filters()
        self._put_output(output)

    def _put_input(self, input_source):
        """Put input string to ffmpeg command."""
        input_cmd = shlex.split(str(input_source))
        if len(input_cmd) > 1:
            self._argv.extend(input_cmd)
        else:
            self._argv.extend(['-i', input_source])

    def _put_output(self, output):
        """Put output string to ffmpeg command."""
        if output is None:
            self._argv.extend(['-f', 'null', '-'])
            return

        output_cmd = shlex.split(str(output))
        if len(output_cmd) > 1:
            self._argv.extend(output_cmd)
        else:
            self._argv.append(output)

    def _merge_filters(self):
        """Merge all filter config in command line."""
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

    def _clear(self):
        """Clear member variable after close."""
        self._argv = None
        self._proc = None

    async def open(self, cmd, input_source, output="-", extra_cmd=None,
                   stdout_pipe=True, stderr_pipe=False):
        """Start a ffmpeg instance and pipe output."""
        stdout = asyncio.subprocess.PIPE if stdout_pipe\
            else asyncio.subprocess.DEVNULL
        stderr = asyncio.subprocess.PIPE if stderr_pipe\
            else asyncio.subprocess.DEVNULL

        if self.is_running:
            _LOGGER.warning("FFmpeg is already running!")
            return True

        # set command line
        self._generate_ffmpeg_cmd(cmd, input_source, output, extra_cmd)

        # start ffmpeg
        _LOGGER.debug("Start FFmpeg with %s", str(self._argv))
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self._argv,
                loop=self._loop,
                stdin=asyncio.subprocess.PIPE,
                stdout=stdout,
                stderr=stderr
            )
        # pylint: disable=broad-except
        except Exception as err:
            _LOGGER.exception("FFmpeg fails %s", err)
            self._clear()
            return False

        return self._proc is not None

    async def close(self, timeout=5):
        """Stop a ffmpeg instance."""
        if not self.is_running:
            _LOGGER.warning("FFmpeg isn't running!")
            return

        try:
            # send stop to ffmpeg
            with async_timeout.timeout(timeout, loop=self._loop):
                await self._proc.communicate(input=b'q')
            _LOGGER.debug("Close FFmpeg process")

        except (asyncio.TimeoutError, ValueError):
            _LOGGER.warning("Timeout while waiting of FFmpeg")
            self._proc.kill()

        finally:
            self._clear()

    @property
    def is_running(self):
        """Return True if ffmpeg is running."""
        if self._proc is None or self._proc.returncode is not None:
            return False
        return True

    def read(self, count=-1):
        """Read data like a file handle.

        Return a coroutine
        """
        return self._proc.stdout.read(count)


class HAFFmpegWorker(HAFFmpeg):
    """Read FFmpeg output to que."""

    def __init__(self, ffmpeg_bin, loop):
        """Init noise sensor."""
        super().__init__(ffmpeg_bin, loop)

        self._que = asyncio.Queue(loop=loop)
        self._input = None
        self._read_task = None

    def close(self, timeout=5):
        """Stop a ffmpeg instance.

        Return a coroutine
        """
        if self._read_task is not None and not self._read_task.cancelled():
            self._read_task.cancel()

        return super().close(timeout)

    async def _process_lines(self, pattern=None):
        """Read line from pipe they match with pattern."""
        if pattern is not None:
            cmp = re.compile(pattern)

        _LOGGER.debug("Start working with pattern '%s'.", pattern)

        # read lines
        while self.is_running:
            try:
                line = await self._input.readline()
                if not line:
                    break
                line = line.decode()
            # pylint: disable=broad-except
            except Exception:
                break

            match = True if pattern is None else cmp.search(line)
            if match:
                _LOGGER.debug("Process: %s", line)
                await self._que.put(line)

        try:
            await self._proc.wait()
        finally:
            await self._que.put(None)
            _LOGGER.debug("Close read ffmpeg output.")

    async def _worker_process(self):
        """Process output line."""
        raise NotImplementedError()

    async def start_worker(self, cmd, input_source, output=None,
                           extra_cmd=None, pattern=None,
                           reading=FFMPEG_STDERR):
        """Start ffmpeg do process data from output."""
        if self.is_running:
            _LOGGER.warning("Can't start worker. It is allready running!")
            return

        if reading == FFMPEG_STDERR:
            stdout = False
            stderr = True
        else:
            stdout = True
            stderr = False

        # start ffmpeg and reading to queue
        await self.open(
            cmd=cmd, input_source=input_source, output=output,
            extra_cmd=extra_cmd, stdout_pipe=stdout, stderr_pipe=stderr)

        self._input = self._proc.stderr if reading == FFMPEG_STDERR \
            else self._proc.stdout

        # start background processing
        self._read_task = self._loop.create_task(self._process_lines(pattern))
        self._loop.create_task(self._worker_process())
