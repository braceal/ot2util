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

## Contributing

Please post an issue to request access to push new code, then run:
```
git checkout -b <branchname>
git add <files you want>
git commit -m 'message'
git push
```
Then open a pull request for a code review.

If contributing to the core ot2util package, please add test cases
mirroring the python module directory/file structure. Test file names
should have the form `test_<module>.py`. Test cases can be run with:
```
pytest test -vs
```

To make the documentation with readthedocs:

```
cd docs/
make html
```

## FAQ

1. If you recieve an error that looks as follows
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ECDSA key sent by the remote host is
Please contact your system administrator.
Add correct host key in /Users/abrace/.ssh/known_hosts to get rid of this message.
Offending ECDSA key in /Users/abrace/.ssh/known_hosts:46
Host key for 192.168.0.103 has changed and you have requested strict checking.
Host key verification failed.
```
Then you can fix it by removing your known_hosts file
```
rm /Users/abrace/.ssh/known_hosts
```

2. If the specific OT2 is not in your known hosts file (locally) then fabric will 
block until you type yes which can throw off the execution when were working with threads.
