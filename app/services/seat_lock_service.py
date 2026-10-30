
from app.services.redis_client import redis_client


# A seat lock expires automatically after 5 minutes.
SEAT_LOCK_TTL_SECONDS = 300


def _seat_lock_key(showtime_id: int, seat_id: int) -> str:
    """Build a unique Redis key for a seat at a particular showtime."""
    return f"seat_lock:{showtime_id}:{seat_id}"


async def acquire_seat_lock(
    showtime_id: int,
    seat_id: int,
    user_id: int,
    ttl_seconds: int = SEAT_LOCK_TTL_SECONDS,
) -> bool:
    """
    Lock a seat for a user.

    Returns True if the lock was acquired or already belongs to this user.
    Returns False if another user holds the lock.
    """
    if showtime_id <= 0 or seat_id <= 0 or user_id <= 0:
        raise ValueError("Showtime, seat, and user IDs must be positive.")

    if ttl_seconds <= 0:
        raise ValueError("Lock expiration must be positive.")

    key = _seat_lock_key(showtime_id, seat_id)
    owner = str(user_id)

    # SET NX is atomic: only one new owner can acquire the lock.
    acquired = await redis_client.set(
        key,
        owner,
        nx=True,
        ex=ttl_seconds,
    )

    if acquired:
        return True

    # Don't extend the lock if it already belongs to this user.
    current_owner = await redis_client.get(key)
    return current_owner == owner


async def release_seat_lock(
    showtime_id: int,
    seat_id: int,
    user_id: int,
) -> bool:
    """
    Release a seat only if the requesting user owns the lock.
    Returns False if the lock is absent or belongs to another user.
    """
    key = _seat_lock_key(showtime_id, seat_id)

    # Check and delete atomically to prevent another user's lock
    # from being deleted between the ownership check and deletion.
    release_script = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
    end
    return 0
    """

    result = await redis_client.eval(
        release_script,
        1,
        key,
        str(user_id),
    )

    return result == 1


async def get_seat_lock_owner(
    showtime_id: int,
    seat_id: int,
) -> str | None:
    """Return the lock owner's user ID, or None if the seat is unlocked."""
    key = _seat_lock_key(showtime_id, seat_id)
    return await redis_client.get(key)
