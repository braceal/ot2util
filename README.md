# ot2util
OT2 protocol utilities

See `examples/` folder for specific protocols

## Development

Make sure to use Python >= 3.9

Locally:
```
python3 -m venv ot2
source ot2/bin/activate
pip3 install -U pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```
To run dev tools (flake8, black, mypy): `make`
