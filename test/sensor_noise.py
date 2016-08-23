import logging
import click

from ../haffmpeg import SensorNoise

@click.command()
@click.option("--input", "-i", help="Input file for ffmpeg")
@click.option("--duration", "-d", default=1, type=INT,
              help="Time duration to detect as noise (peak filter)")
@click.option("--reset", "-r", default=2, type=INT,
              help="Time of silent to set the end of detection")
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(input, duration, reset, extra):
    """FFMPEG noise detection."""

    def callback(state):
        print

if __name__ == "__main__":
    cli()
