r"""
Can be run for days to see how often the internet is up.

Compiled into exe with `pyinstaller -F .\uptime.py`
"""
import argparse
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
import pytz
from zoneinfo import ZoneInfo
from datetime import timezone

sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Get system timezone
try:
    system_timezone = datetime.now(timezone.utc).astimezone().tzinfo
except Exception:
    system_timezone = ZoneInfo('UTC')  # Fallback to UTC if can't determine

LOG_DIR = "log"
SUMMARY_FILE = os.path.join(LOG_DIR, "uptime_master_summary.log")
current_log_date = datetime.now(system_timezone).strftime('%Y-%m-%d')
output_file = os.path.join(LOG_DIR, f"uptime_log_{current_log_date}.log")
win_version = platform.win32_ver()
try:  # Windows 11 starts from build number 22000
    build_number = int(win_version[1].split('.')[2])
    is_win_11 = build_number >= 22000
except (IndexError, ValueError):
    is_win_11 = False

os_is_windows = platform.system() == 'Windows'

if is_win_11 or not os_is_windows:
    # print_and_log()("Windows 11 or Linux detected")
    checkmark = '✅'
    x = '❌'
else:
    checkmark = '[√]'
    x = '[X]'

if os_is_windows:
    ping_arg = "-n"
else:
    ping_arg = "-c"


@dataclass(slots=True)
class Outage:
    _start: float
    _end: float

    @property
    def start(self) -> float:
        return round(self._start, 2)

    @start.setter
    def start(self, value: float):
        self._start = value

    @property
    def end(self) -> float:
        return round(self._end, 2)

    @end.setter
    def end(self, value: float):
        self._end = value

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 2)


@dataclass(slots=True)
class Host:
    address: str
    name: str = ''
    success_pings: int = 0
    failed_pings: int = 0
    total_pings: int = 0
    response_times: list[float] = field(default_factory=list)
    total_response_time: float = 0.0
    high_response_time: float = 0
    low_response_time: float = float('inf')
    uptime_percentage: float = 0
    avg_response_time: float = 0

    def __post_init__(self):
        if not self.name:
            name = self.address

    def update_response_time(self, time_: float):
        self.response_times.append(time_)
        self.total_response_time += time_
        self.high_response_time = max(self.high_response_time, time_)
        self.low_response_time = min(self.low_response_time, time_)

    def calculate_stats(self):
        total_pings = self.success_pings + self.failed_pings
        if total_pings > 0:
            self.uptime_percentage = (self.success_pings / total_pings) * 100
        if self.response_times:
            self.avg_response_time = sum(self.response_times) / len(self.response_times)


def main() -> None:
    host_quad9 = Host(address='9.9.9.9', name='Quad9')
    host_cloudflare = Host(address='1.1.1.1', name='Cloudflare')
    host_google = Host(address='8.8.8.8', name='Google')
    all_hosts: list[Host] = [host_quad9, host_cloudflare, host_google]

    parser = argparse.ArgumentParser(description="Add extra hosts.")
    parser.add_argument(
        '-e', '--extra-hosts',
        nargs='*',
        metavar=('ADDRESS', 'NAME'),
        help="Add extra hosts in the form of address and name pairs. Example: --extra-hosts 8.8.4.4 GoogleDNS"
    )

    args = parser.parse_args()

    if args.extra_hosts:
        extra_hosts = args.extra_hosts
        for i in range(0, len(extra_hosts), 2):
            try:
                address = extra_hosts[i]
                name = extra_hosts[i + 1]
                all_hosts.append(Host(address=address, name=name))
            except IndexError:
                print("Error: Each extra host requires an address and a name.")
                return

    ping_interval_seconds = 3
    info_print_interval_seconds = 40
    ljust_num = 12
    num_outages = 0
    timeout_limit = 7
    outage_start = 0.0
    outages: list[Outage] = []
    start_time = 0.0

    formatted_names = " " * 22 + ''.join([host.name.ljust(17) for host in all_hosts])
    print_and_log("\nMonitoring internet uptime by pinging DNS servers:\n" + "-" * len(formatted_names) + "\n")
    print_and_log(formatted_names)
    script_start = time.time()

    try:
        while True:
            all_failed = True
            ping_result_output = []
            for host in all_hosts:
                start_time = time.time()
                host.total_pings += 1
                try:
                    ping_result = subprocess.run(["ping", ping_arg, "1", host.address], stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, timeout=timeout_limit)
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                except subprocess.TimeoutExpired:
                    host.failed_pings += 1
                    ping_result_output.append("⏱️ timeout".ljust(ljust_num + 1))
                    continue

                if ping_result.returncode == 0:
                    all_failed = False
                    host.success_pings += 1
                    host.update_response_time(response_time)
                    ping_result_output.append(f"{checkmark} {response_time:.2f} ms".ljust(ljust_num))
                else:
                    host.failed_pings += 1
                    ping_result_output.append(x.ljust(ljust_num))

            if all_failed:
                print_and_log(f"{datetime.now(system_timezone).strftime('%Y-%m-%d %H:%M:%S')} - {x * 7} Internet Outage {x * 7} ")
                if not outage_start:
                    outage_start = time.time()
            else:
                if outage_start:
                    outage_end = time.time()
                    num_outages += 1
                    outage = Outage(outage_start, outage_end)
                    outages.append(outage)
                    outage_start = 0.0
                print_and_log(
                    f"{datetime.now(system_timezone).strftime('%Y-%m-%d %H:%M:%S')} - {'    '.join(ping_result_output)}"[:-2])

            if all_hosts[0].total_pings % info_print_interval_seconds == 0:  # Every x seconds
                for host in all_hosts:
                    host.uptime_percentage = host.success_pings / host.total_pings * 100
                    host.avg_response_time = host.total_response_time / len(host.response_times)

                # Always update the summary file with latest stats (overwrite)
                with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                    f.write("Current Uptime and Response Times\n\n")
                    # Write stats directly to summary file
                    stats = []
                    column_names = ["Host", "Uptime", "Average", "Low", "High"]
                    for host in all_hosts:
                        uptime = f"{host.uptime_percentage:.2f}%"
                        high = f"{host.high_response_time:.2f} ms"
                        low = f"{host.low_response_time:.2f} ms"
                        average = f"{host.avg_response_time:.2f} ms"
                        stats.append([host.address, uptime, average, low, high])
                    
                    # Calculate column widths
                    col_widths = [max(len(str(item)) for item in col) for col in zip(*stats, column_names)]
                    
                    # Write formatted stats
                    f.write(" | ".join(header.ljust(width) for header, width in zip(column_names, col_widths)) + "\n")
                    f.write("-+-".join('-' * width for width in col_widths) + "\n")
                    for stat in stats:
                        f.write(" | ".join(str(item).ljust(width) for item, width in zip(stat, col_widths)) + "\n")
                    
                    # Add outage information
                    f.write("\n")
                    if outages:
                        f.write(f"Total outages: {len(outages)}\n")
                        f.write("Outage History (last 100 outages):\n")
                        
                        # Show up to last 100 outages, newest first
                        recent_outages = outages[-100:]
                        recent_outages.reverse()  # Show newest first
                        
                        # Format as a table for better readability
                        f.write("\nStart Time           | End Time             | Duration\n")
                        f.write("-"*19 + "+" + "-"*20 + "+" + "-"*20 + "\n")
                        for outage in recent_outages:
                            start_time = datetime.fromtimestamp(outage.start).strftime('%Y-%m-%d %H:%M:%S')
                            end_time = datetime.fromtimestamp(outage.end).strftime('%Y-%m-%d %H:%M:%S')
                            duration = format_seconds(outage.duration).ljust(18)
                            f.write(f"{start_time} | {end_time} | {duration}\n")
                    elif outage_start:
                        f.write(f"\nOngoing outage since {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
                    else:
                        f.write("No outages\n")
                    
                    # Add run time
                    current_runtime = time.time() - script_start
                    f.write(f"\nProgram running for: {format_seconds(current_runtime)}\n")
                    f.write(f"Last updated: {datetime.now(system_timezone).strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Only print to console, don't write stats to log file
                print("\nCurrent Uptime and Response Times:")
                calculate_stats(all_hosts, console_only=True)
                if outages:
                    print_outage_info(outages, console_only=True)
                elif outage_start:
                    print(f"\nOngoing outage since {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print("\nNo outages")
                print("\n" + formatted_names)

            time.sleep(ping_interval_seconds)

    except KeyboardInterrupt:
        print_and_log("\nFinal Uptime and Response Times:", to_summary=True)
        calculate_stats(all_hosts, to_summary=True)
        script_end = time.time()
        total_time = script_end - script_start
        message = format_seconds(total_time)
        if outages:
            print_outage_info(outages, to_summary=True)
        else:
            print_and_log("\nNo outages", to_summary=True)
        print_and_log(f"\nProgram ran for: {message}\n", to_summary=True)


def print_outage_info(all_outages: list[Outage], console_only: bool = False) -> None:
    print(f"\nTotal outages: {len(all_outages)}")
    print("Outage Log:")
    column_names = ["Start", "End", "Duration"]

    stats: list[list] = []
    for outage in all_outages:
        stats.append([datetime.fromtimestamp(outage.start).strftime('%Y-%m-%d %H:%M:%S'),
                      datetime.fromtimestamp(outage.end).strftime('%Y-%m-%d %H:%M:%S'),
                      format_seconds(outage.duration)])

    # Calculate column widths and format output
    col_widths = [max(len(str(item)) for item in col) for col in zip(*stats, column_names)]
    
    # Print header
    print(" | ".join(header.ljust(width) for header, width in zip(column_names, col_widths)))
    print("-+-".join('-' * width for width in col_widths))
    
    # Print stats
    for stat in stats:
        print(" | ".join(str(item).ljust(width) for item, width in zip(stat, col_widths)))


def calculate_stats(all_hosts: list[Host], console_only: bool = False) -> None:
    print("\n")
    column_names = ["Host", "Uptime", "Average", "Low", "High"]

    stats: list[list] = []
    for host in all_hosts:
        uptime = f"{host.uptime_percentage:.2f}%"
        high = f"{host.high_response_time:.2f} ms"
        low = f"{host.low_response_time:.2f} ms"
        average = f"{host.avg_response_time:.2f} ms"
        stats.append([host.address, uptime, average, low, high])

    # Calculate column widths and format output
    col_widths = [max(len(str(item)) for item in col) for col in zip(*stats, column_names)]
    
    # Print header
    print(" | ".join(header.ljust(width) for header, width in zip(column_names, col_widths)))
    print("-+-".join('-' * width for width in col_widths))
    
    # Print stats
    for stat in stats:
        print(" | ".join(str(item).ljust(width) for item, width in zip(stat, col_widths)))


def print_formatted_stats(stats: list[list], column_names: list, to_summary: bool = False) -> None:
    # Determine column widths for alignment
    col_widths = [max(len(str(item)) for item in col) for col in zip(*stats, column_names)]

    # Print header
    print_and_log(" | ".join(header.ljust(width) for header, width in zip(column_names, col_widths)), to_summary=to_summary)
    print_and_log("-+-".join('-' * width for width in col_widths), to_summary=to_summary)

    # Print stats
    for stat in stats:
        print_and_log(" | ".join(str(item).ljust(width) for item, width in zip(stat, col_widths)), to_summary=to_summary)


def format_seconds(seconds_time: float) -> str:
    total_time_minutes: float = seconds_time / 60
    total_time_message: str = f"{seconds_time:.2f}s ({total_time_minutes:.2f} minutes)"
    if total_time_minutes > 60:
        total_time_hours: float = total_time_minutes / 60
        total_time_message += f" ({total_time_hours:.2f} hours)"
        if total_time_hours > 24:
            total_time_days: float = total_time_hours / 24
            total_time_message += f" ({total_time_days:.2f} days)"

    return total_time_message


def print_and_log(output: str, to_summary: bool = False) -> None:
    global output_file, current_log_date
    print(output)
    new_log_date = datetime.now(system_timezone).strftime('%Y-%m-%d')
    if new_log_date != current_log_date:
        # Roll to new log file
        current_log_date = new_log_date
        output_file = os.path.join(LOG_DIR, f"uptime_log_{current_log_date}.log")
        # Remove daily log files older than 14 days (exclude master summary)
        now = time.time()
        for fname in os.listdir(LOG_DIR):
            fpath = os.path.join(LOG_DIR, fname)
            if fname.startswith("uptime_log_") and fname.endswith(".log") and fname != os.path.basename(SUMMARY_FILE):
                try:
                    mtime = os.path.getmtime(fpath)
                    if (now - mtime) > 14 * 86400:
                        os.remove(fpath)
                except Exception:
                    pass
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    # Write to the appropriate file based on the to_summary flag
    if to_summary:
        try:
            # When writing summary, use 'w' mode to clear the file if it's the start of a new summary
            mode = "w" if output.startswith("\nFinal Uptime") else "a"
            print(f"Debug: Writing to summary file {SUMMARY_FILE} with mode {mode}")
            print(f"Debug: Summary directory exists: {os.path.exists(os.path.dirname(SUMMARY_FILE))}")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
            
            # Write to the summary file
            with open(SUMMARY_FILE, mode, encoding="utf-8") as f:
                f.write(output + "\n")
            
            print(f"Debug: Successfully wrote to summary file")
        except Exception as e:
            print(f"Debug: Error writing to summary file: {str(e)}")
    else:
        # Write to daily log file
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(output + "\n")


if __name__ == '__main__':
    main()
