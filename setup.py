"""Setup configuration for render-dashboard."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="render-dashboard",
    version="0.1.0",
    author="Your Name",
    description="Monitor and manage Render services from the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "textual>=0.47.0",
        "httpx>=0.25.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "rdash=render_dashboard.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
