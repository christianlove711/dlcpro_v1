import argparse
import collections
import struct
import time

import serial


def read_capture(ser, adc_clock_mhz, buffer_size, trigger_type, threshold):
    command = bytearray()
    command.append(adc_clock_mhz & 0xFF)
    command.extend(struct.pack("<H", buffer_size))
    command.append(trigger_type & 0xFF)
    command.extend(struct.pack("<H", threshold & 0xFFFF))

    ser.write(command)
    ser.flush()

    raw = bytearray()
    deadline = time.perf_counter() + 8.0
    while len(raw) < buffer_size:
        chunk = ser.read(buffer_size - len(raw))
        if chunk:
            raw.extend(chunk)
        elif time.perf_counter() > deadline:
            raise TimeoutError(f"received {len(raw)} / {buffer_size} bytes")
    return bytes(raw)


def summarize_lane(raw, lane):
    data = raw[lane::4]
    counter = collections.Counter(data)
    common = " ".join(f"{value}:{count}" for value, count in counter.most_common(8))
    return {
        "count": len(data),
        "min": min(data) if data else None,
        "max": max(data) if data else None,
        "unique": len(counter),
        "common": common,
        "first": list(data[:24]),
    }


def summarize_samples(raw):
    samples = list(raw[0::2])
    if len(samples) < 2:
        return samples, 0, None

    steps = [abs(current - previous) for previous, current in zip(samples, samples[1:])]
    max_step = max(steps)
    return samples, max_step, steps.index(max_step) + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--clock", type=int, default=5)
    parser.add_argument("--size", type=int, default=4096)
    parser.add_argument("--trigger", type=int, default=3)
    parser.add_argument("--threshold", type=int, default=128)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    with serial.Serial(args.port, args.baud, timeout=2.0, write_timeout=2.0) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for frame in range(1, args.repeat + 1):
            raw = read_capture(
                ser,
                args.clock,
                args.size,
                args.trigger,
                args.threshold,
            )
            print(f"frame {frame}/{args.repeat}: received {len(raw)} bytes")
            print("first 64 raw bytes:")
            print(" ".join(f"{b:02X}" for b in raw[:64]))
            print()

            samples, max_step, max_step_index = summarize_samples(raw)
            print(
                f"chronological samples: count={len(samples)} "
                f"min={min(samples)} max={max(samples)} "
                f"max_step={max_step} at index={max_step_index}"
            )
            print(f"  first: {samples[:32]}")
            print()

            for lane in range(4):
                info = summarize_lane(raw, lane)
                print(
                    f"lane raw[{lane}::4]: count={info['count']} "
                    f"min={info['min']} max={info['max']} unique={info['unique']}"
                )
                print(f"  most_common: {info['common']}")
                print(f"  first: {info['first']}")
            print()

            if frame != args.repeat:
                time.sleep(args.delay)


if __name__ == "__main__":
    main()
