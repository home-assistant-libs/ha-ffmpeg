import asyncio
import logging
import sys
import os
import click
from time import sleep

from haffmpeg.camera import CameraMjpeg

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--output", "-o", help="Output image path")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, output, extra):
    """FFMPEG capture frame as image."""
    loop = asyncio.get_event_loop()
    stream = CameraMjpeg(ffmpeg_bin=ffmpeg, loop=loop)

    async def read_stream():
        """Read stream inside loop."""
        await stream.open_camera(source, extra)

        reader = await stream.get_reader()
        try:
            while True:
                data = await reader.read(2048)
                print(data)
        except OSError:
            pass

    future = asyncio.ensure_future(read_stream())
    try:
        loop.run_until_complete(future)
    finally:
        loop.call_soon_threadsafe(future.cancel)
        loop.run_until_complete(stream.close())


if __name__ == "__main__":
    cli()
