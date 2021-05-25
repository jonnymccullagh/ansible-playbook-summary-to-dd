#!/usr/bin/env python3
"""Reads ansible playbook summary and sends them to DataDog
   Run with playbook name e.g.
   python3 ./playbook_stats_to_dd.py --playbook-file my-playbook-file.yml
"""

import argparse
import os
from datadog import initialize, api

DD_API_KEY = os.environ["DATADOG_API_KEY"]
DD_APP_KEY = os.environ["DATADOG_APP_KEY"]


def parse_arguments():
    """Get parameters passed at runtime"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--playbook-file",
                        dest="playbook_file",
                        default=None,
                        type=str)
    parser.add_argument("--env",
                        dest="env",
                        default="dev",
                        type=str)
    if not parser.parse_args().playbook_file:
        parser.error(
            "No playbook file specified: e.g. --playbook-file my-playbook-file.yml"
        )

    return parser.parse_args()


def main():  # pylint: disable=W0613
    """Main starting point"""
    args = parse_arguments()

    options = {"api_key": DD_API_KEY, "app_key": DD_APP_KEY}
    print("Initializing DataDog Client...\n")
    initialize(**options)

    # Open the summary of the playbook run
    ansible_log = open("playbook_summary.txt", "r")
    metrics = []
    while ansible_line := ansible_log.readline():
        # someservername-10-100-1-2 : ok=145
        # changed=0    unreachable=0    failed=0
        # skipped=96   rescued=0    ignored=0
        host_name = ansible_line.split()[0]
        stats_string = ansible_line.split(":")[1]
        stats_dict = dict(x.split("=") for x in stats_string.split())
        for key, value in stats_dict.items():
            metrics.append(
                {
                    "type": "metric",
                    "metric": "ansible.tasks." + key,
                    "points": int(value),
                    "host": host_name,
                    "tags": [
                        f"playbook:{args.playbook_file.split('.')[0]}",
                    ],
                }
            )

    print(metrics)
    response = api.Metric.send(metrics)
    print(response)


if __name__ == "__main__":  # pylint: disable=W0621, C0103, W0613
    main()
