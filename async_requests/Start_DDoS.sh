#! /bin/bash

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install pyinstaller requests aiohttp
pyinstaller --onefile --clean --log-level ERROR async_client.spec
deactivate
rm -rf venv
rm -rf __pycache__ build

printf "\n\n"
date && ./dist/async_client
printf "\n\n"

echo "Done!"
