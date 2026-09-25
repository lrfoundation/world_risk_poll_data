# External (non-poll) data

A few report findings compare World Risk Poll results with public data from other
organisations, for example GDP per capita or a rule-of-law score. This folder holds that
data. The rules are:

- **Committed** files are snapshots whose licence allows redistribution alongside this
  repository (CC BY 4.0, or Lloyd's Register Foundation's own material). Each is named
  `<report_folder>__<source>.csv`.
- **Not committed** files have no open licence, or allow only non-commercial use. Download
  them with `fetch_external.py`, which saves them to `downloaded/` (ignored by git):

  ```
  pip install pandas openpyxl
  python reports/external/fetch_external.py        # every source
  python reports/external/fetch_external.py wjp    # one source
  ```

  Without them, the findings that need them are reported as `EXTERNAL_ONLY`, and every
  other finding still runs.

Providers revise their data, so a new download can differ slightly from what a report
used. Each report's README records the release and year used, and the download date.

| File | Source | Licence | Used by | In repo? |
| --- | --- | --- | --- | --- |
| `core_engineering_safer_workplaces__worldbank_NY.GDP.PCAP.CD.csv` | World Bank, World Development Indicators: GDP per capita (current US$) | CC BY 4.0 | `WRP_2023/core_engineering_safer_workplaces` | Yes |
| `core_engineering_safer_workplaces__wrp_interview_mode.csv` | Interview mode by country, from the World Risk Poll 2021 and 2023 methodology reports | Lloyd's Register Foundation, CC BY-SA 4.0 | `WRP_2023/core_engineering_safer_workplaces` | Yes |
| `focus_on_fossil_fuels_and_climate_change__worldbank_TX.VAL.FUEL.ZS.UN.csv` | World Bank, WDI: fuel exports (% of merchandise exports) | CC BY 4.0 | `WRP_2021/focus_on_fossil_fuels_and_climate_change` | Yes |
| `core_a_digital_world__wjp_rule_of_law_index_2021.csv` | World Justice Project Rule of Law Index 2021, overall score | No open licence; free download, cite the WJP Rule of Law Index | `WRP_2021/core_a_digital_world` | No: `fetch_external.py wjp` |
| `core_alone_together__ndgain_vulnerability.csv` | ND-GAIN Country Index, 2024 release: vulnerability | No formal licence ("free and open-access"); cite ND-GAIN, University of Notre Dame | `WRP_2025/core_alone_together` | No: `fetch_external.py ndgain` |
| `core_resilience_in_a_changing_world__worldbank.csv` | World Bank, WDI: GDP per capita, GDP growth and inflation | CC BY 4.0 | `WRP_2023/core_resilience_in_a_changing_world` | Yes |
| `core_the_quiet_hazards__worldbank_pm25.csv` | World Bank, WDI: PM2.5 mean annual exposure (`EN.ATM.PM25.MC.M3`) | CC BY 4.0 | `WRP_2025/core_the_quiet_hazards` | Yes |
| `core_the_quiet_hazards__gwis_burned_area.csv` | Global Wildfire Information System (European Commission JRC / Copernicus), 2025 burned area by country | Copernicus data policy: free, full and open access, redistribution allowed with attribution (Delegated Regulation (EU) No 1159/2013); cite GWIS | `WRP_2025/core_the_quiet_hazards` | Yes |
| `core_world_risk_poll_2019__worldbank.csv` | World Bank, WDI: 7 indicators (GDP per capita and growth, Gini, death rate, injury deaths, basic drinking water, climate-hazard exposure) | CC BY 4.0 | `WRP_2019/core_world_risk_poll_2019` | Yes |
| `core_world_risk_poll_2019__worldbank_gdp.csv` | World Bank, WDI: GDP per capita (current US$, PPP current and PPP constant) | CC BY 4.0 | `WRP_2019/core_world_risk_poll_2019` | Yes |
| `core_world_risk_poll_2019__worldbank_SI.POV.GINI.csv` | World Bank, WDI: Gini index (Chapter 8) | CC BY 4.0 | `WRP_2019/core_world_risk_poll_2019` | Yes |
| `core_world_risk_poll_2019__freedom_house.csv` | Freedom House, Freedom in the World 2020 | Free for non-commercial use; commercial use needs permission | `WRP_2019/core_world_risk_poll_2019` | No: `fetch_external.py freedomhouse` |
| `core_world_risk_poll_2019__who_seatbelt_laws.csv` | WHO, Global status report on road safety 2018, Table A7 (seat-belt laws), parsed from the PDF (needs poppler's `pdftotext`) | CC BY-NC-SA 3.0 IGO (non-commercial) | `WRP_2019/core_world_risk_poll_2019` | No: `fetch_external.py who_seatbelt` |
| `core_world_risk_poll_2019__ul_safety_index.csv` | UL Safety Index (safety frameworks) | Discontinued in April 2020 and no longer published | `WRP_2019/core_world_risk_poll_2019` (X5_41) | No, and it cannot be downloaded: X5_41 stays `EXTERNAL_ONLY` unless you have a copy |
| `focus_on_migration_in_a_warming_world__ndgain_scores.csv` | ND-GAIN Country Index, 2024 release: overall score, readiness and vulnerability by year | No formal licence ("free and open-access"); cite ND-GAIN, University of Notre Dame | `WRP_2023/focus_on_migration_in_a_warming_world` | No: `fetch_external.py ndgain_scores` |
