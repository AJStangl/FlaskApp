from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PrimaryCuration:
    PartitionKey: Optional[str] = None
    RowKey: Optional[str] = None
    accept: Optional[bool] = None
    author: Optional[str] = None
    caption: Optional[str] = None
    curated: Optional[bool] = None
    exists: Optional[bool] = None
    hash: Optional[str] = None
    id: Optional[str] = None
    image_name: Optional[str] = None
    model: Optional[str] = None
    original_url: Optional[str] = None
    path: Optional[str] = None
    permalink: Optional[str] = None
    subreddit: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None


@dataclass
class SecondaryCuration:
    PartitionKey: Optional[str] = None
    RowKey: Optional[str] = None
    accept: Optional[bool] = None
    additional_captions: Optional[str] = None
    author: Optional[str] = None
    azure_caption: Optional[str] = None
    azure_crop_accept: Optional[bool] = None
    azure_thumbnail_path: Optional[str] = None
    best_caption: Optional[str] = None
    caption: Optional[str] = None
    curated: Optional[bool] = None
    exists: Optional[bool] = None
    hash: Optional[str] = None
    id: Optional[str] = None
    image_name: Optional[str] = None
    large_azure_path: Optional[str] = None
    large_azure_path_exits: Optional[bool] = None
    large_smart_path: Optional[str] = None
    large_smart_path_exits: Optional[bool] = None
    model: Optional[str] = None
    original_url: Optional[str] = None
    path: Optional[str] = None
    permalink: Optional[str] = None
    pil_caption: Optional[str] = None
    pil_crop_accept: Optional[bool] = None
    pil_thumbnail_path: Optional[str] = None
    reddit_caption: Optional[str] = None
    smart_caption: Optional[str] = None
    smart_crop_accept: Optional[bool] = None
    subreddit: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail_accept: Optional[bool] = None
    thumbnail_curated: Optional[bool] = None
    thumbnail_exists: Optional[bool] = None
    thumbnail_path: Optional[str] = None
    title: Optional[str] = None


@dataclass
class Training:
    PartitionKey: Optional[str] = None
    RowKey: Optional[str] = None
    GPT: Optional[str] = None
    caption: Optional[str] = None
    subreddit: Optional[str] = None
    remote_exists: Optional[bool] = None
    local_exists: Optional[bool] = None
    format_caption: Optional[str] = None
    id: Optional[str] = None
    local_path: Optional[str] = None
    remote_path: Optional[str] = None
    tags: Optional[str] = None
    title: Optional[str] = None
    training_count: Optional[int] = None
    type: Optional[str] = None
    captions: Optional[str] = None
