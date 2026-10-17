#!/bin/bash
# Usage: ./EDA_create_timestamps.sh 2023

YEAR=${1:?Usage: $0 YEAR}

starts=("${YEAR}-01-01" "${YEAR}-04-01" "${YEAR}-07-01" "${YEAR}-10-01")
ends=("${YEAR}-03-31" "${YEAR}-06-30" "${YEAR}-09-30" "${YEAR}-12-31")
names=("Q1_Jan-Mar" "Q2_Apr-Jun" "Q3_Jul-Sep" "Q4_Oct-Dec")

for i in 0 1 2 3; do
    outfile="EDA_timestamps_${names[$i]}.lst"
    > "$outfile"
    
    current="${starts[$i]}"
    end="${ends[$i]}"
    while [[ $(date -d "$current" +%s) -le $(date -d "$end" +%s) ]]; do
        echo "${current}-00 ${current}-21" >> "$outfile"
        current=$(date -d "$current + 1 day" +%Y-%m-%d)
    done
    
    echo "Created $outfile ($(wc -l < $outfile) days)"
done