"""Raspberry Pi 5 module that validates UNO keypad input against Django confirmation codes.

The Pi reads the `confirmation_code` stored in the local `db.sqlite3` database,
receives 4-digit codes from an Arduino UNO via serial, compares the values, and
then sends `UNLOCK` or `LOCK` commands back to the UNO.

Usage example:
    python3 raspberry_pi.py \
        --db-path /home/pi/jungo/db.sqlite3 \
        --uno-port /dev/ttyACM0 \
        --order-id 3

Requirements:
    pip install pyserial

The UNO sketch must send lines like `CODE:1234` when the user enters a code, and
must react to `UNLOCK` / `LOCK` commands sent back by the Pi.
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from dataclasses import dataclass
from typing import Optional

try:
    import serial  # type: ignore
except ImportError as exc:  # pragma: no cover
    serial = None
    SERIAL_IMPORT_ERROR = exc
else:
    SERIAL_IMPORT_ERROR = None

LOGGER = logging.getLogger("raspberry_pi.module")


@dataclass
class DoorModuleConfig:
    db_path: str
    uno_port: str
    uno_baudrate: int = 9600
    order_id: Optional[int] = None
    poll_interval: float = 0.2
    debug: bool = False


class DoorController:
    def __init__(self, config: DoorModuleConfig) -> None:
        if serial is None:
            raise RuntimeError(
                "pyserial is required to communicate with the UNO: pip install pyserial"
            ) from SERIAL_IMPORT_ERROR
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None
        self._uno: Optional[serial.Serial] = None
        self._current_code: str = ""

    # ------------------------------------------------------------------
    def start(self) -> None:
        self._open_database()
        self._open_uno()
        LOGGER.info("Controller started. Listening for UNO keypad input ...")
        try:
            while True:
                self._process_uno_messages()
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            LOGGER.info("Stopping controller (Ctrl+C).")
        finally:
            self.close()

    # ------------------------------------------------------------------
    def _open_database(self) -> None:
        LOGGER.debug("Opening SQLite DB at %s", self.config.db_path)
        self._conn = sqlite3.connect(self.config.db_path, check_same_thread=False)
        self._conn.row_factory = lambda cursor, row: row[0]

    def _open_uno(self) -> None:
        LOGGER.debug(
            "Opening UNO serial port %s @ %s baud",
            self.config.uno_port,
            self.config.uno_baudrate,
        )
        self._uno = serial.Serial(
            self.config.uno_port,
            self.config.uno_baudrate,
            timeout=1.0,
        )
        time.sleep(2)  # give the UNO time to reset
        LOGGER.info("UNO serial connected.")

    def close(self) -> None:
        if self._uno and self._uno.is_open:
            self._uno.close()
        if self._conn:
            self._conn.close()

    # ------------------------------------------------------------------
    def _process_uno_messages(self) -> None:
        if not self._uno or not self._uno.is_open:
            return
        try:
            line = self._uno.readline().decode("utf-8", errors="ignore").strip()
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed reading from UNO: %s", exc)
            return

        if not line:
            return

        LOGGER.debug("UNO -> Pi: %s", line)
        if line.startswith("CODE:"):
            user_code = line[5:].strip()
            self._handle_user_code(user_code)
        elif line.startswith("ACK"):
            LOGGER.info("UNO acknowledgement: %s", line)
        else:
            LOGGER.info("UNO message: %s", line)

    def _handle_user_code(self, user_code: str) -> None:
        expected = self._fetch_confirmation_code()
        if not expected:
            LOGGER.warning("No confirmation code available in DB.")
            self._send_to_uno("LOCK")
            return

        if expected != self._current_code:
            self._current_code = expected
            LOGGER.info("Latest confirmation code loaded from DB: %s", expected)

        if user_code == expected:
            LOGGER.info("Code matched (%s). Unlocking.", user_code)
            self._send_to_uno("UNLOCK")
        else:
            LOGGER.info("Code mismatch (entered %s, expected %s).", user_code, expected)
            self._send_to_uno("LOCK")

    def _fetch_confirmation_code(self) -> str:
        if not self._conn:
            return ""
        try:
            if self.config.order_id is not None:
                query = (
                    "SELECT confirmation_code FROM orders_order "
                    "WHERE id = ? AND confirmation_code IS NOT NULL"
                )
                row = self._conn.execute(query, (self.config.order_id,)).fetchone()
            else:
                query = (
                    "SELECT confirmation_code FROM orders_order "
                    "WHERE confirmation_code IS NOT NULL "
                    "ORDER BY created_at DESC LIMIT 1"
                )
                row = self._conn.execute(query).fetchone()
        except sqlite3.Error as exc:
            LOGGER.error("SQLite error: %s", exc)
            return ""
        return row or ""

    def _send_to_uno(self, command: str) -> None:
        if not self._uno or not self._uno.is_open:
            return
        data = (command.strip().upper() + "\n").encode("ascii", errors="ignore")
        try:
            self._uno.write(data)
            self._uno.flush()
            LOGGER.debug("Pi -> UNO: %s", command)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Failed to send %s to UNO: %s", command, exc)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jungo Raspberry Pi door module")
    parser.add_argument("--db-path", required=True, help="Path to db.sqlite3")
    parser.add_argument(
        "--uno-port",
        required=True,
        help="Serial port connected to the UNO (e.g. /dev/ttyACM0)",
    )
    parser.add_argument("--uno-baudrate", type=int, default=9600, help="UNO serial baudrate")
    parser.add_argument(
        "--order-id",
        type=int,
        help="Specific order ID to watch (defaults to latest with confirmation code)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.2,
        help="Seconds between serial polls",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)5s | %(message)s")


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.debug)

    config = DoorModuleConfig(
        db_path=args.db_path,
        uno_port=args.uno_port,
        uno_baudrate=args.uno_baudrate,
        order_id=args.order_id,
        poll_interval=args.poll_interval,
        debug=args.debug,
    )

    controller = DoorController(config)
    controller.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())

