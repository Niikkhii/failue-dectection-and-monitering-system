import time
from datetime import datetime

import psutil

from storage.database import Database


class MetricsCollector:
    def __init__(self, db_path: str = "monitoring.db", interval_seconds: int = 5):
        self.db = Database(db_path)
        self.interval_seconds = interval_seconds
        self.collection_count = 0

    def collect_once(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent

        self.db.insert_raw_metric("cpu", round(cpu_percent, 2))
        self.db.insert_raw_metric("memory", round(memory_percent, 2))
        self.db.insert_raw_metric("disk", round(disk_percent, 2))

        self.collection_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{timestamp}] sample={self.collection_count} "
            f"cpu={cpu_percent:.2f}% mem={memory_percent:.2f}% disk={disk_percent:.2f}%"
        )

    def run(self):
        print("Metrics collector started")
        while True:
            try:
                self.collect_once()
                time.sleep(self.interval_seconds)
            except KeyboardInterrupt:
                print("\nMetrics collector stopped")
                break
            except Exception as exc:
                print(f"Collector error: {exc}")
                time.sleep(self.interval_seconds)


if __name__ == "__main__":
    MetricsCollector().run()
