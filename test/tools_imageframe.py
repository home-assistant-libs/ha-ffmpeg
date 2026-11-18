import asyncio
import logging

import click

from haffmpeg.tools import ImageFrame, IMAGE_JPEG

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", required=True, help="Input file for ffmpeg")
@click.option("--format_img", "-f", default=IMAGE_JPEG, help="Image output format")
@click.option("--output", "-o", required=True, help="Output image file")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
@click.option("--extra-input", "-E", help="Extra ffmpeg command line arguments for input")
def cli(ffmpeg, source, format_img, output, extra, extra_input):
    """FFMPEG capture frame as image."""

    async def capture_image():
        stream = ImageFrame(ffmpeg_bin=ffmpeg)
        return await stream.get_image(
            input_source=source, output_format=format_img, extra_cmd=extra, extra_input_cmd=extra_input
        )

    image = asyncio.run(capture_image())

    if image:
        with open(output, "wb") as fh_img:
            fh_img.write(image)
    else:
        print("No image returned. Skipping writing output")


if __name__ == "__main__":
    cli()
