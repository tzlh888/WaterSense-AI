# Extreme-value review

**Dataset inspected:** NIEA River Water Quality Monitoring 1990–2024 — All Parameters  
**Inspection date:** 2026-09-30

No value was removed in this review. “Outside 1.5 × IQR” is a statistical flag, not proof of measurement error. The official source warns that typos, sampling error or contamination may create values several orders of magnitude above expected values, but it does not identify which individual records are erroneous.

## Distribution review

| Variable | Min | Median | 95th percentile | 99th percentile | Max | Outside 1.5 × IQR |
|---|---:|---:|---:|---:|---:|---:|
| BOD (mg/L) | 0.5 | 2.0 | 4.6 | 9.3 | 632.0 | 13,978 |
| Conductivity (µS/cm) | 5 | 265 | 563 | 736 | 39,900 | 2,715 |
| Dissolved oxygen (mg/L) | 0.1 | 10.5 | 12.9 | 14.5 | 41.9 | 5,028 |
| Soluble reactive phosphorus (mg/L) | 0.001 | 0.05 | 0.303 | 0.86 | 67.0 | 16,160 |
| Suspended solids (mg/L) | 1 | 4 | 26 | 85 | 3,232 | 9,913 |

## Records associated with the largest values

| Variable | Value | Station | Date |
|---|---:|---|---|
| BOD | 632.0 mg/L | `UKGBNIF10565` | 1993-06-10 |
| BOD | 465.0 mg/L | `UKGBNIF10566` | 1993-10-08 |
| BOD | 415.0 mg/L | `UKGBNIF10566` | 1993-08-24 |
| Conductivity | 39,900 µS/cm | `UKGBNIF10564` | 1996-04-10 |
| Conductivity | 37,200 µS/cm | `UKGBNIF10564` | 1996-06-07 |
| Conductivity | 33,400 µS/cm | `UKGBNIF10564` | 1998-05-28 |
| Dissolved oxygen | 41.9 mg/L | `UKGBNIF10608` | 1992-11-06 |
| Dissolved oxygen | 36.3 mg/L | `UKGBNIF10511` | 1992-12-09 |
| Dissolved oxygen | 35.4 mg/L | `UKGBNIF10531` | 1992-09-02 |
| Soluble reactive phosphorus | 67.0 mg/L | `UKGBNIF10525` | 1990-12-06 |
| Soluble reactive phosphorus | 23.0 mg/L | `UKGBNIF10500` | 1990-05-02 |
| Soluble reactive phosphorus | 14.54 mg/L | `UKGBNIF10703` | 1991-06-02 |
| Suspended solids | 3,232 mg/L | `UKGBNIF10501` | 1995-01-06 |
| Suspended solids | 3,232 mg/L | `UKGBNIF10569` | 1992-02-12 |
| Suspended solids | 2,940 mg/L | `UKGBNIF10763` | 2002-02-28 |

## Interpretation

- Several maxima are far above their 99th percentiles and deserve source-level review.
- Repeated high conductivity values at `UKGBNIF10564` and repeated high BOD or suspended-solids values at some stations show that rarity alone cannot distinguish site conditions from errors.
- The extreme records are concentrated in earlier years, but this observation does not identify a cause or prove a historical measurement problem.
- A legitimate high-flow, pollution or unusual site event can be a statistical outlier. Conversely, a plausible-looking value can still be erroneous.
- No documented evidence currently proves that any listed record is wrong.

## Phase 3 decision

The baseline retains all eligible uncensored target values, including extreme values. Model errors will be inspected across the dissolved-oxygen distribution, including its lowest and highest test-set deciles. No winsorisation, clipping or automatic IQR deletion is applied. If later source documentation verifies an error, exclusion must be recorded by source row, reason and evidence.

