#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md", encoding='utf-8') as readme_file:
    readme = readme_file.read()

requirements = []

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Talley Lambert",
    author_email="talley.lambert@gmail.com",
    python_requires=">=3.6",
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
    description="build GUIs from functions, using magic.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords="magicgui",
    name="magicgui",
    packages=find_packages(include=["magicgui", "magicgui.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/tlambert03/magicgui",
    version="0.1.0",
    zip_safe=False,
)
