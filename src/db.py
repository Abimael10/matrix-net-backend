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
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("bio", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("location", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("avatar_url", sqlalchemy.String, nullable=True),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),
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
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
    sqlalchemy.UniqueConstraint("post_id", "user_id", name="uq_likes_post_user"),
)

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column("post_id", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
    # Denormalized username snapshot to avoid joins and preserve history on username change
    sqlalchemy.Column("username", sqlalchemy.ForeignKey("users.username")),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),
)

connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URI else {}
engine = sqlalchemy.create_engine(config.DATABASE_URI, connect_args=connect_args)

metadata.create_all(engine)
database = databases.Database(
    config.DATABASE_URI, force_rollback=config.DB_FORCE_ROLL_BACK
)

# Only run runtime migrations for SQLite (dev/test convenience)
if "sqlite" in config.DATABASE_URI:
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
        # Ensure unique like per user per post
        like_indexes = {idx["name"] for idx in inspector.get_indexes("likes")}
        if "uq_likes_post_user" not in like_indexes:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_likes_post_user ON likes (post_id, user_id)"
                )
            )
        # Ensure users table has expected columns
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "bio" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN bio VARCHAR"))
        if "location" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR"))
        if "avatar_url" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
        if "created_at" not in user_columns:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"
                )
            )
        # Ensure comments table has expected columns
        comment_columns = {col["name"] for col in inspector.get_columns("comments")}
        if "created_at" not in comment_columns:
            conn.execute(
                text(
                    "ALTER TABLE comments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"
                )
            )
        if "username" not in comment_columns:
            # username is optional (nullable) to support existing rows
            conn.execute(text("ALTER TABLE comments ADD COLUMN username VARCHAR"))
