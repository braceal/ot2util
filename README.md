# ot2util
OT-2 protocol utilities

See `examples/` folder for specific protocols

## Development

On the OT-2 raspberry (this modifies the default python environment):
```
git clone https://github.com/braceal/ot2util.git
pip install -r ot2util/requirments/ot2-minimal.txt
pip install ot2util
```

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
