#!/usr/bin/env sh
black --check src
isort --check src
flake518 src
mypy src
