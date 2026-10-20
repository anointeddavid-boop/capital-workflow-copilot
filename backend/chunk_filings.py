import glob
import json
import os
import sys

IN_DIR = "data/filings"
OUT_DIR = "data/chunks"


def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start, end)
            if cut <= start + size // 2:
                cut = text.rfind(" ", start, end)
            if cut > start + size // 2:
                end = cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    overlap = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    files = sorted(glob.glob(os.path.join(IN_DIR, "*.txt")))
    if not files:
        sys.exit("No filings found. Run download_filings.py first.")

    os.makedirs(OUT_DIR, exist_ok=True)
    for path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        pieces = chunk_text(text, size, overlap)
        name = os.path.basename(path).replace(".txt", "")
        records = [
            {"chunk_id": i, "source": name, "text": t}
            for i, t in enumerate(pieces)
        ]
        out_path = os.path.join(OUT_DIR, f"{name}_size{size}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f)
        avg = sum(len(t) for t in pieces) // len(pieces)
        print("File:", name)
        print("Chunk size:", size, "| Overlap:", overlap)
        print("Chunks created:", len(pieces))
        print("Average chunk length:", avg)
        print("Saved:", out_path)
        print("--- Sample chunk #200 ---")
        print(pieces[min(200, len(pieces) - 1)])


if __name__ == "__main__":
    main()
