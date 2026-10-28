"""Small CPU-only pilot: stop when the desktop's available memory is low."""
import os
import threading
import time


def available_mib():
    with open('/proc/meminfo') as stream:
        fields = dict(line.split(':', 1) for line in stream)
    return int(fields['MemAvailable'].split()[0]) / 1024


def start_guard():
    def check():
        minimum = float('inf')
        while True:
            available = available_mib()
            minimum = min(minimum, available)
            if available < 3072:
                print(f'STOP: desktop reserve: {available:.0f} MiB available', flush=True)
                os._exit(75)
            time.sleep(0.5)
    if available_mib() < 3072:
        raise SystemExit('STOP: less than 3 GiB available before startup')
    threading.Thread(target=check, daemon=True).start()
