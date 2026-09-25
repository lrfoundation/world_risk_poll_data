# Reproduce World Risk Poll 2024 Focus On: Risk perceptions and experiences of ocean workers.
#
# Run from the repository root:
#   Rscript reports/WRP_2023/focus_on_ocean_workers/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

d <- load_wave(2023, c(
  "PROJWT", "EMP_2010", "WP23340", "WP22331", "WP20719", "WP20723", "WP22445",
  "WP22214", "WP22448", "WP23335", "WP23337", "WP23338"
))

# --- Derived variables ---------------------------------------------------------

# Ocean workers: Job Sector (Coded) WP23340 = 2 "Fishing", whatever the
# respondent's current employment status (478 respondents). The public
# release has no code for shipping, ports or offshore work.
OCEAN <- 2
d$ocean <- d$WP23340 %in% OCEAN

# Other workers: the current workforce (EMP_2010 1-5: employed full or part
# time, self-employed or unemployed; not out of the workforce) who are not
# ocean workers. The sector charts use the same current workforce.
d$workforce <- d$EMP_2010 %in% 1:5
d$group <- ifelse(d$ocean, 1, ifelse(d$workforce, 2, NA)) # 1 = ocean, 2 = other workers

# Chart 1.2 compares ocean workers with every other respondent.
d$group_all <- ifelse(d$ocean, 1, 2)

# OSH training (Chart 2.4): 1 = trained in the past two years, 2 = trained
# more than two years ago, 3 = not trained, or trained with no answer on
# when. Base: everyone asked WP23337.
d$osh_timing <- with(d, case_when(
  WP23337 %in% 1 & WP23338 %in% 1 ~ 1,
  WP23337 %in% 1 & WP23338 %in% 2 ~ 2,
  !is.na(WP23337) ~ 3,
  TRUE ~ NA_real_
))

# Unweighted count, for Chart 2.2 (see README).
d$UNWEIGHTED <- 1

PERSONALLY <- c(1, 3) # experienced harm: 1 = yes, personally; 3 = both personally and someone known
WORRIED <- c(1, 2)    # very or somewhat worried
SECTORS <- c(         # WP23340 codes of the other sectors in Charts 2.2 and 2.3
  construction = 4, mining = 5, agriculture = 1, market_services = 7,
  non_market_services = 8, manufacturing = 3, utilities = 6
)
SECTOR_NAMES <- c(ocean = "Ocean workers", construction = "Construction", mining = "Mining and quarrying",
                  agriculture = "Agriculture (excluding fishing)", market_services = "Market services",
                  non_market_services = "Non-market services", manufacturing = "Manufacturing",
                  utilities = "Electricity, gas or water supply")

# --- Helpers -------------------------------------------------------------------

# % of ocean workers and of other workers whose `var` is in `codes`.
by_group <- function(var, codes, groups = "group") {
  r <- pct(d, var, codes, by = groups)
  c(ocean = unname(r["1"]), other = unname(r["2"]))
}

# % by sector: ocean workers (PROJWT) and the current workforce of each other sector.
by_sector <- function(var, codes, weight = "PROJWT") {
  workforce <- d[d$workforce, ]
  c(ocean = pct(d[d$ocean, ], var, codes),
    sapply(SECTORS, function(code) pct(workforce[workforce$WP23340 %in% code, ], var, codes, weight = weight)))
}

# % very or somewhat worried about harm from work, as in Chart 2.2.
work_worry_by_sector <- function() {
  very <- by_sector("WP22214", 1, weight = "UNWEIGHTED")
  some <- by_sector("WP22214", 2, weight = "UNWEIGHTED")
  very["ocean"] <- pct(d[d$ocean, ], "WP22214", 1)
  some["ocean"] <- pct(d[d$ocean, ], "WP22214", 2)
  list(very = very, some = some)
}

# Rank of ocean workers (1 = highest) among the sectors in `values`.
rank_of_ocean <- function(values) 1 + sum(values[names(values) != "ocean"] > values[["ocean"]])

# --- Climate change and ocean workers ---------------------------------------------

finding(report, "X01", function() pct(d, "WP20719", c(1, 2)))
finding(report, "X02", function() pct(d, "WP22331", 19))
finding(report, "X03", function() by_group("WP22331", 19)[["ocean"]])
finding(report, "X04", function() {
  r <- by_group("WP22331", 19)
  r[["ocean"]] - r[["other"]]
})
finding(report, "X05", function() by_group("WP22331", 19)[["other"]])
finding(report, "X06", function() {
  r <- by_group("WP22331", 19)
  r[["ocean"]] / r[["other"]]
})
finding(report, "X07", function() by_group("WP20719", c(1, 2))[["ocean"]])
finding(report, "X08", function() by_group("WP20719", c(1, 2))[["other"]])

finding(report, "C1_1", function() by_group("WP22331", 19))
finding(report, "C1_2", function() {
  cats <- list(very = 1, somewhat = 2, dk = c(98, 99), not = 3)
  out <- c()
  for (key in names(cats)) {
    r <- by_group("WP20719", cats[[key]], groups = "group_all")
    out[paste0(names(r), "_", key)] <- r
  }
  out
})

finding(report, "X09", function() by_group("WP20723", WORRIED)[["ocean"]])
finding(report, "X10", function() by_group("WP20723", WORRIED)[["other"]])
finding(report, "X11", function() by_group("WP20723", 1)[["ocean"]])
finding(report, "X12", function() by_group("WP20723", 1)[["other"]])
finding(report, "X13", function() pct(d, "WP20723", 1))
finding(report, "X14", function() by_group("WP22445", PERSONALLY)[["ocean"]])
finding(report, "X15", function() by_group("WP22445", PERSONALLY)[["other"]])

finding(report, "C1_3", function() {
  very <- by_group("WP20723", 1)
  some <- by_group("WP20723", 2)
  c(ocean_very = very[["ocean"]], ocean_somewhat = some[["ocean"]],
    other_very = very[["other"]], other_somewhat = some[["other"]])
})
finding(report, "C1_4", function() by_group("WP22445", PERSONALLY))

# --- The cost of work at sea ----------------------------------------------------------

finding(report, "X16", function() by_group("WP22331", 17)[["ocean"]])
finding(report, "X17", function() by_group("WP22331", 17)[["other"]])
finding(report, "X18", function() {
  r <- by_group("WP22331", 17)
  r[["ocean"]] / r[["other"]]
})
finding(report, "C2_1", function() by_group("WP22331", 17))

finding(report, "X19", function() by_group("WP22214", WORRIED)[["ocean"]])
finding(report, "X20", function() by_group("WP22214", WORRIED)[["other"]])
finding(report, "X21", function() by_group("WP22214", 1)[["ocean"]])
finding(report, "X22", function() by_group("WP22214", 1)[["other"]])
finding(report, "X23", function() {
  w <- work_worry_by_sector()
  rank_of_ocean(w$very + w$some)
})
finding(report, "X24", function() {
  w <- work_worry_by_sector()
  total <- w$very + w$some
  unname(SECTOR_NAMES[names(total)[which.max(total)]])
})
finding(report, "X25", function() by_group("WP22448", PERSONALLY)[["ocean"]])
finding(report, "X26", function() by_group("WP22448", PERSONALLY)[["other"]])
finding(report, "X27", function() rank_of_ocean(by_sector("WP22448", PERSONALLY)))

finding(report, "C2_2", function() {
  w <- work_worry_by_sector()
  out <- c()
  for (key in names(w$very)) {
    out[paste0(key, "_very")] <- w$very[[key]]
    out[paste0(key, "_somewhat")] <- w$some[[key]]
  }
  out
})
finding(report, "C2_3", function() {
  # global: the current workforce, all sectors
  c(by_sector("WP22448", PERSONALLY), global = pct(d[d$workforce, ], "WP22448", PERSONALLY))
})

finding(report, "X28", function() by_group("WP23337", 1)[["ocean"]])
finding(report, "X29", function() by_group("WP23337", 1)[["other"]])
finding(report, "X30", function() by_group("osh_timing", 1)[["ocean"]])
finding(report, "C2_4", function() {
  recent <- by_group("osh_timing", 1)
  older <- by_group("osh_timing", 2)
  c(ocean_recent = recent[["ocean"]], ocean_older = older[["ocean"]],
    other_recent = recent[["other"]], other_older = older[["other"]])
})

finding(report, "X31", function() by_group("WP23335", 1)[["ocean"]])
finding(report, "X32", function() by_group("WP23335", 1)[["other"]])
finding(report, "C2_5", function() by_group("WP23335", 1))

status <- run_report(report)
if (!interactive()) quit(status = status)
