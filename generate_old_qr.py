import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.ticket import Ticket
from app.services.qr_code_service import generate_ticket_qr


async def generate_missing_qr_codes():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Ticket).where(Ticket.qr_code_path.is_(None))
        )

        tickets = result.scalars().all()

        if not tickets:
            print("All tickets already have QR codes.")
            return

        for ticket in tickets:
            ticket.qr_code_path = generate_ticket_qr(
                booking_reference=ticket.booking_reference,
                ticket_id=ticket.id,
            )

            print(
                f"QR generated for Ticket {ticket.id}: "
                f"{ticket.qr_code_path}"
            )

        await db.commit()

        print(f"\nSuccessfully generated {len(tickets)} QR codes.")


if __name__ == "__main__":
    asyncio.run(generate_missing_qr_codes())