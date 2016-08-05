"""
Base functionality of ffmpeg HA wrapper.
"""
import logger
import shlex
import subprocess

_LOGGER = logging.getLogger(__name__)

ITER_STDOUT = 'OUT'
ITER_STDERR = 'ERR'

HAFFmpeg(object):
    """Base HA FFmpeg process.
    
    Object is iterable but only for data streams! For other things use the process
    property
    to call from Popen object.
    """

    def __init__(self, ffmpeg_bin, chunk_size=1024, iter_input=ITER_STDOUT):
        """Base initialize."""
        self._ffmpeg = ffmpeg_bin
        self._argv = [ffmpeg_bin]
        self._proc = None
        self._chunk_size = chunk_size
        self._iter_input = iter_input

    def open(self, cmd, output="-", extra_cmd=None, text=False,
               stdout_pipe=True, stderr_pipe=False):
        """Start a ffmpeg instance and pipe output."""
        stdout = subprocess.PIPE if stdout_pipe else subprocess.DEVNULL
        stderr = subprocess.PIPE if stderr_pipe else subprocess.DEVNULL

        if self._proc is not None:
            _LOGGER.critical("FFmpeg is allready running!")
            return

        # add cmds
        self._argv.append(cmd)

        # exists a extra cmd from customer
        if extra_cmd is not None:
            self._argv.extend(shlex.split(extra_cmd))

        # add output
        self._argv.append(output)

        # start ffmpeg
        self._proc = subprocess.Popen(
            self._argv,
            stderr=stderr,
            stdout=stdout,
            universal_newlines=text
        )

    def close(self, timeout=15):
        """Stop a ffmpeg instance."""

        if self._proc is None:
            _LOGGER.error("FFmpeg isn't running!")
            return

        # send stop to ffmpeg
        self._proc.terminate()

        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _LOGGER.warning("Timeout while waiting of FFmpeg.")

        # clean ffmpeg cmd
        self._argv = [self._ffmpeg]
        self._proc = None

    @property
    def process(self):
        return self._proc

    def __iter__(self):
        """Read data from ffmpeg PIPE/STDERR as iter."""
        return self
        
    def __next__(self):
        """Get next buffer data."""
        if self._proc is None or self._proc.poll() is not None:
            raise StopIteration
        
        # generate reading from
        if self._iter_input == ITER_STDERR:
            read_from = self._proc.stderr
        else
            read_from = self._proc.stdout
            
        # check if reading from pipe
        if read_from is None:
            raise StopIteration
            
        return read_from.read(self._chunk_size)
