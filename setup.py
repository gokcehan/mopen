from setuptools import setup

setup(
    name='mopen',
    version='1',
    description='File opener using mimetypes and mailcap',
    url='https://github.com/gokcehan/mopen',
    author='Gokcehan Kara',
    author_email='gokcehankara@gmail.com',
    packages=['mopen'],
    entry_points={
        'console_scripts': [
            'mopen=mopen:main',
        ],
    },
)
