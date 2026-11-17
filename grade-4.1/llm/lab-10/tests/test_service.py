import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from decide.service import Predictor, app, get_predictor

CANONICAL = json.loads((Path(__file__).parents[1] / "canonical_request.json").read_text())


@pytest.fixture
def served(tokenizer, toy_model):
    app.dependency_overrides[get_predictor] = lambda: Predictor(toy_model, tokenizer, "decide-toy")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_canonical_request(served):
    response = served.post("/v1/systemone", json=CANONICAL)
    assert response.status_code == 200
    body = response.json()
    answers = body["answers"]
    assert set(answers) == set(CANONICAL["questions"])
    assert {key: a["type"] for key, a in answers.items()} == {
        key: q["type"] for key, q in CANONICAL["questions"].items()
    }
    assert 0.0 <= answers["wants_refund"]["noul"] <= 1.0
    department = answers["department"]
    assert set(department["probabilities"]) == set(CANONICAL["questions"]["department"]["criteria"])
    assert list(department["probabilities"].values()) == sorted(
        department["probabilities"].values(), reverse=True
    )
    assert department["choice"] == next(iter(department["probabilities"]))
    assert abs(sum(department["probabilities"].values()) - 1) < 1e-3
    frustration = answers["frustration"]
    assert 0.0 <= frustration["score"] <= 2.0
    assert list(frustration["probabilities"]) == list(frustration["legend"]) == ["0", "1", "2"]
    assert body["usage"]["output_tokens"] == 0
    assert body["usage"]["input_tokens"] > 0
    assert served.get("/health").json() == {"status": "ok"}


def over_limit_requests():
    def changed(path, value):
        request = copy.deepcopy(CANONICAL)
        target = request
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return request

    many = {f"q{i}": {"type": "noul", "instructions": "is it"} for i in range(17)}
    yield changed(["questions"], {})
    yield changed(["questions"], many)
    yield changed(["questions", "department", "criteria"], {"billing": "only one"})
    yield changed(["questions", "department", "criteria"], {f"k{i}": "x" for i in range(27)})
    yield changed(["questions", "frustration", "criteria"], ["one level"])
    yield changed(["questions", "frustration", "criteria"], [str(i) for i in range(11)])
    yield changed(["questions", "wants_refund", "type"], "essay")
    yield changed(["questions", "wants_refund", "instructions"], "is it " * 600)


@pytest.mark.parametrize("request_body", list(over_limit_requests()))
def test_over_limit_requests_return_422(served, request_body):
    assert served.post("/v1/systemone", json=request_body).status_code == 422
