
import asyncio

from app.services.redis_client import redis_client
from app.services.seat_lock_service import (
    acquire_seat_lock,
    release_seat_lock,
    get_seat_lock_owner,
)


async def main():
    showtime_id = 999
    seat_id = 999
    user_one = 101
    user_two = 202

    # Clear any leftover test lock.
    await redis_client.delete(f"seat_lock:{showtime_id}:{seat_id}")

    try:
        first = await acquire_seat_lock(
            showtime_id, seat_id, user_one
        )
        print("User 101 acquired lock:", first)

        second = await acquire_seat_lock(
            showtime_id, seat_id, user_two
        )
        print("User 202 acquired same lock:", second)

        owner = await get_seat_lock_owner(showtime_id, seat_id)
        print("Current lock owner:", owner)

        wrong_release = await release_seat_lock(
            showtime_id, seat_id, user_two
        )
        print("User 202 released User 101 lock:", wrong_release)

        correct_release = await release_seat_lock(
            showtime_id, seat_id, user_one
        )
        print("User 101 released lock:", correct_release)

    finally:
        await redis_client.delete(f"seat_lock:{showtime_id}:{seat_id}")
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
