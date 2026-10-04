from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(title) <> ''", name=op.f("ck_notes_title_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
    )
    op.create_index("ix_notes_created_at", "notes", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notes_created_at", table_name="notes")
    op.drop_table("notes")
