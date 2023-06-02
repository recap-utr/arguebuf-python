{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    devenv = {
      url = "github:cachix/devenv";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = inputs @ {
    flake-parts,
    nixpkgs,
    poetry2nix,
    devenv,
    systems,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import systems;
      imports = [devenv.flakeModule];
      perSystem = {
        pkgs,
        lib,
        system,
        ...
      }: let
        python = pkgs.python311;
        poetry = pkgs.poetry;
      in {
        packages = let
          inherit (poetry2nix.legacyPackages.${system}) mkPoetryApplication;
          app = mkPoetryApplication {
            inherit python;
            projectDir = ./.;
            preferWheels = true;
            # overrides = overrides.withDefaults (self: super: {
            #   protobuf = super.protobuf.override {
            #     preferWheel = false;
            #   };
            #   arg-services = (super.arg-services.override {
            #     preferWheel = true;
            #   }) // (super.arg-services.overridePythonAttrs (old: {
            #     propagatedBuildInputs = (old.propagatedBuildInputs or [ ]) ++ [ super.poetry ];
            #   }));
            # });
          };
        in {
          arguebuf = app;
          default = app;
        };
        devenv.shells.default = {
          packages = with pkgs; [graphviz d2 stdenv.cc.cc];
          languages.python = {
            enable = true;
            package = python;
            poetry = {
              enable = true;
              install = {
                enable = true;
                allExtras = true;
              };
            };
          };
        };
        # devShells.default = pkgs.mkShell {
        #   packages = [poetry python];
        #   propagatedBuildInputs = with pkgs; [graphviz d2];
        #   POETRY_VIRTUALENVS_IN_PROJECT = true;
        #   LD_LIBRARY_PATH = lib.makeLibraryPath [pkgs.stdenv.cc.cc];
        #   shellHook = ''
        #     ${lib.getExe poetry} env use ${lib.getExe python}
        #     ${lib.getExe poetry} install --all-extras --no-root
        #   '';
        # };
      };
    };
}
