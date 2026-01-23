from enum import Enum


class AccessPolicy(str, Enum):
    STANDARD = "standard"
    PUBLIC = "public"
