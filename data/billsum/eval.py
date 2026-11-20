"""BillSum scores under the pinned authors' ROUGE 0.3.2 configuration.

The upstream script sends the gold summary as the first ROUGE argument and
reports the ROUGE-1, ROUGE-2 and ROUGE-L F-scores.
https://github.com/FiscalNote/BillSum/blob/f1cbe1c9e1a35a2f7ed3ddedafed54abfc3fac8b/billsum/utils/compute_rouge_from_texts.py
"""

ATTEMPTS = 1
MAX_OUTPUT_CHARS = 2000
INSTRUCTION = f"Summarize the bill in at most {MAX_OUTPUT_CHARS:,} characters. Return only the summary."


def messages(task):
    _, separator, rendered = task["prompt"].partition("\n\n# Bill text\n\n~~~\n")
    if not separator or not rendered.endswith("\n~~~"):
        raise ValueError(f"{task['key']}: missing fenced bill text")
    text = rendered.removesuffix("\n~~~")
    return [{"role": "user", "content": f"{text}\n\n{INSTRUCTION}"}]


def sentences(summary):
    # The pinned library splits on periods and collapses whitespace per sentence.
    return [tuple(" ".join(part.split()).split(" ")) for part in summary.split(".") if part]


def ngram_score(first, second, size):
    first_grams = set(zip(*(first[offset:] for offset in range(size))))
    second_grams = set(zip(*(second[offset:] for offset in range(size))))
    common = len(first_grams & second_grams)
    precision = common / len(first_grams) if first_grams else 0.0
    recall = common / len(second_grams) if second_grams else 0.0
    return 2.0 * ((precision * recall) / (precision + recall + 1e-8))


def shared_subsequence_words(left, right):
    lengths = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for i, word in enumerate(left, 1):
        for j, other in enumerate(right, 1):
            if word == other:
                lengths[i][j] = lengths[i - 1][j - 1] + 1
            else:
                lengths[i][j] = max(lengths[i - 1][j], lengths[i][j - 1])

    words = set()
    i, j = len(left), len(right)
    while i and j:
        if left[i - 1] == right[j - 1]:
            words.add(left[i - 1])
            i -= 1
            j -= 1
        elif lengths[i - 1][j] > lengths[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return words


def score(task, output):
    gold = sentences(task["solution"])
    prediction = sentences(output)
    if not gold or not prediction:
        return None
    gold_words = tuple(word for sentence in gold for word in sentence)
    prediction_words = tuple(word for sentence in prediction for word in sentence)
    gold_count, prediction_count = len(set(gold_words)), len(set(prediction_words))
    if gold == prediction:
        common = gold_count
    else:
        union = set()
        for generated_sentence in prediction:
            for gold_sentence in gold:
                # Preserve the pinned library's tie-breaking and argument order.
                union.update(shared_subsequence_words(generated_sentence, gold_sentence))
        common = len(union)
    precision = common / gold_count
    recall = common / prediction_count
    beta_squared = (precision / (recall + 1e-12)) ** 2
    rouge_l = (1 + beta_squared) * recall * precision / (recall + beta_squared * precision + 1e-12)
    return {
        "rouge-1": ngram_score(gold_words, prediction_words, 1),
        "rouge-2": ngram_score(gold_words, prediction_words, 2),
        "rouge-l": rouge_l,
    }
