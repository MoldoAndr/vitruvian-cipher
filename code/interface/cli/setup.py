from setuptools import setup, find_packages

setup(
    name="vitruvian-cipher",
    version="2.0.0",
    description="Vitruvian Cipher CLI for cryptography and security analysis agents",
    author="Agent Interface Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.7.0",
        "prompt_toolkit>=3.0.43",
        "httpx>=0.26.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.7",
        "tabulate>=0.9.0",
        "humanize>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "vitruvian-cipher=agent_cli.main:main",
            "agent-cli=agent_cli.main:main",
            "acli=agent_cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
