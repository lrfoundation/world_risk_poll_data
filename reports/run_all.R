# Run every report's reproduce.R.
#
# Run from the repository root:
#   Rscript reports/run_all.R                # every report
#   Rscript reports/run_all.R WRP_2021       # only folders whose path contains WRP_2021
#
# Each script writes output/reproduced_r.csv in its report folder and prints
# how its figures compare with the published ones. Run reports/run_all.py
# afterwards to fold the R results into each RESULTS.md and the summary.

args <- commandArgs(trailingOnly = TRUE)
pattern <- if (length(args)) args[1] else ""

scripts <- sort(Sys.glob(file.path("reports", "WRP_*", "*", "reproduce.R")))
scripts <- scripts[grepl(pattern, scripts, fixed = TRUE)]
if (!length(scripts)) {
  message("No reproduce.R scripts found. Run this from the repository root.")
}

rscript <- file.path(R.home("bin"), "Rscript")
failed <- character(0)
for (s in scripts) {
  cat(sprintf("\n== %s\n", dirname(s)))
  if (system2(rscript, s) != 0) failed <- c(failed, dirname(s))
}

if (length(failed)) {
  cat("\nScripts with code errors:\n", paste0("  ", failed, "\n"), sep = "")
  quit(status = 1)
}
