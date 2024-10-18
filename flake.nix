{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    flocken = {
      url = "github:mirkolenz/flocken/v2";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs =
    inputs@{
      self,
      flake-parts,
      nixpkgs,
      systems,
      flocken,
      poetry2nix,
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
          python = pkgs.python312;
          poetry = pkgs.poetry;
          propagatedBuildInputs = with pkgs; [
            graphviz
            d2
          ];
        in
        {
          _module.args.pkgs = import nixpkgs {
            inherit system;
            overlays = [ poetry2nix.overlays.default ];
          };
          overlayAttrs = {
            inherit (config.packages) arguebuf;
          };
          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              ruff-check.enable = true;
              ruff-format.enable = true;
              nixfmt.enable = true;
            };
          };
          checks = {
            inherit (config.packages) arguebuf;
          };
          packages = {
            default = config.packages.arguebuf;
            arguebase = pkgs.fetchFromGitHub {
              owner = "recap-utr";
              repo = "arguebase-public";
              rev = "468f32818cebe90a837427f4e5f471463159b637";
              hash = "sha256-dF5vJBxVG4qJr+9ZJje27HXU1B+UmP9uzPh+ERUnRsg=";
            };
            link-arguebase = pkgs.writeShellScriptBin "link-arguebase" ''
              mkdir -p data
              rm -f data/arguebase
              ln -sf ${config.packages.arguebase} data/arguebase
            '';
            arguebuf = pkgs.poetry2nix.mkPoetryApplication {
              inherit python;
              projectDir = ./.;
              preferWheels = true;
              preCheck = ''
                ${lib.getExe config.packages.link-arguebase}
                PATH="${lib.makeBinPath propagatedBuildInputs}:$PATH"
              '';
              # postInstall = ''
              #   wrapProgram $out/bin/arguebuf \
              #     --prefix PATH : ${lib.makeBinPath propagatedBuildInputs}
              # '';
              nativeCheckInputs = with python.pkgs; [
                pytestCheckHook
                pytest-cov-stub
              ];
              meta = {
                description = "Create and analyze argument graphs and serialize them via Protobuf";
                license = lib.licenses.mit;
                maintainers = with lib.maintainers; [ mirkolenz ];
                platforms = with lib.platforms; darwin ++ linux;
                homepage = "https://github.com/recap-utr/arguebuf-python";
                mainProgram = "arguebuf";
              };
            };
            docker = pkgs.dockerTools.buildLayeredImage {
              name = "arguebuf";
              tag = "latest";
              created = "now";
              config = {
                entrypoint = [ (lib.getExe config.packages.default) ];
                cmd = [ ];
              };
            };
            release-env = pkgs.buildEnv {
              name = "release-env";
              paths = [ poetry ];
            };
          };
          apps.docker-manifest.program = flocken.legacyPackages.${system}.mkDockerManifest {
            github = {
              enable = true;
              token = "$GH_TOKEN";
            };
            version = builtins.getEnv "VERSION";
            images = with self.packages; [
              x86_64-linux.docker
              aarch64-linux.docker
            ];
          };
          devShells.default = pkgs.mkShell rec {
            inherit propagatedBuildInputs;
            buildInputs = with pkgs; [ stdenv.cc.cc ];
            packages = [
              poetry
              python
              config.treefmt.build.wrapper
            ];
            POETRY_VIRTUALENVS_IN_PROJECT = true;
            LD_LIBRARY_PATH = lib.makeLibraryPath buildInputs;
            shellHook = ''
              ${lib.getExe poetry} env use ${lib.getExe python}
              ${lib.getExe poetry} install --all-extras --no-root
              ${lib.getExe config.packages.link-arguebase}
            '';
          };
        };
    };
}
