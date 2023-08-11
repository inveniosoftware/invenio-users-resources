# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-Users-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Decorators for users services."""

from functools import wraps
from inspect import getfullargspec

from flask import current_app
from invenio_cache.errors import LockedError
from invenio_cache.lock import CachedMutex


def parse_from_args_or_kwargs(arg_name, args_spec, args, kwargs):
    """Retrieves the value of an argument if the argument exists either in `kwargs` or `args`.

    :param arg_name: The name of the argument to retrieve.
    :type arg_name: str
    :param args_spec: The argument specification object, typically obtained from `inspect.getfullargspec(function_name)`. It contains information about the function's arguments.
    :type args_spec: ``inspect.ArgSpec``
    :param args: The list of positional arguments.
    :type args: list
    :param kwargs: The dictionary of keyword arguments.
    :type kwargs: dict

    .. note::

        This function assumes that `arg_name` exists either in `kwargs` or `args`. If the argument is not
        present in either, it will return None.
    """
    if arg_name in kwargs:
        return kwargs[arg_name]

    # Try to retrieve from args
    try:
        idx = args_spec.args.index(arg_name)
        return args[idx]
    except ValueError:
        pass
    return None


def lock_user_moderation(lock_prefix, arg_name, timeout):
    """Decorator to lock a user moderation execution for only one action at the time.

    The lock is not released at the end of the function, since moderation actions have callbacks that
    run asynchornously.
    The idea of this strategy is to create a short lock that can later be reused by another execution
    thread (e.g. a celery task).
    If the lock is not renewed afterwards, it will automatically expire after some seconds.

    The value of the user_id is retrieved from ``parse_from_args_or_kwargs``.

    :param lock_prefix: The prefix of the lock ID.
    :param arg_name: name of the identifier parameter, fetched from either ``args`` or ``kwargs`` of the decorated function.
    :type arg_name: str
    :param timeout: Timeout, in seconds, for the lock to be automatically released.
    """

    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            identifier = parse_from_args_or_kwargs(
                arg_name, getfullargspec(f), args, kwargs
            )
            assert identifier, f"{arg_name} not found in function kwargs or args."

            lock_id = f"{lock_prefix}.{identifier}"
            lock = CachedMutex(lock_id)
            try:
                if lock.acquire(timeout=timeout):
                    return f(*args, **kwargs)
                else:
                    current_app.logger.debug(
                        f"Resource with lock {lock.lock_id} is already locked."
                    )
                    raise LockedError(lock)
            except:
                lock.release()
                raise

        return decorate

    return decorator_builder
