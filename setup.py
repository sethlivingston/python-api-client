import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / 'README').read_text()

# This call to setup() does all the work
setup(
    name='apiendpoints',
    version='0.9.0',
    description='Wraps Python Requests with an (even) easier to use '
                'programming model for accessing a REST API.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/sethlivingston/python-api-client',
    author='Seth M. Livingston',
    author_email='webdevbyseth@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    packages=['apiendpoints'],
    include_package_data=True,
    install_requires=['requests'],
)
