{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";
    flake-parts.url = "github:hercules-ci/flake-parts";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = inputs@{ flake-parts, nixpkgs, poetry2nix, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = nixpkgs.lib.systems.flakeExposed;
      perSystem = { pkgs, lib, system, ... }:
        let
          python = pkgs.python311;
          poetry = pkgs.poetry;
        in
        {
          packages =
            let
              inherit (poetry2nix.legacyPackages.${system}) mkPoetryApplication;
              app = mkPoetryApplication {
                inherit python;
                projectDir = ./.;
                preferWheels = true;
              };
            in
            {
              arguebuf = app;
              default = app;
            };
          devShells.default =
            pkgs.mkShell {
              packages = [ pkgs.graphviz poetry python ];
              shellHook = ''
                ${lib.getExe poetry} env use ${lib.getExe python}
                ${lib.getExe poetry} install --all-extras --no-root
              '';
            };
        };
    };
}
