#!/bin/sh
set -e

echo "Upgrde pip..."
pip install --upgrade pip

echo "Installing pipenv..."
pip install pipenv

echo "Installing requirements..."

if [ "${BUILD_ENV}" = "TEST" ]; then
  pipenv install --dev --system --deploy --ignore-pipfile
else
  pipenv install --system --deploy --ignore-pipfile
fi

echo "Cleaning up..."
find "/usr/local/lib/python3.7" -name '*.c' -delete
find "/usr/local/lib/python3.7" -name '*.pxd' -delete
find "/usr/local/lib/python3.7" -name '*.pyd' -delete
find "/usr/local/lib/python3.7" -name '__pycache__' | xargs rm -r

echo "Done."
