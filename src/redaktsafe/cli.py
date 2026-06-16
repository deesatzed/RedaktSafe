from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from redaktsafe import __version__
from redaktsafe.artifacts import write_artifacts
from redaktsafe.benchmarks import compare_benchmark_backends, list_benchmarks, run_benchmark
from redaktsafe.contracts import LearningContextCategory, LearningErrorType, PipelineConfig, schema_models
from redaktsafe.eval import run_eval
from redaktsafe.learning import LearningLedger, export_finetuning_dataset, run_context_canary_eval, run_learning_audit
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
    packet.add_argument("--hf-model-id")
    packet.add_argument("--hf-min-score", type=float, default=0.30)
    packet.set_defaults(handler=_packet)

    text = subparsers.add_parser("text", help="Create a trust packet from command-line text.")
    text.add_argument("text")
    text.add_argument("--out", required=True, type=Path)
    text.add_argument("--strict", action="store_true")
    text.add_argument("--hf-model-id")
    text.add_argument("--hf-min-score", type=float, default=0.30)
    text.set_defaults(handler=_text)

    eval_parser = subparsers.add_parser("eval", help="Run synthetic evaluation fixtures.")
    eval_parser.add_argument("--fixtures", required=True, type=Path)
    eval_parser.add_argument("--out", required=True, type=Path)
    eval_parser.set_defaults(handler=_eval)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run optional external PII benchmark datasets.")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command")
    benchmark_list = benchmark_subparsers.add_parser("list", help="List supported benchmark adapters.")
    benchmark_list.set_defaults(handler=_benchmark_list)
    benchmark_run = benchmark_subparsers.add_parser("run", help="Run a local benchmark export through RedaktSafe.")
    benchmark_run.add_argument("--source", required=True)
    benchmark_run.add_argument("--input", required=True, type=Path)
    benchmark_run.add_argument("--out", required=True, type=Path)
    benchmark_run.add_argument("--limit", type=int)
    benchmark_run.add_argument("--hf-model-id")
    benchmark_run.add_argument("--hf-min-score", type=float, default=0.30)
    benchmark_run.set_defaults(handler=_benchmark_run)
    benchmark_compare = benchmark_subparsers.add_parser("compare", help="Compare deterministic and optional model benchmark backends.")
    benchmark_compare.add_argument("--source", required=True)
    benchmark_compare.add_argument("--input", required=True, type=Path)
    benchmark_compare.add_argument("--out", required=True, type=Path)
    benchmark_compare.add_argument("--limit", type=int)
    benchmark_compare.add_argument("--hf-model-id")
    benchmark_compare.add_argument("--hf-min-score", type=float, default=0.30)
    benchmark_compare.set_defaults(handler=_benchmark_compare)

    learning_parser = subparsers.add_parser("learning", help="Manage local opt-in learning corrections.")
    learning_subparsers = learning_parser.add_subparsers(dest="learning_command")
    add_correction = learning_subparsers.add_parser("add-correction", help="Append an encrypted local learning correction.")
    add_correction.add_argument("--store", required=True, type=Path)
    add_correction.add_argument("--passphrase", required=True)
    add_correction.add_argument("--text", required=True)
    add_correction.add_argument("--span-text", required=True)
    add_correction.add_argument("--entity-type", required=True)
    add_correction.add_argument("--error-type", required=True, choices=[item.value for item in LearningErrorType])
    add_correction.add_argument("--context-category", required=True, choices=[item.value for item in LearningContextCategory])
    add_correction.add_argument("--downstream-exposure", default="local")
    add_correction.add_argument("--detector-disagreement", action="store_true")
    add_correction.add_argument("--reviewer-id")
    add_correction.add_argument("--note")
    add_correction.set_defaults(handler=_learning_add_correction)
    learning_queue = learning_subparsers.add_parser("queue", help="List learning corrections ordered by review priority.")
    learning_queue.add_argument("--store", required=True, type=Path)
    learning_queue.set_defaults(handler=_learning_queue)
    learning_corpus = learning_subparsers.add_parser("corpus", help="Summarize reviewed learning correction corpus coverage.")
    learning_corpus.add_argument("--store", required=True, type=Path)
    learning_corpus.set_defaults(handler=_learning_corpus)
    learning_audit = learning_subparsers.add_parser("audit", help="Run local learning audit when activity exists.")
    learning_audit.add_argument("--store", required=True, type=Path)
    learning_audit.add_argument("--out", required=True, type=Path)
    learning_audit.add_argument("--if-due", action="store_true")
    learning_audit.add_argument("--interval-hours", type=int, default=24)
    learning_audit.add_argument("--teacher-model-id")
    learning_audit.set_defaults(handler=_learning_audit)
    learning_export = learning_subparsers.add_parser("export-finetune", help="Export reviewed corrections for fine-tuning or dry-run readiness.")
    learning_export.add_argument("--store", required=True, type=Path)
    learning_export.add_argument("--out", required=True, type=Path)
    learning_export.add_argument("--passphrase", required=True)
    learning_export.add_argument("--min-examples", type=int, default=100)
    learning_export.add_argument("--dry-run", action="store_true")
    learning_export.set_defaults(handler=_learning_export_finetune)
    learning_canaries = learning_subparsers.add_parser("canaries", help="Run context ambiguity learning canaries.")
    learning_canaries.add_argument("--out", required=True, type=Path)
    learning_canaries.set_defaults(handler=_learning_canaries)

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
    result = run_packet_pipeline(raw_text, _config_from_args(args), source_name=str(args.input))
    result = write_artifacts(result, args.out)
    print(json.dumps(_summary(result), indent=2, sort_keys=True))
    if args.strict and strict_should_fail(result.safe_packet.residual_risk.lane):
        return 3
    return 0


def _text(args: argparse.Namespace) -> int:
    result = run_packet_pipeline(args.text, _config_from_args(args), source_name="cli-text")
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


def _benchmark_list(_args: argparse.Namespace) -> int:
    print(json.dumps(list_benchmarks(), indent=2, sort_keys=True))
    return 0


def _benchmark_run(args: argparse.Namespace) -> int:
    results = run_benchmark(args.source, args.input, args.out, limit=args.limit, config=_config_from_args(args))
    summary_keys = [
        "benchmark_id",
        "case_count",
        "recall",
        "precision",
        "false_positive_count",
        "unsafe_pass_count",
        "latency_ms_p50",
        "artifact_completeness_rate",
        "receipt_completeness_rate",
        "no_raw_input_violations",
    ]
    print(json.dumps({key: results[key] for key in summary_keys}, indent=2, sort_keys=True))
    return 1 if results["unsafe_pass_count"] else 0


def _benchmark_compare(args: argparse.Namespace) -> int:
    config = _config_from_args(args) if args.hf_model_id else None
    result = compare_benchmark_backends(args.source, args.input, args.out, limit=args.limit, model_config=config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _learning_add_correction(args: argparse.Namespace) -> int:
    ledger = LearningLedger(args.store, passphrase=args.passphrase)
    correction = ledger.append_correction(
        text=args.text,
        span_text=args.span_text,
        entity_type=args.entity_type,
        error_type=args.error_type,
        context_category=args.context_category,
        downstream_exposure=args.downstream_exposure,
        detector_disagreement=args.detector_disagreement,
        reviewer_id=args.reviewer_id,
        note=args.note,
    )
    print(json.dumps(correction.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


def _learning_queue(args: argparse.Namespace) -> int:
    ledger = LearningLedger(args.store)
    print(json.dumps([item.model_dump(mode="json") for item in ledger.review_queue()], indent=2, sort_keys=True))
    return 0


def _learning_corpus(args: argparse.Namespace) -> int:
    ledger = LearningLedger(args.store)
    print(json.dumps(ledger.corpus_summary(), indent=2, sort_keys=True))
    return 0


def _learning_audit(args: argparse.Namespace) -> int:
    from redaktsafe.learning import UnavailableTeacherAuditAdapter

    teacher_adapter = UnavailableTeacherAuditAdapter(args.teacher_model_id) if getattr(args, "teacher_model_id", None) else None
    report = run_learning_audit(
        store=args.store,
        out_dir=args.out,
        if_due=args.if_due,
        interval_hours=args.interval_hours,
        teacher_adapter=teacher_adapter,
    )
    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


def _learning_export_finetune(args: argparse.Namespace) -> int:
    result = export_finetuning_dataset(
        store=args.store,
        out_dir=args.out,
        passphrase=args.passphrase,
        min_examples=args.min_examples,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _learning_canaries(args: argparse.Namespace) -> int:
    result = run_context_canary_eval(args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


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


def _config_from_args(args: argparse.Namespace) -> PipelineConfig:
    if getattr(args, "hf_model_id", None):
        return PipelineConfig(
            adapters_enabled=["hf_token_classifier"],
            model_adapters={
                "hf_token_classifier": {
                    "model_id": args.hf_model_id,
                    "min_score": args.hf_min_score,
                }
            },
        )
    return PipelineConfig()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
