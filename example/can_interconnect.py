# CAN interconnect test for two XIAO STM32C5 boards
#
# Wiring:
#   Board1 CANH -- Board2 CANH
#   Board1 CANL -- Board2 CANL
#   Board1 GND  -- Board2 GND
#   (optional) 120 ohm resistor between CANH-CANL at each end
#
# Usage:
#   Board 1 (master):  import can_interconnect as ci; ci.master()
#   Board 2 (slave):   import can_interconnect as ci; ci.slave()
#
# Or auto-negotiate:
#   import can_interconnect as ci; ci.auto()

import sys
import time
import struct
from machine import Pin
from CAN import CAN

# CAN transceiver standby pin: PB14, active-low = normal operation
_CAN_STB = ("gpiob", 14)
# CAN settings
_CAN_DEV = "fdcan2"
_CAN_BITRATE = 500000
_CAN_DATA_BITRATE = 2000000
_CAN_FD = True

_passed = 0
_failed = 0


def _result(name, ok, msg=""):
    global _passed, _failed
    state = "PASS" if ok else "FAIL"
    suffix = " - " + str(msg) if msg else ""
    print("[{0}] {1}{2}".format(state, name, suffix))
    if ok:
        _passed += 1
    else:
        _failed += 1
    return ok


def _hex_dump(data, max_len=16):
    if len(data) <= max_len:
        return " ".join("{:02X}".format(b) for b in data)
    return " ".join("{:02X}".format(b) for b in data[:max_len]) + "..."


def can_init():
    """Initialize CAN with transceiver enabled."""
    # Enable transceiver
    stb = Pin(_CAN_STB, Pin.OUT)
    stb.value(0)
    time.sleep_ms(10)

    can = CAN(_CAN_DEV, bitrate=_CAN_BITRATE,
              data_bitrate=_CAN_DATA_BITRATE, fd=_CAN_FD)
    print("CAN init: {0} @ {1}kbps/{2}kbps FD".format(
        _CAN_DEV, _CAN_BITRATE // 1000, _CAN_DATA_BITRATE // 1000))
    return can


def can_recv_timeout(can, timeout_ms):
    """Receive with timeout, return None on timeout."""
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        frame = can.recv(50)
        if frame is not None:
            return frame
    return None


# ============================================================
# Test cases
# ============================================================

def test_ping(can):
    """Master sends a ping, waits for pong from slave."""
    print("\n--- Test 1: Ping/Pong ---")
    ping_id = 0x200
    pong_id = 0x201
    ping_data = bytes((0x50, 0x49, 0x4E, 0x47))  # "PING"
    pong_data = bytes((0x50, 0x4F, 0x4E, 0x47))  # "PONG"

    for attempt in range(3):
        can.send(ping_id, ping_data)
        print("  master sent: PING (id=0x{0:03X})".format(ping_id))
        frame = can_recv_timeout(can, 500)
        if frame and frame[0] == pong_id and frame[1] == pong_data:
            return _result("Ping/Pong", True, "PONG received in {0}ms".format(attempt + 1))
        print("  attempt {0}: no PONG".format(attempt + 1))
    return _result("Ping/Pong", False, "no PONG after 3 attempts")


def test_basic_tx_rx(can, n_frames=10):
    """Master sends sequential frames, slave verifies sequence."""
    print("\n--- Test 2: Basic TX/RX ({0} frames) ---".format(n_frames))
    base_id = 0x300
    lost = 0
    mismatch = 0
    last_seq = -1

    for seq in range(n_frames):
        data = bytes((seq, 0xC5, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06))
        can.send(base_id + seq, data)
        time.sleep_ms(5)

    # Wait for all frames
    for _ in range(n_frames):
        frame = can_recv_timeout(can, 200)
        if frame is None:
            lost += 1
            continue
        seq = frame[0] - base_id
        if 0 <= seq < n_frames:
            if seq != last_seq + 1:
                mismatch += 1
            last_seq = seq
        else:
            mismatch += 1

    if lost == 0 and mismatch == 0:
        return _result("Basic TX/RX", True, "{0}/{0} ok".format(n_frames))
    msg = "{0}/{1} ok".format(n_frames - lost, n_frames)
    if lost:
        msg += ", lost={0}".format(lost)
    if mismatch:
        msg += ", mismatch={0}".format(mismatch)
    return _result("Basic TX/RX", (lost == 0 and mismatch <= 1), msg)


def test_fd_large_payload(can):
    """Test CAN FD with 64-byte payload."""
    print("\n--- Test 3: CAN FD Large Payload (64 bytes) ---")
    test_id = 0x400
    # Create a test pattern: 0x00, 0x01, 0x02, ..., 0x3F
    payload = bytes(range(64))

    can.send(test_id, payload)
    print("  master sent: 64 bytes, id=0x{0:03X}".format(test_id))

    frame = can_recv_timeout(can, 500)
    if frame is None:
        return _result("FD 64B", False, "timeout")

    if frame[0] == test_id and frame[1] == payload:
        return _result("FD 64B", True, "64 bytes ok")
    elif frame[0] == test_id and len(frame[1]) == 64:
        return _result("FD 64B", False, "data mismatch")
    else:
        return _result("FD 64B", False, "len={0}, expected 64".format(len(frame[1])))


def test_stress(can, n_frames=200):
    """Stress test: rapid back-to-back frames.

    Drains the RX queue during the send loop to avoid overflowing the
    32-frame msgq; a final drain after sending catches any late echoes.
    """
    print("\n--- Test 4: Stress Test ({0} frames) ---".format(n_frames))
    base_id = 0x500
    received_ids = set()
    t_start = time.ticks_ms()

    # Send all frames, draining RX inline to prevent msgq overflow
    for i in range(n_frames):
        data = bytes((i & 0xFF, (i >> 8) & 0xFF, 0xC5, 0xC5))
        try:
            can.send(base_id + i, data)
        except Exception:
            pass  # TX queue full, continue
        # Drain any received frames (non-blocking)
        while True:
            frame = can.recv(0)
            if frame is None:
                break
            if base_id <= frame[0] < base_id + n_frames:
                received_ids.add(frame[0])
        if i % 10 == 0:  # small delay every 10 frames
            time.sleep_ms(1)

    t_send = time.ticks_diff(time.ticks_ms(), t_start)

    # Final drain: slave may still be echoing remaining frames
    deadline = time.ticks_add(time.ticks_ms(), 3000)
    while len(received_ids) < n_frames and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        frame = can.recv(50)
        if frame is None:
            continue
        if base_id <= frame[0] < base_id + n_frames:
            received_ids.add(frame[0])

    received = len(received_ids)

    if received == n_frames:
        t_total = time.ticks_diff(time.ticks_ms(), t_start)
        fps = n_frames * 1000 / max(t_total, 1)
        return _result("Stress {0}f".format(n_frames), True,
                       "send={0}ms total={1}ms {2:.0f} fps".format(t_send, t_total, fps))
    else:
        pct = received * 100 // n_frames
        return _result("Stress {0}f".format(n_frames), pct >= 50,
                       "{0}/{1} ({2}%), send={3}ms".format(received, n_frames, pct, t_send))


def test_burst(can, burst_size=30, n_bursts=3):
    """Burst test: send burst of frames, then check all received.

    Drains the RX queue during each burst to prevent msgq overflow.
    """
    print("\n--- Test 5: Burst ({0}x{1} frames) ---".format(n_bursts, burst_size))
    base_id = 0x600
    total = burst_size * n_bursts
    sent = 0
    received_ids = set()

    for burst in range(n_bursts):
        for j in range(burst_size):
            data = bytes((burst, j, 0xC5, 0x01))
            try:
                can.send(base_id + sent, data)
            except Exception:
                pass  # TX queue full, continue
            sent += 1
            # Drain any received frames (non-blocking)
            while True:
                frame = can.recv(0)
                if frame is None:
                    break
                if base_id <= frame[0] < base_id + total:
                    received_ids.add(frame[0])
        time.sleep_ms(100)  # gap between bursts to let slave drain queue

    # Final drain: catch any late echoes
    deadline = time.ticks_add(time.ticks_ms(), 2000)
    while len(received_ids) < total and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        frame = can.recv(50)
        if frame is None:
            continue
        if base_id <= frame[0] < base_id + total:
            received_ids.add(frame[0])

    received = len(received_ids)
    return _result("Burst", received == total,
                   "{0}/{1} ok".format(received, total))


def test_bidirectional(can, n_pairs=20):
    """Bidirectional: master sends, waits for echo from slave each time."""
    print("\n--- Test 6: Bidirectional ({0} pairs) ---".format(n_pairs))
    master_id = 0x700
    slave_id = 0x701
    ok = 0

    for i in range(n_pairs):
        data = bytes((i, 0xA5, 0x5A, 0xC3))
        can.send(master_id, data)
        frame = can_recv_timeout(can, 200)
        if frame and frame[0] == slave_id:
            # Slave echoes back with incremented counter
            if len(frame[1]) >= 2 and frame[1][0] == i:
                ok += 1

    return _result("Bidirectional", ok >= n_pairs * 0.9,
                   "{0}/{1} ok".format(ok, n_pairs))


def test_variable_speed(can):
    """Test at different bitrates (single-board loopback self-test)."""
    print("\n--- Test 7: Variable Speed ---")
    speeds = [
        (125000, None, False, "125k Classic"),
        (250000, None, False, "250k Classic"),
        (500000, None, False, "500k Classic"),
        (500000, 2000000, True, "500k/2M FD"),
        (500000, 4000000, True, "500k/4M FD"),
    ]
    all_ok = True

    for nominal, data, fd, label in speeds:
        # Release the main controller so can2 can (re)configure this speed.
        try:
            can.deinit()
        except Exception:
            pass
        time.sleep_ms(50)

        try:
            can2 = CAN(_CAN_DEV, bitrate=nominal,
                       data_bitrate=data or 2000000, fd=fd, loopback=True)
            can2.send(0x100, b"TEST")
            frame = can_recv_timeout(can2, 300)
            if frame and frame[0] == 0x100:
                print("  {0}: OK".format(label))
            else:
                print("  {0}: FAIL (no loopback)".format(label))
                all_ok = False
            can2.deinit()
        except Exception as exc:
            print("  {0}: FAIL ({1})".format(label, exc))
            all_ok = False

        time.sleep_ms(50)

    return _result("Variable speed", all_ok)


# ============================================================
# Slave mode
# ============================================================

def slave():
    """Slave: receives and responds to master's tests."""
    global _passed, _failed
    _passed = _failed = 0

    print("=" * 50)
    print("  CAN Interconnect Test - SLAVE")
    print("  Waiting for master...")
    print("=" * 50)

    can = can_init()

    while True:
        # Drain all available frames (non-blocking)
        frame = can.recv(0)
        if frame is None:
            time.sleep_ms(1)  # yield if queue is empty
            continue

        fid = frame[0]
        data = frame[1]

        # Ping (0x200) -> reply Pong (0x201)
        if fid == 0x200 and data[:4] == b"PING":
            can.send(0x201, b"PONG")
            print("  PING -> PONG")

        # Sequential frames (0x300-0x3FF) -> echo back
        elif 0x300 <= fid < 0x400:
            can.send(fid, data)
            if fid == 0x309:
                print("  Basic TX/RX: echoed 10 frames")

        # FD large payload (0x400) -> echo back
        elif fid == 0x400:
            can.send(fid, data)
            print("  FD 64B: echoed {0} bytes".format(len(data)))

        # Stress frames (0x500-0x5FF) -> echo back
        elif 0x500 <= fid < 0x600:
            can.send(fid, data)
            if fid == 0x5C7:
                print("  Stress: echoed 200 frames")

        # Burst frames (0x600-0x6FF) -> echo back
        elif 0x600 <= fid < 0x700:
            can.send(fid, data)
            if fid == 0x659:
                print("  Burst: echoed 90 frames")

        # Bidirectional (0x700) -> echo with same data
        elif fid == 0x700:
            can.send(0x701, data)

        # test_variable_speed (master) uses 0x100 "TEST" with loopback=True.
        # STM32 FDCAN CAN_MODE_LOOPBACK is external (frame hits the bus + loops
        # back internally), so slave sees these frames. Ignore them silently
        # to keep the log clean.
        elif fid == 0x100 and data == b"TEST":
            pass

        # Print any unexpected frame
        else:
            print("  unexpected: id=0x{0:03X} data={1}".format(fid, _hex_dump(data)))


# ============================================================
# Master mode
# ============================================================

def master():
    """Master: runs all tests in sequence."""
    global _passed, _failed
    _passed = _failed = 0

    print("=" * 50)
    print("  CAN Interconnect Test - MASTER")
    print("  Make sure slave is running first!")
    print("=" * 50)

    can = can_init()
    print("Starting tests in 3 seconds...")
    time.sleep(3)

    test_ping(can)
    test_basic_tx_rx(can, 10)
    test_fd_large_payload(can)
    test_stress(can, 200)
    test_burst(can, 30, 3)
    test_bidirectional(can, 20)

    # Variable speed test (single-board loopback, do last)
    test_variable_speed(can)

    can.deinit()
    print("\n" + "=" * 50)
    total = _passed + _failed
    print("  CAN Interconnect Results: {0} PASS, {1} FAIL ({2} total)".format(
        _passed, _failed, total))
    print("=" * 50)


# ============================================================
# Auto mode
# ============================================================

def auto():
    """Auto-detect role: try to ping, if no response, become master."""
    print("=" * 50)
    print("  CAN Interconnect Test - AUTO")
    print("=" * 50)

    can = can_init()

    # Try to receive a ping first
    print("Listening for master ping...")
    frame = can_recv_timeout(can, 2000)
    if frame and frame[0] == 0x200:
        print("Detected master ping, running as SLAVE")
        can.deinit()
        time.sleep_ms(100)
        slave()
        return

    print("No ping detected, running as MASTER")
    can.deinit()
    time.sleep_ms(100)
    master()


# ============================================================
# Quick test (single-board loopback)
# ============================================================

def quick():
    """Quick single-board loopback test (no external wiring)."""
    global _passed, _failed
    _passed = _failed = 0

    print("=" * 50)
    print("  CAN Quick Loopback Test (single board)")
    print("=" * 50)

    can = CAN(_CAN_DEV, bitrate=_CAN_BITRATE,
              data_bitrate=_CAN_DATA_BITRATE, fd=_CAN_FD, loopback=True)

    # Basic test
    payload = bytes((0xC5, 0x01, 0x02, 0x03))
    can.send(0x123, payload)
    frame = can.recv(200)
    _result("Loopback basic", frame is not None and frame[1] == payload)

    # FD 64B test
    payload64 = bytes(range(64))
    can.send(0x456, payload64)
    frame = can.recv(200)
    _result("Loopback FD 64B", frame is not None and frame[1] == payload64)

    # Stress
    ok = 0
    for i in range(100):
        can.send(0x100 + i, bytes((i, 0xC5)))
        f = can.recv(100)
        if f:
            ok += 1
    _result("Loopback stress 100f", ok == 100, "{0}/100 ok".format(ok))

    can.deinit()
    print("\n  Quick test: {0} PASS, {1} FAIL".format(_passed, _failed))


# Help
def help():
    print("""
CAN Interconnect Test Commands:
  ci.quick()    - Quick single-board loopback test (no wiring)
  ci.master()   - Run as master (needs slave on other board)
  ci.slave()    - Run as slave (needs master on other board)
  ci.auto()     - Auto-detect role

Wiring (two boards):
  Board1 CANH -- Board2 CANH
  Board1 CANL -- Board2 CANL
  Board1 GND  -- Board2 GND
  (optional) 120 ohm resistor CANH-CANL at each end
""")