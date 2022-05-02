import setuptools
import os

base_dir = os.path.dirname(__file__)
readme_path = os.path.join(base_dir, "readme.md")
if os.path.exists(readme_path):
    with open(readme_path) as stream:
        long_description = stream.read()
else:
    long_description = ""

setuptools.setup(
    name="pypr0",
    version="0.2.7",
    author="itssme",
    author_email="itssme3000@gmail.com",
    description="Implementation of the pr0gramm api in python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itssme/pypr0",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    license="GNU GPLv3",
    install_requires=[
          'requests',
    ]
)
