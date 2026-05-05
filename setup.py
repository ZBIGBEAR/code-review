from setuptools import setup, find_packages
import sys
sys.path.insert(0, '.')
from code_review import __version__

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="alex-code-review",
    version=__version__,
    author="Alex",
    author_email="664141154@qq.com",
    description="Multi-agent code review system with LLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZBIGBEAR/code-review",
    packages=find_packages(exclude=["config", "reports", "actions", "scripts"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ],
    python_requires='>=3.10',
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0",
        "gitpython>=3.1",
        "anthropic>=0.18",
        "python-dotenv>=1.0",
    ],
    entry_points={
        'console_scripts': [
            'alex-code-review=code_review.main:cli',
        ],
    },
    include_package_data=True,
)
