# pcb-tester
PCB HITL tester for Illini Electric Motorsports FSAE Team

## Usage

### Using Nix

1. Install Nix using the [Determinate Systems Installer](https://github.com/DeterminateSystems/nix-installer).
```
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Note:** If using WSL2, you need to ensure that `systemd` is running before installing Nix. Open `/etc/wsl.conf` with your favorite text editor (eg. `sudo vim /etc/wsl.conf`) and make sure it looks like below:
```
[boot]
systemd=true
```
If not, add these lines and restart WSL.

2. Reload/reopen shell, run `nix --version` to verify that Nix is installed.

3. Run `nix develop` in the root directory to enter the shell.

### Using `venv`

1. `python3 -m venv venv` to create a `venv` environment.
2. `source venv/bin/activate` to enter the environment.
3. `pip3 install -r requirements.txt` to install required packages.
