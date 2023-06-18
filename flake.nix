{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = inputs @ {
    flake-parts,
    nixpkgs,
    poetry2nix,
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
      in {
        packages = {
          default = poetry2nix.legacyPackages.${system}.mkPoetryApplication {
            inherit python;
            projectDir = ./.;
            preferWheels = true;
          };
          arguebuf = self'.packages.default;
          releaseEnv = pkgs.buildEnv {
            name = "release-env";
            paths = [poetry python];
          };
        };
        devShells.default = pkgs.mkShell {
          packages = [poetry python];
          propagatedBuildInputs = with pkgs; [graphviz d2];
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
