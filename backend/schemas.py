from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MidiFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_hash: str
    filename: str
    source_url: str
    page_url: str | None
    source_name: str
    title: str | None
    composer: str | None
    genre: str | None
    bpm: float | None
    duration_sec: float | None
    track_count: int | None
    time_signature: str | None
    scraped_at: datetime
    file_size: int | None
    play_count: int


class MidiFileList(BaseModel):
    items: list[MidiFileSchema]
    total: int
    page: int
    limit: int


class ScrapeSourceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    display_name: str
    base_url: str
    last_scraped: datetime | None
    file_count: int
    error_count: int
    enabled: bool


class ScrapeErrorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_name: str
    url: str | None
    error_msg: str
    occurred_at: datetime


class AgentRunStepSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tool_name: str
    tool_input: str
    tool_result: str | None
    executed_at: datetime


class AgentRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    files_added: int
    summary: str | None
    steps: list[AgentRunStepSchema] = []
