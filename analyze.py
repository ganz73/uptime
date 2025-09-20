import re
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt

LOG_FILE = "uptime_log_combined.txt"
OUTAGE_LINE = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ❌+.*Internet Outage")

# Collect timestamps
timestamps = []

with open(LOG_FILE, "r", encoding="utf-8") as f:
    for line in f:
        match = OUTAGE_LINE.search(line)
        if match:
            dt = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            timestamps.append(dt)

# Analyze by hour of day
hour_counts = Counter(dt.hour for dt in timestamps)
day_counts = Counter(dt.strftime("%A") for dt in timestamps)

# Plot hourly pattern
plt.figure(figsize=(10, 4))
plt.bar(hour_counts.keys(), hour_counts.values(), color="skyblue")
plt.xticks(range(24))
plt.xlabel("Hour of Day")
plt.ylabel("Outage Count")
plt.title("Outages by Hour of Day")
plt.grid(True)
plt.tight_layout()
plt.savefig("outages_by_hour.png")
plt.close()

# Plot daily pattern
plt.figure(figsize=(8, 4))
days_ordered = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_values = [day_counts.get(day, 0) for day in days_ordered]
plt.bar(days_ordered, day_values, color="salmon")
plt.xlabel("Day of Week")
plt.ylabel("Outage Count")
plt.title("Outages by Day of Week")
plt.grid(True)
plt.tight_layout()
plt.savefig("outages_by_day.png")
plt.close()

# Print summary
print("Outages by Hour of Day:")
for hour in sorted(hour_counts):
    print(f"{hour:02d}:00 — {hour_counts[hour]} outages")

print("\nOutages by Day of Week:")
for day in days_ordered:
    print(f"{day}: {day_counts.get(day, 0)} outages")
