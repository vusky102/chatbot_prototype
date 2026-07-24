"""CLI script for running Q&A evaluation."""

import argparse
import sys

from src.config import Settings
from src.eval.eval_runner import EvalRunner
from src.rag.service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG accuracy on question.csv")
    parser.add_argument("--batch-size", type=int, default=1, help="Number of questions per LLM call")
    parser.add_argument("--start", type=int, default=1, help="Start at question number N")
    parser.add_argument("--limit", type=int, default=None, help="Process only N questions")
    args = parser.parse_args()

    settings = Settings.from_env()
    service = RAGService(settings)
    runner = EvalRunner(service, settings)

    question_csv = "docs/Training_data_GD4/input/question.csv"
    ground_truth_md = "docs/Training_data_GD4/real_answer.md"
    output_csv = "docs/Training_data_GD4/evaluation_results.csv"

    print("Loading data...")
    ground_truth = runner.load_ground_truth(ground_truth_md)
    questions = runner.load_questions(question_csv)

    print(f"Found {len(questions)} questions. Ground truth available for {len(ground_truth)}.")

    def progress_callback(done: int, total: int, msg: str) -> None:
        sys.stdout.write(f"\rProgress: {done}/{total} - {msg: <40}")
        sys.stdout.flush()

    print(f"\nStarting evaluation (batch_size={args.batch_size})...")
    results = runner.run(
        questions=questions,
        batch_size=args.batch_size,
        start=args.start,
        limit=args.limit,
        on_progress=progress_callback
    )
    print("\n\nEvaluation finished. Saving results...")

    stats = runner.save_results(results, ground_truth, questions, output_csv)
    
    print("\n--- Evaluation Results ---")
    print(f"Accuracy: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")
    print(f"Saved to: {stats['file']} (Column: {stats['column']})")


if __name__ == "__main__":
    main()
