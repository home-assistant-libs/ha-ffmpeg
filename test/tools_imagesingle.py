import logging
import sys
import click
import asyncio

from haffmpeg.tools import ImageFrame, IMAGE_JPEG, IMAGE_PNG

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--format_img", "-f", default=IMAGE_JPEG, help="Image output format")
@click.option("--output", "-o", help="Output image file")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, format_img, output, extra):
    """FFMPEG capture frame as image."""
    loop = asyncio.get_event_loop()

    stream = ImageFrame(ffmpeg_bin=ffmpeg, loop=loop)
    future = asyncio.ensure_future(
        stream.get_image(input_source=source, output_format=format_img, extra_cmd=extra)
    )
    image = loop.run_until_complete(future)

    if image is not None:
        with open(output, "wb") as fh_img:
            fh_img.write(image)


if __name__ == "__main__":
    cli()
