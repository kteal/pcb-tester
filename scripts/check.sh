#!/usr/bin/env sh
set -e
black --check src
isort --check src
flake518 src
mypy src
set +e
