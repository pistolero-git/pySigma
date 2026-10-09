from typing import Any
from pydantic import BaseModel, Field, field_validator


class ValidateRequest(BaseModel):
    sigma: str = Field(..., min_length=1, description="Sigma YAML. Multiple YAML documents are supported.")


class ValidationIssue(BaseModel):
    type: str
    message: str


class ValidateResponse(BaseModel):
    valid: bool
    rule_count: int = 0
    titles: list[str] = Field(default_factory=list)
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


class ConvertRequest(BaseModel):
    sigma: str = Field(..., min_length=1)
    backend: str = Field(..., min_length=1, examples=["splunk"])
    pipelines: list[str] = Field(default_factory=list, examples=[["splunk_windows"]])
    format: str = Field(default="default")
    backend_options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("backend", "format")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("pipelines")
    @classmethod
    def normalize_pipelines(cls, values: list[str]) -> list[str]:
        return [value.strip().lower() for value in values]


class ConvertResponse(BaseModel):
    success: bool
    backend: str
    pipelines: list[str]
    format: str
    rule_count: int
    output: list[Any]
    warnings: list[str] = Field(default_factory=list)


class PipelineInfo(BaseModel):
    id: str
    name: str
    description: str


class BackendInfo(BaseModel):
    id: str
    name: str
    description: str
    formats: list[str]
    recommended_pipelines: list[str] = Field(default_factory=list)


class CatalogResponse(BaseModel):
    backends: list[BackendInfo]
    pipelines: list[PipelineInfo]
