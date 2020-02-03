#!/bin/sh
set -e

set -- tests/*/*_test.py
if [ -f "$1" ]; then
    echo "Starting unittests..."
else
    echo "Unittests not found, skipping."
    exit 0
fi

pytest -k tests

echo "Done."
