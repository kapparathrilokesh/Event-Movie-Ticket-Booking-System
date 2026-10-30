
import os
import qrcode

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
TICKETS_DIR = BASE_DIR / "tickets"

TICKETS_DIR.mkdir(parents=True, exist_ok=True)


def generate_ticket_qr(
    booking_reference: str,
    ticket_id: int,
) -> str:
    """Generate a QR-code image for a booked ticket."""

    qr_data = (
        f"Booking Reference: {booking_reference}\n"
        f"Ticket ID: {ticket_id}"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    filename = f"ticket_{ticket_id}_{booking_reference}.png"
    file_path = TICKETS_DIR / filename

    image.save(file_path)

    return str(file_path.relative_to(BASE_DIR))

