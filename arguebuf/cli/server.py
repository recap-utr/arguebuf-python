from pathlib import Path

import arg_services
import grpc
import typer
from arg_services.cbr.v1beta import casebase_pb2, casebase_pb2_grpc
from arg_services.cbr.v1beta.model_pb2 import AnnotatedGraph

import arguebuf

cli = typer.Typer()


class CasebaseService(casebase_pb2_grpc.CasebaseServiceServicer):
    def __init__(self, basepath: Path, glob: str):
        self.basepath = basepath
        self.glob = glob

    def Casebase(
        self, req: casebase_pb2.CasebaseRequest, context: grpc.ServicerContext
    ) -> casebase_pb2.CasebaseResponse:
        cases = arguebuf.load.casebase(
            req.include, req.exclude, self.basepath, self.glob
        )

        return casebase_pb2.CasebaseResponse(
            cases={
                str(path.relative_to(self.basepath)): AnnotatedGraph(
                    graph=arguebuf.dump.protobuf(case), text="TODO"
                )
                for path, case in cases.items()
            }
        )


def add_services(casebase_service: CasebaseService):
    def callback(server: grpc.Server):
        casebase_pb2_grpc.add_CasebaseServiceServicer_to_server(
            casebase_service, server
        )

    return callback


@cli.command()
def start(
    address: str = typer.Argument("127.0.0.1:50051"),
    basepath: Path = typer.Option(Path(".")),
    glob: str = typer.Option("*/*"),
):
    arg_services.serve(
        address,
        add_services(CasebaseService(basepath, glob)),
        [arg_services.full_service_name(casebase_pb2, "CasebaseService")],
    )


if __name__ == "__main__":
    cli()
