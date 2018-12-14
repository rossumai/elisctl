#!/usr/bin/env python3.7
from setuptools import setup, find_packages


setup(
    name="elis_tools",
    version="0.1.0",
    description="Tools for ELIS operations",
    url="https://gitlab.rossum.ai/elis/tools",
    author="ELIS authors",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers" "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(exclude=("tests*",)),
    install_requires=["pandas", "click", "xlrd", "requests", "jsondiff"],
    python_requires="~=3.7",
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-cov", "openpyxl", "requests_mock"],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "csv_to_options = tools.csv_to_options:cli",
            "xls_to_csv = tools.xls_to_csv:cli",
            "transform_schema = tools.transform_schema:cli",
            "download = tools.download:cli",
            "upload = tools.upload:cli",
            "compare = tools.compare:cli",
        ]
    },
)
