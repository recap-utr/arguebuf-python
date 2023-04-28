{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/release-22.11";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };
  outputs = inputs@{ flake-parts, nixpkgs, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = nixpkgs.lib.systems.flakeExposed;
      perSystem = { pkgs, ... }: {
        devShells.default =
          pkgs.mkShell {
            # TODO: add dvc once no longer broken
            packages = with pkgs; [ graphviz poetry python311 ];
            shellHook = with pkgs; ''
              ${poetry}/bin/poetry env use ${python311}/bin/python
              ${poetry}/bin/poetry install --all-extras
            '';
          };
      };
    };
}
