"""Jama API client — demonstrates orphaned raise-site exceptions.

Exception classes are defined elsewhere (not in this file). They are imported
here and raised — so raise-site extraction picks up the class names, but they
are NOT in this file's public-symbol surface.
"""
from jama.exceptions import (
    JamaArtifactTypeError,
    JamaValueMapError,
    JamaSkippedValueError,
)


def authenticate(user, token):
    if not user:
        raise JamaAuthError("user required")
    return token


def fetch_artifact(artifact_id):
    if artifact_id is None:
        raise JamaArtifactTypeError("artifact id required")
    return {}


def fetch_value_map(map_id):
    if map_id is None:
        raise JamaValueMapError("map id required")
    return {}


def skip_artifact(reason):
    raise JamaSkippedValueError(reason)


class JamaClient:
    def call(self, endpoint):
        return endpoint
