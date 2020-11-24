# Home-Assistant ffmpeg interface

A Python library to control ffmepg from asyncio for [Home Assistant](https://www.home-assistant.io).

- Emulate webcam from any video input source for HA
- Analyse a video/audio stream for noise or motion detection
- Grab image from a stream

Be carfull that you protect function calls to this library with `asyncio.shield`.
