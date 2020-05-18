#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()


setup(
    name="magicgui",
    version="0.1.3",
    packages=find_packages(exclude=["tests"]),
    install_requires=["qtpy>=1.7.0"],
    python_requires=">=3.6",
    author="Talley Lambert",
    author_email="talley.lambert@gmail.com",
    description="build GUIs from functions, using magic.",
    url="https://github.com/napari/magicgui",
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords="magicgui",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    extras_require={"PySide2": ["PySide2>=5.12.0"], "PyQt5": ["PyQt5>=5.12.0"]},
)
