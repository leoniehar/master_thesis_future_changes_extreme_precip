#!/bin/bash

# Usage: ./timestamps_creation.sh 2020-06-01 2021-06-01 timestamps_example.lst

if [ $# -ne 3 ]; then
    echo "Usage: $0 <start_date> <end_date>"
    echo "Example: $0 2020-06-01 2021-06-01"
    exit 1
fi

output="$3" #"timestamps.lst"
> "$output"

start="$1"
end="$2"

times=("0000" "0300" "0600" "0900" "1200" "1500" "1800" "2100")

current="$start"
while [[ "$current" < "$end" || "$current" == "$end" ]]; do
    for time in "${times[@]}"; do
        echo "${current}-${time}" >> "$output"
    done
    current=$(date -d "$current + 1 day" +%Y-%m-%d)
done

echo "Done: $(wc -l < $output) timestamps written to $output"