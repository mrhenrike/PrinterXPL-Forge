from setuptools import setup, find_packages

setup(
    name="PrinterReaper",
    version="1.0.0",
    author="mrhenrike",
    description="Toolkit for abusing Printer's Languages for fun and profit.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mrhenrike/PrinterReaper",
    
    packages=find_packages(),
    
    install_requires=[
        "requests",
        "colorama",
        "pysnmp-lextudio==5.0.31"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
    ],
    
    python_requires=">=3.9",
    
    entry_points={
        "console_scripts": [
            "pret=src.pret:main2",
        ],
    },
)