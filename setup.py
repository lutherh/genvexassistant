"""Setup configuration for genvexassistant."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="genvexassistant",
    version="0.1.0",
    author="Luther",
    description="Control Genvex Ventilation systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lutherh/genvexassistant",
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyserial>=3.5",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-asyncio>=0.21",
        ],
    },
)
