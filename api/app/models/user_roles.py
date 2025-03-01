from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    MANAGE_TEAMS = "MANAGE_TEAMS"
    MANAGE_ATLASES = "MANAGE_ATLASES"
    LOAD_DATA = "LOAD_DATA"
    LOAD_ICONS = "LOAD_ICONS"
