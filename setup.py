from setuptools import setup, find_packages

setup(
    name="dbridge",
    version="0.8.0b",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "SQLAlchemy>=2.0.0",
        "pymysql>=1.0.2",
        "psycopg2-binary>=2.9.5",
        "pandas>=1.5.2",
        "matplotlib>=3.6.2",
    ],
    entry_points={
        "console_scripts": [
            "dbridge=src.main:main",
        ],
    },
    author="David Leavitt",
    author_email="david@leavitt.pro",
    description="A user-friendly SQL client for Linux, Windows, and macOS",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/davleav/dbridge",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.8",
)