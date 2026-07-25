"""Evaluation chain for token-efficient MCQ parsing."""

import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from src.config import Settings
from src.lc.chain import build_chat_model


SYSTEM_PROMPT_SINGLE = """
You are taking a multiple-choice exam. Based ONLY on the provided context, select exactly {num_answers} correct answer(s).
Output ONLY the letter(s): A, B, C, or D. If {num_answers} > 1, separate them with commas (e.g. A,C).
DO NOT output any explanations. DO NOT output any other text.
""".strip()

SYSTEM_PROMPT_BATCH = """
You are taking a multiple-choice exam. For each numbered question below, based ONLY on its provided context, select the requested number of correct answers as specified in the question text.
Output exactly one line per question in the format: {{number}}:{{letter(s)}}
If a question requires multiple answers, separate the letters with commas (e.g., A,C).
Example:
1:A
2:B,C
3:D

DO NOT output any explanations. DO NOT output any other text.
""".strip()


def parse_single_answer(output: str) -> str:
    """Parse output like 'A' or 'A, C' into 'A' or 'A,C'.
    
    Only matches standalone A/B/C/D letters (not embedded in words).
    """
    text = output.strip().upper()
    # Match only standalone letters A-D (surrounded by word boundaries)
    letters = re.findall(r'\b([ABCD])\b', text)
    if not letters:
        return "X"  # unparseable
    # Return unique sorted letters joined by comma
    return ",".join(sorted(set(letters)))


def parse_batch_answers(output: str) -> dict[int, str]:
    """Parse output like '1:A\\n2:B,C' into {1: 'A', 2: 'B,C'}."""
    results = {}
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        try:
            q_num_str, ans_str = line.split(":", 1)
            q_num = int(q_num_str.strip())
            
            letters = re.findall(r'\b([A-Da-d])\b', ans_str.upper())
            if letters:
                results[q_num] = ",".join(sorted(list(set(letters))))
            else:
                results[q_num] = "X"
        except ValueError:
            pass
    return results


def build_single_eval_chain(settings: Settings) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_SINGLE),
        ("human", "Question (choose {num_answers} answer(s)): {question}\n\nA: {a}\nB: {b}\nC: {c}\nD: {d}\n\nContext:\n{context}"),
    ])
    llm = build_chat_model(settings)
    
    # We want a string out from the model
    from langchain_core.output_parsers import StrOutputParser
    
    return prompt | llm | StrOutputParser() | RunnableLambda(parse_single_answer)


def build_batch_eval_chain(settings: Settings) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_BATCH),
        ("human", "{batched_content}"),
    ])
    llm = build_chat_model(settings)
    from langchain_core.output_parsers import StrOutputParser
    
    return prompt | llm | StrOutputParser() | RunnableLambda(parse_batch_answers)
