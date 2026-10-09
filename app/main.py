from importlib.metadata import PackageNotFoundError, version

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import (
    BackendInfo,
    CatalogResponse,
    ConvertRequest,
    ConvertResponse,
    PipelineInfo,
    ValidateRequest,
    ValidateResponse,
    ValidationIssue,
)
from app.registry import BACKENDS, PIPELINES
from app.security import require_api_key
from app.service import ApiInputError, convert_sigma, parse_sigma

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="HTTP API for validating Sigma rules and converting them with pySigma.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        length = request.headers.get("content-length")
        if length is not None:
            try:
                if int(length) > settings.max_sigma_bytes * 2:
                    raise HTTPException(status_code=413, detail="Request body too large")
            except ValueError:
                pass
    return await call_next(request)


@app.get("/health", tags=["system"])
def health():
    try:
        pysigma_version = version("pysigma")
    except PackageNotFoundError:
        pysigma_version = "unknown"
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version, "pysigma": pysigma_version}


@app.get(f"{settings.api_prefix}/catalog", response_model=CatalogResponse, tags=["catalog"])
def catalog(_: None = Depends(require_api_key)):
    return CatalogResponse(
        backends=[
            BackendInfo(
                id=item.id,
                name=item.name,
                description=item.description,
                formats=list(item.formats),
                recommended_pipelines=list(item.recommended_pipelines),
            )
            for item in BACKENDS.values()
        ],
        pipelines=[
            PipelineInfo(id=item.id, name=item.name, description=item.description)
            for item in PIPELINES.values()
        ],
    )


@app.get(f"{settings.api_prefix}/backends", tags=["catalog"])
def backends(_: None = Depends(require_api_key)):
    return catalog(_).backends


@app.get(f"{settings.api_prefix}/pipelines", tags=["catalog"])
def pipelines(_: None = Depends(require_api_key)):
    return catalog(_).pipelines


@app.get(f"{settings.api_prefix}/formats/{{backend_id}}", tags=["catalog"])
def formats(backend_id: str, _: None = Depends(require_api_key)):
    backend = BACKENDS.get(backend_id.lower())
    if backend is None:
        raise HTTPException(status_code=404, detail=f"Unknown backend: {backend_id}")
    return {"backend": backend.id, "formats": list(backend.formats)}


@app.post(f"{settings.api_prefix}/validate", response_model=ValidateResponse, tags=["sigma"])
def validate(request: ValidateRequest, _: None = Depends(require_api_key)):
    if len(request.sigma.encode("utf-8")) > settings.max_sigma_bytes:
        raise HTTPException(status_code=413, detail="Sigma document too large")

    try:
        collection = parse_sigma(request.sigma)
        titles = [str(rule.title) for rule in collection.rules]
        return ValidateResponse(valid=True, rule_count=len(collection.rules), titles=titles)
    except Exception as exc:
        return ValidateResponse(
            valid=False,
            errors=[ValidationIssue(type=exc.__class__.__name__, message=str(exc))],
        )


@app.post(f"{settings.api_prefix}/convert", response_model=ConvertResponse, tags=["sigma"])
def convert(request: ConvertRequest, _: None = Depends(require_api_key)):
    if len(request.sigma.encode("utf-8")) > settings.max_sigma_bytes:
        raise HTTPException(status_code=413, detail="Sigma document too large")

    try:
        collection, output = convert_sigma(
            sigma_yaml=request.sigma,
            backend_id=request.backend,
            pipeline_ids=request.pipelines,
            output_format=request.format,
            backend_options=request.backend_options,
        )
        return ConvertResponse(
            success=True,
            backend=request.backend,
            pipelines=request.pipelines,
            format=request.format,
            rule_count=len(collection.rules),
            output=output,
        )
    except ApiInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"type": exc.__class__.__name__, "message": str(exc)},
        ) from exc
