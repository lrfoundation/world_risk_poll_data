# Reports on the World Risk Poll 2025 (wave 4)

The 2025 poll: fieldwork in 2025, 143,459 respondents in 140 countries and areas. Its reports are published as the *World Risk Poll 2026* reports.

Data: [`WRP_2025/`](../../WRP_2025/). Each folder below reproduces one report in Python and R; see [`reports/README.md`](../README.md) for how to run them and the conventions they share.

| Folder | Report | Type | Published |
| --- | --- | --- | --- |
| [`core_alone_together`](core_alone_together/) | [Alone Together: The hidden consensus on climate change](https://www.lrfoundation.org.uk/sites/default/files/2026-09/wrp-report-2026-the-hidden-consensus-on-climate-change.pdf) | Core report | 2026-06 |
| [`core_the_quiet_hazards`](core_the_quiet_hazards/) | [The Quiet Hazards: How everyday risk shapes daily life](https://www.lrfoundation.org.uk/sites/default/files/2026-09/world-risk-poll-report-2026-how-everyday-risk-shapes-daily-life.pdf) | Core report | 2026-06 |
| [`core_after_the_storm`](core_after_the_storm/) | [After the storm: How disasters reshape resilience and trust](https://doi.org/10.60743/16n7-bn41) | Core report | Not yet published |
| [`core_early_warnings`](core_early_warnings/) | [From alert to agency: What turns warnings into action?](https://doi.org/10.60743/yx1k-t541) | Core report | Not yet published |
| [`core_a_resilient_life`](core_a_resilient_life/) | [A resilient life: How wellbeing shapes the capacity to cope](https://doi.org/10.60743/sbwn-m411) | Core report | Not yet published |

## Reports not yet published

*After the storm*, *From alert to agency* and *A resilient life* are reproduced from pre-publication
drafts. Their figures and page numbers may change before launch, and their DOI links work only once
they are published. When one of them launches:

1. Check the final PDF against the report's `published_figures.csv` (values and page numbers). Edit
   the CSV where they differ, then rerun `reproduce.R` and `reproduce.py`.
2. In the report's README, delete the "Not yet published" note and link the final PDF.
3. In the table above and in [`reports/report_inventory.csv`](../report_inventory.csv), set the
   publication month and the PDF link. Update the counts in [`reports/README.md`](../README.md).
4. Run `Rscript reports/run_all.R`, then `python reports/run_all.py` to refresh
   [`REPRODUCTION_SUMMARY.md`](../REPRODUCTION_SUMMARY.md).
