"""Upload client — exception hierarchy declared, only two actually raised."""


class UploadAuthError(Exception):
    """Raised on authentication failure."""


class UploadArtifactTypeError(Exception):
    """Declared but never raised — dead class."""


class UploadSkippedValueError(Exception):
    """Declared but never raised — dead class."""


class UploadValueMapError(Exception):
    """Declared but never raised — dead class."""


class UploadTransportError(Exception):
    """Raised on transport failure."""


def authenticate(token: str) -> None:
    if not token:
        raise UploadAuthError("missing token")


def send(payload: bytes) -> None:
    if not payload:
        raise UploadTransportError("empty payload")
