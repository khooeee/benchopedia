#!/bin/sh
# Downloads the outside datasets that scripts/import-scores.ts reads into .cache/sources/.
#   Epoch AI benchmark data (CC BY 4.0)       https://epoch.ai/benchmarks
#   Benchmark Radar scores (MIT; mixes sources) https://huggingface.co/datasets/ktwu01/benchmark-radar
set -eu
dir=.cache/sources
mkdir -p "$dir/epoch"
curl -fsSL -o "$dir/benchmark_data.zip" https://epoch.ai/data/benchmark_data.zip
unzip -oq "$dir/benchmark_data.zip" -d "$dir/epoch"
curl -fsSL -o "$dir/radar_scores.jsonl" https://huggingface.co/datasets/ktwu01/benchmark-radar/resolve/main/data/scores.jsonl
echo "sources ready in $dir"
