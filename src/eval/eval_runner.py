"""Core runner for evaluation pipeline."""

import csv
import datetime
import os
from collections.abc import Callable

from src.config import Settings
from src.lc.eval_chain import build_batch_eval_chain, build_single_eval_chain
from src.rag.service import RAGService


class EvalRunner:
    """Runner for multiple-choice Q&A evaluation."""

    def __init__(self, service: RAGService, settings: Settings):
        self.service = service
        self.settings = settings
        self._single_chain = None
        self._batch_chain = None

    @property
    def single_chain(self):
        """Lazily build single eval chain on first use."""
        if self._single_chain is None:
            self._single_chain = build_single_eval_chain(self.settings)
        return self._single_chain

    @property
    def batch_chain(self):
        """Lazily build batch eval chain on first use."""
        if self._batch_chain is None:
            self._batch_chain = build_batch_eval_chain(self.settings)
        return self._batch_chain

    def load_ground_truth(self, md_path: str) -> dict[int, str]:
        """Parse real_answer.md to map question_number -> correct_answer."""
        ground_truth = {}
        if not os.path.exists(md_path):
            return ground_truth

        with open(md_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if (
                    not line
                    or line.startswith("###")
                    or "question_number" in line.lower().replace("\\_", "_")
                    or "question" in line.lower() and "num" in line.lower()
                ):
                    continue
                try:
                    parts = line.split(",")
                    q_num = int(parts[0].strip())
                    # The answers part could be "A" or '"A,B,C"'
                    ans = line.split(",", 2)[2].strip()
                    # Remove quotes and spaces
                    ans = ans.strip('"').replace(" ", "")
                    # Ensure comma separation is normalized
                    if "," in ans:
                        ans = ",".join(sorted(ans.split(",")))
                    
                    ground_truth[q_num] = ans
                except Exception:
                    pass
        return ground_truth

    def load_questions(self, csv_path: str) -> list[dict]:
        """Parse question.csv."""
        questions = []
        if not os.path.exists(csv_path):
            return questions

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            for i, row in enumerate(reader):
                if len(row) >= 6:
                    questions.append({
                        "question_number": i + 1,
                        "question": row[0],
                        "A": row[1],
                        "B": row[2],
                        "C": row[3],
                        "D": row[4],
                        "source_folder": row[5]
                    })
        return questions

    def _retrieve_context(self, question_text: str) -> str:
        """Retrieve context for a single question."""
        try:
            results = self.service.retrieve(question_text)
            if not results:
                return "No context found."
            from src.rag.retriever import format_context
            return format_context(results)
        except Exception:
            return "Error retrieving context."

    def run(
        self,
        questions: list[dict],
        batch_size: int = 1,
        start: int = 1,
        limit: int | None = None,
        on_progress: Callable[[int, int, str], None] | None = None,
        max_workers: int = 1,
    ) -> list[dict]:
        """
        Run the evaluation using asyncio for concurrent requests.
        Returns a list of dicts: {"question_number": int, "ai_answer": str}
        """
        import asyncio
        
        # Filter questions by start and limit
        filtered = [q for q in questions if q["question_number"] >= start]
        if limit is not None:
            filtered = filtered[:limit]

        total = len(filtered)
        done = 0
        ai_answers = []

        async def process_single(q):
            # retrieve_context is blocking, so we run it in a thread
            context = await asyncio.to_thread(self._retrieve_context, q["question"])
            try:
                # Use ainvoke for async LangChain call
                ans = await self.single_chain.ainvoke({
                    "question": q["question"],
                    "a": q["A"],
                    "b": q["B"],
                    "c": q["C"],
                    "d": q["D"],
                    "context": context
                })
            except Exception:
                ans = "X"
            return {"question_number": q["question_number"], "ai_answer": ans}

        async def process_batch(batch):
            batched_content = ""
            for q in batch:
                context = await asyncio.to_thread(self._retrieve_context, q["question"])
                batched_content += f"Question {q['question_number']}: {q['question']}\n"
                batched_content += f"A: {q['A']}\nB: {q['B']}\nC: {q['C']}\nD: {q['D']}\n"
                batched_content += f"Context:\n{context}\n\n"

            try:
                batch_results = await self.batch_chain.ainvoke({"batched_content": batched_content})
            except Exception:
                batch_results = {}
                
            results = []
            for q in batch:
                ans = batch_results.get(q["question_number"], "X")
                results.append({"question_number": q["question_number"], "ai_answer": ans})
            return results

        async def _run_async():
            nonlocal done
            semaphore = asyncio.Semaphore(max_workers)
            
            async def sem_task(task_func, item):
                async with semaphore:
                    return await task_func(item), item

            if batch_size <= 1:
                tasks = [sem_task(process_single, q) for q in filtered]
            else:
                batches = [filtered[i:i + batch_size] for i in range(0, total, batch_size)]
                tasks = [sem_task(process_batch, b) for b in batches]

            # Process as they complete to update UI correctly
            for f in asyncio.as_completed(tasks):
                res, item = await f
                if isinstance(item, list):
                    ai_answers.extend(res)
                    done += len(item)
                    if on_progress:
                        on_progress(done, total, f"Completed batch of {len(item)}")
                else:
                    ai_answers.append(res)
                    done += 1
                    if on_progress:
                        on_progress(done, total, f"Completed Q{res['question_number']}")

        # Handle Streamlit's environment (asyncio.run is safe if no loop is running)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(asyncio.run, _run_async()).result()
        else:
            asyncio.run(_run_async())

        # Sort answers by question number to restore original order
        ai_answers.sort(key=lambda x: x["question_number"])
        
        return ai_answers

    def save_results(
        self,
        ai_results: list[dict],
        ground_truth: dict[int, str],
        questions: list[dict],
        output_path: str,
        batch_size: int = 1,
        max_workers: int = 1,
    ) -> dict:
        """
        Append a new timestamped column to the results CSV and save metadata.
        Returns accuracy dict.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_col_name = f"ai_answer_{timestamp}"

        # Load existing data if any
        existing_data = {}
        headers = ["question_number", "question", "correct_answer", "source_folder"]
        
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                try:
                    file_headers = next(reader)
                    headers = file_headers
                except StopIteration:
                    pass
                for row in reader:
                    if row:
                        try:
                            q_num = int(row[0])
                            existing_data[q_num] = row
                        except ValueError:
                            pass

        if new_col_name not in headers:
            headers.append(new_col_name)
        new_col_idx = headers.index(new_col_name)

        # Convert questions to a dict for easy lookup
        q_dict = {q["question_number"]: q for q in questions}
        
        # Merge new results
        results_map = {res["question_number"]: res["ai_answer"] for res in ai_results}
        
        correct = 0
        total_eval = 0

        # We will rewrite the whole file with the new column
        output_rows = []
        
        # Determine all question numbers to output
        all_q_nums = sorted(list(set(existing_data.keys()) | set(q_dict.keys())))
        
        for q_num in all_q_nums:
            if q_num in existing_data:
                row = existing_data[q_num]
                # Pad row to correct length
                while len(row) < len(headers):
                    row.append("")
            else:
                q_info = q_dict.get(q_num, {})
                row = [""] * len(headers)
                row[0] = str(q_num)
                row[1] = q_info.get("question", "")
                row[2] = ground_truth.get(q_num, "")
                row[3] = q_info.get("source_folder", "")

            # If we evaluated this question in this run, update the new column
            if q_num in results_map:
                ai_ans = results_map[q_num]
                row[new_col_idx] = ai_ans
                total_eval += 1
                if ai_ans == row[2]:
                    correct += 1
            
            output_rows.append(row)

        # Write out
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(output_rows)

        accuracy = (correct / total_eval * 100) if total_eval > 0 else 0
        
        # Save metadata
        import json
        metadata_path = output_path.replace(".csv", "_metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as fm:
                    metadata = json.load(fm)
            except Exception:
                pass
                
        metadata[new_col_name] = {
            "timestamp": timestamp,
            "batch_size": batch_size,
            "max_workers": max_workers,
            "model": self.settings.chat_model,
            "accuracy": accuracy,
            "correct": correct,
            "total": total_eval
        }
        with open(metadata_path, "w", encoding="utf-8") as fm:
            json.dump(metadata, fm, indent=2)
        
        return {
            "correct": correct,
            "total": total_eval,
            "accuracy": accuracy,
            "column": new_col_name,
            "file": output_path
        }

    def get_history(self, output_path: str) -> list[dict]:
        """Extract historical accuracy from the CSV and merge with metadata."""
        if not os.path.exists(output_path):
            return []
            
        history = []
        import json
        metadata_path = output_path.replace(".csv", "_metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as fm:
                    metadata = json.load(fm)
            except Exception:
                pass

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return history
                
            # Find AI answer columns
            ai_cols = [(i, h) for i, h in enumerate(headers) if h.startswith("ai_answer_")]
            if not ai_cols:
                return history
                
            col_stats = {h: {"correct": 0, "total": 0} for _, h in ai_cols}
            
            for row in reader:
                if len(row) < 3:
                    continue
                correct_ans = row[2]
                for i, h in ai_cols:
                    if i < len(row) and row[i]:
                        col_stats[h]["total"] += 1
                        if row[i] == correct_ans:
                            col_stats[h]["correct"] += 1
                            
            for h, stats in col_stats.items():
                acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
                run_meta = metadata.get(h, {})
                
                history.append({
                    "Run": h.replace("ai_answer_", ""),
                    "Model": run_meta.get("model", "Unknown"),
                    "Accuracy (%)": round(acc, 2),
                    "Correct": stats["correct"],
                    "Total": stats["total"],
                    "Batch Size": run_meta.get("batch_size", "-"),
                    "Max Workers": run_meta.get("max_workers", "-")
                })
                
        # Sort history by run desc
        history.sort(key=lambda x: x["Run"], reverse=True)
        return history
