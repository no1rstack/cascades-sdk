from cascades_sdk import CascadesClient, CascadeClient


def test_alias_types_match():
    assert CascadeClient is CascadesClient
