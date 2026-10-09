from typing import Any

from sigma.collection import SigmaCollection
from sigma.processing.resolver import ProcessingPipelineResolver

from app.registry import BACKENDS, PIPELINES


class ApiInputError(ValueError):
    """An input error that should be returned to the API caller."""


def parse_sigma(sigma_yaml: str) -> SigmaCollection:
    return SigmaCollection.from_yaml(sigma_yaml)


def resolve_pipeline(pipeline_ids: list[str]):
    if not pipeline_ids:
        return None

    resolver = ProcessingPipelineResolver()
    for pipeline_id in pipeline_ids:
        definition = PIPELINES.get(pipeline_id)
        if definition is None:
            raise ApiInputError(f"Unknown pipeline: {pipeline_id}")
        resolver.add_pipeline_class(definition.factory())

    return resolver.resolve(resolver.pipelines)


def normalize_output(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def convert_sigma(
    sigma_yaml: str,
    backend_id: str,
    pipeline_ids: list[str],
    output_format: str,
    backend_options: dict[str, Any] | None = None,
) -> tuple[SigmaCollection, list[Any]]:
    definition = BACKENDS.get(backend_id)
    if definition is None:
        raise ApiInputError(f"Unknown backend: {backend_id}")

    if output_format not in definition.formats:
        raise ApiInputError(
            f"Unsupported format '{output_format}' for backend '{backend_id}'. "
            f"Supported formats: {', '.join(definition.formats)}"
        )

    collection = parse_sigma(sigma_yaml)
    pipeline = resolve_pipeline(pipeline_ids)
    options = backend_options or {}

    # All supported pySigma backends accept the processing pipeline as the
    # first argument. Keyword backend options are passed through explicitly.
    backend = definition.backend_class(pipeline, **options)
    converted = backend.convert(collection, output_format=output_format)
    return collection, normalize_output(converted)
