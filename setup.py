"""Setup script for renpy-cloud package."""

from setuptools import setup, find_packages
import os


def read_file(filename):
    """Read contents of a file."""
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()


setup(
    name='renpy-cloud',
    version='0.1.0',
    author='renpy-cloud contributors',
    description='Cloud save synchronization for Ren\'Py games',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/renpy-cloud',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/renpy-cloud/issues',
        'Source': 'https://github.com/yourusername/renpy-cloud',
        'Documentation': 'https://github.com/yourusername/renpy-cloud#readme',
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'infra', 'example_game']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='renpy visual-novel games cloud-save sync aws s3 cognito',
    python_requires='>=3.8',
    install_requires=[
        # No external dependencies - uses only stdlib
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [],
    },
    include_package_data=True,
    zip_safe=False,
    license='MIT',
)

