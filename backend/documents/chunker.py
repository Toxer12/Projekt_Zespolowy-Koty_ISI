from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    text: str
    char_count: int
    chunk_type: str


def fixed_chunker(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TextChunk]:
    text = text.strip()
    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(TextChunk(
                index=index,
                text=chunk_text,
                char_count=len(chunk_text),
                chunk_type='fixed',
            ))
            index += 1
        start += chunk_size - overlap

    return chunks


def _split_sentences(text: str) -> list[str]:

    text = re.sub(r'\s+', ' ', text).strip()

    parts = re.split(r'(?<=[.!?…])\s+(?=[A-ZŁŚĆŻŹĄĘÓ„"(])', text)

    ABBREV = re.compile(r'\b[a-zA-ZąćęłńóśźżA-ZŁŚĆŻŹĄĘÓ]{1,3}\.$')
    merged = []
    for part in parts:
        if merged and ABBREV.search(merged[-1]):
            merged[-1] = merged[-1] + ' ' + part
        else:
            merged.append(part)

    return [s.strip() for s in merged if s.strip()]


def sentence_chunker(
    text: str,
    max_chars: int = 600,
    min_chars: int = 80,
) -> list[TextChunk]:
    sentences = _split_sentences(text)
    chunks: list[TextChunk] = []
    current: list[str] = []
    current_len = 0
    index = 0

    def flush():
        nonlocal current, current_len, index
        merged = ' '.join(current).strip()
        if merged:
            chunks.append(TextChunk(
                index=index,
                text=merged,
                char_count=len(merged),
                chunk_type='sentence',
            ))
            index += 1
        current = []
        current_len = 0

    for sent in sentences:
        sent_len = len(sent)

        if sent_len > max_chars:
            if current:
                flush()
            sub = fixed_chunker(sent, chunk_size=max_chars, overlap=0)
            for s in sub:
                s.index = index
                s.chunk_type = 'sentence'
                chunks.append(s)
                index += 1
            continue

        if current_len + sent_len + 1 > max_chars:
            flush()

        current.append(sent)
        current_len += sent_len + 1

    if current:
        flush()

    if len(chunks) >= 2 and chunks[-1].char_count < min_chars:
        prev = chunks[-2]
        last = chunks.pop()
        merged_text = prev.text + ' ' + last.text
        chunks[-1] = TextChunk(
            index=prev.index,
            text=merged_text,
            char_count=len(merged_text),
            chunk_type='sentence',
        )

    return chunks


def chunk_text(text: str, method: str = 'sentence') -> list[TextChunk]:
    if method == 'sentence':
        return sentence_chunker(text)
    return fixed_chunker(text)