# collapsed-branches

Demonstrates the subjective `branch_count_aligned` failure mode. The function `read_csv` has four observably different branches (encoding error, csv.Error, empty result, success path), but the CREQ is a single shall-clause that only describes the success path. Score 1: the mechanical axes all pass, but the subjective axis flags the collapse. Remediation splits the CREQ or enumerates the four branches.
