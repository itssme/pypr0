import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pypr0",
    version="0.1.1",
    author="itssme",
    author_email="itssme3000@gmail.com",
    description="Implementation of the pr0gramm api in python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itssme/pypr0",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)