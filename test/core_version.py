import logging
import sys
import click
import asyncio

sys.path.append("../")
from haffmpeg import HAFFmpeg

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
def cli(ffmpeg):
    """FFMPEG version."""

    loop = asyncio.get_event_loop()
    ha_ffmpeg = HAFFmpeg(ffmpeg_bin=ffmpeg, loop=loop)
    future = asyncio.ensure_future(ha_ffmpeg.version())
    loop.run_until_complete(future)
    print(future.result())


if __name__ == "__main__":
    cli()
