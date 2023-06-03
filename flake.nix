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
        devShells.default = pkgs.mkShell {
          packages = [poetry python];
          propagatedBuildInputs = with pkgs; [graphviz d2];
          POETRY_VIRTUALENVS_IN_PROJECT = true;
          shellHook = ''
            export LD_LIBRARY_PATH=${lib.makeLibraryPath [pkgs.stdenv.cc.cc]};
            ${lib.getExe poetry} env use ${lib.getExe python}
            ${lib.getExe poetry} install --all-extras --no-root
          '';
          postShellHook = ''
            unset LD_LIBRARY_PATH;
          '';
        };
      };
    };
}
