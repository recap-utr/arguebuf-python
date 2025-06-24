{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    flocken = {
      url = "github:mirkolenz/flocken/v2";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  nixConfig = {
    extra-substituters = [
      "https://nix-community.cachix.org"
      "https://recap.cachix.org"
      "https://pyproject-nix.cachix.org"
    ];
    extra-trusted-public-keys = [
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "recap.cachix.org-1:KElwRDtaJbbQxmmS2SyxWHqs9bdJbaZHzb2iINTfQws="
      "pyproject-nix.cachix.org-1:UNzugsOlQIu2iOz0VyZNBQm2JSrL/kwxeCcFGw+jMe0="
    ];
  };
  outputs =
    inputs@{
      self,
      flake-parts,
      nixpkgs,
      systems,
      flocken,
      uv2nix,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import systems;
      imports = [
        flake-parts.flakeModules.easyOverlay
        inputs.treefmt-nix.flakeModule
      ];
      perSystem =
        {
          pkgs,
          lib,
          system,
          config,
          ...
        }:
        let
          inherit
            (pkgs.callPackage ./default.nix {
              inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
              inherit (config.packages) link-arguebase;
            })
            pythonSet
            mkApplication
            ;
        in
        {
          _module.args.pkgs = import nixpkgs {
            inherit system;
            overlays = lib.singleton (
              final: prev: {
                uv = uv2nix.packages.${system}.uv-bin;
              }
            );
          };
          overlayAttrs = {
            inherit (config.packages) arguebuf arguebuf-wrapped;
          };
          checks = pythonSet.arguebuf.passthru.tests // {
            inherit (pythonSet.arguebuf.passthru) docs;
          };
          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              ruff-check.enable = true;
              ruff-format.enable = true;
              nixfmt.enable = true;
            };
          };
          packages = {
            default = config.packages.arguebuf-wrapped;
            arguebase = pkgs.fetchFromGitHub {
              owner = "recap-utr";
              repo = "arguebase-public";
              rev = "468f32818cebe90a837427f4e5f471463159b637";
              hash = "sha256-dF5vJBxVG4qJr+9ZJje27HXU1B+UmP9uzPh+ERUnRsg=";
            };
            link-arguebase = pkgs.writeShellScriptBin "link-arguebase" ''
              mkdir -p data
              ln -snf ${config.packages.arguebase} data/arguebase
            '';
            inherit (pythonSet.arguebuf.passthru) docs;
            arguebuf = mkApplication {
              venv = pythonSet.mkVirtualEnv "arguebuf-env" {
                arguebuf = [ "all" ];
              };
              package = pythonSet.arguebuf;
            };
            arguebuf-wrapped =
              pkgs.runCommand "arguebuf"
                {
                  nativeBuildInputs = with pkgs; [ makeWrapper ];
                }
                ''
                  mkdir -p $out/bin
                  makeWrapper ${lib.getExe config.packages.arguebuf} "$out/bin/arguebuf" \
                    --prefix PATH : ${
                      lib.makeBinPath [
                        pkgs.d2
                        pkgs.graphviz
                      ]
                    }
                '';
            docker = pkgs.dockerTools.streamLayeredImage {
              name = "arguebuf";
              tag = "latest";
              created = "now";
              config.Entrypoint = [ (lib.getExe config.packages.default) ];
            };
            release-env = pkgs.buildEnv {
              name = "release-env";
              paths = with pkgs; [
                uv
                python3
              ];
            };
          };
          legacyPackages.docker-manifest = flocken.legacyPackages.${system}.mkDockerManifest {
            github = {
              enable = true;
              token = "$GH_TOKEN";
            };
            version = builtins.getEnv "VERSION";
            imageStreams = with self.packages; [
              x86_64-linux.docker
              aarch64-linux.docker
            ];
          };
          devShells.default = pkgs.mkShell {
            packages = with pkgs; [
              uv
              config.treefmt.build.wrapper
              d2
              graphviz
            ];
            nativeBuildInputs = with pkgs; [ zlib ];
            LD_LIBRARY_PATH = lib.makeLibraryPath [
              pkgs.stdenv.cc.cc
              pkgs.zlib
            ];
            UV_PYTHON = lib.getExe pkgs.python3;
            shellHook = ''
              uv sync --all-extras --locked
              ${lib.getExe config.packages.link-arguebase}
            '';
          };
        };
    };
}
