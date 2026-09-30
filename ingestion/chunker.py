from pathlib import Path
import json

def save_chunks_to_json(chunks: list[dict], output_path: str) -> None:
    """
    Saves the list of chunk dicts to a JSON file, pretty-printed
    and with proper UTF-8 handling (your KB files may contain
    characters outside plain ASCII).
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)



def load_and_split_by_blank_lines(filepath: str) -> list[str]:
    """
    Reads a text file and splits it into sections wherever there's
    a blank line (i.e. two or more consecutive newlines).
    Returns a list of non-empty, stripped section strings.
    """
    text = Path(filepath).read_text(encoding="utf-8")
    raw_sections = text.split('\n\n')
    sections = [i.strip() for i in raw_sections if i.strip()]
    return sections


def merge_small_sections(sections: list[str], min_chars: int = 100) -> list[str]:
    """
    Merges sections shorter than min_chars into the following section,
    repeatedly, until every resulting chunk is >= min_chars
    (except possibly the last one, which has nothing left to merge into).
    """
    merged = []
    buffer = ""

    for section in sections:
        if buffer:
            buffer += "\n\n" + section
        else:
            buffer += section

        if len(buffer) >= min_chars:
            merged.append(buffer)
            buffer = ""

    if buffer:
        if merged:
            merged[-1] += "\n\n" + buffer
        else:
            merged.append(buffer)

    return merged


def split_oversized_section(section: str, max_chars: int = 400) -> list[str]:
    """
    If `section` looks like a header + bullet list ("\n- " present), split it
    into one chunk per bullet, with the header text prepended to each bullet
    for context — regardless of the section's total size, since bulleted
    content is always split for sharper retrieval.

    `max_chars` is currently unused for bulleted sections (always split),
    but kept as a parameter for a future fallback: splitting oversized
    PROSE / numbered-list sections (no "\n- ") that have no dash-bullets.
    """
    if "\n- " not in section:
        # No dash-bullet structure to split on — leave it whole for now
        return [section]

    pieces = section.split("\n- ")
    header = pieces[0]
    bullets = pieces[1:]

    result = [(header + " " + b) for b in bullets]

    return result


def load_kb_directory(kb_dir: str) -> list[dict]:
    """
    Runs the full chunking pipeline (split -> merge -> split_oversized)
    on every .txt file in kb_dir, and tags each resulting chunk with
    its source filename.
    Returns a list of dicts: {"text": <chunk string>, "source": <filename>}
    """
    all_chunks = []

    txt_files = Path(kb_dir).glob('*.txt')

    for filepath in txt_files:
        sections = load_and_split_by_blank_lines(str(filepath))
        merged_sections = merge_small_sections(sections, min_chars=100)

        file_chunks = []
        for s in merged_sections:
            file_chunks.extend(split_oversized_section(s, max_chars=400))

        for chunk_text in file_chunks:
            all_chunks.append({"text": chunk_text, "source": filepath.name})

    return all_chunks

if __name__ == "__main__":
    all_chunks = load_kb_directory(r"D:\ITI\Final Project\kb")
    print(f"Got {len(all_chunks)} total chunks across all KB files\n")

    save_chunks_to_json(all_chunks, r"D:\ITI\Final Project\kb_chunks.json")
    print("Saved to kb_chunks.json")

    for i, c in enumerate(all_chunks[:5]):
        print(f"--- Chunk {i} (source: {c['source']}, {len(c['text'])} chars) ---")
        print(c['text'][:120], "...\n")