#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()


setup(
    name="magicgui",
    use_scm_version={"write_to": "magicgui/_version.py"},
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    install_requires=["qtpy>=1.7.0", "typing_extensions"],
    python_requires=">=3.7",
    author="Talley Lambert",
    author_email="talley.lambert@gmail.com",
    description="build GUIs from functions, using magic.",
    url="https://github.com/napari/magicgui",
    project_urls={
        "Documentation": "https://napari.org/magicgui",
        "Say Thanks!": "http://saythanks.io/to/example",
        "Source": "https://github.com/napari/magicgui",
        "Tracker": "https://github.com/napari/magicgui/issues",
        "Changelog": "https://github.com/napari/magicgui/blob/master/CHANGELOG.md",
    },
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    extras_require={
        "PySide2": [
            "PySide2>=5.13 ; python_version=='3.7'",
            "PySide2>=5.14 ; python_version=='3.8'",
            "PySide2>=5.15 ; python_version=='3.9'",
        ],
        "PyQt5": "PyQt5>=5.12.0",
    },
)
