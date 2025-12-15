from __future__ import annotations

from functools import partial
from typing import Dict, List, Type

from src.adapters.notifications import LogNotifier, AbstractNotifier
from src.adapters.repository import SqlAlchemyPostRepository, SqlAlchemyUserRepository
from src.adapters.storage import AbstractFileStorage, B2FileStorage
from src.domain import commands, events
from src.service_layer import handlers, messagebus, unit_of_work
from src.service_layer.messagebus import MessageBus
from src.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from src import security


def bootstrap(
    uow: unit_of_work.AbstractUnitOfWork | None = None,
    notifier: AbstractNotifier | None = None,
    file_storage: AbstractFileStorage | None = None,
) -> MessageBus:
    uow = uow or SqlAlchemyUnitOfWork()
    notifier = notifier or LogNotifier()
    file_storage = file_storage or B2FileStorage()

    command_handlers: Dict[Type[commands.Command], callable] = {
        commands.RegisterUser: partial(
            handlers.register_user, uow=uow, hash_password=security.get_password_hash
        ),
        commands.CreatePost: partial(handlers.create_post, uow=uow),
        commands.AddComment: partial(handlers.add_comment, uow=uow),
        commands.ToggleLike: partial(handlers.toggle_like, uow=uow),
        commands.UploadFile: partial(handlers.upload_file, uow=uow, file_storage=file_storage.upload),
        commands.UpdateProfile: partial(handlers.update_profile, uow=uow),
        commands.ChangePassword: partial(handlers.change_password, uow=uow),
        commands.DeleteAccount: partial(handlers.delete_account, uow=uow),
    }

    event_handlers: Dict[Type[events.Event], List[callable]] = {
        events.UserRegistered: [partial(handlers.handle_user_registered, uow=uow)],
        events.FileUploaded: [partial(handlers.handle_file_uploaded, uow=uow)],
    }

    return MessageBus(uow=uow, event_handlers=event_handlers, command_handlers=command_handlers)
