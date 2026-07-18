import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Settings
from src.ingest.pipeline import ingest_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract, embed and index PDF content in Pinecone."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", type=Path, help="Path to one PDF file")
    source.add_argument("--dir", type=Path, help="Directory containing PDF files")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of PDFs when using --dir",
    )
    parser.add_argument(
        "--no-visuals",
        action="store_true",
        help="Skip image extraction and vision captioning",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["heading", "page", "fixed", "paragraph"],
        default=None,
        help="Chunk strategy override (default: RAG_CHUNK_STRATEGY / heading)",
    )
    return parser.parse_args()


def collect_pdfs(args: argparse.Namespace) -> list[Path]:
    if args.pdf:
        return [args.pdf]
    pdfs = sorted(args.dir.glob("*.pdf"))
    return pdfs[: args.limit] if args.limit else pdfs


def main() -> int:
    args = parse_args()
    pdfs = collect_pdfs(args)
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 1

    settings = Settings.from_env()
    if args.strategy:
        settings = Settings(**{**settings.__dict__, "chunk_strategy": args.strategy})
    succeeded = 0
    for index, pdf_path in enumerate(pdfs, 1):
        print(f"\n[{index}/{len(pdfs)}] Ingesting {pdf_path}")
        try:
            result = ingest_pdf(
                pdf_path,
                settings=settings,
                include_visuals=not args.no_visuals,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            succeeded += 1
        except Exception as error:
            print(f"Failed: {error}", file=sys.stderr)

    print(f"\nCompleted: {succeeded}/{len(pdfs)} PDFs")
    return 0 if succeeded == len(pdfs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
