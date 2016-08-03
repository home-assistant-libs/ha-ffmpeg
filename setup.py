from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

VERSION = "0.1"

setup(
    name='ha_ffmpeg',
    version=VERSION,
    license='BSD License',
    author='Pascal Vizeli',
    author_email='pvizeli@syshack.ch',
    url='https://github.com/pvizeli/ha_ffmpeg',
    download_url='https://github.com/pvizeli/ha_ffmpeg/tarball/'+VERSION,
    description=('a Python module that provides an interface to the Yahoo! '
                 'Weather RSS feed.'),
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
    py_modules=['haffmpeg'],
)
