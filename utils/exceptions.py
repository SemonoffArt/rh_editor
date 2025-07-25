#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bot Errors Module."""


class IllegalArgumentError(Exception):
    pass


class CameraBotError(Exception):
    pass


class ConfigError(Exception):
    pass


class TrassirObjectsError(Exception):
    pass


class FileOpenError(Exception):
    pass


class DirFindError(Exception):
    pass


class FileFindError(Exception):
    pass


class UserAuthError(Exception):
    pass


class HikvisionCamError(Exception):
    pass


class ServiceError(Exception):
    pass


class ECS(Exception):
    pass


class ECSWinOpenError(Exception):
    pass


class VNCError(Exception):
    pass


class PLGLoginFault(Exception):
    pass


class PLGOpenPageError(Exception):
    pass
