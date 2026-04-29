from __future__ import annotations

from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from app.schemas.enums import RssFeedRuntimeStatus


_RSS_FEED_RUNTIME_STATUS_ENUM = sa.Enum(
    RssFeedRuntimeStatus,
    name="rss_feed_runtime_status",
    values_callable=lambda enum_class: [member.value for member in enum_class],
)


class RssFeedRuntime(Base):
    __tablename__ = "rss_feed_runtime"
    __table_args__ = (
        sa.CheckConstraint(
            "consecutive_error_count >= 0",
            name="ck_rss_feed_runtime_consecutive_error_count",
        ),
        sa.CheckConstraint(
            "last_error_code IS NULL OR (last_error_code >= 100 AND last_error_code <= 599)",
            name="ck_rss_feed_runtime_last_error_code",
        ),
        sa.Index("idx_rss_feed_runtime_last_status", "last_status"),
        sa.Index(
            "idx_rss_feed_runtime_last_article_published_at",
            "last_article_published_at",
        ),
    )

    feed_id: Mapped[int] = mapped_column(
        sa.ForeignKey("rss_feeds.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_scraped_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    last_status: Mapped[RssFeedRuntimeStatus] = mapped_column(
        _RSS_FEED_RUNTIME_STATUS_ENUM,
        nullable=False,
        server_default=sa.text("'pending'::rss_feed_runtime_status"),
    )
    etag: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    last_feed_update: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    last_article_published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    consecutive_error_count: Mapped[int] = mapped_column(
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
    )
    last_error_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    feed: Mapped["RssFeed"] = relationship("RssFeed", back_populates="runtime")
