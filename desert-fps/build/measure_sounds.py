"""Measures each sound of a recorded audition: python measure_sounds.py <wav> <schedule.csv>

The recording: in a playtest, play a beep, then each candidate sound in turn 0.3 s apart, while ffmpeg records
the PC's sound (HANDOFF.md, "Sound"). schedule.csv has a line for each sound: group,id,at,length, where at is
the seconds after the beep was started and length the sound's TimeLength.

Prints for each sound: the lead-in before it starts, how long it is heard, how many separate events it has,
how fast it dies away, its level, and where its energy is (share below 250 Hz, 250-2k, 2k-6k, above 6k).

Keep a recording under half a minute. The recording's clock drifts against Studio's by about 2 ms a second,
so later sounds slide out of the window they are looked for in, and their levels then read far too low.
"""
import sys
import wave

import numpy as np


def load(path):
    with wave.open(path, "rb") as f:
        rate, channels = f.getframerate(), f.getnchannels()
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return data.reshape(-1, channels).mean(axis=1), rate


def envelope(x, rate, window=0.005):
    n = max(1, int(rate * window))
    count = len(x) // n
    return np.sqrt((x[: count * n].reshape(count, n) ** 2).mean(axis=1)), window


def main():
    x, rate = load(sys.argv[1])
    env, step = envelope(x, rate)
    floor = np.median(env) + 1e-6
    loud = np.nonzero(env > max(0.01, floor * 20))[0]
    beep = loud[0] * step
    print(f"sync beep at {beep:.3f} s, noise floor {20 * np.log10(floor):.0f} dB")
    rows = [line.strip().split(",") for line in open(sys.argv[2]) if line.strip()]
    rows = [(g, i, float(a), float(l)) for g, i, a, l in rows]
    # Every sound comes out a little after it is started, and the beep later than the rest, so a sound may be
    # heard before the beep says it starts. Each is looked for in a window that holds it whole and none of
    # its neighbours (they are 0.3 s apart); the earliest of them all gives the offset.
    BEFORE, AFTER = 0.2, 0.1
    firsts = []
    for group, ident, at, length in rows:
        seg = env[int((beep + at - BEFORE) / step):int((beep + at + length + AFTER) / step)]
        firsts.append(np.nonzero(seg > seg.max() * 0.1)[0][0] * step - BEFORE)
    offset = min(firsts)
    print(f"the earliest sound is heard {offset * 1000:.0f} ms from where the beep puts its start")
    print(f"{'group':10}{'id':>12} {'len':>5} {'lead':>6} {'heard':>6} {'events':>6} {'die':>5} {'peak':>6} {'rms':>6}   low  mid  high  air  centroid")
    for group, ident, at, length in rows:
        start = beep + at - BEFORE
        seg = env[int(start / step):int((start + BEFORE + length + AFTER) / step)]
        peak = seg.max()
        if peak < floor * 5:
            print(f"{group:10}{ident:>12} {length:5.2f}  SILENT")
            continue
        over = np.nonzero(seg > peak * 0.1)[0]
        heard = np.nonzero(seg > peak * 0.03)[0]
        lead = over[0] * step - BEFORE - offset
        end = heard[-1] * step
        high = seg > peak * 0.25
        events, last = 0, -1e9
        for index in np.nonzero(high)[0]:
            if (index - last) * step > 0.06:
                events += 1
            last = index
        top = int(seg.argmax())
        after = np.nonzero(seg[top:] < peak * 0.1)[0]
        die = after[0] * step if len(after) else float("nan")
        s0 = int((start + over[0] * step) * rate)
        s1 = int((start + end) * rate)
        part = x[s0:max(s1, s0 + 256)]
        spec = np.abs(np.fft.rfft(part * np.hanning(len(part)))) ** 2
        freq = np.fft.rfftfreq(len(part), 1 / rate)
        total = spec.sum() + 1e-12
        bands = [spec[(freq >= lo) & (freq < hi)].sum() / total for lo, hi in ((0, 250), (250, 2000), (2000, 6000), (6000, 30000))]
        centroid = (spec * freq).sum() / total
        rms = np.sqrt((part**2).mean())
        print(
            f"{group:10}{ident:>12} {length:5.2f} {lead * 1000:5.0f}ms {end - over[0] * step:5.2f}s {events:6d} {die:5.2f} "
            f"{20 * np.log10(np.abs(part).max() + 1e-9):6.1f} {20 * np.log10(rms + 1e-9):6.1f}  "
            + " ".join(f"{share * 100:4.0f}" for share in bands)
            + f"  {centroid:7.0f}"
        )


if __name__ == "__main__":
    main()
