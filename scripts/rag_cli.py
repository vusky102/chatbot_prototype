import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.rag import RAGService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query the Pinecone RAG backend.")
    parser.add_argument(
        "--search",
        type=str,
        help="Retrieve matching chunks without generating an answer",
    )
    parser.add_argument(
        "--ask",
        type=str,
        help="Retrieve context and generate a grounded answer",
    )
    parser.add_argument(
        "--image-search",
        type=str,
        help="Find indexed visuals by image path or hex aHash",
    )
    parser.add_argument(
        "--max-distance",
        type=int,
        default=5,
        help="Max Hamming distance for --image-search (default: 5)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print Pinecone namespace stats and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service = RAGService()

    if args.stats:
        print(json.dumps(service.stats(), ensure_ascii=False, indent=2))
        return 0

    if args.search:
        results = [
            {
                "citation": result.citation,
                "score": result.score,
                "content_type": result.content_type,
                "text": result.text,
            }
            for result in service.retrieve(args.search)
        ]
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    if args.image_search:
        results = [
            {
                "citation": result.citation,
                "score": result.score,
                "content_type": result.content_type,
                "image_path": result.image_path,
                "ahash": result.ahash,
                "hamming_distance": result.raw_metadata.get("hamming_distance"),
                "text": result.text,
            }
            for result in service.retrieve_image_by_hash(
                args.image_search,
                max_distance=args.max_distance,
            )
        ]
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    if args.ask:
        print(json.dumps(service.answer(args.ask), ensure_ascii=False, indent=2))
        return 0

    print("RAG CLI started. Type 'exit' or 'quit' to stop.")
    history = []
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        response = service.answer(question, history=history)
        answer = str(response["answer"])
        print(f"Assistant: {answer}")
        if response["sources"]:
            print("Sources:")
            for source in response["sources"]:
                print(
                    f"- {source['source_file']}, page {source['page']} "
                    f"(score={source['score']:.3f}, type={source['content_type']})"
                )
        history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
