from setuptools import setup, find_packages
import os
import sys

# Add src to path to import version dynamically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
try:
    from version import get_version_string
    VERSION = get_version_string()
except:
    VERSION = "2.5.3"  # Fallback version

setup(
    name="PrinterReaper",
    version=VERSION,
    author="Andre Henrique (mrhenrike)",
    author_email="",  # Add if desired
    description="Advanced Printer Penetration Testing Toolkit",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mrhenrike/PrinterReaper",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    install_requires=[
        "requests>=2.31.0",
        "urllib3>=2.0.0",
        "pysnmp-lextudio>=5.0.31",
        "colorama>=0.4.6",
    ],
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
    ],
    
    python_requires=">=3.8",
    
    entry_points={
        "console_scripts": [
            "printerreaper=main:main",
            "pret=main:main",  # Alias for PRET compatibility
        ],
    },
    
    project_urls={
        "Bug Reports": "https://github.com/mrhenrike/PrinterReaper/issues",
        "Source": "https://github.com/mrhenrike/PrinterReaper",
    },
)