import asyncio
import logging

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
@click.option("--extra-input", "-E", help="Extra ffmpeg command line arguments for input")
def cli(ffmpeg, source, reset, repeat_time, repeat, changes, extra, extra_input):
    """FFMPEG noise detection."""

    def callback(state):
        print("Motion detection is: %s" % str(state))

    async def run():

        sensor = SensorMotion(ffmpeg_bin=ffmpeg, callback=callback)
        sensor.set_options(
            time_reset=reset, changes=changes, repeat=repeat, time_repeat=repeat_time
        )
        await sensor.open_sensor(input_source=source, extra_cmd=extra, extra_input_cmd=extra_input)
        try:
            while True:
                await asyncio.sleep(0.1)
        finally:
            await sensor.close()

    asyncio.run(run())


if __name__ == "__main__":
    cli()
