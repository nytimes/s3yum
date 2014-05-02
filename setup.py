from distutils.core import setup, Extension

setup(name = 's3yum',
       version = '1.3',
       description = 'Command line utility for managing yum repos in S3',
       author = 'Andrew Canaday',
       author_email = 'andrew.canaday@nytimes.com',
       scripts = ['bin/s3yum'])

# EOF

