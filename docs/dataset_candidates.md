# Dataset candidates

This comparison was performed on 2026-09-30 using original agency or research-repository pages. Rows marked “not stated” were not estimated. Dataset popularity was not used as a selection criterion.

| Dataset | Source | Rows | Important features | Location / time | Target | ML suitability | Limitations |
|---|---|---:|---|---|---|---|---|
| **River Water Quality Monitoring 1990–2024 — All Parameters** | [Northern Ireland Environment Agency (NIEA), via OpenDataNI](https://www.data.gov.uk/dataset/0840ab33-18ae-4670-8523-ac43105f5902/river-water-quality-monitoring-1990-to-2024-all-parameters) | **178,680** verified in the API and downloaded CSV; 40 columns | Alkalinity, BOD, conductivity, dissolved Cu/Fe/O₂, ammonia, nitrite, nitrate, soluble reactive phosphorus, pH, suspended solids, dissolved Zn | 1,311 Northern Ireland river stations; 1990–2024; dated sampling events with irregular frequency | No supervised risk/status label. Dissolved oxygen is a possible continuous regression outcome. | Strong: official provenance, large sample, long time coverage, coordinates, basins, repeated measurements, 13 chemistry variables, and a coherent river-monitoring story. | Uneven missingness; censored values; extreme values explicitly warned about by source; repeated sites and time create leakage risk; no temperature; no classification target. |
| **Water Quality Explorer** | [Environment Agency, England](https://www.data.gov.uk/dataset/583e771f-1af6-4934-b8f0-28f1d1ddd48c/water-quality-explorer) | More than 72 million observations from more than 5 million samples | Temperature, pH, conductivity, turbidity, salinity, nitrate, ammoniacal nitrogen, dissolved oxygen, metals, organics and many other determinands | Tens of thousands of sampling points across England; rivers, lakes, groundwater, canals and coastal/estuarine waters; since 2000 | No single dataset-wide target | Potentially excellent after a carefully bounded API extract for one water type, region, period and group of determinands. | Far too broad for a first student dataset without substantial query design; long-format observations require pivoting and unit/determinand harmonisation; mixed water types must not be treated as interchangeable. |
| **Waterbase — Water Quality ICM 2026** | [European Environment Agency](https://www.eea.europa.eu/en/datahub/datahubitem-view/fbf3717c-cd7b-4785-933a-d0cf510542e1/image_icon) | Not stated on the landing page; multiple large normalised tables | Nutrients, organic matter, hazardous substances, pesticides and other chemicals | European rivers, lakes, groundwater and transitional/coastal/marine waters; reported coverage 1900–2025 | No single supervised target | Strong for cross-country or time-series research after filtering by water-body type, determinand, unit and reporting country. | Complex relational structure, heterogeneous reporting, mixed water types, very large scope, and substantial harmonisation requirements make it less beginner-friendly. |
| **LOCATE: monthly river chemistry and organic matter** | [NERC Environmental Information Data Centre](https://catalogue.ceh.ac.uk/id/08223cdd-5e01-43ad-840d-15ff81e58acf) | Not stated on the catalogue page; monthly sampling at 41 rivers | Ammonia, nitrate, phosphate, alkalinity, pH, particulate/dissolved organic carbon, isotopes, fluorescence and absorbance | 41 rivers across Great Britain during 2017 | No supervised target | Strong documentation and focused research design make it good for multivariate exploration or regression. | One-year collection period and a much smaller sampling frame limit long-term temporal modelling. Some variables are specialised for carbon-transfer research rather than general water-quality prediction. |
| **National Lakes Assessment 2017** | [US Environmental Protection Agency](https://www.epa.gov/national-aquatic-resource-surveys/reports-and-data-national-lakes-assessment-2017) | Not stated on the landing page; distributed across linked files | Water chemistry, hydrographic profiles, chlorophyll-a, Secchi depth, habitat, biological indicators and site information | Probability-based survey of lakes in the conterminous United States during 2017 | Separate EPA condition-estimate files contain documented assessment classes; they are ecological-condition indicators, not drinking-water safety labels. | Strong scientific design and documentation; could support a carefully defined classification or regression study after justified joins. | Data are split across indicator files; joins and survey weights require care; lake-condition classes answer a different question from river chemistry and must not be relabelled as “safe/unsafe.” |

## Recommendation

Select **NIEA River Water Quality Monitoring 1990–2024 — All Parameters** for this project.

Why it best fits WaterSense AI:

- **Scientific credibility:** it comes from the NIEA water-quality database and is published by the Northern Ireland government under the UK Open Government Licence.
- **Useful scale:** 178,680 sampling events are large enough for robust exploratory work while the 31.7 MB CSV remains practical on a student computer.
- **Relevant measurements:** 13 reported chemistry variables include BOD, conductivity, dissolved oxygen, ammonia, nitrate, nitrite, phosphorus and pH.
- **Environmental context:** station identifiers, coordinates, locations, primary basins, dates and times permit spatial and temporal analysis.
- **Explainability potential:** a later regression study could examine which measured variables are most predictive of dissolved oxygen, while clearly treating importance as association rather than causation.
- **Honest limitations:** the official source itself warns about possible erroneous extremes, and the export preserves detection-limit qualifiers. These issues create a credible data-cleaning and methodological story rather than an artificially tidy exercise.

The selection does **not** justify a water-safety classification. The source explicitly says that raw data cannot be used to provide status without processing, and the file contains no ecological-status or regulatory-compliance target.

## Licence notes

- NIEA/OpenDataNI: [UK Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- LOCATE: UK Open Government Licence, with dataset citation requested by the repository.
- Licence details for the EEA and EPA candidates should be rechecked on the exact downloaded products before reuse; they were not needed for the selected dataset.

