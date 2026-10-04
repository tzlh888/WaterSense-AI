| strategy | sample_count | mae | rmse | r2 | bias | mean_actual | mean_predicted | median_absolute_error | p90_absolute_error | p95_absolute_error | train_rows | test_rows | train_stations | test_stations | station_overlap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Random rows | 30207 | 0.8410 | 1.3285 | 0.5363 | -0.0100 | 10.3290 | 10.3390 | 0.5662 | 1.8207 | 2.5115 | 120824 | 30207 | 833 | 813 | 806 |
| Unseen stations | 31341 | 0.8312 | 1.2911 | 0.5391 | -0.0301 | 10.3345 | 10.3645 | 0.5654 | 1.7972 | 2.5018 | 119690 | 31341 | 672 | 168 | 0 |
| Future years | 9676 | 0.6730 | 0.9557 | 0.6646 | -0.2410 | 10.2834 | 10.5244 | 0.4943 | 1.4003 | 1.8924 | 132766 | 9676 | 832 | 508 | 500 |
| Spatiotemporal Holdout | 1828 | 0.6918 | 1.0241 | 0.6429 | -0.2461 | 10.3044 | 10.5505 | 0.4947 | 1.3952 | 2.0123 | 120955 | 1828 | 733 | 101 | 0 |
