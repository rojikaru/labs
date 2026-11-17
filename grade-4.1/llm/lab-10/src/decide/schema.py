from typing import Annotated, Literal

from pydantic import BaseModel, Field

Probability = Annotated[float, Field(ge=0.0, le=1.0)]


class NoulQuestion(BaseModel):
    type: Literal["noul"]
    instructions: str


class ChoiceQuestion(BaseModel):
    type: Literal["choice"]
    instructions: str
    criteria: Annotated[dict[str, str], Field(min_length=2, max_length=26)]


class ScoreQuestion(BaseModel):
    type: Literal["score"]
    instructions: str
    criteria: Annotated[list[str], Field(min_length=2, max_length=10)]


Question = Annotated[NoulQuestion | ChoiceQuestion | ScoreQuestion, Field(discriminator="type")]


class Request(BaseModel):
    model: str = "jev-latest"
    state: str
    questions: Annotated[dict[str, Question], Field(min_length=1, max_length=16)]


class NoulAnswer(BaseModel):
    type: Literal["noul"] = "noul"
    noul: Probability


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    choice: str
    probabilities: dict[str, Probability]
    confidence: Probability


class ScoreAnswer(BaseModel):
    type: Literal["score"] = "score"
    score: Annotated[float, Field(ge=0.0)]
    confidence: Probability
    probabilities: dict[str, Probability]
    legend: dict[str, str]


Answer = Annotated[NoulAnswer | ChoiceAnswer | ScoreAnswer, Field(discriminator="type")]


class Usage(BaseModel):
    input_tokens: int
    output_tokens: Literal[0] = 0


class Response(BaseModel):
    model: str
    answers: dict[str, Answer]
    usage: Usage
