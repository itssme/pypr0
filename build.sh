#!/usr/bin/env bash
python3 setup.py sdist bdist_wheel

# if -up is passed the package will be uploaded to pypi
if [ "$1" = "-up" ]
then
    # be sure twine is at version 1.12.1 or the markdown in the readme won't work
    twine upload  dist/*
fi

# if -up is passed the package will be uploaded to pypi
if [ "$1" = "-up-test" ]
then
    twine upload --repository testpypi dist/*
fi
