import requests
import json
import time

languages = [
    "C++",
    "Java",
    "Python",
    "Python3",
    "C",
    "C#",
    "JavaScript",
    "Ruby",
    "Swift",
    "Go",
    "Scala",
    "Kotlin",
    "Rust",
    "PHP",
    "TypeScript",
    "Racket",
    "Erlang",
    "Elixir",
    "Dart",
]

categories = [
    "array",
    "string",
    "hash-table",
    "math",
    "dynamic-programming",
    "sorting",
    "greedy",
    "depth-first-search",
    "binary-search",
    "database",
    "breadth-first-search",
    "tree",
    "matrix",
    "two-pointers",
    "binary-tree",
    "bit-manipulation",
    "heap-priority-queue",
    "stack",
    "prefix-sum",
    "graph",
    "design",
    "simulation",
    "counting",
    "backtracking",
    "sliding-window",
    "union-find",
    "linked-list",
    "ordered-set",
    "monotonic-stack",
    "enumeration",
    "recursion",
    "trie",
    "divide-and-conquer",
    "binary-search-tree",
    "bitmask",
    "queue",
    "number-theory",
    "memoization",
    "segment-tree",
    "geometry",
    "topological-sort",
    "binary-indexed-tree",
    "hash-function",
    "game-theory",
    "shortest-path",
    "combinatorics",
    "data-stream",
    "interactive",
    "string-matching",
    "rolling-hash",
    "brainteaser",
    "randomized",
    "monotonic-queue",
    "merge-sort",
    "iterator",
    "concurrency",
    "doubly-linked-list",
    "probability-and-statistics",
    "quickselect",
    "bucket-sort",
    "suffix-array",
    "minimum-spanning-tree",
    "counting-sort",
    "shell",
    "line-sweep",
    "reservoir-sampling",
    "eulerian-circuit",
    "radix-sort",
    "strongly-connected-component",
    "rejection-sampling",
    "biconnected-component",
]


def query(payload):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }

    get = requests.post("https://leetcode.com/graphql/",
                        json=payload,
                        headers=headers
                        )
    return get.json()


def get_random_problem(difficulty, language):
    content_payload = {
        "query": "\n    query questionContent($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    content\n    mysqlSchemas\n  }\n}\n    ",
        "variables": {"titleSlug": "two-sum"}, "operationName": "questionContent"
    }
    test_cases_payload = {
        "query": "\n    query consolePanelConfig($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    questionTitle\n    enableDebugger\n    enableRunCode\n    enableSubmit\n    enableTestMode\n    exampleTestcaseList\n    metaData\n  }\n}\n    ",
        "variables": {"titleSlug": "two-sum"}, "operationName": "consolePanelConfig"}
    snippet_payload = {
        "query": "\n    query questionEditorData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    codeSnippets {\n      lang\n      langSlug\n      code\n    }\n    envInfo\n    enableRunCode\n  }\n}\n    ",
        "variables": {
            "titleSlug": "add-two-numbers"
        },
        "operationName": "questionEditorData"
    }

    while True:  # Retry
        titleSlug = query(payload={
            "query": "\n    query randomQuestion($categorySlug: String, $filters: QuestionListFilterInput) {\n  randomQuestion(categorySlug: $categorySlug, filters: $filters) {\n    titleSlug\n  }\n}\n    ",
            "variables":
                {
                    "categorySlug": "",
                    "filters": {
                        "difficulty": f"{difficulty}"
                    }
                },
            "operationName": "randomQuestion"})["data"]["randomQuestion"]["titleSlug"]

        # Code Snippet Prompt
        snippet_payload["variables"]["titleSlug"] = titleSlug
        snippet_resp = query(snippet_payload)
        snippets = snippet_resp["data"]["question"]["codeSnippets"]
        questionId = snippet_resp["data"]["question"]["questionId"]

        # Question Content
        content_payload["variables"]["titleSlug"] = titleSlug
        content_resp = query(content_payload)
        q_content = content_resp["data"]["question"]["content"]

        # Test Cases
        test_cases_payload["variables"]["titleSlug"] = titleSlug
        test_cases_resp = query(test_cases_payload)
        test_cases = test_cases_resp["data"]["question"]["exampleTestcaseList"]

        lang_index = languages.index(language)
        if lang_index < 0:
            continue
        try:
            prompt_snippet = snippets[lang_index]["code"]
        except IndexError:
            continue  # If language is not found for it.

        return {
            "title": titleSlug.replace("-", " ").title(),
            "titleSlug": titleSlug,
            "questionId": questionId,
            "content": q_content,
            "test_cases": test_cases,
            "prompt_snippet": prompt_snippet
        }


def send_solution(language, question_id, title_id, typed_code):
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "origin": "https://leetcode.com",
        "referer": "https://leetcode.com/problems/two-sum/submissions/",
        "x-csrftoken": "9jokfyWLmfapayIzHOhYefYdQN7VOVDgMma3qJkr9xgyvbg2Fh53Iih8OtnZzTSK",
        "cookie": 'csrftoken=9jokfyWLmfapayIzHOhYefYdQN7VOVDgMma3qJkr9xgyvbg2Fh53Iih8OtnZzTSK; '
                  'LEETCODE_SESSION=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiODg4MTYwOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiZGY4YjcyMzliNGE3NTM1NWNlOGViYzlkMmYyMWZiYTY0NmVhMGU4ZCIsImlkIjo4ODgxNjA5LCJlbWFpbCI6ImJlbmFzdGFobEBnbWFpbC5jb20iLCJ1c2VybmFtZSI6ImJlbmFzdGFobCIsInVzZXJfc2x1ZyI6ImJlbmFzdGFobCIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNvbS91c2Vycy9hdmF0YXJzL2F2YXRhcl8xNjc3NzMwMTk1LnBuZyIsInJlZnJlc2hlZF9hdCI6MTY4NDg1NTUwMiwiaXAiOiIyNjA1OjY0NDA6NDAxMTpjMDAxOjozYTFmIiwiaWRlbnRpdHkiOiIzNWRhZDcwYWJjNjAxZTIyOWUxMTVkMjAwY2I5YTBiYSIsInNlc3Npb25faWQiOjM4ODAzNjY1LCJfc2Vzc2lvbl9leHBpcnkiOjEyMDk2MDB9.aSLwwu1OTuN8MkbOhIeFNwgsOW-URRHQeh915VAa1d8; ',
    }
    submit = requests.post(
        f"https://leetcode.com/problems/{title_id}/submit/",
        json={
            "lang": language.lower(),
            "question_id": question_id,
            "typed_code": typed_code
        },
        headers=headers
    )

    if submit.status_code != 200:
        print(submit.text)
        print(f"Failed to submit solution ({submit.status_code}).")
        return

    submission_id = submit.json()["submission_id"]

    pending = True
    check = None
    while pending:  # Server processing solution response.
        check = requests.get(
            f"https://leetcode.com/submissions/detail/{submission_id}/check/",
            headers=headers
        )

        if check.status_code != 200:
            print(f"Failed to check solution ({check.status_code})")
            return

        pending = check.json().get("state") != "SUCCESS"
        time.sleep(2)
    return check.json()


if __name__ == '__main__':
    r = get_random_problem(difficulty="EASY", language="Python3")
    print(r)
