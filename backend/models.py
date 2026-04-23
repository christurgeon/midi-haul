from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship
from backend.database import Base


class MidiFile(Base):
    __tablename__ = "midi_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    page_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    composer: Mapped[str | None] = mapped_column(String, nullable=True)
    genre: Mapped[str | None] = mapped_column(String, nullable=True)
    bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    track_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_signature: Mapped[str | None] = mapped_column(String, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_midi_source", "source_name"),
        Index("idx_midi_scraped", "scraped_at"),
        Index("idx_midi_title", "title"),
    )


class ScrapeSource(Base):
    __tablename__ = "scrape_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    last_scraped: Mapped[datetime | None] = mapped_column(nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)


class ScrapeError(Base):
    __tablename__ = "scrape_errors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    error_msg: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    files_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list["AgentRunStep"]] = relationship("AgentRunStep", back_populates="run")


class AgentRunStep(Base):
    __tablename__ = "agent_run_steps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    tool_input: Mapped[str] = mapped_column(Text, nullable=False)   # JSON string
    tool_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    executed_at: Mapped[datetime] = mapped_column(nullable=False)
    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="steps")
