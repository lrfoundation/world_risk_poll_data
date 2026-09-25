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
