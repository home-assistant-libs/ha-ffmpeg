import asyncio
import logging

import click

from haffmpeg.sensor import SensorVolume

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
    help="Time duration to detect volume",
)
@click.option("--extra", "-e", help="Extra ffmpeg command line arguments")
def cli(ffmpeg, source, output, duration, reset, peak, extra):
    """FFMPEG volume detection."""

    def callback(state):
        print("Volume is: %s" % str(state))

    async def run():

        sensor = SensorVolume(ffmpeg_bin=ffmpeg, callback=callback)
        sensor.set_options(time_duration=duration, time_reset=reset, peak=peak)
        await sensor.open_sensor(
            input_source=source, output_dest=output, extra_cmd=extra
        )
        try:
            while True:
                await asyncio.sleep(0.1)
        finally:
            await sensor.close()

    asyncio.run(run())


if __name__ == "__main__":
    cli()
