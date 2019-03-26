import asyncio
import logging
import sys
import click

from haffmpeg.sensor import SensorMotion

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option(
    "--reset",
    "-r",
    default=60,
    type=int,
    help="Time duration to need no motion before reset state",
)
@click.option(
    "--repeat-time",
    "-rt",
    default=0,
    type=int,
    help="Need repeat motion in this time period for trigger state",
)
@click.option(
    "--repeat",
    "-rc",
    default=0,
    type=int,
    help="Need repeat motion to trigger state in repeat-time",
)
@click.option(
    "--changes",
    "-c",
    default=10,
    type=float,
    help="Scene change settings or percent of image they need change",
)
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, reset, repeat_time, repeat, changes, extra):
    """FFMPEG noise detection."""
    loop = asyncio.get_event_loop()

    def callback(state):
        print("Motion detection is: %s" % str(state))

    sensor = SensorMotion(ffmpeg_bin=ffmpeg, loop=loop, callback=callback)
    sensor.set_options(
        time_reset=reset, changes=changes, repeat=repeat, time_repeat=repeat_time
    )
    loop.run_until_complete(sensor.open_sensor(input_source=source, extra_cmd=extra))

    # wait
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(sensor.close())


if __name__ == "__main__":
    cli()
