{
  lib,
  stdenv,
  callPackage,
  fetchFromGitHub,
  python3,
  graphviz,
  d2,
  writeShellScriptBin,
  uv2nix,
  pyproject-nix,
  pyproject-build-systems,
}:
let
  pdocRepo = fetchFromGitHub {
    owner = "mitmproxy";
    repo = "pdoc";
    tag = "v16.0.0";
    hash = "sha256-9amp6CWYIcniVfdlmPKYuRFR7B5JJtuMlOoDxpfvvJA=";
  };
  arguebase = fetchFromGitHub {
    owner = "recap-utr";
    repo = "arguebase-public";
    rev = "468f32818cebe90a837427f4e5f471463159b637";
    hash = "sha256-dF5vJBxVG4qJr+9ZJje27HXU1B+UmP9uzPh+ERUnRsg=";
  };
  link-arguebase = writeShellScriptBin "link-arguebase" ''
    mkdir -p data
    ln -snf ${arguebase} data/arguebase
  '';
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
  pyprojectOverlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  # pygraphviz links against graphviz when built from source
  buildOverlay = final: prev: {
    pygraphviz = prev.pygraphviz.overrideAttrs (old: {
      nativeBuildInputs =
        (old.nativeBuildInputs or [ ]) ++ final.resolveBuildSystem { setuptools = [ ]; };
      buildInputs = (old.buildInputs or [ ]) ++ [ graphviz ];
    });
  };
  baseSet = callPackage pyproject-nix.build.packages {
    python = python3;
  };
  pythonSet = baseSet.overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.wheel
      pyprojectOverlay
      buildOverlay
    ]
  );
  package = pythonSet.arguebuf;
  inherit (callPackage pyproject-nix.build.util { }) mkApplication;
in
(mkApplication {
  inherit package;
  venv = pythonSet.mkVirtualEnv "arguebuf-env" workspace.deps.optionals;
}).overrideAttrs
  (old: {
    meta = old.meta // {
      mainProgram = "arguebuf";
      maintainers = with lib.maintainers; [ mirkolenz ];
      license = lib.licenses.mit;
      homepage = "https://github.com/recap-utr/arguebuf-python";
      description = "Create and analyze argument graphs and serialize them via Protobuf";
      platforms = with lib.platforms; darwin ++ linux;
    };

    passthru = lib.recursiveUpdate old.passthru {
      inherit arguebase link-arguebase;
      tests.pytest = stdenv.mkDerivation {
        name = "${old.name}-pytest";
        inherit (package) src;
        nativeBuildInputs = [
          (pythonSet.mkVirtualEnv "arguebuf-test-env" {
            arguebuf = [
              "cli"
              "test"
            ];
          })
          graphviz
          d2
        ];
        configurePhase = ''
          runHook preConfigure
          ${lib.getExe link-arguebase}
          runHook postConfigure
        '';
        buildPhase = ''
          runHook preBuild
          pytest --cov-report=html
          runHook postBuild
        '';
        installPhase = ''
          runHook preInstall
          mv htmlcov $out
          runHook postInstall
        '';
      };
      docs = stdenv.mkDerivation {
        name = "${old.name}-docs";
        inherit (package) src;
        nativeBuildInputs = [
          (pythonSet.mkVirtualEnv "arguebuf-docs-env" {
            arguebuf = [
              "cli"
              "docs"
            ];
          })
        ];
        dontConfigure = true;
        buildPhase = ''
          runHook preBuild

          typer arguebuf.cli.app utils docs --name arguebuf --output cli.md

          pdoc \
            -d google \
            -t ${pdocRepo}/examples/dark-mode \
            --math \
            -o "$out" \
            arguebuf.cli \
            arguebuf

          runHook postBuild
        '';
        installPhase = ''
          runHook preInstall
          cp -rf ./assets "$out/assets"
          runHook postInstall
        '';
      };
    };
  })
