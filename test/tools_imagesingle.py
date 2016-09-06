import logging
import sys
import click

sys.path.append("../")
from haffmpeg import ImageSingle, IMAGE_JPEG, IMAGE_PNG

logging.basicConfig(level=logging.DEBUG)

@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--format_img", "-f", default=IMAGE_JPEG, help="Image output format")
@click.option("--output", "-o", help="Output image file")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, format_img, output, extra):
    """FFMPEG capture frame as image."""

    stream = ImageSingle(ffmpeg_bin=ffmpeg)
    image = stream.get_image(
        input_source=source,
        output_format=format_img,
        extra_cmd=extra
    )

    if image is not None:
        with open(output, "wb") as fh_img:
            fh_img.write(image)


if __name__ == "__main__":
    cli()
