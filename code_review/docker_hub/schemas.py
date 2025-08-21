from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Image(BaseModel):
    architecture: str
    features: str
    variant: Optional[str]
    digest: str | None = None
    os: str
    os_features: str
    os_version: Optional[str]
    size: int
    status: str
    last_pulled: str | None = None
    last_pushed: str | None = None


class ImageTag(BaseModel):
    creator: int
    id: int
    images: list[Image]
    last_updated: str
    last_updater: int
    last_updater_username: str
    name: str
    repository: int
    full_size: int
    v2: bool
    tag_status: str
    tag_last_pulled: str | None
    tag_last_pushed: str
    media_type: str | None = None
    content_type: str | None = None
    digest: str | None = None