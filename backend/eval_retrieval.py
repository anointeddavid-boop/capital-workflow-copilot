import glob
import json
import sys

from search import search

QUESTIONS = "eval/questions.json"
SIZES = [500, 1000, 2000]
TOP_K = 4


def main():
    questions = json.load(open(sys.argv[1] if len(sys.argv) > 1 else QUESTIONS))
    filing = glob.glob("data/filings/*.txt")[0]
    full_text = " ".join(open(filing, encoding="utf-8").read().lower().split())

    usable = []
    for q in questions:
        if any(" ".join(k.lower().split()) in full_text for k in q["keywords"]):
            usable.append(q)
        else:
            print("Skipped (keywords not found in the filing):", q["question"])

    print(f"\nScoring {len(usable)} questions, top {TOP_K} results per question\n")
    results = {}
    for size in SIZES:
        hits = 0
        rr_total = 0.0
        misses = []
        for q in usable:
            rows = search(q["question"], size=size, top_k=TOP_K)
            rank_found = None
            for rank, (source, chunk_id, content, score) in enumerate(rows, 1):
                if any(" ".join(k.lower().split()) in " ".join(content.lower().split()) for k in q["keywords"]):
                    rank_found = rank
                    break
            if rank_found:
                hits += 1
                rr_total += 1 / rank_found
            else:
                misses.append(q["question"])
        results[size] = {
            "hit_rate": round(hits / len(usable), 3),
            "mrr": round(rr_total / len(usable), 3),
            "misses": misses,
        }
        print(f"Chunk size {size}: hit rate {hits}/{len(usable)} = {hits / len(usable):.0%}, MRR {rr_total / len(usable):.3f}")
        for m in misses:
            print("   missed:", m)

    json.dump(results, open("eval/results_retrieval.json", "w"), indent=2)
    print("\nSaved: eval/results_retrieval.json")


if __name__ == "__main__":
    main()
