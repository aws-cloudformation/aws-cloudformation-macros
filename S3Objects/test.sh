#!/bin/bash

pip3 install -r requirements-dev.txt
python3 -m pytest -v unit-tests/
