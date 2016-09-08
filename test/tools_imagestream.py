import logging
import sys
import os
import click
from time import sleep

sys.path.append("../")
from haffmpeg import ImageStream, IMAGE_JPEG, IMAGE_PNG

logging.basicConfig(level=logging.DEBUG)

@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--format_img", "-f", default=IMAGE_JPEG, help="Image output format")
@click.option("--output", "-o", help="Output image path")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
@click.option("--interval", "-i", default=10, help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, format_img, output, extra, interval):
    """FFMPEG capture frame as image."""
    count = 0

    def _callback(image):
        count += 1
        name = os.path.join(output, "image{0}.{1}".format(count, format_img))
        with open(, "wb") as fh_img:
            fh_img.write(image)

    stream = ImageStream(ffmpeg_bin=ffmpeg, callback=_callback)
    image = stream.open_stream(
        input_source=source,
        output_format=format_img,
        extra_cmd=extra,
        interval=interval,
    )

    sleep(120)
    stream.close()

if __name__ == "__main__":
    cli()
