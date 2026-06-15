from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from redaktsafe import __version__
from redaktsafe.artifacts import write_artifacts
from redaktsafe.contracts import PipelineConfig, schema_models
from redaktsafe.eval import run_eval
from redaktsafe.pipeline import run_packet_pipeline, strict_should_fail


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="redaktsafe")
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="Check local RedaktSafe runtime status.")
    doctor.set_defaults(handler=_doctor)

    schemas = subparsers.add_parser("schemas", help="Export JSON schemas.")
    schemas.add_argument("--out", required=True, type=Path)
    schemas.set_defaults(handler=_schemas)

    packet = subparsers.add_parser("packet", help="Create a trust packet from a local text file.")
    packet.add_argument("input", type=Path)
    packet.add_argument("--out", required=True, type=Path)
    packet.add_argument("--strict", action="store_true")
    packet.set_defaults(handler=_packet)

    text = subparsers.add_parser("text", help="Create a trust packet from command-line text.")
    text.add_argument("text")
    text.add_argument("--out", required=True, type=Path)
    text.add_argument("--strict", action="store_true")
    text.set_defaults(handler=_text)

    eval_parser = subparsers.add_parser("eval", help="Run synthetic evaluation fixtures.")
    eval_parser.add_argument("--fixtures", required=True, type=Path)
    eval_parser.add_argument("--out", required=True, type=Path)
    eval_parser.set_defaults(handler=_eval)

    serve_parser = subparsers.add_parser("serve", help="Run the local API and browser UI.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8765, type=int)
    serve_parser.set_defaults(handler=_serve)

    return parser


def _doctor(_args: argparse.Namespace) -> int:
    payload = {
        "status": "ok",
        "package": "redaktsafe",
        "version": __version__,
        "network_required": False,
        "credentials_required": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _schemas(args: argparse.Namespace) -> int:
    args.out.mkdir(parents=True, exist_ok=True)
    for name, model in schema_models().items():
        path = args.out / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(schema_models())} schemas to {args.out}")
    return 0


def _packet(args: argparse.Namespace) -> int:
    raw_text = args.input.read_text(encoding="utf-8")
    result = run_packet_pipeline(raw_text, PipelineConfig(), source_name=str(args.input))
    result = write_artifacts(result, args.out)
    print(json.dumps(_summary(result), indent=2, sort_keys=True))
    if args.strict and strict_should_fail(result.safe_packet.residual_risk.lane):
        return 3
    return 0


def _text(args: argparse.Namespace) -> int:
    result = run_packet_pipeline(args.text, PipelineConfig(), source_name="cli-text")
    result = write_artifacts(result, args.out)
    print(json.dumps(_summary(result), indent=2, sort_keys=True))
    if args.strict and strict_should_fail(result.safe_packet.residual_risk.lane):
        return 3
    return 0


def _eval(args: argparse.Namespace) -> int:
    results = run_eval(args.fixtures, args.out)
    print(json.dumps({key: results[key] for key in [
        "case_count",
        "recall",
        "precision",
        "false_positive_count",
        "unsafe_pass_count",
        "latency_ms_p50",
        "artifact_completeness_rate",
        "receipt_completeness_rate",
        "no_raw_input_violations",
    ]}, indent=2, sort_keys=True))
    return 1 if results["unsafe_pass_count"] else 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("redaktsafe.api.main:app", host=args.host, port=args.port, reload=False)
    return 0


def _summary(result) -> dict[str, object]:
    return {
        "risk_lane": result.safe_packet.residual_risk.lane.value,
        "artifact_count": len(result.validation_summary.required_artifacts),
        "counts_by_entity_type": result.receipt.counts_by_entity_type,
        "review_required": result.safe_packet.residual_risk.review_required,
        "receipt_id": result.receipt.receipt_id,
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
