from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Annotated, override

import grpc
import typer
from arg_services.cbr.v1beta import casebase_pb2, casebase_pb2_grpc
from arg_services.cbr.v1beta.model_pb2 import AnnotatedGraph
from arg_services.grpcio import ValidationInterceptor, serve
from arg_services.validation import require_all

import arguebuf

cli = typer.Typer()


@dataclass(slots=True, frozen=True)
class CasebaseService(casebase_pb2_grpc.CasebaseServiceServicer):
    basepath: Path
    glob: str

    @override
    def Casebase(
        self, request: casebase_pb2.CasebaseRequest, context: grpc.ServicerContext
    ) -> casebase_pb2.CasebaseResponse:
        require_all(["include"], request)
        cases = arguebuf.load.casebase(
            request.include,
            request.exclude if request.HasField("exclude") else None,
            self.basepath,
            self.glob,
        )

        return casebase_pb2.CasebaseResponse(
            cases={
                str(path.relative_to(self.basepath)): AnnotatedGraph(
                    graph=arguebuf.dump.protobuf(case), text="TODO"
                )
                for path, case in cases.items()
            }
        )


@cli.command()
def start(
    address: Annotated[str, typer.Argument()] = "127.0.0.1:50051",
    basepath: Path = Path("."),
    glob: str = "*/*",
) -> None:
    serve(
        address,
        partial(
            casebase_pb2_grpc.add_CasebaseServiceServicer_to_server,
            CasebaseService(basepath, glob),
        ),
        reflection=[casebase_pb2.DESCRIPTOR],
        # turns validation errors into INVALID_ARGUMENT responses
        interceptors=[ValidationInterceptor()],
    )


if __name__ == "__main__":
    cli()
