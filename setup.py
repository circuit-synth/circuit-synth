#!/usr/bin/env python
"""Setup script for circuit_synth package."""

from setuptools import setup, find_packages

# Read the contents of README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="circuit_synth",
    version="0.1.0",
    author="Circuit Synth Contributors",
    author_email="contact@circuitsynth.com",
    description="Pythonic circuit design for production-ready KiCad projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/circuitsynth/circuit-synth",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.3.0",
        "networkx>=2.6.0",
        "pydantic>=2.0.0",
        "PyYAML>=5.4.0",
        "click>=8.0.0",
        "rich>=10.0.0",
        "loguru>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
        ]
    },
    zip_safe=False,
    include_package_data=True,
    package_data={
        "circuit_synth": ["py.typed"],
    },
)