# Reproduce World Risk Poll 2026: Alone together: The hidden consensus on climate change.
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_alone_together/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

DK <- c(98, 99) # don't know, refused: kept in the base, and shown as "don't know" in the report
PERSONAL <- "WP20719" # 1 = very serious, 2 = somewhat serious, 3 = not a threat
PERCEIVED <- "WP24225"
LOW <- "1"; LOWER_MIDDLE <- "2"; UPPER_MIDDLE <- "3"; HIGH <- "4" # CountryIncomeLevel
GROUPS <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high")
REGIONS <- c( # GlobalRegion codes -> keys used in Chart 2.2
  "1" = "eastern_africa", "2" = "cw_africa", "3" = "northern_africa", "4" = "southern_africa", "5" = "latam",
  "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
  "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
  "14" = "southern_europe", "15" = "anz"
)
EU <- c("AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL",
        "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE")
THREAT <- list(very = 1, somewhat = 2, dk = DK, not = 3)
ALIGN <- c("1" = "more_personal", "2" = "aligned", "3" = "more_societal")

d <- load_wave(2025, c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel",
                       PERSONAL, PERCEIVED))

# --- Derived variables ---------------------------------------------------------

# Alignment (Charts 2.2, 2.8): among respondents with a substantive answer
# (1-3) to both questions. A lower code is a more serious threat, so
# 1 = more personal than perceived societal concern, 2 = aligned (same
# answer), 3 = more perceived societal than personal concern.
both <- d[[PERSONAL]] %in% 1:3 & d[[PERCEIVED]] %in% 1:3
d$alignment <- ifelse(!both, NA,
  ifelse(d[[PERSONAL]] < d[[PERCEIVED]], 1, ifelse(d[[PERSONAL]] == d[[PERCEIVED]], 2, 3)))
d$answered_both <- ifelse(both, 1, 2) # 2 = DK/refused to at least one question

# Income groups for the trend: the report classifies every wave's countries
# by the 2025 World Bank classification (CountryIncomeLevel in the 2025
# file). Countries not surveyed in 2025 get no group and drop out of Chart 1.2.
INCOME_2025 <- tapply(d$CountryIncomeLevel, d$COUNTRY_ISO3, function(x) x[1])

# Trend file (Charts 1.1-1.4): the personal climate question in each wave.
CLIMATE <- c("2019" = "L5", "2021" = "WP20719", "2023" = "WP20719", "2025" = "WP20719")
t <- bind_rows(lapply(names(CLIMATE), function(y) {
  x <- load_wave(as.integer(y), c("COUNTRY_ISO3", "PROJWT", CLIMATE[[y]]))
  data.frame(COUNTRY_ISO3 = x$COUNTRY_ISO3, PROJWT = x$PROJWT, climate = as.numeric(x[[CLIMATE[[y]]]]),
             Year = as.integer(y))
}))
t$income2025 <- unname(INCOME_2025[t$COUNTRY_ISO3])

# Country table (Charts 2.4, 2.5 and the country counts): % very serious,
# personal and perceived societal. The report's country gaps are the
# difference of the rounded percentages (see README).
personal_c <- pct(d, PERSONAL, 1, by = "COUNTRY_ISO3")
perceived_c <- pct(d, PERCEIVED, 1, by = "COUNTRY_ISO3")
country <- data.frame(iso = names(personal_c), personal = unname(personal_c),
                      perceived = unname(perceived_c[names(personal_c)]))
country$income <- unname(INCOME_2025[country$iso])
country$gap <- round(country$personal) - round(country$perceived)
rownames(country) <- country$iso
top10 <- head(country[order(-country$gap), ], 10)

# Change in % very serious, 2023 to 2025 (Chart 1.4), countries in both waves.
# `change` is unrounded (a "significant" change is more than 4 points, the
# chart's margin of error); `change_rounded` uses the rounded percentages,
# as the country annotations and the "eight high-income countries" do.
very <- pct(t[t$Year %in% c(2023, 2025), ], "climate", 1, by = c("COUNTRY_ISO3", "Year"))
v23 <- very[grepl("_2023$", names(very))]; names(v23) <- sub("_2023$", "", names(v23))
v25 <- very[grepl("_2025$", names(very))]; names(v25) <- sub("_2025$", "", names(v25))
in_both <- intersect(names(v23), names(v25))
change <- data.frame(iso = in_both, v2023 = unname(v23[in_both]), v2025 = unname(v25[in_both]))
change$change <- change$v2025 - change$v2023
change$change_rounded <- round(change$v2025) - round(change$v2023)
change$income <- unname(INCOME_2025[change$iso])
rownames(change) <- change$iso

# ND-GAIN vulnerability (Chart 2.7): external snapshot, 2024 release, latest year.
# Not redistributed here: python reports/external/fetch_external.py ndgain downloads it.
NDGAIN <- "core_alone_together__ndgain_vulnerability.csv"
NDGAIN_YEAR <- "2022"

# --- Helpers -------------------------------------------------------------------

# % in `codes` of `var` for one CountryIncomeLevel group.
income <- function(df, var, codes, group) pct(df, var, codes, by = "CountryIncomeLevel")[[group]]

# % very or somewhat serious in `year`, for a 2025 income group.
trend_any <- function(year, group) pct(t[t$Year == year, ], "climate", c(1, 2), by = "income2025")[[group]]

isos <- function(x) paste(sort(x), collapse = ", ")

aligned_by_region <- function() distribution(d, "alignment", by = "GlobalRegion")

wave <- function(year, codes) pct(t[t$Year == year, ], "climate", codes)

# Named numbers -> character, so they can be returned alongside text values.
num <- function(x) setNames(as.character(x), names(x))

# --- Foreword and executive summary ------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() pct(d, PERSONAL, c(1, 2)))
finding(report, "X04", function() sum(country$gap > 30))
finding(report, "X05", function() pct(d, PERSONAL, 1))
finding(report, "X06", function() pct(d, PERSONAL, 2))
finding(report, "X07", function() {
  r <- pct(t, "climate", c(1, 2), by = "Year")
  as.integer(names(r)[which.max(r)])
})
finding(report, "X08", function() trend_any(2019, LOWER_MIDDLE))
finding(report, "X09", function() income(d, PERSONAL, c(1, 2), LOWER_MIDDLE))
finding(report, "X10", function() trend_any(2019, UPPER_MIDDLE))
finding(report, "X11", function() income(d, PERSONAL, c(1, 2), UPPER_MIDDLE))
finding(report, "X12", function() pct(d, PERCEIVED, c(1, 2)))
finding(report, "X13", function() pct(d, PERCEIVED, 1))
finding(report, "X14", function() income(d, PERSONAL, 1, HIGH))
finding(report, "X15", function() income(d, PERCEIVED, 1, HIGH))
finding(report, "X16", function() sum(country$gap >= 40))

# --- Chapter 1: concern about climate change, 2019-2025 ------------------------------

finding(report, "X17", function() wave(2021, 2))
finding(report, "X18", function() wave(2025, DK))
finding(report, "X19", function() wave(2019, DK))
finding(report, "X20", function() wave(2021, DK))
finding(report, "X21", function() wave(2025, 3))

finding(report, "C1_1", function() {
  out <- numeric(0)
  for (key in names(THREAT)) for (y in names(CLIMATE)) out[paste(key, y, sep = "_")] <- wave(as.integer(y), THREAT[[key]])
  out["any_2025"] <- wave(2025, c(1, 2))
  out
})

finding(report, "C1_2", function() {
  out <- numeric(0)
  for (code in names(GROUPS)) {
    g <- GROUPS[[code]]
    sub <- t[t$income2025 %in% as.numeric(code), ]
    for (key in c("very", "somewhat")) {
      for (y in c(2019, 2025)) out[paste(g, key, y, sep = "_")] <- pct(sub[sub$Year == y, ], "climate", THREAT[[key]])
    }
    r <- pct(sub, "climate", c(1, 2), by = "Year")
    out[paste0(g, "_peak")] <- as.integer(names(r)[which.max(r)])
  }
  out
})

finding(report, "X22", function() income(d, PERSONAL, c(1, 2), HIGH))

# No values are printed on Chart 1.3; recorded for Python/R comparison only.
finding(report, "C1_3", function() {
  sel <- c("ESP", "GBR", "IRL", "CAN", "NZL", "DNK", "HRV", "KWT")
  pct(t[t$COUNTRY_ISO3 %in% sel, ], "climate", 1, by = c("COUNTRY_ISO3", "Year"))
})

high_income_falls <- function() {
  hi <- change[change$income %in% as.numeric(HIGH), ]
  hi$iso[hi$change_rounded <= -10]
}
finding(report, "X23", function() length(high_income_falls()))
finding(report, "X24", function() isos(high_income_falls()))

finding(report, "C1_4", function() {
  hi <- change[change$income %in% as.numeric(HIGH), ]
  lower <- change[change$income %in% as.numeric(c(LOW, LOWER_MIDDLE)), ]
  out <- c(
    num(c(TUN_2023 = change["TUN", "v2023"], TUN_change = change["TUN", "change_rounded"],
          VNM_2023 = change["VNM", "v2023"], VNM_change = change["VNM", "change_rounded"])),
    largest_fall = change$iso[which.min(change$change)], largest_rise = change$iso[which.max(change$change)],
    num(c(high_countries = nrow(hi), high_fall = sum(hi$change < -4),
          lower_countries = nrow(lower), lower_rise = sum(lower$change > 4),
          lower_fall_share = 100 * mean(lower$change < -4), high_rise_share = 100 * mean(hi$change > 4)))
  )
  # Every country's change (no values printed): for Python/R comparison only.
  c(out, num(setNames(change$change, paste0("change_", change$iso))))
})

# --- Chapter 2: second-order beliefs ---------------------------------------------------

finding(report, "X25", function() pct(d, "alignment", 2))
finding(report, "X26", function() pct(d, "alignment", 3))
finding(report, "X27", function() pct(d, "alignment", 1))

finding(report, "C2_1", function() {
  c(sapply(THREAT, function(codes) pct(d, PERSONAL, codes)) |> setNames(paste0("personal_", names(THREAT))),
    sapply(THREAT, function(codes) pct(d, PERCEIVED, codes)) |> setNames(paste0("perceived_", names(THREAT))))
})

finding(report, "X28", function() pct(d, "alignment", 2))
finding(report, "X29", function() pct(d, "alignment", c(1, 3)))
finding(report, "X30", function() pct(d, "answered_both", 2))
finding(report, "X31", function() sum(aligned_by_region()[c("7", "8", "9", "10"), "2"] >= 70))
finding(report, "X32", function() sum(aligned_by_region()[, "2"] < 50))
finding(report, "X33", function() {
  r <- aligned_by_region()
  sum(r[, "1"] > r[, "2"])
})

finding(report, "C2_2", function() {
  tab <- aligned_by_region()
  out <- numeric(0)
  for (code in names(ALIGN)) out[paste0("global_", ALIGN[[code]])] <- pct(d, "alignment", as.numeric(code))
  for (reg in rownames(tab)) for (code in names(ALIGN)) out[paste(REGIONS[[reg]], ALIGN[[code]], sep = "_")] <- tab[reg, code]
  out
})

finding(report, "X34", function() income(d, PERSONAL, c(1, 2), LOW))
finding(report, "X35", function() income(d, PERCEIVED, c(1, 2), HIGH))
finding(report, "X36", function() income(d, PERSONAL, c(1, 2), HIGH) - income(d, PERCEIVED, c(1, 2), HIGH))
finding(report, "X37", function() {
  max(sapply(c(LOW, LOWER_MIDDLE, UPPER_MIDDLE), function(g) abs(income(d, PERSONAL, c(1, 2), g) - income(d, PERCEIVED, c(1, 2), g))))
})
finding(report, "X38", function() {
  max(sapply(c(LOW, LOWER_MIDDLE, UPPER_MIDDLE), function(g) income(d, PERSONAL, 1, g) - income(d, PERCEIVED, 1, g)))
})

finding(report, "C2_3", function() {
  out <- numeric(0)
  for (code in names(GROUPS)) {
    for (m in c("perceived", "personal")) {
      var <- if (m == "personal") PERSONAL else PERCEIVED
      out[paste(GROUPS[[code]], m, "very", sep = "_")] <- income(d, var, 1, code)
      out[paste(GROUPS[[code]], m, "somewhat", sep = "_")] <- income(d, var, 2, code)
      out[paste(GROUPS[[code]], m, "total", sep = "_")] <- income(d, var, c(1, 2), code)
    }
  }
  out
})

# No values are printed on Chart 2.4; recorded for Python/R comparison only.
finding(report, "C2_4", function() {
  c(setNames(country$personal, paste0(country$iso, "_personal")),
    setNames(country$perceived, paste0(country$iso, "_perceived")))
})

finding(report, "X39", function() sum(country$gap >= 5))
finding(report, "X40", function() sum(country$gap <= -5))
finding(report, "X41", function() isos(country$iso[country$gap <= -5]))
finding(report, "X42", function() sum(top10$income %in% as.numeric(HIGH)))
# Income group labels. wrp.R's value_labels() reads the dictionary with
# fileEncoding = "UTF-8-BOM", which stops at the first non-ASCII character
# when R runs in the C locale (39 of the 228 rows of the 2025 dictionary,
# with warnings). Reading it without re-encoding works in any locale.
income_labels <- function() {
  dd <- read.csv(file.path(WRP_ROOT, "WRP_2025", "WRP_2025_data_dictionary.csv"), encoding = "UTF-8",
                 stringsAsFactors = FALSE)
  parts <- strsplit(dd$value_labels[dd$variable == "CountryIncomeLevel"], " | ", fixed = TRUE)[[1]]
  setNames(sub("^[^=]+ = ", "", parts), sub(" = .*$", "", parts))
}
finding(report, "X43", function() {
  codes <- top10$income[!top10$income %in% as.numeric(HIGH)]
  paste(income_labels()[as.character(codes)], collapse = "; ")
})
finding(report, "X44", function() country["PRT", "gap"])
finding(report, "X45", function() country["USA", "gap"])
finding(report, "X46", function() min(top10$gap))

finding(report, "C2_5", function() {
  vals <- c(setNames(top10$personal, paste0(top10$iso, "_personal")),
            setNames(top10$perceived, paste0(top10$iso, "_perceived")),
            setNames(top10$gap, paste0(top10$iso, "_gap")))
  c(top10 = isos(top10$iso), num(vals))
})

area <- function(key) if (key == "EU") d[d$COUNTRY_ISO3 %in% EU, ] else d[d$COUNTRY_ISO3 == key, ]

finding(report, "X47", function() pct(area("CHN"), PERSONAL, c(1, 2)))
finding(report, "X48", function() pct(area("USA"), PERSONAL, c(1, 2)))
finding(report, "X49", function() pct(area("USA"), PERSONAL, 1))
finding(report, "X50", function() pct(area("CHN"), PERSONAL, 1))
finding(report, "X51", function() pct(area("USA"), PERCEIVED, 1))
finding(report, "X52", function() pct(area("CHN"), PERCEIVED, 1) - pct(area("CHN"), PERSONAL, 1))
finding(report, "X53", function() pct(area("IND"), PERSONAL, DK))
finding(report, "X54", function() pct(area("IND"), PERCEIVED, DK))
finding(report, "X55", function() pct(area("EU"), PERSONAL, 1))
finding(report, "X56", function() pct(area("EU"), PERCEIVED, 1))

finding(report, "C2_6", function() {
  out <- numeric(0)
  for (key in c("CHN", "IND", "EU", "USA")) {
    for (m in c("perceived", "personal")) {
      var <- if (m == "personal") PERSONAL else PERCEIVED
      for (k in names(THREAT)) out[paste(key, m, k, sep = "_")] <- pct(area(key), var, THREAT[[k]])
    }
  }
  out
})

vulnerability_correlation <- function(measure) {
  nd <- read.csv(external_path(NDGAIN), check.names = FALSE)
  m <- merge(country, data.frame(iso = nd$ISO3, vulnerability = nd[[NDGAIN_YEAR]]), by = "iso")
  m <- m[!is.na(m$vulnerability) & !is.na(m[[measure]]), ]
  cor(m[[measure]], m$vulnerability)
}
finding(report, "X57", function() vulnerability_correlation("personal"))
finding(report, "X58", function() vulnerability_correlation("perceived"))

# Needs Gallup's National Institutions Index (INDEX_NI: confidence in the
# national government, honesty of elections, the military, and the judicial
# system and courts), which is not in the public release.
finding(report, "C2_8", function() {
  g <- merge_gallup(d[!is.na(d$alignment), ], "INDEX_NI")
  r <- wmean(g, "INDEX_NI", by = c("CountryIncomeLevel", "alignment"))
  inc <- sub("_.*$", "", names(r))
  al <- sub("^.*_", "", names(r))
  keep <- inc %in% names(GROUPS)
  setNames(r[keep], paste(GROUPS[inc[keep]], ALIGN[al[keep]], sep = "_"))
})

# --- Conclusion ---------------------------------------------------------------------

finding(report, "X59", function() income(d, PERSONAL, 1, HIGH) - income(d, PERCEIVED, 1, HIGH))

status <- run_report(report)
if (!interactive()) quit(status = status)
