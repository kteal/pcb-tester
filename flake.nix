{
  description = "A flake for the PCB tester";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-24.05";

    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        pydwf = pkgs.python311Packages.buildPythonPackage {
          pname = "pydwf";
          version = "1.1.19";
          pyproject = true;

          src = pkgs.fetchPypi {
            pname = "pydwf";
            version = "1.1.19";
            sha256 = "9b953fa0d9758c0004d80b868ab86be326583a5a4d854065f3a565362715f81b";
          };

          nativeBuildInputs = [
            pkgs.python311Packages.setuptools
            pkgs.python311Packages.numpy
          ];

          meta = with pkgs.lib; {
            description = "A package to control Digilent Waveforms devices";
            homepage = "https://pypi.org/project/pydwf/";
            license = licenses.mit;
          };
        };

        pythonEnv = pkgs.python311.withPackages (
          ps: with ps; [
            mypy
            black
            isort
            numpy
            matplotlib
            pydwf
            pytest
          ]
        );
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            pythonEnv
            git
          ];

          shellHook = ''
            export PYTHONNOUSERSITE=1
            set +e
          '';
        };
      }
    );
}
