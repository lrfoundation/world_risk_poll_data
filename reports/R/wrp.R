# Shared helpers for reproducing the World Risk Poll reports in R.
#
# The R counterpart of reports/wrp/ (Python): same function names, same
# conventions, same outputs. See reports/README.md.
#
# Requires: arrow, dplyr
#   install.packages(c("arrow", "dplyr"))

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
})

# Repository root: two levels above this file (reports/R/wrp.R).
WRP_ROOT <- local({
  this <- tryCatch(sys.frame(1)$ofile, error = function(e) NULL)
  if (!is.null(this)) {
    normalizePath(file.path(dirname(this), "..", ".."))
  } else {
    d <- normalizePath(getwd())
    while (!dir.exists(file.path(d, "WRP_2019")) && dirname(d) != d) d <- dirname(d)
    d
  }
})

# Fieldwork year -> wave number. Report folders use the fieldwork year.
WAVES <- c("2019" = 1L, "2021" = 2L, "2023" = 3L, "2025" = 4L)

# The 37-variable harmonised block (docs/CODEBOOK.md).
HARMONISED_COLS <- c(
  "WPID_RANDOM", "Wave", "Year", "WP5", "Country", "COUNTRY_ISO2",
  "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT",
  "Age", "AgeGroups3", "AgeGroups4", "AgeGroups5", "Gender", "Education",
  "Urbanicity", "Urbanicity2", "EMP_2010", "INCOME_5", "HouseholdSize",
  "ChildrenInHousehold", "worry_score", "worry_score_core7",
  "worry_index_published", "experience_score", "experience_score_self",
  "experience_score_core7", "experience_index_published", "worry_exp_gap",
  "resilience_index", "resilience_index_100", "resilience_idv",
  "resilience_hhl", "resilience_com", "resilience_soc"
)

DEFAULT_WEIGHT <- "PROJWT"

# --- Data ---------------------------------------------------------------

data_path <- function(year, fmt = "parquet") {
  if (!as.character(year) %in% names(WAVES)) {
    stop(sprintf("No World Risk Poll wave for %s", year))
  }
  file.path(WRP_ROOT, sprintf("WRP_%s", year), sprintf("WRP_%s.%s", year, fmt))
}

# Load one wave from its Parquet file, optionally only some columns.
load_wave <- function(year, columns = NULL) {
  if (is.null(columns)) {
    as.data.frame(read_parquet(data_path(year)))
  } else {
    as.data.frame(read_parquet(data_path(year), col_select = all_of(columns)))
  }
}

# Stack several waves on the harmonised block (or a subset of it).
stack_waves <- function(years, columns = HARMONISED_COLS) {
  bind_rows(lapply(years, load_wave, columns = columns))
}

.dictionaries <- new.env()

# The wave's data dictionary: one row per variable.
dictionary <- function(year) {
  key <- as.character(year)
  if (is.null(.dictionaries[[key]])) {
    path <- file.path(WRP_ROOT, sprintf("WRP_%s", year), sprintf("WRP_%s_data_dictionary.csv", year))
    # arrow reads UTF-8 whatever the system locale; base read.csv can stop
    # part-way through the file under a non-UTF-8 locale.
    .dictionaries[[key]] <- as.data.frame(read_csv_arrow(path))
  }
  .dictionaries[[key]]
}

# Code -> label mapping for a categorical variable, as a named character
# vector (names are the codes).
value_labels <- function(year, variable) {
  dd <- dictionary(year)
  raw <- dd$value_labels[dd$variable == variable]
  if (length(raw) == 0) stop(sprintf("%s is not in the %s data dictionary", variable, year))
  if (is.na(raw) || raw == "") return(character(0))
  parts <- strsplit(raw, " | ", fixed = TRUE)[[1]]
  codes <- sub(" = .*$", "", parts)
  labels <- sub("^[^=]+ = ", "", parts)
  setNames(labels, as.character(as.integer(as.numeric(codes))))
}

variable_label <- function(year, variable) {
  dd <- dictionary(year)
  dd$label[dd$variable == variable]
}

# ISO3 codes of countries surveyed in every one of `years`.
countries_in_all <- function(years) {
  sets <- lapply(years, function(y) unique(load_wave(y, "COUNTRY_ISO3")$COUNTRY_ISO3))
  sort(Reduce(intersect, sets))
}

# --- Weighted estimates -------------------------------------------------
# Same conventions as reports/wrp/stats.py: PROJWT by default; rows where
# the variable is missing are dropped; DK/refused stay in the base unless
# listed in `exclude`.

.group_keys <- function(d, by) {
  do.call(paste, c(lapply(by, function(b) as.character(d[[b]])), sep = "_"))
}

.by_groups <- function(d, by, numerator, denominator) {
  if (is.null(by)) return(sum(numerator) / sum(denominator))
  keep <- stats::complete.cases(d[by])
  keys <- .group_keys(d[keep, , drop = FALSE], by)
  num <- rowsum(numerator[keep], keys, reorder = TRUE)
  den <- rowsum(denominator[keep], keys, reorder = TRUE)
  setNames(as.vector(num / den), rownames(num))
}

# Weighted mean of `value` over rows where it is present.
wmean <- function(df, value, weight = DEFAULT_WEIGHT, by = NULL) {
  d <- df[!is.na(df[[value]]), , drop = FALSE]
  .by_groups(d, by, d[[value]] * d[[weight]], d[[weight]])
}

# Weighted % of respondents whose `var` is one of `codes`.
pct <- function(df, var, codes, weight = DEFAULT_WEIGHT, by = NULL, exclude = NULL) {
  d <- df[!is.na(df[[var]]) & !(df[[var]] %in% exclude), , drop = FALSE]
  100 * .by_groups(d, by, d[[weight]] * (d[[var]] %in% codes), d[[weight]])
}

# Weighted % in every answer category of `var`: a named vector, or a
# matrix with one row per `by` group.
distribution <- function(df, var, weight = DEFAULT_WEIGHT, by = NULL, exclude = NULL, labels = NULL) {
  d <- df[!is.na(df[[var]]) & !(df[[var]] %in% exclude), , drop = FALSE]
  groups <- if (is.null(by)) rep("All", nrow(d)) else .group_keys(d, by)
  tab <- tapply(d[[weight]], list(groups, d[[var]]), sum)
  tab[is.na(tab)] <- 0
  tab <- 100 * tab / rowSums(tab)
  if (!is.null(labels)) colnames(tab) <- ifelse(colnames(tab) %in% names(labels), labels[colnames(tab)], colnames(tab))
  if (is.null(by)) tab[1, ] else tab
}

# --- Optional Gallup World Poll items ------------------------------------
# See reports/wrp/gallup.py for the full note. GWP items are Gallup's
# proprietary data and must be licensed from Gallup directly. Set
# GALLUP_WP_PATH to a .parquet or .csv file with WPID_RANDOM plus the
# items; without it, findings needing them are reported as GALLUP_ONLY.

gallup_data_required <- function(message) {
  structure(class = c("gallup_data_required", "error", "condition"),
            list(message = message, call = NULL))
}

load_gallup <- function(columns) {
  path <- Sys.getenv("GALLUP_WP_PATH")
  if (path == "") {
    stop(gallup_data_required(sprintf(
      "needs Gallup World Poll item(s) %s, which are not in the public release; license them from Gallup and set GALLUP_WP_PATH",
      paste(columns, collapse = ", ")
    )))
  }
  gwp <- switch(tolower(tools::file_ext(path)),
    parquet = as.data.frame(read_parquet(path)),
    csv = read.csv(path),
    stop("GALLUP_WP_PATH must point to a .parquet or .csv file")
  )
  wanted <- c("WPID_RANDOM", columns)
  missing <- setdiff(wanted, names(gwp))
  if (length(missing)) stop(gallup_data_required(sprintf("%s does not contain %s", basename(path), paste(missing, collapse = ", "))))
  gwp[wanted]
}

merge_gallup <- function(df, columns) {
  gwp <- load_gallup(columns)
  gwp <- gwp[!duplicated(gwp$WPID_RANDOM), , drop = FALSE]
  merged <- left_join(df, gwp, by = "WPID_RANDOM")
  matched <- mean(!is.na(merged[[columns[1]]]))
  if (matched < 0.9) message(sprintf("  warning: only %.0f%% of rows matched a Gallup World Poll record", 100 * matched))
  merged
}

# --- Public non-poll data -------------------------------------------------
# See reports/wrp/external.py. Files that may be redistributed are committed
# in reports/external/; others are downloaded by
# reports/external/fetch_external.py into reports/external/downloaded/.
# Without them, the findings that need them are reported as EXTERNAL_ONLY.

external_data_required <- function(message) {
  structure(class = c("external_data_required", "error", "condition"),
            list(message = message, call = NULL))
}

external_path <- function(name) {
  for (folder in file.path(WRP_ROOT, "reports", "external", c("", "downloaded"))) {
    path <- file.path(folder, name)
    if (file.exists(path)) return(normalizePath(path))
  }
  stop(external_data_required(sprintf(
    "needs %s, which is not redistributed here; run python reports/external/fetch_external.py to download it", name
  )))
}

# --- Report registry ------------------------------------------------------
# Mirrors reports/wrp/results.py. A finding function returns one value
# (recorded under its id), or a named vector / matrix (recorded as
# "<id>_<name>", "<id>_<row>_<col>").

wrp_report <- function(dir) {
  report <- new.env()
  report$dir <- normalizePath(dir)
  report$published <- read.csv(file.path(dir, "published_figures.csv"), colClasses = "character", na.strings = character(0))
  report$functions <- list()
  report
}

finding <- function(report, finding_id, fn) {
  report$functions[[length(report$functions) + 1]] <- list(id = finding_id, fn = fn)
  invisible(report)
}

.ids_for <- function(report, finding_id) {
  ids <- report$published$finding_id
  hit <- ids[ids == finding_id | startsWith(ids, paste0(finding_id, "_"))]
  if (length(hit)) hit else finding_id
}

.flatten <- function(finding_id, value) {
  if (is.matrix(value)) {
    grid <- expand.grid(r = rownames(value), c = colnames(value), stringsAsFactors = FALSE)
    return(data.frame(finding_id = paste(finding_id, grid$r, grid$c, sep = "_"), value = as.vector(value)))
  }
  if (length(value) > 1 || !is.null(names(value))) {
    return(data.frame(finding_id = paste(finding_id, names(value), sep = "_"), value = unname(value)))
  }
  data.frame(finding_id = finding_id, value = value)
}

.decimals <- function(x) ifelse(grepl(".", x, fixed = TRUE), nchar(sub("^[^.]*\\.", "", x)), 0)

.compare <- function(published, reproduced, tolerance) {
  pub <- suppressWarnings(as.numeric(published))
  rep <- suppressWarnings(as.numeric(reproduced))
  if (is.na(pub)) return(ifelse(tolower(trimws(reproduced)) == tolower(trimws(published)), "MATCH", "DIFFERENT"))
  if (is.na(rep)) return("DIFFERENT")
  if (round(rep, .decimals(published)) == pub) return("MATCH")
  if (abs(rep - pub) <= tolerance + 1e-9) "WITHIN_TOLERANCE" else "DIFFERENT"
}

run_report <- function(report) {
  rows <- list()
  for (f in report$functions) {
    result <- tryCatch(
      .flatten(f$id, f$fn()) |> transform(status = "ok", message = ""),
      gallup_data_required = function(e) data.frame(finding_id = .ids_for(report, f$id), value = NA, status = "GALLUP_ONLY", message = conditionMessage(e)),
      external_data_required = function(e) data.frame(finding_id = .ids_for(report, f$id), value = NA, status = "EXTERNAL_ONLY", message = conditionMessage(e)),
      error = function(e) data.frame(finding_id = .ids_for(report, f$id), value = NA, status = "ERROR", message = conditionMessage(e))
    )
    rows[[length(rows) + 1]] <- result
  }
  out <- do.call(rbind, rows)
  out$value <- if (is.numeric(out$value)) sprintf("%.17g", out$value) else as.character(out$value)
  out$value[out$value %in% c("NA", NA)] <- ""
  dir.create(file.path(report$dir, "output"), showWarnings = FALSE)
  write.csv(out, file.path(report$dir, "output", "reproduced_r.csv"), row.names = FALSE)

  pub <- report$published
  status <- vapply(seq_len(nrow(pub)), function(i) {
    hit <- out[out$finding_id == pub$finding_id[i], , drop = FALSE]
    if (nrow(hit) == 0) return("NOT_RUN")
    if (hit$status[1] != "ok") return(hit$status[1])
    tol <- if (nzchar(pub$tolerance[i])) as.numeric(pub$tolerance[i]) else 1
    .compare(pub$published_value[i], hit$value[1], tol)
  }, character(1))
  counts <- table(factor(status, levels = c("MATCH", "WITHIN_TOLERANCE", "DIFFERENT", "GALLUP_ONLY", "EXTERNAL_ONLY", "ERROR", "NOT_RUN")))
  counts <- counts[counts > 0]
  cat(sprintf("%d findings: %s\n", nrow(pub), paste(names(counts), counts, collapse = ", ")))
  for (i in which(status %in% c("DIFFERENT", "ERROR", "NOT_RUN"))) {
    hit <- out[out$finding_id == pub$finding_id[i], , drop = FALSE]
    message(sprintf("  %-10s %s: published %s, reproduced %s", status[i], pub$finding_id[i],
                    pub$published_value[i], if (nrow(hit)) hit$value[1] else "-"))
  }
  invisible(if (any(out$status == "ERROR")) 1L else 0L)
}
