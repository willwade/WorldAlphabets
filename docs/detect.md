# Language Detection

The runtime uses small Top-200 token lists stored under `data/freq/top200`. Each
file is a UTF-8 list of tokens in rank order. Languages without explicit word
boundaries contain a header line `# type=bigram` followed by character bigrams.

At runtime the directory can be overridden by setting the environment variable
`WORLDALPHABETS_FREQ_DIR` to a custom path.

Scores combine script/codepoint priors with token overlap using the weights
`PRIOR_WEIGHT` (default `0.65`) and `FREQ_WEIGHT` (default `0.35`). These
constants can also be overridden via environment variables
`WA_FREQ_PRIOR_WEIGHT` and `WA_FREQ_OVERLAP_WEIGHT`.
