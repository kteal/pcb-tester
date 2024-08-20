#!/usr/bin/bash
isort --check src
black --check src
mypy src
