"""Setup script for Cerebras CLI."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "cerebras-cloud-sdk",
        "click>=8.0.0",
        "rich>=13.0.0",
        "aiohttp>=3.8.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
    ]

setup(
    name="cerebras-cli",
    version="1.0.0",
    author="Addhe Warman Putra (Awan)",
    author_email="addhe@example.com",
    description="AI-powered command-line interface for Cerebras models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/addheputra/cerebras-chatgpt-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Terminals",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "enhanced": [
            "keyring>=24.0.0",
            "gitpython>=3.1.0",
            "pygments>=2.13.0",
            "prompt-toolkit>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cerebras-cli=cerebras_cli.cli.main:main",
            "cerebras-legacy=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cerebras_cli": ["*.yaml", "*.yml"],
    },
    keywords=[
        "ai", "cli", "chatgpt", "cerebras", "machine-learning", 
        "natural-language-processing", "llm", "terminal", "assistant"
    ],
    project_urls={
        "Bug Reports": "https://github.com/addheputra/cerebras-chatgpt-cli/issues",
        "Source": "https://github.com/addheputra/cerebras-chatgpt-cli",
        "Documentation": "https://github.com/addheputra/cerebras-chatgpt-cli/blob/main/README.md",
    },
)
