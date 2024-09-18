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
          ];

          propagatedBuildInputs = [
            pkgs.python311Packages.numpy
          ];

          meta = with pkgs.lib; {
            description = "A package to control Digilent Waveforms devices";
            homepage = "https://pypi.org/project/pydwf/";
            license = licenses.mit;
          };
        };

        flake518 = pkgs.python311Packages.buildPythonPackage {
          pname = "flake518";
          version = "1.6.0";
          pyproject = true;

          src = pkgs.fetchPypi {
            pname = "flake518";
            version = "1.6.0";
            sha256 = "e02efcacb9609e4250265600c7efd559576ae75c93b8898e019fec63128c90b5";
          };

          nativeBuildInputs = [
            pkgs.python311Packages.pdm-backend
          ];

          propagatedBuildInputs = [
            pkgs.python311Packages.flake8
          ];
        };

        pythonEnv = pkgs.python311.withPackages (
          ps: with ps; [
            mypy
            black
            isort
            numpy
            flake518
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
            set -e
            ./scripts/check.sh
            set +e
          '';
        };
      }
    );
}
