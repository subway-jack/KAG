import re
import json
import string
import traceback
from collections import Counter


def normalize_answer(s):
    """
    Normalizes the answer string.

    This function standardizes the answer string through a series of steps including removing articles,
    fixing whitespace, removing punctuation, and converting text to lowercase. This ensures consistency
    and fairness when comparing answers.

    Parameters:
    s (str): The answer string to be standardized.

    Returns:
    str: The standardized answer string.
    """

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def contains_chinese(text):
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def white_space_fix(text):
        if contains_chinese(text):
            return " ".join([char for char in text])
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return str(text).lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def f1_score(prediction, ground_truth):
    """
    Calculates the F1 score between the predicted answer and the ground truth.

    The F1 score is the harmonic mean of precision and recall, used to evaluate the model's performance in question answering tasks.

    Parameters:
    prediction (str): The predicted answer from the model.
    ground_truth (str): The actual ground truth answer.

    Returns:
    tuple: A tuple containing the F1 score, precision, and recall.
    """

    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)

    ZERO_METRIC = (0, 0, 0)

    if (
        normalized_prediction in ["yes", "no", "noanswer"]
        and normalized_prediction != normalized_ground_truth
    ):
        return ZERO_METRIC

    if (
        normalized_ground_truth in ["yes", "no", "noanswer"]
        and normalized_prediction != normalized_ground_truth
    ):
        return ZERO_METRIC

    prediction_tokens = normalized_prediction.split()
    ground_truth_tokens = normalized_ground_truth.split()

    # Calculate the number of matching words between the predicted and ground truth answers
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return ZERO_METRIC

    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)

    return f1, precision, recall


def exact_match_score(prediction, ground_truth):
    """
    Calculates the exact match score between a predicted answer and the ground truth answer.

    This function normalizes both the predicted answer and the ground truth answer before comparing them.
    Normalization is performed to ensure that non-essential differences such as spaces and case are ignored.

    Parameters:
    prediction (str): The predicted answer string.
    ground_truth (str): The ground truth answer string.

    Returns:
    int: 1 if the predicted answer exactly matches the ground truth answer, otherwise 0.
    """

    return 1 if normalize_answer(prediction) == normalize_answer(ground_truth) else 0


def get_em_f1(prediction, gold):
    """
    Calculates the Exact Match (EM) score and F1 score between the prediction and the gold standard.

    This function evaluates the performance of a model in text similarity tasks by calculating the EM score and F1 score to measure the accuracy of the predictions.

    Parameters:
    prediction (str): The output predicted by the model.
    gold (str): The gold standard output (i.e., the correct output).

    Returns:
    tuple: A tuple containing two floats, the EM score and the F1 score. The EM score represents the exact match accuracy, while the F1 score is a combination of precision and recall.
    """

    em = exact_match_score(prediction, gold)
    f1, precision, recall = f1_score(prediction, gold)

    return float(em), f1


def compare_summarization_answers(
    query,
    answer1,
    answer2,
    *,
    api_key="EMPTY",
    base_url="http://127.0.0.1:38080/v1",
    model="gpt-4o-mini",
    language="English",
    retries=3,
):
    """
    Given a query and two answers, compare the answers with an LLM for Comprehensiveness, Diversity and Empowerment.

    This function is adapted from LightRAG for evaluating GraphRAG and LightRAG in QFS (query-focused summarization)
    tasks:

      https://github.com/HKUDS/LightRAG/blob/45cea6e/examples/batch_eval.py

    Parameters:
    query (str): The query inputed to LLMs.
    answer1 (str): Answer generated by an LLM.
    answer2 (str): Answer generated by another LLM.
    api_key (str): API key to use when invoke the evaluating LLM.
    base_url (str): base url to use when invoke the evaluating LLM.
    model (str): model name to use when invoke the evaluating LLM.
    language (str): language of the explanation
    retries (int): number of retries

    Returns:
    str: response content generated by the evaluating LLM.
    """
    from openai import OpenAI

    sys_prompt = """
    ---Role---
    You are an expert tasked with evaluating two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.
    """
    prompt = f"""
    You will evaluate two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.

    - **Comprehensiveness**: How much detail does the answer provide to cover all aspects and details of the question?
    - **Diversity**: How varied and rich is the answer in providing different perspectives and insights on the question?
    - **Empowerment**: How well does the answer help the reader understand and make informed judgments about the topic?

    For each criterion, give each answer a score between 0 and 10, choose the better answer (either Answer 1 or Answer 2) and explain why.
    Then, give each answer an overall score between 0 and 10, and select an overall winner based on these three categories.

    Here is the question:
    {query}

    Here are the two answers:

    **Answer 1:**
    {answer1}

    **Answer 2:**
    {answer2}

    Evaluate both answers using the three criteria listed above and provide detailed explanations for each criterion.

    Output your evaluation in the following JSON format:

    {{
        "Comprehensiveness": {{
            "Score 1": [Score of Answer 1 - an integer between 0 and 10],
            "Score 2": [Score of Answer 2 - an integer between 0 and 10],
            "Winner": "[Answer 1 or Answer 2]",
            "Explanation": "[Provide explanation in {language} here]"
        }},
        "Diversity": {{
            "Score 1": [Score of Answer 1 - an integer between 0 and 10],
            "Score 2": [Score of Answer 2 - an integer between 0 and 10],
            "Winner": "[Answer 1 or Answer 2]",
            "Explanation": "[Provide explanation in {language} here]"
        }},
        "Empowerment": {{
            "Score 1": [Score of Answer 1 - an integer between 0 and 10],
            "Score 2": [Score of Answer 2 - an integer between 0 and 10],
            "Winner": "[Answer 1 or Answer 2]",
            "Explanation": "[Provide explanation in {language} here]"
        }},
        "Overall": {{
            "Score 1": [Score of Answer 1 - an integer between 0 and 10],
            "Score 2": [Score of Answer 2 - an integer between 0 and 10],
            "Winner": "[Answer 1 or Answer 2]",
            "Explanation": "[Summarize why this answer is the overall winner based on the three criteria in {language}]"
        }}
    }}
    """
    for index in range(retries):
        content = None
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            if content.startswith("```json") and content.endswith("```"):
                content = content[7:-3]
            metrics = json.loads(content)
            return metrics
        except Exception:
            if index == retries - 1:
                message = (
                    f"Comparing summarization answers failed.\n"
                    f"query: {query}\n"
                    f"answer1: {answer1}\n"
                    f"answer2: {answer2}\n"
                    f"content: {content}\n"
                    f"exception:\n{traceback.format_exc()}"
                )
                print(message)
                return None


def compute_rouge(hyps, refs):
    import jieba
    from rouge_chinese import Rouge

    assert len(hyps) == len(refs)
    hyps = [" ".join(jieba.cut(h)) for h in hyps]
    hyps = [h if h.strip() != "" else "无内容" for h in hyps]
    refs = [" ".join(jieba.cut(r)) for r in refs]
    return Rouge().get_scores(hyps, refs)
