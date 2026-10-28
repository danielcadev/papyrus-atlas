"""Command-line interface for bounded standalone surface recovery."""
import argparse
import json
from pathlib import Path
from .graft import boundary_graft
from .mesh import Mesh
from .recovery import recover_cycle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    graft = commands.add_parser("graft", help="Recover source owners from complete graph evidence")
    graft.add_argument("input", type=Path)
    graft.add_argument("output", type=Path)
    recover = commands.add_parser("recover", help="Fill an isolated source boundary cycle")
    recover.add_argument("source", type=Path)
    recover.add_argument("cycle", type=Path)
    recover.add_argument("output", type=Path)
    recover.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or (args.command == "recover" and args.report.exists()):
        parser.error("Output already exists; preserve earlier results")
    if args.command == "graft":
        data = json.loads(args.input.read_text())
        result = boundary_graft(data["labels"], data["adjacency"], data["conflicts"], complete=data["complete"])
        with args.output.open("x") as stream:
            json.dump(result, stream, indent=2)
    else:
        mesh = Mesh.read(args.source)
        cycle = json.loads(args.cycle.read_text())
        candidate, result = recover_cycle(mesh, cycle)
        # Refused proposals produce a report only, never an apparent mesh fill.
        if result["accepted"]:
            candidate.write(args.output)
        with args.report.open("x") as stream:
            json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ("labels", "witnesses", "added_indices")}))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
