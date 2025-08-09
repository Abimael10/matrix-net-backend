import databases
import sqlalchemy
from sqlalchemy import text
from src.config import config

metadata = sqlalchemy.MetaData()

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False)
)

post_table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
    sqlalchemy.Column("username", sqlalchemy.ForeignKey("users.username")),
    sqlalchemy.Column("image_url", sqlalchemy.String),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),
)

likes_table = sqlalchemy.Table(
    "likes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("post_id", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False)
)

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column("post_id", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False)
)

connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URI else {}
engine = sqlalchemy.create_engine(
    config.DATABASE_URI, connect_args=connect_args
)

metadata.create_all(engine)
database = databases.Database(
    config.DATABASE_URI, force_rollback = config.DB_FORCE_ROLL_BACK
)

# Lightweight runtime migration to add missing columns (dev/test convenience)
with engine.begin() as conn:
    inspector = sqlalchemy.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("posts")}
    if "created_at" not in columns:
        # SQLite-compatible
        conn.execute(
            text(
                "ALTER TABLE posts ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"
            )
        )