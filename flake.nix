{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    flocken = {
      url = "github:mirkolenz/flocken/v2";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = inputs @ {
    self,
    flake-parts,
    nixpkgs,
    systems,
    flocken,
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
        apps.dockerManifest = {
          type = "app";
          program = lib.getExe (flocken.legacyPackages.${system}.mkDockerManifest {
            github = {
              enable = true;
              token = builtins.getEnv "GH_TOKEN";
            };
            version = builtins.getEnv "VERSION";
            images = with self.packages; [x86_64-linux.docker aarch64-linux.docker];
          });
        };
        packages = {
          default = pkgs.poetry2nix.mkPoetryApplication {
            inherit python propagatedBuildInputs;
            projectDir = ./.;
            preferWheels = true;
          };
          arguebuf = self'.packages.default;
          docker = pkgs.dockerTools.buildLayeredImage {
            name = "arguebuf";
            tag = "latest";
            created = "now";
            config = {
              entrypoint = [(lib.getExe self'.packages.default)];
              cmd = [];
            };
          };
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
