import asyncio
import logging

import click

from haffmpeg.tools import FFVersion

logging.basicConfig(level=logging.DEBUG)


@click.command()
@click.option("--ffmpeg", "-f", default="ffmpeg", help="FFmpeg binary")
def cli(ffmpeg):
    """FFMPEG version."""

    async def get_version():
        ffversion = FFVersion(ffmpeg_bin=ffmpeg)
        print(await ffversion.get_version())

    asyncio.run(get_version())


if __name__ == "__main__":
    cli()
