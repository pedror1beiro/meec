"""Record real PRUMO serial rows without inventing or resampling data."""

import argparse
import csv
import time
from pathlib import Path

FIELDS = (
    "t_ms,sample_ms,seq,ax_mg,ay_mg,az_mg,x_cdeg,y_cdeg,zero_x_cdeg,zero_y_cdeg,"
    "tol_cdeg,hold,sensor_ok,tilt_valid,i2c_errors,missed_polls,uart_dropped"
).split(",")


def parse_row(line):
    values = line.strip().split(",")
    if len(values) != len(FIELDS):
        return None
    try:
        return [int(value) for value in values]
    except ValueError:
        return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True)
    p.add_argument("--seconds", type=float, default=30)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.seconds <= 0:
        p.error("--seconds must be positive")
    if args.output.exists():
        p.error("Output already exists; choose a new filename to preserve the original data.")
    try:
        import serial
    except ImportError:
        raise SystemExit("Install tools/requirements-logger.txt in a Python venv first.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    try:
        with (
            serial.Serial(args.port, 115200, timeout=1) as port,
            args.output.open("x", newline="", encoding="utf-8") as f,
        ):
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            deadline = time.monotonic() + args.seconds
            buffer = bytearray()
            synchronized = False
            while time.monotonic() < deadline:
                buffer.extend(port.read_until(b"\n", size=512))
                while b"\n" in buffer:
                    raw, _, remaining = buffer.partition(b"\n")
                    buffer = bytearray(remaining)
                    # Opening a running stream may start in the middle of a row.
                    if not synchronized:
                        synchronized = True
                        continue
                    row = parse_row(raw.decode("ascii", errors="replace"))
                    if row is not None:
                        writer.writerow(row)
                        count += 1
                if len(buffer) > 512:
                    buffer.clear()
                    synchronized = False
    except KeyboardInterrupt:
        pass
    print(f"Saved {count} real serial rows to {args.output}")


if __name__ == "__main__":
    main()
