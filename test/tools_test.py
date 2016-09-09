import logging
import sys
import click

sys.path.append("../")
from haffmpeg import Test

logging.basicConfig(level=logging.DEBUG)

@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
def cli(ffmpeg, source):
    """FFMPEG capture frame as image."""

    stream = Test(ffmpeg_bin=ffmpeg)
    stream.run_test(
        input_source=source,
    )


if __name__ == "__main__":
    cli()
