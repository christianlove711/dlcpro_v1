# Target for complex_time_only_scope_test.csv

- CSV: `complex_time_only_scope_test.csv`
- Columns: `time, transmission, error1, error2`
- Answer key for offline testing: the correct peak is located near `time = 8.348` in this CSV trace.
- This is not a lock input and not a real device parameter. It is only the known peak location used to check whether the algorithm found the intended resonance.
- In the actual one-click workflow, the user should only load the CSV and click `One-click lock`; the algorithm should find this peak by changing `PZT center`, `bias offset`, and `scan span`.
- The CSV has no `pzt` column on purpose. Its `time` column is just the recorded trace axis for offline replay.
