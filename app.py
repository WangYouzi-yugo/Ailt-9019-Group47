import json
import math
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HERE, "corpus.json")

# Stems are used so that plural forms such as "batteries" are also caught.
REFUSE_WORDS = [
    "batter", "chemical", "lamp", "tube", "paint", "medicine", "syringe"
]

# Generic words do not identify the item being asked about, so ignore them
# during matching. This helps avoid matching an unrelated item just because
# the question contains a word such as "recycle".
STOPWORDS = {
    "a", "an", "the", "i", "can", "do", "does", "how", "what", "which", "where",
    "is", "are", "be", "to", "of", "in", "at", "on", "for", "it", "my", "this",
    "into", "should", "go", "goes", "put", "throw", "dispose", "bin", "bins",
    "recycle", "recycling", "recyclable", "recycled", "category", "belong",
    "hku", "re", "kiosk", "campus", "way", "correct",
}

MIN_SCORE = 0.25


def load_corpus():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def tokenize(text):
    tokens = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def build_index(corpus):
    df = Counter()
    token_lists = []
    for doc in corpus:
        # Match only on the item name: text before the first colon.
        # The rule/answer text may mention "plastic" or "paper", but those
        # words alone must not make an unrelated item match a coffee-cup rule.
        item_name = doc["text"].split(":", 1)[0]
        tokens = tokenize(item_name)
        token_lists.append(tokens)
        for token in set(tokens):
            df[token] += 1
    n = len(corpus)
    idf = {token: math.log((n + 1) / (count + 1)) + 1 for token, count in df.items()}
    return token_lists, idf


def tfidf_vector(tokens, idf):
    tf = Counter(tokens)
    vec = {}
    for token, count in tf.items():
        vec[token] = (1 + math.log(count)) * idf.get(token, 0.0)
    norm = math.sqrt(sum(value * value for value in vec.values())) or 1.0
    return {token: value / norm for token, value in vec.items()}


def cosine_similarity(vec_a, vec_b):
    common = set(vec_a) & set(vec_b)
    return sum(vec_a[token] * vec_b[token] for token in common)


def retrieve(query, corpus, k=2):
    token_lists, idf = build_index(corpus)
    query_vec = tfidf_vector(tokenize(query), idf)
    scored = []
    for i, doc in enumerate(corpus):
        doc_vec = tfidf_vector(token_lists[i], idf)
        score = cosine_similarity(query_vec, doc_vec)
        scored.append((score, i))
    scored.sort(reverse=True)
    return [(corpus[index], score) for score, index in scored[:k]]


def should_refuse(query, best_score):
    if any(word in query.lower() for word in REFUSE_WORDS):
        return True
    return best_score < MIN_SCORE


def format_answer(query):
    corpus = load_corpus()
    results = retrieve(query, corpus, k=2)
    if not results:
        return (
            "[Refusal] No sufficient information is currently available to answer this question.\n"
            "Please refer to the official recycling guidelines from the Hong Kong EPD or the HKU Sustainability Office."
        )
    doc, score = results[0]
    if should_refuse(query, score):
        return (
            "[Refusal] Recycling Rules Helper: No reliable official basis has been found. "
            "To avoid misinformation, I cannot provide a direct answer.\n"
            "Please refer to the official channels: HKU Sustainability Office / Hong Kong EPD Recycling Guidelines."
        )
    lines = [
        f"Answer: {doc['answer']}",
        "",
        f"Original Reference: {doc['text']}",
        f"Source: {doc['source_name']}  Link: {doc['url']}  Accessed on: {doc['accessed_on']}",
    ]
    return "\n".join(lines)


DEMO_QUERIES = [
    "plastic bottle how to recycle",
    "can batteries be put in recycling bins",
    "what category does a banana peel belong to for recycling",
]


def run_demo():
    for query in DEMO_QUERIES:
        print("=" * 60)
        print(f"INPUT : {query}")
        print("-" * 60)
        print(format_answer(query))
    print("=" * 60)


def main():
    args = sys.argv[1:]
    if "--demo" in args:
        run_demo()
        return
    if "--ask" in args:
        index = args.index("--ask") + 1
        if index < len(args):
            print(format_answer(args[index]))
        else:
            print('Usage: python app.py --ask "How to recycle a plastic bottle?"')
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
