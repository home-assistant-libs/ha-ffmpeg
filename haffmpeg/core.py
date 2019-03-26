"""Base functionality of ffmpeg HA wrapper."""
import asyncio
import functools
import logging
import re
import shlex
import subprocess
from typing import List, Optional

_LOGGER = logging.getLogger(__name__)

FFMPEG_STDOUT = "stdout"
FFMPEG_STDERR = "stderr"


class HAFFmpeg:
    """HA FFmpeg process async.

    Object is iterable or use the process property to call from Popen object.
    """

    def __init__(self, ffmpeg_bin: str, loop: asyncio.BaseEventLoop):
        """Base initialize."""
        self._loop = loop
        self._ffmpeg = ffmpeg_bin
        self._argv = None
        self._proc = None

    @property
    def process(self) -> subprocess.Popen:
        """Return a Popen object or None of not running."""
        return self._proc

    @property
    def is_running(self) -> bool:
        """Return True if ffmpeg is running."""
        if self._proc is None or self._proc.returncode is not None:
            return False
        return True

    def _generate_ffmpeg_cmd(
        self,
        cmd: List[str],
        input_source: Optional[str],
        output: Optional[str],
        extra_cmd: Optional[str] = None,
    ) -> None:
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

    def _put_input(self, input_source: str) -> None:
        """Put input string to ffmpeg command."""
        input_cmd = shlex.split(str(input_source))
        if len(input_cmd) > 1:
            self._argv.extend(input_cmd)
        else:
            self._argv.extend(["-i", input_source])

    def _put_output(self, output: Optional[str]) -> None:
        """Put output string to ffmpeg command."""
        if output is None:
            self._argv.extend(["-f", "null", "-"])
            return

        output_cmd = shlex.split(str(output))
        if len(output_cmd) > 1:
            self._argv.extend(output_cmd)
        else:
            self._argv.append(output)

    def _merge_filters(self) -> None:
        """Merge all filter config in command line."""
        for opts in (["-filter:a", "-af"], ["-filter:v", "-vf"]):
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

    def _clear(self) -> None:
        """Clear member variable after close."""
        self._argv = None
        self._proc = None

    async def open(
        self,
        cmd: List[str],
        input_source: Optional[str],
        output: Optional[str] = "-",
        extra_cmd: Optional[str] = None,
        stdout_pipe: bool = True,
        stderr_pipe: bool = False,
    ) -> bool:
        """Start a ffmpeg instance and pipe output."""
        stdout = subprocess.PIPE if stdout_pipe else subprocess.DEVNULL
        stderr = subprocess.PIPE if stderr_pipe else subprocess.DEVNULL

        if self.is_running:
            _LOGGER.warning("FFmpeg is already running!")
            return True

        # set command line
        self._generate_ffmpeg_cmd(cmd, input_source, output, extra_cmd)

        # start ffmpeg
        _LOGGER.debug("Start FFmpeg with %s", str(self._argv))
        try:
            proc_func = functools.partial(
                subprocess.Popen,
                self._argv,
                bufsize=0,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
            )
            self._proc = await self._loop.run_in_executor(None, proc_func)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("FFmpeg fails %s", err)
            self._clear()
            return False

        return self._proc is not None

    async def close(self, timeout=5) -> None:
        """Stop a ffmpeg instance."""
        if not self.is_running:
            _LOGGER.warning("FFmpeg isn't running!")
            return

        # Can't use communicate because we attach the output to a streamreader
        def _close():
            """Close ffmpeg."""
            self._proc.stdin.write(b"q")
            self._proc.wait(timeout=timeout)

        # send stop to ffmpeg
        try:
            await self._loop.run_in_executor(None, _close)
            _LOGGER.debug("Close FFmpeg process")

        except (subprocess.TimeoutExpired, ValueError):
            _LOGGER.warning("Timeout while waiting of FFmpeg")
            self.kill()

        finally:
            self._clear()

    def kill(self) -> None:
        """Kill ffmpeg job."""
        self._proc.kill()
        self._loop.run_in_executor(None, self._proc.communicate)

    async def get_reader(self, source=FFMPEG_STDOUT) -> asyncio.StreamReader:
        """Create and return streamreader."""
        reader = asyncio.StreamReader(loop=self._loop)
        reader_protocol = asyncio.StreamReaderProtocol(reader)

        # Attach stream
        if source == FFMPEG_STDOUT:
            await self._loop.connect_read_pipe(
                lambda: reader_protocol, self._proc.stdout
            )
        else:
            await self._loop.connect_read_pipe(
                lambda: reader_protocol, self._proc.stderr
            )

        # Start reader
        return reader


class HAFFmpegWorker(HAFFmpeg):
    """Read FFmpeg output to que."""

    def __init__(self, ffmpeg_bin: str, loop: asyncio.BaseEventLoop):
        """Init noise sensor."""
        super().__init__(ffmpeg_bin, loop)

        self._que = asyncio.Queue(loop=loop)
        self._input = None
        self._read_task = None

    def close(self, timeout: int = 5) -> None:
        """Stop a ffmpeg instance.

        Return a coroutine
        """
        if self._read_task is not None and not self._read_task.cancelled():
            self._read_task.cancel()

        return super().close(timeout)

    async def _process_lines(self, pattern: Optional[str] = None) -> None:
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
            except Exception:  # pylint: disable=broad-except
                break

            match = True if pattern is None else cmp.search(line)
            if match:
                _LOGGER.debug("Process: %s", line)
                await self._que.put(line)

        try:
            await self._loop.run_in_executor(None, self._proc.wait)
        finally:
            await self._que.put(None)
            _LOGGER.debug("Close read ffmpeg output.")

    async def _worker_process(self) -> None:
        """Process output line."""
        raise NotImplementedError()

    async def start_worker(
        self,
        cmd: List[str],
        input_source: str,
        output: Optional[str] = None,
        extra_cmd: Optional[str] = None,
        pattern: Optional[str] = None,
        reading: str = FFMPEG_STDERR,
    ) -> None:
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
            cmd=cmd,
            input_source=input_source,
            output=output,
            extra_cmd=extra_cmd,
            stdout_pipe=stdout,
            stderr_pipe=stderr,
        )

        self._input = await self.get_reader(reading)

        # start background processing
        self._read_task = self._loop.create_task(self._process_lines(pattern))
        self._loop.create_task(self._worker_process())
