from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from services.prompt_service import prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptTemplateCreateRequest(BaseModel):
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    name: str
    content: str
    tags: list[str] = Field(default_factory=list)


class PromptTemplateVersionRequest(BaseModel):
    content: str
    tags: list[str] | None = None


class PromptTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    user_id: uuid.UUID | None
    name: str
    version: int
    content: str
    tags: list[str]


class PromptTemplateDiffResponse(BaseModel):
    diff: str


@router.post(
    "",
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt_template(
    payload: PromptTemplateCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PromptTemplateResponse:
    template = await prompt_service.create_template(db, **payload.model_dump())
    return PromptTemplateResponse.model_validate(template)


@router.get("", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    project_id: uuid.UUID | None = None,
    tag: str | None = None,
    latest_only: bool = True,
    db: AsyncSession = Depends(get_db_session),
) -> list[PromptTemplateResponse]:
    templates = await prompt_service.list_templates(
        db,
        project_id=project_id,
        tag=tag,
        latest_only=latest_only,
    )
    return [PromptTemplateResponse.model_validate(template) for template in templates]


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> PromptTemplateResponse:
    template = await prompt_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found.")
    return PromptTemplateResponse.model_validate(template)


@router.post(
    "/{template_id}/versions",
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt_template_version(
    template_id: uuid.UUID,
    payload: PromptTemplateVersionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PromptTemplateResponse:
    template = await prompt_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found.")
    created = await prompt_service.create_version(
        db,
        template=template,
        content=payload.content,
        tags=payload.tags,
    )
    return PromptTemplateResponse.model_validate(created)


@router.get("/{template_id}/diff", response_model=PromptTemplateDiffResponse)
async def diff_prompt_template_versions(
    template_id: uuid.UUID,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db_session),
) -> PromptTemplateDiffResponse:
    template = await prompt_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found.")
    try:
        diff = await prompt_service.diff_versions(
            db,
            template=template,
            from_version=from_version,
            to_version=to_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromptTemplateDiffResponse(diff=diff)


@router.post("/{template_id}/rollback", response_model=PromptTemplateResponse)
async def rollback_prompt_template(
    template_id: uuid.UUID,
    version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db_session),
) -> PromptTemplateResponse:
    template = await prompt_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found.")
    try:
        rolled_back = await prompt_service.rollback(
            db,
            template=template,
            version=version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromptTemplateResponse.model_validate(rolled_back)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    template = await prompt_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found.")
    await prompt_service.delete_template(db, template)
