from app.domain.enums import (
    DurationBucket,
    HireType,
    InteractionChannel,
    InteractionSource,
    InteractionType,
    RecommendationType,
    RelationshipState,
)


def test_canonical_enum_values_match_the_frozen_specification() -> None:
    assert list(RelationshipState) == [
        RelationshipState.NEW,
        RelationshipState.CLOSE,
        RelationshipState.ACTIVE,
        RelationshipState.WEAK,
        RelationshipState.DORMANT,
        RelationshipState.RECONNECTED,
    ]
    assert list(HireType) == [HireType.GRADUATE, HireType.EXPERIENCED, HireType.OTHER]
    assert list(RecommendationType) == [
        RecommendationType.RECONNECT,
        RecommendationType.DISCOVER,
        RecommendationType.KEEP_IN_TOUCH,
        RecommendationType.RAMP,
        RecommendationType.WELCOME,
        RecommendationType.INTRODUCE,
    ]
    assert list(InteractionChannel) == [
        InteractionChannel.DIGITAL,
        InteractionChannel.ANALOG,
    ]
    assert list(InteractionSource) == [
        InteractionSource.SYSTEM,
        InteractionSource.SELF_REPORTED,
        InteractionSource.MUTUAL_CONFIRMED,
        InteractionSource.INFERRED,
    ]
    assert [value.value for value in InteractionType] == [
        "TEAMS_CHAT",
        "EMAIL",
        "ONLINE_1ON1",
        "GROUP_MEETING",
        "OFFICE_CHAT",
        "COFFEE",
        "LUNCH",
        "DINNER",
        "COMMUNITY",
        "ACTIVITY",
        "OTHER",
    ]
    assert list(DurationBucket) == [
        DurationBucket.SHORT,
        DurationBucket.MEDIUM,
        DurationBucket.LONG,
    ]
