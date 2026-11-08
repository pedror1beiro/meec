"""Seeded application-channel emulation, independent of DDS and ROS.

This models delivery delay/loss/outages above ROS, not radio propagation or
measured DDS packet loss. Sensor-to-controller traffic stays local to each rover.
"""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import math
import random


def link_config(config, profile="config"):
    profiles = {
        "ideal": dict(loss=0.0, delay=0.0, jitter=0.0, blackouts=[]),
        "degraded": dict(loss=0.15, delay=0.12, jitter=0.05, blackouts=[]),
        "outage": dict(
            loss=0.15,
            delay=0.12,
            jitter=0.05,
            blackouts=[dict(rover="rover1", start=20.0, end=32.0)],
        ),
    }
    values = dict(seed=0, loss=0.0, delay=0.0, jitter=0.0, range_m=0.0, blackouts=[])
    values.update(config.get("network", {}))
    if profile != "config":
        values.update(profiles[profile])
    for name in ("loss", "delay", "jitter", "range_m"):
        if not math.isfinite(values[name]) or values[name] < 0:
            raise ValueError(f"network.{name} must be finite and nonnegative")
    if values["loss"] > 1 or values["jitter"] > values["delay"]:
        raise ValueError("Require loss<=1 and jitter<=delay")
    for outage in values["blackouts"]:
        if (
            outage["rover"] not in {r["id"] for r in config["rovers"]}
            or not 0 <= outage["start"] < outage["end"]
        ):
            raise ValueError("Blackouts need a known rover and 0<=start<end")
    return values


@dataclass
class Packet:
    channel: str
    rover: str
    payload: object
    sent_at: float
    due: float
    expires: float
    reliable: bool


class LinkEmulator:
    def __init__(self, config):
        self.config = config
        self.enabled, self.positions, self.pending = {}, {}, {}
        self.counts = defaultdict(Counter)
        self.delays = defaultdict(lambda: deque(maxlen=10000))
        self.randoms = {}
        self.serial = 0

    def stream(self, rover, channel):
        key = rover + "/" + channel
        if key not in self.randoms:
            self.randoms[key] = random.Random(str(self.config["seed"]) + ":" + key)
        return self.randoms[key]

    def available(self, rover, now):
        if not self.enabled.get(rover, True):
            return False
        if any(
            o["rover"] == rover and o["start"] <= now < o["end"] for o in self.config["blackouts"]
        ):
            return False
        radius = self.config.get("range_m", 0)
        return not radius or math.dist(self.positions.get(rover, (0, 0)), (0, 0)) <= radius

    def submit(self, channel, rover, payload, now, *, reliable=False, ttl=1.0, key=None):
        count = self.counts[rover + "/" + channel]
        count["offered"] += 1
        self.serial += 1
        packet_key = (rover, channel, self.serial if key is None else key)
        rng = self.stream(rover, channel)
        due = (
            now + self.config["delay"] + rng.uniform(-self.config["jitter"], self.config["jitter"])
        )
        if packet_key in self.pending:
            due = min(due, self.pending[packet_key].due)
            count["coalesced"] += 1
        if len(self.pending) >= 512 and packet_key not in self.pending:
            oldest = next(iter(self.pending))
            removed = self.pending.pop(oldest)
            self.counts[removed.rover + "/" + removed.channel]["queue_evicted"] += 1
        self.pending[packet_key] = Packet(channel, rover, payload, now, due, now + ttl, reliable)

    def poll(self, now):
        delivered = []
        for key, packet in list(self.pending.items()):
            count = self.counts[packet.rover + "/" + packet.channel]
            if now > packet.expires:
                count["expired"] += 1
                self.pending.pop(key)
                continue
            if now < packet.due:
                continue
            count["attempts"] += 1
            lost = (
                not self.available(packet.rover, now)
                or self.stream(packet.rover, packet.channel).random() < self.config["loss"]
            )
            if lost:
                count["lost_attempts"] += 1
                if packet.reliable:
                    count["retries"] += 1
                    packet.due = now + 0.2
                else:
                    self.pending.pop(key)
            else:
                self.pending.pop(key)
                count["delivered"] += 1
                self.delays[packet.rover + "/" + packet.channel].append(now - packet.sent_at)
                delivered.append(packet)
        return delivered

    def report(self, now):
        streams = {}
        for key, count in self.counts.items():
            delays = sorted(self.delays[key])
            streams[key] = dict(count)
            streams[key]["mean_delay_s"] = sum(delays) / len(delays) if delays else None
            streams[key]["p95_delay_s"] = (
                delays[min(len(delays) - 1, int(0.95 * len(delays)))] if delays else None
            )
        return dict(
            time=now,
            model="seeded application-channel emulator, not measured DDS/radio loss",
            configuration=self.config,
            pending=len(self.pending),
            streams=streams,
            online={r: self.available(r, now) for r in self.enabled},
        )
