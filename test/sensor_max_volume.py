import asyncio
import logging

import click

from haffmpeg.sensor import MaxSensorVolume

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
def cli(ffmpeg, source, output, duration, extra):
    """FFMPEG max volume detection."""

    def callback(state):
        print("Max volume is: %s" % str(state))

    async def run():

        sensor = MaxSensorVolume(ffmpeg_bin=ffmpeg, callback=callback)
        sensor.set_options(time_duration=duration)
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
