from __future__ import annotations

import logging
from typing import Callable

from src.domain import commands, events, exceptions, model
from src.service_layer import unit_of_work

logger = logging.getLogger(__name__)


# --- Command handlers ---


def register_user(cmd: commands.RegisterUser, uow: unit_of_work.AbstractUnitOfWork, hash_password: Callable[[str], str]) -> int:
    # Preconditions
    if uow.users.get_by_email(cmd.email):
        raise exceptions.UserExists(f"User with email {cmd.email} already exists")
    if cmd.username and uow.users.get_by_username(cmd.username):
        raise exceptions.UserExists(f"Username {cmd.username} already exists")

    # Derive username if missing
    username = cmd.username or cmd.email.split("@")[0]
    user_id = uow.users._next_id if hasattr(uow.users, "_next_id") else None  # placeholder for fakes
    user_entity = model.User(id=user_id or 0, email=cmd.email, username=username)
    user_agg = model.UserAggregate(
        user=user_entity,
        bio=cmd.bio,
        location=cmd.location,
        avatar_url=cmd.avatar_url,
        password_hash=hash_password(cmd.password),
    )
    uow.users.add(user_agg)
    # Emit event on aggregate
    events_list = getattr(user_agg, "events", None)
    if events_list is None:
        user_agg.events = []  # type: ignore[attr-defined]
    user_agg.events.append(events.UserRegistered(user_id=user_entity.id, email=cmd.email, username=username))  # type: ignore[attr-defined]

    uow.commit()
    return user_entity.id


def create_post(cmd: commands.CreatePost, uow: unit_of_work.AbstractUnitOfWork) -> int:
    user = uow.users.get(cmd.user_id)
    if not user:
        raise exceptions.Unauthorized("User not found")

    post = model.PostAggregate(
        id=cmd.post_id,
        user_id=cmd.user_id,
        username=cmd.username,
        body=cmd.body,
    )
    uow.posts.add(post)
    _ensure_events_list(post).append(events.PostCreated(post_id=cmd.post_id, user_id=cmd.user_id, username=cmd.username))
    uow.commit()
    return post.id


def add_comment(cmd: commands.AddComment, uow: unit_of_work.AbstractUnitOfWork) -> int:
    post = uow.posts.get(cmd.post_id)
    if not post:
        raise exceptions.PostNotFound(f"Post {cmd.post_id} not found")
    # Let the repository assign IDs; use a placeholder (None) in the aggregate
    comment = post.add_comment(comment_id=None, user_id=cmd.user_id, body=cmd.body)
    # Persist post/comment to get DB-generated ID
    uow.posts.save(post)
    # Collect the actual ID after save if available
    new_id = getattr(uow.posts, "last_comment_id", None) or getattr(comment, "id", None) or cmd.comment_id
    _ensure_events_list(post).append(
        events.CommentAdded(post_id=cmd.post_id, comment_id=new_id, user_id=cmd.user_id)
    )
    uow.commit()
    return new_id


def toggle_like(cmd: commands.ToggleLike, uow: unit_of_work.AbstractUnitOfWork):
    post = uow.posts.get(cmd.post_id)
    if not post:
        raise exceptions.PostNotFound(f"Post {cmd.post_id} not found")
    result = post.toggle_like(user_id=cmd.user_id)
    liked = result is not None
    _ensure_events_list(post).append(events.LikeToggled(post_id=cmd.post_id, user_id=cmd.user_id, liked=liked))
    uow.commit()
    return liked


def upload_file(cmd: commands.UploadFile, uow: unit_of_work.AbstractUnitOfWork, file_storage: Callable[[str, str], str]) -> str:
    file_url = file_storage(cmd.local_path, cmd.file_name)
    # No aggregate here; emit a standalone event
    standalone = type("Standalone", (), {"events": []})()
    standalone.events.append(events.FileUploaded(file_name=cmd.file_name, file_url=file_url))
    # collect_new_events will not see this; just return the event in results
    uow.commit()
    return file_url


def update_profile(cmd: commands.UpdateProfile, uow: unit_of_work.AbstractUnitOfWork):
    user = uow.users.get(cmd.user_id)
    if not user:
        raise exceptions.Unauthorized("User not found")
    user.update_profile(bio=cmd.bio, location=cmd.location, avatar_url=cmd.avatar_url)
    uow.users.save(user)
    uow.commit()
    return user.user.id


def change_password(cmd: commands.ChangePassword, uow: unit_of_work.AbstractUnitOfWork):
    user = uow.users.get(cmd.user_id)
    if not user:
        raise exceptions.Unauthorized("User not found")
    user.change_password(cmd.new_password_hash)
    uow.users.save(user)
    _ensure_events_list(user).append(events.PasswordChanged(user_id=cmd.user_id))
    uow.commit()
    return user.user.id


def delete_account(cmd: commands.DeleteAccount, uow: unit_of_work.AbstractUnitOfWork):
    user = uow.users.get(cmd.user_id)
    if not user:
        raise exceptions.Unauthorized("User not found")
    # Real impl would cascade deletions; for now, just drop the aggregate
    uow.users._delete(cmd.user_id) if hasattr(uow.users, "_delete") else None  # type: ignore[attr-defined]
    uow.commit()
    return cmd.user_id


# --- Event handlers (stubs/placeholders) ---


def handle_user_registered(event: events.UserRegistered, uow: unit_of_work.AbstractUnitOfWork, notifier=None):
    logger.info("User registered: %s", event)
    if notifier:
        notifier.send(
            to=event.email,
            subject="Welcome to Matrix-Net",
            body=f"Hi {event.username}, your account has been created.",
        )


def handle_file_uploaded(event: events.FileUploaded, uow: unit_of_work.AbstractUnitOfWork):
    logger.info("File uploaded: %s", event.file_url)
    # Placeholder for side-effects (e.g., store metadata)


# --- Helpers ---


def _ensure_events_list(aggregate) -> list:
    if not hasattr(aggregate, "events") or getattr(aggregate, "events") is None:
        aggregate.events = []  # type: ignore[attr-defined]
    return aggregate.events  # type: ignore[attr-defined]
