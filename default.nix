{
  lib,
  stdenv,
  callPackage,
  fetchFromGitHub,
  uv2nix,
  pyproject-nix,
  pyproject-build-systems,
  python3,
  graphviz,
  d2,
  makeWrapper,
  cacert,
  link-arguebase,
}:
let
  pdocRepo = fetchFromGitHub {
    owner = "mitmproxy";
    repo = "pdoc";
    tag = "v15.0.1";
    hash = "sha256-HDrDGnK557EWbBQtsvDzTst3oV0NjLRm4ilXaxd6/j8=";
  };
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
  projectOverlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };
  buildSystemOverlay =
    final: prev:
    lib.mapAttrs
      (
        name: value:
        prev.${name}.overrideAttrs (old: {
          nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ (final.resolveBuildSystem value);
        })
      )
      {
        pygraphviz = {
          setuptools = [ ];
        };
      };
  packageOverlay =
    final: prev:
    lib.mapAttrs (name: value: prev.${name}.overrideAttrs value) {
      pygraphviz = old: {
        buildInputs = (old.buildInputs or [ ]) ++ [ graphviz ];
      };
      arguebuf = old: {
        meta = (old.meta or { }) // {
          mainProgram = "arguebuf";
          description = "Create and analyze argument graphs and serialize them via Protobuf";
          maintainers = with lib.maintainers; [ mirkolenz ];
          license = lib.licenses.mit;
          homepage = "https://github.com/recap-utr/arguebuf";
          platforms = with lib.platforms; darwin ++ linux;
        };
        passthru = lib.recursiveUpdate (old.passthru or { }) {
          tests.pytest = stdenv.mkDerivation {
            name = "${final.arguebuf.name}-pytest";
            inherit (final.arguebuf) src;
            nativeBuildInputs = [
              cacert
              (final.mkVirtualEnv "arguebuf-test-env" {
                arguebuf = [
                  "all"
                  "test"
                ];
              })
            ];
            buildInputs = [
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
            name = "${final.arguebuf.name}-docs";
            inherit (final.arguebuf) src;
            nativeBuildInputs = [
              cacert
              (final.mkVirtualEnv "arguebuf-docs-env" {
                arguebuf = [
                  "all"
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
      };
    };
  baseSet = callPackage pyproject-nix.build.packages {
    python = python3;
  };
in
{
  inherit workspace;
  inherit (callPackage pyproject-nix.build.util { }) mkApplication;
  pythonSet = baseSet.overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.default
      projectOverlay
      buildSystemOverlay
      packageOverlay
    ]
  );
}
