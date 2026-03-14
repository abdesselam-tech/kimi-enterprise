#!/usr/bin/env python3
"""
Kimi Enterprise - Multi-agent orchestration framework for Kimi CLI
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="kimi-enterprise",
    version="2.0.0",
    author="Kimi Enterprise Contributors",
    author_email="",
    description="Enterprise-grade multi-agent orchestration for Kimi CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abdesselam-tech/kimi-enterprise",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "mcp>=1.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "kimi-enterprise-cli=kimi_enterprise.cli:main",
            "ke=kimi_enterprise.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "kimi_enterprise": ["../share/**/*"],
    },
    project_urls={
        "Bug Reports": "https://github.com/abdesselam-tech/kimi-enterprise/issues",
        "Source": "https://github.com/abdesselam-tech/kimi-enterprise",
        "Documentation": "https://github.com/abdesselam-tech/kimi-enterprise#readme",
    },
)
