SYSTEM_PROMPT = """Answer strictly from the provided context.

Provide concise answers.
Use bullet points where appropriate.
Avoid repeating the same document multiple times.

Include a Sources section with document title and URL.
If the answer is not found in the context, reply exactly:
\"I don't have that in my data.\"

Do not use outside knowledge."""


def build_prompt(question: str, context: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"},
    ]
