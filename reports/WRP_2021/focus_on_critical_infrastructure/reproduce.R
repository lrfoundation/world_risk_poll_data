# Reproduce World Risk Poll 2021 Focus On: Critical infrastructure resilience and
# perceptions of disaster preparedness.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/focus_on_critical_infrastructure/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

REGIONS <- c( # GlobalRegion code -> key
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america_caribbean", "6" = "northern_america", "7" = "central_asia", "8" = "east_asia",
  "9" = "south_eastern_asia", "10" = "south_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
)
# Went without for more than a day in the past 12 months (1 = yes).
SERVICES <- c(electricity = "WP22254", water = "WP22255", food = "WP22256",
              medicine = "WP22257", telephone = "WP22258")
EASTERN_AFRICA <- c("MOZ", "TZA", "UGA", "ZWE", "ZMB", "KEN", "MUS") # Chart 7

d <- load_wave(2021, c(
  "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "WP22245", "WP22241", "WP22526", "WP22244", "WP22252",
  unname(SERVICES)
))

# --- Derived variables ---------------------------------------------------------

d$region <- unname(REGIONS[as.character(d$GlobalRegion)])

# National government well prepared: WP22241. Myanmar was asked about "the
# government in power" (WP22526) instead; it is used there.
d$national <- ifelse(is.na(d$WP22241), d$WP22526, d$WP22241)
LOCAL <- "WP22244" # local government well prepared (1 = yes, well prepared)

# Lost access to at least one of the five services (does not apply, DK and
# refused count as no; everyone is in the base).
d$lost_any <- ifelse(rowSums(d[SERVICES] == 1, na.rm = TRUE) > 0, 1, 2)
disaster <- d[d$WP22245 %in% 1, ] # experienced a disaster in the past five years
no_disaster <- d[d$WP22245 %in% 2, ]
disaster_lost <- disaster[disaster$lost_any == 1, ]

# --- Helpers -------------------------------------------------------------------

# Percentage-point gap: % national government well prepared minus % local.
# Each percentage uses the respondents asked that question (DK/refused kept).
national_minus_local <- function(df, by = NULL) {
  n <- pct(df, "national", 1, by = by)
  l <- pct(df, LOCAL, 1, by = by)
  if (is.null(by)) return(n - l)
  k <- intersect(names(n), names(l))
  n[k] - l[k]
}

# Mean perceived governmental preparedness: mean of the national and local %.
mean_preparedness <- function(df, by = NULL) {
  n <- pct(df, "national", 1, by = by)
  l <- pct(df, LOCAL, 1, by = by)
  if (is.null(by)) return((n + l) / 2)
  k <- intersect(names(n), names(l))
  (n[k] + l[k]) / 2
}

# Chart 7: the mean over the five services of fn() among those who experienced
# a disaster and lost that service.
over_services <- function(fn, by = NULL) {
  parts <- lapply(SERVICES, function(var) fn(disaster[disaster[[var]] %in% 1, ], by = by))
  if (is.null(by)) return(mean(unlist(parts)))
  k <- Reduce(intersect, lapply(parts, names))
  Reduce(`+`, lapply(parts, function(p) p[k])) / length(parts)
}

# Table 1: mean preparedness, % experienced a disaster and its rank, by country.
country_table <- function() {
  m <- mean_preparedness(d, by = "COUNTRY_ISO3")
  dis <- pct(d, "WP22245", 1, by = "COUNTRY_ISO3")[names(m)]
  data.frame(mean = m, disaster = dis, rank = rank(-dis, ties.method = "min"), row.names = names(m))
}

half_up <- function(x) floor(x + 0.5)

lost_by_service <- function(df) sapply(SERVICES, function(var) pct(df, var, 1))

# --- Page 1: summary ---------------------------------------------------------------

finding(report, "X01", function() pct(d, "lost_any", 1))
finding(report, "X02", function() pct(disaster, "lost_any", 1))
finding(report, "X03", function() pct(d, "national", 1))
finding(report, "X04", function() pct(d, LOCAL, 1))
finding(report, "X05", function() national_minus_local(d))
finding(report, "X06", function() national_minus_local(disaster[disaster[[SERVICES[["water"]]]] %in% 1, ]))

# --- Page 2 ---------------------------------------------------------------------

finding(report, "X07", function() pct(disaster, "lost_any", 1))

# --- Page 3: Charts 1 and 2 ----------------------------------------------------------

finding(report, "C1", function() {
  yes <- lost_by_service(disaster)
  no <- lost_by_service(no_disaster)
  c(setNames(yes, paste0(names(yes), "_disaster")), setNames(no, paste0(names(no), "_no_disaster")))
})
finding(report, "X08", function() lost_by_service(disaster)[["electricity"]])
finding(report, "X09", function() lost_by_service(disaster)[["food"]])
finding(report, "X10", function() names(which.max(lost_by_service(disaster))))
finding(report, "X11", function() names(which.min(lost_by_service(disaster))))

# One point per region: mean perceived governmental preparedness (x) against
# % who could protect themselves or their family in a future disaster (y).
finding(report, "C2", function() {
  x <- mean_preparedness(d, by = "region")
  y <- pct(d, "WP22252", 1, by = "region")[names(x)]
  c(r2 = cor(x, y)^2,
    setNames(x, paste0(names(x), "_preparedness")),
    setNames(y, paste0(names(y), "_protect")))
})

# --- Page 4: Chart 3 and Table 1 ----------------------------------------------------------

region_mean <- function() mean_preparedness(d, by = "region")
finding(report, "X12", function() region_mean()[["south_eastern_asia"]])
finding(report, "X13", function() region_mean()[["south_asia"]])
finding(report, "X14", function() region_mean()[["latin_america_caribbean"]])
finding(report, "X15", function() region_mean()[["central_western_africa"]])

finding(report, "C3", function() {
  local <- pct(d, LOCAL, 1, by = "region")
  national <- pct(d, "national", 1, by = "region")
  mean <- region_mean()
  out <- numeric(0)
  for (region in REGIONS) {
    out[paste0(region, "_local")] <- local[[region]]
    out[paste0(region, "_national")] <- national[[region]]
    out[paste0(region, "_mean")] <- mean[[region]]
  }
  out
})
finding(report, "X16", function() sum(national_minus_local(d, by = "region") < 0))

finding(report, "T1", function() {
  t <- country_table()
  out <- numeric(0)
  for (iso in c("ARE", "BGD", "PHL", "IDN", "SGP", "ROU", "BOL", "PRY", "LBN", "AFG")) {
    for (col in c("mean", "disaster", "rank")) out[paste(iso, col, sep = "_")] <- t[iso, col]
  }
  out
})
finding(report, "X17", function() nrow(country_table()))
finding(report, "X18", function() {
  t <- country_table()
  paste(sort(rownames(t)[order(-t$mean)][1:5]), collapse = ", ")
})
finding(report, "X19", function() {
  t <- country_table()
  paste(sort(rownames(t)[order(t$mean)][1:5]), collapse = ", ")
})
finding(report, "X20", function() {
  t <- country_table()
  rownames(t)[which.min(t$mean)]
})
finding(report, "X21", function() country_table()["PHL", "disaster"])

# --- Page 5: Chart 4 ---------------------------------------------------------------------

finding(report, "C4", function() {
  gaps <- national_minus_local(d, by = "region")
  mean <- region_mean()
  c(global = national_minus_local(d), gaps[REGIONS], setNames(mean[REGIONS], paste0("mean_", REGIONS)))
})
finding(report, "X22", function() pct(d, "national", 1))
finding(report, "X23", function() pct(d, LOCAL, 1))
finding(report, "X24", function() national_minus_local(d))
# As printed: regions whose gap rounds to below zero.
finding(report, "X25", function() sum(half_up(national_minus_local(d, by = "region")) < 0))

# --- Page 6: Chart 5 ---------------------------------------------------------------------

gap_by_service <- function() {
  sapply(SERVICES, function(var) national_minus_local(disaster[disaster[[var]] %in% 1, ]))
}
finding(report, "X26", function() national_minus_local(disaster_lost))
finding(report, "X27", function() gap_by_service()[["water"]])
finding(report, "X28", function() gap_by_service()[["food"]])
finding(report, "C5", function() gap_by_service())

region_gap <- function(df, region) national_minus_local(df, by = "region")[[region]]
finding(report, "X29", function() region_gap(d, "north_africa"))
finding(report, "X30", function() region_gap(disaster_lost, "north_africa"))
finding(report, "X31", function() region_gap(d, "north_africa") - region_gap(disaster_lost, "north_africa"))
finding(report, "X32", function() region_gap(d, "northern_western_europe"))
finding(report, "X33", function() region_gap(disaster_lost, "northern_western_europe"))
finding(report, "X34", function() {
  region_gap(d, "northern_western_europe") - region_gap(disaster_lost, "northern_western_europe")
})

# --- Page 7: Charts 6 and 7 -----------------------------------------------------------------

finding(report, "C6", function() {
  gaps <- national_minus_local(disaster_lost, by = "region")
  c(global = national_minus_local(disaster_lost), gaps[REGIONS])
})
finding(report, "X35", function() region_gap(disaster_lost, "eastern_africa"))

finding(report, "C7", function() {
  gaps <- over_services(national_minus_local, by = "COUNTRY_ISO3")
  mean <- over_services(mean_preparedness, by = "COUNTRY_ISO3")
  c(regional = over_services(national_minus_local, by = "region")[["eastern_africa"]],
    setNames(gaps[EASTERN_AFRICA], paste0(EASTERN_AFRICA, "_gap")),
    setNames(mean[EASTERN_AFRICA], paste0(EASTERN_AFRICA, "_mean")))
})

# --- Pages 8-9: case studies ------------------------------------------------------------------

finding(report, "X36", function() over_services(mean_preparedness, by = "COUNTRY_ISO3")[["TZA"]])
finding(report, "X37", function() over_services(national_minus_local, by = "COUNTRY_ISO3")[["TZA"]])
finding(report, "X38", function() over_services(mean_preparedness, by = "COUNTRY_ISO3")[["MUS"]])

status <- run_report(report)
if (!interactive()) quit(status = status)
