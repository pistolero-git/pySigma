from dataclasses import dataclass, field
from typing import Any, Callable

from sigma.backends.elasticsearch import LuceneBackend
from sigma.backends.opensearch import OpensearchLuceneBackend
from sigma.backends.opensearch.opensearch_ppl import OpenSearchPPLBackend
from sigma.backends.splunk import SplunkBackend
from sigma.pipelines.elasticsearch.windows import ecs_windows
from sigma.pipelines.splunk import splunk_windows_pipeline
from sigma.pipelines.sysmon import sysmon_pipeline


PipelineFactory = Callable[[], Any]


@dataclass(frozen=True)
class PipelineDefinition:
    id: str
    name: str
    description: str
    factory: PipelineFactory


@dataclass(frozen=True)
class BackendDefinition:
    id: str
    name: str
    description: str
    backend_class: type
    formats: tuple[str, ...]
    recommended_pipelines: tuple[str, ...] = field(default_factory=tuple)


PIPELINES: dict[str, PipelineDefinition] = {
    "splunk_windows": PipelineDefinition(
        id="splunk_windows",
        name="Splunk Windows",
        description="Splunk Windows log source field mappings.",
        factory=splunk_windows_pipeline,
    ),
    "ecs_windows": PipelineDefinition(
        id="ecs_windows",
        name="Elastic Common Schema - Windows",
        description="Maps Windows fields to ECS/Winlogbeat fields.",
        factory=ecs_windows,
    ),
    "sysmon": PipelineDefinition(
        id="sysmon",
        name="Sysmon",
        description="Generic Sysmon processing pipeline.",
        factory=sysmon_pipeline,
    ),
}


BACKENDS: dict[str, BackendDefinition] = {
    "splunk": BackendDefinition(
        id="splunk",
        name="Splunk",
        description="Splunk Search Processing Language (SPL).",
        backend_class=SplunkBackend,
        formats=("default", "savedsearches"),
        recommended_pipelines=("splunk_windows",),
    ),
    "elasticsearch": BackendDefinition(
        id="elasticsearch",
        name="Elasticsearch Lucene",
        description="Elasticsearch Lucene query syntax.",
        backend_class=LuceneBackend,
        formats=("default",),
        recommended_pipelines=("ecs_windows",),
    ),
    "opensearch": BackendDefinition(
        id="opensearch",
        name="OpenSearch Lucene",
        description="OpenSearch Lucene query syntax and monitor output.",
        backend_class=OpensearchLuceneBackend,
        formats=("default", "monitor_rule", "dsl_lucene"),
        recommended_pipelines=("ecs_windows",),
    ),
    "opensearch-ppl": BackendDefinition(
        id="opensearch-ppl",
        name="OpenSearch PPL",
        description="OpenSearch Piped Processing Language (PPL), including Sigma correlations.",
        backend_class=OpenSearchPPLBackend,
        formats=("default",),
        recommended_pipelines=(),
    ),
}
