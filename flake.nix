{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };
  outputs = inputs @ {
    flake-parts,
    nixpkgs,
    systems,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import systems;
      perSystem = {
        pkgs,
        lib,
        system,
        self',
        ...
      }: let
        python = pkgs.python311;
        poetry = pkgs.poetry;
        propagatedBuildInputs = with pkgs; [graphviz d2];
      in {
        packages = {
          default = pkgs.poetry2nix.mkPoetryApplication {
            inherit python propagatedBuildInputs;
            projectDir = ./.;
            preferWheels = true;
          };
          arguebuf = self'.packages.default;
          releaseEnv = pkgs.buildEnv {
            name = "release-env";
            paths = [poetry];
          };
        };
        devShells.default = pkgs.mkShell {
          inherit propagatedBuildInputs;
          packages = [poetry python];
          POETRY_VIRTUALENVS_IN_PROJECT = true;
          LD_LIBRARY_PATH = lib.makeLibraryPath [pkgs.stdenv.cc.cc];
          shellHook = ''
            ${lib.getExe poetry} env use ${lib.getExe python}
            ${lib.getExe poetry} install --all-extras --no-root
          '';
        };
      };
    };
}
