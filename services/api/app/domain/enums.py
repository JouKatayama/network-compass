from enum import StrEnum


class RelationshipState(StrEnum):
    NEW = "NEW"
    CLOSE = "CLOSE"
    ACTIVE = "ACTIVE"
    WEAK = "WEAK"
    DORMANT = "DORMANT"
    RECONNECTED = "RECONNECTED"


class HireType(StrEnum):
    GRADUATE = "GRADUATE"
    EXPERIENCED = "EXPERIENCED"
    OTHER = "OTHER"


class RecommendationType(StrEnum):
    RECONNECT = "RECONNECT"
    DISCOVER = "DISCOVER"
    KEEP_IN_TOUCH = "KEEP_IN_TOUCH"
    RAMP = "RAMP"
    WELCOME = "WELCOME"
    INTRODUCE = "INTRODUCE"


class InteractionChannel(StrEnum):
    DIGITAL = "DIGITAL"
    ANALOG = "ANALOG"


class InteractionSource(StrEnum):
    SYSTEM = "SYSTEM"
    SELF_REPORTED = "SELF_REPORTED"
    MUTUAL_CONFIRMED = "MUTUAL_CONFIRMED"
    INFERRED = "INFERRED"


class InteractionType(StrEnum):
    TEAMS_CHAT = "TEAMS_CHAT"
    EMAIL = "EMAIL"
    ONLINE_1ON1 = "ONLINE_1ON1"
    GROUP_MEETING = "GROUP_MEETING"
    OFFICE_CHAT = "OFFICE_CHAT"
    COFFEE = "COFFEE"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    COMMUNITY = "COMMUNITY"
    ACTIVITY = "ACTIVITY"
    OTHER = "OTHER"


class DurationBucket(StrEnum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class Visibility(StrEnum):
    PRIVATE = "PRIVATE"
    NETWORK = "NETWORK"
    ORGANIZATION = "ORGANIZATION"
