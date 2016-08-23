import logging
import sys
import click

from time import sleep

sys.path.append("../")
from haffmpeg import SensorNoise

logging.basicConfig(level=logging.DEBUG)

@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
@click.option("--source", "-s", help="Input file for ffmpeg")
@click.option("--output", "-o", default=None, help="Output ffmpeg target")
@click.option("--duration", "-d", default=1, type=int,
              help="Time duration to detect as noise (peak filter)")
@click.option("--reset", "-r", default=2, type=int,
              help="Time of silent to set the end of detection")
@click.option("--peak", "-p", default=-30, type=int,
              help="dB for detect a peak. Default -30")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
@click.option("--wait", "-w", default=30, type=int,
              help="Run sensor for seconds")
def cli(ffmpeg, source, output, duration, reset, peak, extra, wait):
    """FFMPEG noise detection."""

    def callback(state):
        print("Noise detection is: %s" % str(state))

    sensor = SensorNoise(ffmpeg_bin=ffmpeg, callback=callback)
    sensor.set_options(time_duration=duration, time_reset=reset, peak=peak)
    sensor.open_sensor(input_source=source, output_dest=output, extra_cmd=extra)

    # wait
    sleep(wait)
    sensor.close()

if __name__ == "__main__":
    cli()

