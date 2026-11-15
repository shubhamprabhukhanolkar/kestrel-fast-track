from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

FIELDS = ("credits", "debits", "average_balance", "gstr1", "gstr3b")


class Citation(BaseModel):
    source_doc: str
    page_number: int = Field(ge=1)
    line_ref: str
    raw_text_quote: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class Cell(BaseModel):
    month: str
    field: Literal["credits", "debits", "average_balance", "gstr1", "gstr3b"]
    value: float = Field(ge=0, allow_inf_nan=False)
    citation: Citation


class Extraction(BaseModel):
    cells: list[Cell] = Field(min_length=60, max_length=60)


class Memo(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class PromptUpdate(BaseModel):
    content: str = Field(min_length=20, max_length=16000)


class PolicyUpdate(BaseModel):
    gst_variance_threshold_pct: float = Field(ge=0, le=100, allow_inf_nan=False)


class VerifyCell(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    cell_id: int
    value: float = Field(ge=0, allow_inf_nan=False)
    reason: str = Field(min_length=5, max_length=2000)


class Decision(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    outcome: Literal["approve", "return_to_rm", "decline"]
    signature: str = Field(min_length=3)
    rationale: str = Field(min_length=30, max_length=5000)


class FailoverConfig(BaseModel):
    simulate_503: bool = False
    simulate_429: bool = False


class TonePreview(BaseModel):
    case_id: str = "KF-2026-0892"
    tone: Literal[
        "Strict CRO Regulatory Memo",
        "Concise Analyst Dossier",
        "Polite RM Document Chaser",
    ] = "Concise Analyst Dossier"


class Login(BaseModel):
    persona: Literal["vikram", "meena", "arjun", "farhan"]
    password: str = Field(default="", max_length=256)
