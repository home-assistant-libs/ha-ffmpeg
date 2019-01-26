import logging
import sys
import click
import asyncio

sys.path.append("../")
from haffmpeg.tools import FFVersion

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
def cli(ffmpeg):
    """FFMPEG version."""

    loop = asyncio.get_event_loop()
    ffversion = FFVersion(ffmpeg_bin=ffmpeg, loop=loop)
    future = asyncio.ensure_future(ffversion.get_version())
    loop.run_until_complete(future)
    print(future.result())


if __name__ == "__main__":
    cli()
