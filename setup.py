from setuptools import setup
from esppy.version import get_version


setup(
    name='esppy',
    version=get_version(),
    author='Aliaksiej Homza',
    author_email='aliakei.homza@gmail.com',
    description='Erlang style process for python',
    license='MIT',
    packages=['esppy'],
    long_description='',
    scripts=['esppy/esppy']
)
