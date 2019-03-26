import asyncio
import logging
import sys
import click

from haffmpeg.sensor import SensorNoise

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--output", "-o", default=None, help="Output ffmpeg target")
@click.option(
    "--duration",
    "-d",
    default=1,
    type=int,
    help="Time duration to detect as noise (peak filter)",
)
@click.option(
    "--reset",
    "-r",
    default=2,
    type=int,
    help="Time of silent to set the end of detection",
)
@click.option(
    "--peak", "-p", default=-30, type=int, help="dB for detect a peak. Default -30"
)
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, output, duration, reset, peak, extra):
    """FFMPEG noise detection."""
    loop = asyncio.get_event_loop()

    def callback(state):
        print("Noise detection is: %s" % str(state))

    sensor = SensorNoise(ffmpeg_bin=ffmpeg, loop=loop, callback=callback)
    sensor.set_options(time_duration=duration, time_reset=reset, peak=peak)
    loop.run_until_complete(
        sensor.open_sensor(input_source=source, output_dest=output, extra_cmd=extra)
    )

    # wait
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(sensor.close())


if __name__ == "__main__":
    cli()

