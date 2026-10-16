import asyncio
import logging

import click

from haffmpeg.camera import CameraMjpeg

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--output", "-o", help="Output image path")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
@click.option("--extra-input", "-E", help="Extra ffmpeg command line arguments for input")
def cli(ffmpeg, source, output, extra, extra_input):
    """FFMPEG capture frame as image."""

    async def read_stream():
        """Read stream inside loop."""
        stream = CameraMjpeg(ffmpeg_bin=ffmpeg)
        await stream.open_camera(input_source=source, extra_cmd=extra, extra_input_cmd=extra_input)

        reader = await stream.get_reader()
        try:
            while True:
                data = await reader.read(2048)
                print(data)
        except OSError:
            pass
        finally:
            await stream.close()

    asyncio.run(read_stream())


if __name__ == "__main__":
    cli()
