# ot2util
OT-2 protocol utilities

See `examples/` folder for specific protocols

## Development

On the OT-2 raspberry (this modifies the default python environment):
```
git clone https://github.com/braceal/ot2util.git
pip install -r ot2util/requirements/ot2-minimal.txt
pip install ot2util/
```

Issuing commands from ssh causes the OT-2 to look for calibration files
in the ~/.opentrons folder. You can update the calibration files via:
```
mv .opentrons/ .opentrons-back
cp -r /var/data/* ~/.opentrons/
```

Pip Locally:
```
python3 -m venv ot2
source ot2/bin/activate
pip3 install -U pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```

Conda Locally: 
```
conda create -n ot2 python=3.9 
conda activate ot2
pip install -U pip setuptools wheel
pip install -r requirements/dev.txt
pip install -r requirements/requirements.txt
pip install -e .
```

To run dev tools (flake8, black, mypy): `make`

## Setup

When setting up an ssh key to connect to the opentrons, it is
helpful to make a new one without a passphrase.
For more information on setting up an ssh connection see:
- https://support.opentrons.com/en/articles/3203681-setting-up-ssh-access-to-your-ot-2
- https://support.opentrons.com/en/articles/3287453-connecting-to-your-ot-2-with-ssh
