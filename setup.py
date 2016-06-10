import os
import sys

# Make sure we have setuptools:
try:
    from setuptools import setup
except:
    print >>sys.stderr, "s3yum requires setuptools to build!"
    sys.exit(1)

# Get commit hash, if possible:
try:
    import subprocess
    commit_info = " (commit: {0})".format(
        subprocess.check_output(["git"], ["git rev-parse HEAD"]))
except:
    commit_info = "n/a"

DESCRIPTION = "Command line utility for managing yum repos in Amazon S3"
setup(
    # Metadata:
    name="s3yum",
    version="1.6.1",
    url="https://github.com/NYTimes/s3yum",
    author="New York Times Digital",
    author_email="code@nytimes.com",
    maintainer="New York Times Digital",
    maintainer_email="code@nytimes.com",
    description=DESCRIPTION,
    long_description=DESCRIPTION + commit_info,
    license="Apache",
    classifiers=[
        "Environment :: Console",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet",
    ],

    # Package data:
    packages=["s3yum"],
    entry_points={
        'console_scripts': [
            's3yum = s3yum.s3yum_cli:main'
        ]},
    data_files=[
        ('share/doc/nytimes/s3yum',['README.md']),
    ],
)

# EOF

