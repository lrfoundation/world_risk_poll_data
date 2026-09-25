# Reproduce the findings of <REPORT TITLE> (<wave> data).
#
# Run from the repository root:
#   Rscript reports/WRP_YYYY/<report_folder>/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

df <- load_wave(2019, c("WPID_RANDOM", "PROJWT", "Gender", "L5"))

# L5: 1 = very serious threat. DK/refused stay in the base.
finding(report, "F01", function() pct(df, "L5", 1))

# One value per group -> F02_1 (men), F02_2 (women).
finding(report, "F02", function() pct(df, "L5", 1, by = "Gender"))

# Needs a Gallup World Poll item; GALLUP_ONLY without GALLUP_WP_PATH.
finding(report, "F03", function() pct(merge_gallup(df, "WP_EXAMPLE"), "WP_EXAMPLE", 1))

status <- run_report(report)
if (!interactive()) quit(status = status)
