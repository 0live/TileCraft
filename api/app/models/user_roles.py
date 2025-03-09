from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    MANAGE_TEAMS = "MANAGE_TEAMS"
    MANAGE_ATLASES_AND_MAPS = "MANAGE_ATLASES_AND_MAPS"
    LOAD_DATA = "LOAD_DATA"
    LOAD_ICONS = "LOAD_ICONS"
