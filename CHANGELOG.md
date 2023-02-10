# Changelog

## [2.0.0-beta.22](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.21...v2.0.0-beta.22) (2023-02-10)


### Bug Fixes

* allow comparing nodes/edges to None ([821d574](https://github.com/recap-utr/arguebuf-python/commit/821d574b1700f4c9489cdc015ac6dccfa777d08c))
* **microtexts:** properly parse scheme edges ([122ca44](https://github.com/recap-utr/arguebuf-python/commit/122ca44250e33ed175faacf824208db7fd8028b3))

## [2.0.0-beta.21](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.20...v2.0.0-beta.21) (2023-02-08)


### Features

* make nodes and edges hashable ([bc33e86](https://github.com/recap-utr/arguebuf-python/commit/bc33e8685998c5dee73c58d95ffe678027916ac2))

## [2.0.0-beta.20](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.19...v2.0.0-beta.20) (2023-02-08)


### Bug Fixes

* imported texts were missing the first line ([f95551e](https://github.com/recap-utr/arguebuf-python/commit/f95551e1e7e94fe00eee53f44ff866dead22a0b5))
* only add resource if text is a different file ([4c9d558](https://github.com/recap-utr/arguebuf-python/commit/4c9d55859d3b6b04bf15fa512fd40c1d3ce41827))

## [2.0.0-beta.19](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.18...v2.0.0-beta.19) (2023-02-08)


### Bug Fixes

* improve saving to file ([15bdc59](https://github.com/recap-utr/arguebuf-python/commit/15bdc591eb249c5ba85f84ba17553a09d70ac129))

## [2.0.0-beta.18](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.17...v2.0.0-beta.18) (2023-02-07)


### Features

* allow creating graphs from plain texts ([309e959](https://github.com/recap-utr/arguebuf-python/commit/309e959fa2d934faef198183f0aff18a1eee80b2))

## [2.0.0-beta.17](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.16...v2.0.0-beta.17) (2023-02-07)


### Bug Fixes

* all enums now inherit from str ([846af05](https://github.com/recap-utr/arguebuf-python/commit/846af0586a415d1039d03ab95923a9423c248cfb))

## [2.0.0-beta.16](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.15...v2.0.0-beta.16) (2023-02-07)


### Bug Fixes

* **cli:** convert enum members to strings ([7a21b87](https://github.com/recap-utr/arguebuf-python/commit/7a21b87926269bd57b96b15b559d3d477b7d3795))

## [2.0.0-beta.15](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.14...v2.0.0-beta.15) (2023-02-06)


### Features

* add grpc server for casebase loader ([7bf5c08](https://github.com/recap-utr/arguebuf-python/commit/7bf5c085f4ff2d22f6fe856e3f5a6b9e2639ec1b))
* allow specification of graphviz dpi ([0da5a47](https://github.com/recap-utr/arguebuf-python/commit/0da5a474bc82361f9657cf6598d36f9923282f5d))


### Bug Fixes

* make casebase loader more reobust ([174b937](https://github.com/recap-utr/arguebuf-python/commit/174b937c783235664d724a53da193082ec1c9256))
* **test:** wrong usage of casebase loader ([6b4dc9d](https://github.com/recap-utr/arguebuf-python/commit/6b4dc9dbee94aa5a09cbdd58915cbf162809b961))

## [2.0.0-beta.14](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.13...v2.0.0-beta.14) (2023-02-06)


### ⚠ BREAKING CHANGES

* restructure package

### Features

* restructure package ([77facb1](https://github.com/recap-utr/arguebuf-python/commit/77facb129fc215ea3f6682a9df91167e5b3e81c8))

## [2.0.0-beta.13](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.12...v2.0.0-beta.13) (2023-02-01)


### Bug Fixes

* update deps ([de8b36d](https://github.com/recap-utr/arguebuf-python/commit/de8b36d67a44d4857055b53a83ff5ae3e5a3770b))

## [2.0.0-beta.12](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.11...v2.0.0-beta.12) (2023-01-30)


### Features

* allow custom folder glob for casebase import ([08f07fe](https://github.com/recap-utr/arguebuf-python/commit/08f07feb33559b9468df1286c822fcd89c640395))
* allow specifying globs in casebase loader ([220fe3a](https://github.com/recap-utr/arguebuf-python/commit/220fe3a3906203c4473ebd2298cd51329ae35152))


### Bug Fixes

* **graphviz:** check format and engine ([29c0a48](https://github.com/recap-utr/arguebuf-python/commit/29c0a4858315479abbb3f34083e9397d6885b0b4))
* **graphviz:** switch engines and renderers ([98396c8](https://github.com/recap-utr/arguebuf-python/commit/98396c876f707fdf1b2ffd00faf8f90ee2d8bafa))
* **ova:** correctly check for body ([e18396e](https://github.com/recap-utr/arguebuf-python/commit/e18396e647636741ccb1c86cb9117a1917bdf508))
* overhaul casebase import to make it robust ([5c07339](https://github.com/recap-utr/arguebuf-python/commit/5c073396dbaf6a57538d166b09af5227b6caaf25))
* properly init graphviz graphs ([514dea3](https://github.com/recap-utr/arguebuf-python/commit/514dea36768a7de4678e08803531e7eca7eb5d8f))

## [2.0.0-beta.11](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.10...v2.0.0-beta.11) (2023-01-24)


### ⚠ BREAKING CHANGES

* completely restructure the package

### Features

* add initial support for loading case bases ([b59ce73](https://github.com/recap-utr/arguebuf-python/commit/b59ce73417535c8e13b3cf3e0fc6f826fa7be002))
* completely restructure the package ([b2d3262](https://github.com/recap-utr/arguebuf-python/commit/b2d32621c5485d8ed6cb556bb12897d8a0d8ba92))

## [2.0.0-beta.10](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.9...v2.0.0-beta.10) (2023-01-19)


### Bug Fixes

* **cli:** wrong import ([d94f62a](https://github.com/recap-utr/arguebuf-python/commit/d94f62abc6e46f2556a4cc886cc77be276c42633))

## [2.0.0-beta.9](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.8...v2.0.0-beta.9) (2023-01-19)


### Features

* add microtexts parser ([99252a5](https://github.com/recap-utr/arguebuf-python/commit/99252a5be4718aec05b318a84210d41ad1313d14))

## [2.0.0-beta.8](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.7...v2.0.0-beta.8) (2023-01-11)


### Features

* drop support for Python 3.8 ([9e423c6](https://github.com/recap-utr/arguebuf-python/commit/9e423c657175aef810037a06db3ee3883eb125b2))
* use collections.abc instead of typing ([c0ced56](https://github.com/recap-utr/arguebuf-python/commit/c0ced565600b3adc613f52b98b1d38f19d22944d))

## [2.0.0-beta.7](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.6...v2.0.0-beta.7) (2023-01-11)


### Bug Fixes

* remove unused pygraphviz import ([a0e6726](https://github.com/recap-utr/arguebuf-python/commit/a0e67267f2014ca5b865ddcc3af67bd9f6787255))

## [2.0.0-beta.6](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.5...v2.0.0-beta.6) (2023-01-09)


### Features

* **traversal:** add option to remove start node ([2cdb412](https://github.com/recap-utr/arguebuf-python/commit/2cdb412886be253593a6ad5e13fdd0e294f04a55))

## [2.0.0-beta.5](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.4...v2.0.0-beta.5) (2023-01-06)


### Features

* add dfs/bfs traversal methods ([03ea313](https://github.com/recap-utr/arguebuf-python/commit/03ea3132f3f3f1db8fd40596cf0da3642bcbcf73))
* add root_nodes function ([e75ef75](https://github.com/recap-utr/arguebuf-python/commit/e75ef756e9c4c195323e21508e4858560ac740a8))


### Bug Fixes

* aml node import typing ([c13fb88](https://github.com/recap-utr/arguebuf-python/commit/c13fb88c8ab93e9d99537781c0f02e7116c690bf))
* export Scheme from init ([3c036ca](https://github.com/recap-utr/arguebuf-python/commit/3c036ca7de2c8f165d3b096a1a582145a558b1f1))

## [2.0.0-beta.4](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.3...v2.0.0-beta.4) (2023-01-04)


### Bug Fixes

* use __all__ to define the arguebuf interface ([a3d434e](https://github.com/recap-utr/arguebuf-python/commit/a3d434e58e7d8ad65bf7a5876aa6badfd597df99))

## [2.0.0-beta.3](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.2...v2.0.0-beta.3) (2022-12-22)


### Bug Fixes

* handling missing edge source/target at import ([899a34f](https://github.com/recap-utr/arguebuf-python/commit/899a34f866c41527d8aeb3827b072426b5f1fcc2))

## [1.2.4](https://github.com/recap-utr/arguebuf-python/compare/v1.2.3...v1.2.4) (2022-12-22)


### Bug Fixes

* handling missing edge source/target at import ([899a34f](https://github.com/recap-utr/arguebuf-python/commit/899a34f866c41527d8aeb3827b072426b5f1fcc2))

## [2.0.0-beta.2](https://github.com/recap-utr/arguebuf-python/compare/v2.0.0-beta.1...v2.0.0-beta.2) (2022-12-21)


### Bug Fixes

* add to_gv to init ([dab7859](https://github.com/recap-utr/arguebuf-python/commit/dab78590615d3ccb241b758d7cf7da7e78a5585a))

## [2.0.0-beta.1](https://github.com/recap-utr/arguebuf-python/compare/v1.2.2...v2.0.0-beta.1) (2022-12-21)


### ⚠ BREAKING CHANGES

* improve graphviz interface

### Features

* improve graphviz interface ([6e594da](https://github.com/recap-utr/arguebuf-python/commit/6e594da5b52dc6cdfb781a4f4d504ce7c179eff5))

## [1.2.3](https://github.com/recap-utr/arguebuf-python/compare/v1.2.2...v1.2.3) (2022-12-20)


### Bug Fixes

* solve cli translator issue ([6c7b1ab](https://github.com/recap-utr/arguebuf-python/commit/6c7b1ab63cc9ee2c2e667670c10a189c96d801e1))

## [1.2.2](https://github.com/recap-utr/arguebuf-python/compare/v1.2.1...v1.2.2) (2022-12-19)


### Bug Fixes

* bump version ([9dc224c](https://github.com/recap-utr/arguebuf-python/commit/9dc224c81d8ebee477da7628712b4a0e3b5bd832))

## [1.2.1](https://github.com/recap-utr/arguebuf-python/compare/v1.2.0...v1.2.1) (2022-12-13)


### Bug Fixes

* **deps:** update dependency sphinx to v5 ([#18](https://github.com/recap-utr/arguebuf-python/issues/18)) ([fa466f1](https://github.com/recap-utr/arguebuf-python/commit/fa466f11cd6c90893f103fa0e4aa4ab6ebc80822))
* **deps:** update dependency sphinx-autoapi to v2 ([#19](https://github.com/recap-utr/arguebuf-python/issues/19)) ([a2af9c6](https://github.com/recap-utr/arguebuf-python/commit/a2af9c68f4988143ccbf478f8e92f4d3c8b35292))
* **deps:** update dependency typer to ^0.7.0 ([#13](https://github.com/recap-utr/arguebuf-python/issues/13)) ([7817b16](https://github.com/recap-utr/arguebuf-python/commit/7817b16d72ecc70a868674f411f3c6a4801ef7eb))
* update deps ([981c5f5](https://github.com/recap-utr/arguebuf-python/commit/981c5f500cbdd0333a1db23d7f5a59ead1df87a4))
