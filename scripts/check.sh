#!/usr/bin/env sh
isort --check src
black --check src
mypy src
