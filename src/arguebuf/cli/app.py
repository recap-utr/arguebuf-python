from typer import Typer

from . import graph, server, text

cli = Typer()
cli.add_typer(
    graph.cli, name="graph", help="Commands for dealing with argument graphs."
)
cli.add_typer(text.cli, name="text", help="Commands for dealing with plain texts.")
cli.add_typer(
    server.cli, name="server", help="Start a gRPC server for loading argument graphs."
)

if __name__ == "__main__":
    cli()
