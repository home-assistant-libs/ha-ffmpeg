from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

VERSION = "1.3"

setup(
    name='ha-ffmpeg',
    version=VERSION,
    license='BSD License',
    author='Pascal Vizeli',
    author_email='pvizeli@syshack.ch',
    url='https://github.com/pvizeli/ha-ffmpeg',
    download_url='https://github.com/pvizeli/ha-ffmpeg/tarball/'+VERSION,
    description=('A library that handling with ffmpeg for home-assistant'),
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords=['ffmpeg', 'homeassistant', 'wrapper', 'api'],
    zip_safe=False,
    platforms='any',
    packages=['haffmpeg'],
    include_package_data=True,
    install_requires=[
        'async_timeout'
    ]
)
