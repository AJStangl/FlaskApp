from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class BaseRecord:
    PartitionKey: Optional[str] = None
    RowKey: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    hash: Optional[str] = None
    remote_path: Optional[str] = None
    remote_exists: Optional[bool] = None
    local_path: Optional[str] = None
    local_exists: Optional[bool] = None
    source: Optional[str] = None
    curated: Optional[bool] = False
    accepted: Optional[bool] = False


@dataclass
class StageRecord(BaseRecord):
    pass


@dataclass
class CuratedRecord(BaseRecord):
    pass


@dataclass
class EnrichedRecord(BaseRecord):
    caption: Optional[str] = None
    captions: Optional[str] = None
    tags: Optional[str] = None


@dataclass
class TagRecord:
    PartitionKey: Optional[str] = None
    RowKey: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    confidence: Optional[float] = None



def convert_to_curated_record(record: BaseRecord) -> CuratedRecord:
    return CuratedRecord(**asdict(record))


def convert_to_stage_record(record: BaseRecord) -> StageRecord:
    return StageRecord(**asdict(record))


def convert_to_enriched_record(record: BaseRecord) -> EnrichedRecord:
    return EnrichedRecord(**asdict(record))