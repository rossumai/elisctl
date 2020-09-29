#!/usr/bin/env python3
from setuptools import setup

setup(
    name="elisctl",
    version="2.10.0",
    description="Command line interface for controlling the Rossum platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://developers.rossum.ai/",
    author="Rossum developers",
    author_email="support@rossum.ai",
    license="MIT",
    project_urls={
        "Source": "https://github.com/rossumai/elisctl",
        "Tracker": "https://github.com/rossumai/elisctl/issues",
    },
    classifiers=[
        "Development Status :: 7 - Inactive",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        "rossum",
    ],
    python_requires=">=3.6",
    zip_safe=False,
    entry_points={"console_scripts": ["elisctl = elisctl.main:entry_point"]},
)
