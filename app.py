import json
import math
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HERE, "corpus.json")

REFUSE_WORDS = [
    "battery", "chemical", "lamp", "tube"
]

MIN_SCORE = 0.12

def load_corpus():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)

def tokenize(text):
    return re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", text.lower())

def build_index(corpus):
    df = Counter()
    token_lists = []
    for doc in corpus:
        tokens = tokenize(doc["text"])
        token_lists.append(tokens)
        for t in set(tokens):
            df[t] += 1
    n = len(corpus)
    idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
    return token_lists, idf

def tfidf_vector(tokens, idf):
    tf = Counter(tokens)
    vec = {}
    for t, c in tf.items():
        vec[t] = (1 + math.log(c)) * idf.get(t, 0.0)
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}

def cosine_similarity(vec_a, vec_b):
    common = set(vec_a) & set(vec_b)
    return sum(vec_a[t] * vec_b[t] for t in common)

def retrieve(query, corpus, k=2):
    token_lists, idf = build_index(corpus)
    query_vec = tfidf_vector(tokenize(query), idf)
    scored = []
    for i, doc in enumerate(corpus):
        doc_vec = tfidf_vector(token_lists[i], idf)
        score = cosine_similarity(query_vec, doc_vec)
        scored.append((score, i))
    scored.sort(reverse=True)
    return [(corpus[idx], score) for score, idx in scored[:k]]

def should_refuse(query, best_score):
    if any(w in query.lower() for w in REFUSE_WORDS):
        return True
    return best_score < MIN_SCORE

def format_answer(query):
    corpus = load_corpus()
    results = retrieve(query, corpus, k=2)
    if not results:
        return ("[Refusal] No sufficient information is currently available to answer this question.\n"
                "Please refer to the official recycling guidelines from the Hong Kong EPD or the HKU Sustainability Office.")
    doc, score = results[0]
    if should_refuse(query, score):
        return ("[Refusal] Recycling Rules Helper No reliable official basis has been found."
                "To avoid misinformation, I cannot provide a direct answer.\n"
                "Please refer to the official channels: HKU Sustainability Office / Hong Kong EPD Recycling Guidelines.")
    lines = [
        f"Answer: {doc['answer']}",
        "",
        f"Original Reference: {doc['text']}",
        f"Source: {doc['source_name']}  Link: {doc['url']}  Accessed on: {doc['accessed_on']}",
    ]
    return "\n".join(lines)

DEMO_QUERIES = [
    " plastic bottle how to recycle",
    "can batteries be put in recycling bins",
    "what category does a banana peel belong to for recycling",
]

def run_demo():
    for q in DEMO_QUERIES:
        print("=" * 60)
        print(f"INPUT : {q}")
        print("-" * 60)
        print(format_answer(q))
    print("=" * 60)

def main():
    args = sys.argv[1:]
    if "--demo" in args:
        run_demo()
        return
    if "--ask" in args:
        idx = args.index("--ask") + 1
        if idx < len(args):
            print(format_answer(args[idx]))
        else:
            print("Usage: python app.py --ask \"How to recycle a plastic bottle?\"")
        return
    print("Recycling Rules Helper — Enter an item name to query its recycling rules (type 'exit' to quit)")
    while True:
        try:
            query = input("> ").strip()
        except EOFError:
            break
        if query.lower() in ("exit", "quit", ""):
            break
        print(format_answer(query))

if __name__ == "__main__":
    main()