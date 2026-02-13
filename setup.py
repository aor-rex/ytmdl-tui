from setuptools import setup, find_packages

setup(
    name="ytmdl-tui",
    version="1.0.0",
    description="tui for downloading music from youtube music with metadata",
    author="aor_rex",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "textual>=0.48.0",
        "yt-dlp>=2023.12.30",
    ],
    entry_points={
        "console_scripts": [
            "ytmdl-tui=app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)