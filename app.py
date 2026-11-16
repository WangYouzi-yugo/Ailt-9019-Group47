"""
AILT9019 Group 47 - HKU Waste Recycling Assistant (CLI prototype)

Retrieval-based Q&A over a curated corpus of HKU recycling items.

- Answers always cite the retrieved record (category / preparation / facility / source).
- Refuses hazardous / unsupported items (no hallucination).
- Optionally drafts the final answer with an LLM; falls back to the retrieved record
  when no API key is configured, so the prototype runs offline.

Run:
    python app.py                 # interactive CLI
    python app.py "paper cup"     # single query
    python app.py --eval          # run eval_cases.json, print accuracy, write test_log.txt
"""

import json
import os
import re
import sys
from datetime import date

CORPUS_FILE = os.environ.get('CORPUS_FILE', 'corpus.json')
EVAL_FILE = os.environ.get('EVAL_FILE', 'eval_cases.json')
LOG_FILE = os.environ.get('LOG_FILE', 'test_log.txt')

# Items that must NEVER receive a recycling answer -> safety refusal.
UNSAFE_KEYWORDS = [
    'lithium battery', 'car battery', 'battery', 'batteries', 'power bank', 'powerbank',
    'broken glass', 'glass shard', 'shattered glass', 'needle', 'syringe', 'sharps',
    'chemical', 'paint', 'solvent', 'asbestos', 'medical waste', 'clinical waste',
    'gas canister', 'gas cylinder', 'fire extinguisher', 'ammunition',
    'dead animal', 'biohazard',
]

# Words that make a query ambiguous -> ask for clarification instead of guessing.
AMBIGUOUS_HINTS = [
    'dirty', 'contaminated', 'greasy', 'stained', 'broken', 'torn', 'mixed',
    'partly', 'not sure', 'unsure', 'some kind', 'kind of', 'maybe',
]


# ---------------------------------------------------------------- data
def load_corpus(filepath=CORPUS_FILE):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError('corpus must be a non-empty JSON list of items.')
    for i, item in enumerate(data):
        for field in ('name', 'category', 'preparation', 'facility', 'source'):
            if field not in item:
                raise ValueError('corpus item #%s (%s) missing field %s.' %
                                 (i, item.get('name', '?'), field))
    return data


# ---------------------------------------------------------------- helpers
def _norm(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _tokens(text):
    return set(_norm(text).split())


def is_unsafe(query):
    q = _norm(query)
    return any(_norm(k) in q for k in UNSAFE_KEYWORDS)


def is_ambiguous(query):
    q = _norm(query)
    return any(h in q for h in AMBIGUOUS_HINTS)


# ---------------------------------------------------------------- retrieval
def retrieve_answer(query, corpus):
    """Keyword/alias scoring over the corpus. Returns (best_item, score) or (None, 0)."""
    q_tokens = _tokens(query)
    best, best_score = None, 0
    for item in corpus:
        name_tokens = _tokens(item['name'])
        alias_tokens = set()
        for alias in item.get('aliases', []):
            alias_tokens |= _tokens(alias)
        cat_tokens = _tokens(item['category'])
        score = 0
        if _norm(item['name']) and _norm(item['name']) in _norm(query):
            score += 10
        if _norm(query) and _norm(query) in _norm(item['name']):
            score += 8
        score += 6 * len(alias_tokens & q_tokens)
        score += 3 * len(name_tokens & q_tokens)
        score += 1 * len(cat_tokens & q_tokens)
        if score > best_score:
            best, best_score = item, score
    if best_score >= 3:
        return best, best_score
    return None, 0


# ---------------------------------------------------------------- answer
def format_record(item):
    return (
        'Item: %s\n'
        'Category: %s\n'
        'Preparation: %s\n'
        'Facility: %s\n'
        'Source: %s (accessed %s)' % (
            item['name'], item['category'], item['preparation'],
            item['facility'], item['source'], item.get('access_date', 'n/a'))
    )


def draft_with_llm(query, item):
    """Optional LLM drafting step. Returns text, or None if unavailable (caller falls back).

    Works with any OpenAI-compatible endpoint. Configure via environment variables:
        OPENAI_API_KEY  (or API_KEY)   secret key, e.g. a DeepSeek "sk-..." key
        OPENAI_BASE_URL endpoint, default https://api.openai.com/v1
                        DeepSeek: https://api.deepseek.com/v1
        OPENAI_MODEL    model name, default gpt-4o-mini
                        DeepSeek: deepseek-chat or deepseek-reasoner
    """
    api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('API_KEY')
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        )
        system = (
            'You are a HKU waste recycling assistant. Use ONLY the retrieved record to answer. '
            'Never invent facilities or preparation steps. Always restate preparation and facility.'
        )
        user = 'Question: %s\nRetrieved record:\n%s' % (query, format_record(item))
        resp = client.chat.completions.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{'role': 'system', 'content': system},
                      {'role': 'user', 'content': user}],
            temperature=0.2, max_tokens=300)
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print('[info] LLM drafting unavailable (%s); using retrieved record.' %
              exc.__class__.__name__, file=sys.stderr)
        return None


def process_query(query, corpus, use_llm=True):
    q = (query or '').strip()
    if not q:
        return 'empty', 'EMPTY', 'Please enter an item to recycle.'
    if is_unsafe(q):
        return 'refused', 'REFUSED', (
            'Sorry, I cannot help with hazardous or unsupported items. '
            'Please do NOT put them in recycling bins. Contact HKU Facilities Office / '
            'the relevant special collection point for safe disposal.')
    if is_ambiguous(q):
        return 'ambiguous', 'AMBIGUOUS', (
            'Your item is partially described or contaminated, so I cannot give a confident answer. '
            'Could you tell me the main material (paper / plastic / metal / glass / e-waste) '
            'and whether it is clean and dry? In general, recyclables must be clean and dry; '
            'heavily contaminated items go to general waste.')
    item, score = retrieve_answer(q, corpus)
    if item is None:
        return 'unsupported', 'UNSUPPORTED', (
            'Sorry, this item is not in my verified HKU corpus. '
            'Please check the official HKU waste management / Facilities Office page before disposing of it.')
    if use_llm:
        drafted = draft_with_llm(q, item)
        if drafted:
            return 'answer', 'ANSWERED', drafted + '\n\n' + format_record(item)
    return 'answer', 'ANSWERED', format_record(item)


# ---------------------------------------------------------------- evaluation
def run_evaluation(corpus, eval_file=EVAL_FILE, log_file=LOG_FILE):
    with open(eval_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    lines = ['HKU Recycling Assistant - evaluation run ' + date.today().isoformat(), '=' * 60]
    correct = 0
    buckets = {}
    for idx, case in enumerate(cases, 1):
        _, code, _ = process_query(case['query'], corpus, use_llm=False)
        ok = code == case['expected']
        correct += ok
        b = buckets.setdefault(case.get('bucket', 'normal'), [0, 0])
        b[1] += 1
        b[0] += ok
        lines.append('Test %d: input=[%s] expected=%s got=%s -> %s' %
                     (idx, case['query'], case['expected'], code, 'PASS' if ok else 'FAIL'))
    acc = correct / len(cases) * 100 if cases else 0
    lines.append('=' * 60)
    lines.append('Overall accuracy: %d/%d = %.1f%%' % (correct, len(cases), acc))
    for name, (c, t) in buckets.items():
        lines.append('  bucket %s: %d/%d' % (name, c, t))
    text = '\n'.join(lines)
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(text + '\n')
    print(text)
    return acc


# ---------------------------------------------------------------- CLI
def main(argv):
    corpus = load_corpus()
    if '--eval' in argv:
        run_evaluation(corpus)
        return
    positional = [a for a in argv if not a.startswith('-')]
    if positional:
        _, code, resp = process_query(' '.join(positional), corpus)
        print('[%s]\n%s' % (code, resp))
        return
    print('=== HKU Waste Recycling Assistant (CLI) ===')
    print("Loaded %d verified items. Type 'quit' to exit.\n" % len(corpus))
    while True:
        try:
            query = input('Query> ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in {'quit', 'exit', 'q'}:
            break
        if not query:
            continue
        _, code, resp = process_query(query, corpus)
        print('\n[%s]\n%s\n' % (code, resp))
    print('Goodbye!')


if __name__ == '__main__':
    main(sys.argv[1:])
