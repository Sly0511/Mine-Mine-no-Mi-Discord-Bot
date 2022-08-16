from uuid import UUID

def get_uuid_from_parts(most: int, least: int) -> str:
    """Get a uuid from the parts."""
    return str(UUID(
            bytes=most.to_bytes(8, "big", signed=True)
            + least.to_bytes(8, "big", signed=True)
        ))