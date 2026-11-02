# Reproduce World Risk Poll 2026: A resilient life: How wellbeing shapes the capacity to cope.
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_a_resilient_life/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

# --- Variables -------------------------------------------------------------------

# Resilience Index (0-100) and its four dimensions (0-1 in the data, x 100 here).
DIMS <- c(index = "resilience_index_100", individual = "resilience_idv", household = "resilience_hhl",
          community = "resilience_com", societal = "resilience_soc")
AGENCY <- "WP22252"         # could protect yourself or family in a future disaster: 1 = yes
FINANCE <- "WP22228"        # could cover basic needs if income was lost: 2 = a month or more
NEIGHBOURS <- "WP22232"     # neighbours care about you: 1 a lot, 2 somewhat, 3 not at all
GOVERNMENT <- "WP22231_ALL" # government cares about you, including Myanmar and Vietnam
CARE <- c(a_lot = 1, somewhat = 2, not_at_all = 3)
DK <- c(98, 99)
DISCRIMINATION <- c("WP22259", "WP22260", "WP22261", "WP22262", "WP22263")
HARM <- c(prolonged_weather = "WP24177", severe_weather = "WP22445", traffic = "WP22446", food = "WP22442",
          water = "WP22443", mental_health = "WP22447", crime = "WP22444")

REGION <- c("1" = "east_africa", "2" = "cw_africa", "3" = "north_africa", "4" = "southern_africa", "5" = "latam",
            "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
            "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
            "14" = "southern_europe", "15" = "anz")
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = not classified
AFRICA <- c("3" = "north_africa", "2" = "cw_africa", "4" = "southern_africa", "1" = "east_africa")
LE <- c("1" = "thriving", "2" = "struggling", "3" = "suffering")
YEARS <- c("2021", "2023", "2025")

BASE <- c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", unname(DIMS))
d25 <- load_wave(2025, c(BASE, AGENCY, FINANCE, NEIGHBOURS, GOVERNMENT, "WP22231", "WP23345", DISCRIMINATION, unname(HARM)))
d23 <- load_wave(2023, c(BASE, AGENCY, FINANCE, NEIGHBOURS, GOVERNMENT, "WP23345"))
d21 <- load_wave(2021, c(BASE, AGENCY, FINANCE, NEIGHBOURS, "WP22231", "WP22469", "WP22525", "WP22253"))
d19 <- load_wave(2019, c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion"))

# Trends use the countries surveyed in 2025 in every wave, classified by their 2025 region.
REGION_2025 <- tapply(d25$GlobalRegion, d25$COUNTRY_ISO3, function(x) x[1])
C25 <- names(REGION_2025)
d21 <- d21[d21$COUNTRY_ISO3 %in% C25, ]
d23 <- d23[d23$COUNTRY_ISO3 %in% C25, ]
d19 <- d19[d19$COUNTRY_ISO3 %in% C25, ]

# --- Derived variables -----------------------------------------------------------

add_dims <- function(d) {
  for (k in names(DIMS)) d[[k]] <- if (k == "index") d[[DIMS[[k]]]] else 100 * d[[DIMS[[k]]]]
  d$region <- unname(REGION_2025[d$COUNTRY_ISO3])
  d
}
d21 <- add_dims(d21)
d23 <- add_dims(d23)
d25 <- add_dims(d25)
d19$region <- unname(REGION_2025[d19$COUNTRY_ISO3])

# 2021 asked Vietnam and Myanmar about "the authorities" and "the government in power".
d21[[GOVERNMENT]] <- dplyr::coalesce(d21$WP22231, d21$WP22469, d21$WP22525)

# Disaster plan known to all household members: 2021 WP22253, 2023-25 WP23345.
d21$plan <- d21$WP22253
d23$plan <- d23$WP23345
d25$plan <- d25$WP23345

WAVES <- list("2021" = d21, "2023" = d23, "2025" = d25)

# Country scores (unrounded): one data frame per wave, rows = ISO3.
country_scores <- function(d) {
  out <- lapply(names(DIMS), function(k) wmean(d, k, by = "COUNTRY_ISO3"))
  isos <- sort(unique(unlist(lapply(out, names))))
  as.data.frame(setNames(lapply(out, function(v) unname(v[isos])), names(DIMS)), row.names = isos)
}
country <- lapply(WAVES, country_scores)

# --- Helpers ---------------------------------------------------------------------

# Round half up to a whole number, as printed (same rule as reproduce.py).
r0 <- function(x) floor(x + 0.5 + 1e-9)

keyed <- function(v, keys) {
  v <- v[names(v) %in% names(keys)]
  setNames(unname(v), unname(keys[names(v)]))
}

score <- function(iso, dim, year) country[[as.character(year)]][iso, dim]

rounded_change <- function(iso, dim, start, end) r0(score(iso, dim, end)) - r0(score(iso, dim, start))

country_pct <- function(y, var, codes, iso, exclude = NULL) {
  d <- WAVES[[as.character(y)]]
  pct(d[d$COUNTRY_ISO3 == iso, ], var, codes, exclude = exclude)
}

pct_change <- function(var, codes, iso, start, end, exclude = NULL) {
  r0(country_pct(end, var, codes, iso, exclude)) - r0(country_pct(start, var, codes, iso, exclude))
}

# % personally harmed: 'yes, personally' + 'both', each rounded first.
harmed <- function(var) {
  t <- distribution(d25, var)
  sum(vapply(c("1", "3"), function(c) if (c %in% names(t)) r0(t[[c]]) else 0, numeric(1)))
}

rank_of <- function(v, iso) {
  v <- v[!is.na(v)]
  rank(-v, ties.method = "min")[[iso]]
}

# Gallup Life Evaluation Index groups from the Cantril ladder (WP16 now, WP18 in
# five years): 1 thriving (7+ and 8+), 3 suffering (both 4 or below), 2 struggling.
life_evaluation <- function(df) {
  g <- merge_gallup(df, c("WP16", "WP18"))
  now <- ifelse(g$WP16 <= 10, g$WP16, NA)
  fut <- ifelse(g$WP18 <= 10, g$WP18, NA)
  g$ladder <- now
  g$life_eval <- ifelse(is.na(now) | is.na(fut), NA,
                        ifelse(now >= 7 & fut >= 8, 1, ifelse(now <= 4 & fut <= 4, 3, 2)))
  g
}

# Country 'not at all' minus 'a lot', from the rounded percentages (Chart 3.2).
care_gaps <- function(var) {
  t <- distribution(d25, var, by = "COUNTRY_ISO3")
  r0(t[, "3"]) - r0(t[, "1"])
}

# Table 3.1: highest % 'not at all', ties at the 10th rounded value included.
top_not_at_all <- function(var) {
  s <- sort(pct(d25, var, 3, by = "COUNTRY_ISO3"), decreasing = TRUE)
  s[r0(s) >= r0(s[10])]
}

global_rounded <- function(dim, year) r0(wmean(WAVES[[as.character(year)]], dim))

# Split "a_b" group keys from a two-variable `by`.
split_key <- function(k, i) vapply(strsplit(k, "_", fixed = TRUE), `[`, character(1), i)

# --- Front matter and executive summary ---------------------------------------------

finding(report, "X01", function() nrow(d25))
finding(report, "X02", function() length(unique(d25$COUNTRY_ISO3)))
finding(report, "X03", function() wmean(d25, "index"))
finding(report, "X04", function() global_rounded("index", 2025) - global_rounded("index", 2021))
finding(report, "X05", function() global_rounded("individual", 2025) - global_rounded("individual", 2023))
finding(report, "X06", function() global_rounded("individual", 2023) - global_rounded("individual", 2021))
finding(report, "X07", function() global_rounded("household", 2025) - global_rounded("household", 2023))
finding(report, "X08", function() global_rounded("community", 2025) - global_rounded("community", 2023))
for (pair in list(c("X09", "GRC"), c("X10", "NZL"), c("X11", "AUS"), c("X12", "NLD"), c("X13", "EST"), c("X14", "FRA"))) {
  local({
    iso <- pair[2]
    finding(report, pair[1], function() rounded_change(iso, "societal", 2021, 2025))
  })
}

table_1_2 <- function() sapply(WAVES, function(d) wmean(d, "index", by = "region"))

finding(report, "X15", function() {
  t <- table_1_2()
  keyed(setNames(r0(t[, "2025"]) - r0(t[, "2023"]), rownames(t)), REGION)
})
finding(report, "X16", function() {
  isos <- c("DZA", "NGA", "KEN", "EGY", "UGA")
  setNames(vapply(isos, function(i) rounded_change(i, "household", 2021, 2025), numeric(1)), isos)
})

# Gallup WP16056: access to the internet (1 = yes), countries surveyed in 2025.
table_1_3 <- function() {
  out <- c()
  for (year in c("2019", "2025")) {
    d <- if (year == "2019") d19 else d25
    g <- merge_gallup(d, "WP16056")
    by_region <- pct(g, "WP16056", 1, by = "region")
    for (code in names(AFRICA)) out[paste(AFRICA[[code]], year, sep = "_")] <- by_region[[code]]
    out[paste("global", year, sep = "_")] <- pct(g, "WP16056", 1)
  }
  out
}
finding(report, "X17", function() {
  t <- table_1_3()
  keys <- c("north_africa", "cw_africa", "southern_africa")
  setNames(r0(t[paste0(keys, "_2025")]) - r0(t[paste0(keys, "_2019")]), keys)
})

agency_change_2023_2025 <- function() {
  a23 <- pct(d23, AGENCY, 1, by = "COUNTRY_ISO3")
  a25 <- pct(d25, AGENCY, 1, by = "COUNTRY_ISO3")
  isos <- intersect(names(a23), names(a25))
  a25[isos] - a23[isos]
}
# A change counts when it rounds to 10 points or more.
finding(report, "X18", function() sum(r0(agency_change_2023_2025()) >= 10))
finding(report, "X19", function() sum(r0(-agency_change_2023_2025()) >= 10))

life_eval_index <- function(dim = "index", by_income = FALSE) {
  g <- life_evaluation(d25)
  wmean(g, dim, by = if (by_income) c("CountryIncomeLevel", "life_eval") else "life_eval")
}
finding(report, "X20", function() {
  s <- life_eval_index()
  r0(s[["1"]]) - r0(s[["3"]])
})
finding(report, "X21", function() {
  s <- life_eval_index(by_income = TRUE)
  min(vapply(names(INCOME), function(i) r0(s[[paste(i, 1, sep = "_")]]) - r0(s[[paste(i, 3, sep = "_")]]), numeric(1)))
})

# Resilience Index by present life rating (0-10) and income group (no printed values).
chart_2_3 <- function() {
  g <- life_evaluation(d25)
  wmean(g, "index", by = c("CountryIncomeLevel", "ladder"))
}
finding(report, "X22", function() {
  g <- life_evaluation(d25)
  keyed(wmean(g[!is.na(g$ladder) & g$ladder <= 2, ], "index", by = "CountryIncomeLevel"), INCOME)
})
finding(report, "X23", function() {
  t <- chart_2_3()
  sum(vapply(names(INCOME), function(i) t[[paste(i, 10, sep = "_")]] < t[[paste(i, 9, sep = "_")]], logical(1)))
})
finding(report, "C2_3", function() {
  t <- chart_2_3()
  t <- t[split_key(names(t), 1) %in% names(INCOME)]
  setNames(unname(t), paste(INCOME[split_key(names(t), 1)], split_key(names(t), 2), sep = "_"))
})

finding(report, "X24", function() r0(pct(d25, GOVERNMENT, 3)) - r0(pct(d21, GOVERNMENT, 3)))
finding(report, "X25", function() sum(care_gaps(GOVERNMENT) >= 10))
finding(report, "X26", function() sum(care_gaps(GOVERNMENT) <= -10))

chart_3_6 <- function() wmean(d25, "household", by = c("CountryIncomeLevel", NEIGHBOURS))
finding(report, "X27", function() {
  t <- chart_3_6()
  setNames(vapply(names(INCOME), function(i) r0(t[[paste(i, 1, sep = "_")]]) - r0(t[[paste(i, 3, sep = "_")]]), numeric(1)),
           unname(INCOME))
})
finding(report, "X28", function() {
  gov <- pct(d25, GOVERNMENT, 3, by = "COUNTRY_ISO3")
  nbr <- pct(d25, NEIGHBOURS, 3, by = "COUNTRY_ISO3")
  isos <- intersect(names(gov), names(nbr))
  cor(gov[isos], nbr[isos])
})

# --- Chapter 1 -------------------------------------------------------------------

finding(report, "X29", function() vapply(HARM, harmed, numeric(1)))

finding(report, "C1_1", function() {
  out <- c()
  for (k in names(DIMS)) for (y in YEARS) out[paste(k, y, sep = "_")] <- wmean(WAVES[[y]], k)
  out
})
finding(report, "C1_2", function() {
  out <- c()
  for (k in names(DIMS)) {
    v <- keyed(wmean(d25, k, by = "CountryIncomeLevel"), INCOME)
    out[paste(k, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "X30", function() {
  s <- wmean(d25, "individual", by = "CountryIncomeLevel")
  r0(s[["4"]]) - r0(s[["3"]])
})
finding(report, "T1_2", function() {
  t <- table_1_2()
  out <- c()
  for (r in names(REGION)) for (y in YEARS) out[paste(REGION[[r]], y, sep = "_")] <- t[r, y]
  out
})

finding(report, "X31", function() {
  isos <- c("POL", "SVK", "HRV", "BGR", "BIH", "MAR")
  setNames(vapply(isos, function(i) rounded_change(i, "individual", 2021, 2025), numeric(1)), isos)
})
finding(report, "X32", function() {
  isos <- intersect(rownames(country[["2021"]]), rownames(country[["2025"]]))
  change <- country[["2025"]][isos, "individual"] - country[["2021"]][isos, "individual"]
  names(change) <- isos
  change <- change[!is.na(change)]
  sum(change < change[["POL"]])
})
finding(report, "X33", function() score("MAR", "individual", 2021))
finding(report, "X34", function() score("MAR", "individual", 2025))
finding(report, "X35", function() {
  isos <- c("SVK", "BGR", "HRV", "POL", "BIH")
  setNames(vapply(isos, function(i) pct_change(AGENCY, 1, i, 2021, 2025), numeric(1)), isos)
})
finding(report, "X36", function() c(DZA = score("DZA", "household", 2025), EGY = score("EGY", "household", 2025)))
# Among those giving an answer (don't know and refused excluded); see README.
finding(report, "X37", function() {
  isos <- c("DZA", "EGY", "UGA", "KEN", "NGA")
  setNames(vapply(isos, function(i) pct_change(FINANCE, 2, i, 2021, 2025, DK), numeric(1)), isos)
})
finding(report, "X38", function() {
  isos <- c("DZA", "KEN")
  setNames(vapply(isos, function(i) pct_change("plan", 1, i, 2021, 2025, DK), numeric(1)), isos)
})
finding(report, "T1_3", table_1_3)
finding(report, "X39", function() {
  c(community_2021 = score("UKR", "community", 2021), community_2023 = score("UKR", "community", 2023),
    community_2025 = score("UKR", "community", 2025), individual_2025 = score("UKR", "individual", 2025))
})
finding(report, "X40", function() setNames(vapply(YEARS, function(y) country_pct(y, NEIGHBOURS, c(1, 2), "UKR"), numeric(1)), YEARS))
finding(report, "X41", function() {
  c(USA_individual = score("USA", "individual", 2025), USA_household = score("USA", "household", 2025),
    SWE_individual = score("SWE", "individual", 2025), VNM_household = score("VNM", "household", 2025),
    USA_community = score("USA", "community", 2025))
})
finding(report, "C1_7", function() {
  dims <- c("individual", "household", "community", "societal")
  sc <- country[["2025"]]
  setNames(vapply(dims, function(k) rank_of(setNames(sc[[k]], rownames(sc)), "USA"), numeric(1)), dims)
})
finding(report, "X42", function() sum(!is.na(country[["2025"]]$societal)))

# Gallup confidence items (1 = yes): WP137 military, WP138 judicial system, WP139 national government.
us_confidence <- function(item, year) {
  d <- if (year == 2019) d19 else d25
  pct(merge_gallup(d[d$COUNTRY_ISO3 == "USA", ], item), item, 1)
}
finding(report, "X43", function() {
  c(national_government = us_confidence("WP139", 2025), judicial = us_confidence("WP138", 2025),
    military_2025 = us_confidence("WP137", 2025), military_2019 = us_confidence("WP137", 2019))
})
finding(report, "X44", function() country_pct(2025, "WP22231", 1, "USA"))
finding(report, "X45", function() setNames(vapply(DISCRIMINATION, function(v) country_pct(2025, v, 1, "USA"), numeric(1)), DISCRIMINATION))
finding(report, "X46", function() {
  items <- c("WP22259", "WP22261", "WP22262")
  setNames(vapply(items, function(v) rank_of(pct(d25, v, 1, by = "COUNTRY_ISO3"), "USA"), numeric(1)), items)
})

country_series <- function(isos, dim, keys = isos) {
  out <- c()
  for (i in seq_along(isos)) for (y in YEARS) out[paste(keys[i], y, sep = "_")] <- score(isos[i], dim, y)
  out
}
finding(report, "C1_3", function() country_series(c("POL", "SVK", "HRV", "BGR", "BIH"), "individual"))
finding(report, "C1_4", function() country_series(c("DZA", "NGA", "KEN", "EGY", "UGA"), "household"))
finding(report, "C1_5", function() {
  out <- c()
  for (k in names(DIMS)) for (y in YEARS) out[paste(k, y, sep = "_")] <- score("UKR", k, y)
  out
})
finding(report, "C1_6", function() country_series(c("GRC", "NZL", "AUS", "NLD", "EST", "FRA"), "societal"))

# --- Chapter 2 (Gallup Life Evaluation Index) -------------------------------------------

finding(report, "C2_1", function() {
  s <- life_eval_index(by_income = TRUE)
  s <- s[split_key(names(s), 1) %in% names(INCOME) & split_key(names(s), 2) %in% names(LE)]
  out <- setNames(unname(s), paste(INCOME[split_key(names(s), 1)], LE[split_key(names(s), 2)], sep = "_"))
  g <- keyed(life_eval_index(), LE)
  c(out, setNames(g, paste("global", names(g), sep = "_")))
})

country_wellbeing <- function() {
  g <- life_evaluation(d25)
  thriving <- pct(g[!is.na(g$life_eval), ], "life_eval", 1, by = "COUNTRY_ISO3")
  ladder <- wmean(g, "ladder", by = "COUNTRY_ISO3")
  sc <- setNames(country[["2025"]]$index, rownames(country[["2025"]]))
  isos <- Reduce(intersect, list(names(thriving), names(ladder), names(sc)[!is.na(sc)]))
  data.frame(thriving = thriving[isos], ladder = ladder[isos], index = sc[isos], row.names = isos)
}
finding(report, "X47", function() {
  t <- country_wellbeing()
  cor(t$ladder, t$index)
})
finding(report, "X48", function() median(country[["2025"]]$index, na.rm = TRUE))
finding(report, "X49", function() {
  g <- life_evaluation(d25)
  median(pct(g[!is.na(g$life_eval), ], "life_eval", 1, by = "COUNTRY_ISO3"))
})
finding(report, "C2_2", function() {
  t <- country_wellbeing()
  out <- c()
  for (iso in rownames(t)) for (k in c("thriving", "index")) out[paste(iso, k, sep = "_")] <- t[iso, k]
  out
})
finding(report, "C2_4", function() {
  out <- c()
  for (k in c("individual", "household", "community", "societal")) {
    v <- keyed(life_eval_index(k), LE)
    out[paste(k, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "C2_5", function() {
  g <- life_evaluation(d25)
  suffering <- g[!is.na(g$life_eval) & g$life_eval == 3, ]
  out <- c()
  for (k in c("individual", "household", "community", "societal")) {
    v <- keyed(wmean(suffering, k, by = "CountryIncomeLevel"), INCOME)
    out[paste(names(v), k, sep = "_")] <- v
  }
  out
})

# --- Chapter 3 -------------------------------------------------------------------

finding(report, "C3_1", function() {
  out <- c()
  for (who in c("government", "neighbours")) {
    var <- if (who == "government") GOVERNMENT else NEIGHBOURS
    for (y in c("2021", "2025")) for (k in names(CARE)) out[paste(who, y, k, sep = "_")] <- pct(WAVES[[y]], var, CARE[[k]])
  }
  out
})
finding(report, "X50", function() r0(pct(d25, GOVERNMENT, 1)) - r0(pct(d21, GOVERNMENT, 1)))
finding(report, "X51", function() r0(pct(d25, GOVERNMENT, 2)) - r0(pct(d21, GOVERNMENT, 2)))
finding(report, "C3_2", function() {
  out <- c()
  for (who in c("gov", "nbr")) {
    g <- care_gaps(if (who == "gov") GOVERNMENT else NEIGHBOURS)
    out[paste0(who, "_a_lot")] <- sum(g <= -10)
    out[paste0(who, "_under_10")] <- sum(g > -10 & g < 10)
    out[paste0(who, "_not_at_all")] <- sum(g >= 10)
  }
  out
})
finding(report, "C3_3", function() {
  out <- c()
  for (who in c("government", "neighbours")) {
    v <- keyed(pct(d25, if (who == "government") GOVERNMENT else NEIGHBOURS, 3, by = "CountryIncomeLevel"), INCOME)
    out[paste(who, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "C3_4", function() {
  g <- life_evaluation(d25)
  keyed(pct(g[!is.na(g$life_eval), ], "life_eval", 1, by = "CountryIncomeLevel"), INCOME)
})
finding(report, "C3_5", function() {
  out <- c()
  for (who in c("government", "neighbours")) {
    v <- keyed(pct(d25, if (who == "government") GOVERNMENT else NEIGHBOURS, 3, by = "GlobalRegion"), REGION)
    out[paste(who, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "T3_1", function() {
  out <- c()
  for (who in c("government", "neighbours")) {
    top <- top_not_at_all(if (who == "government") GOVERNMENT else NEIGHBOURS)
    out[paste0(who, "_top10")] <- paste(sort(names(top), method = "radix"), collapse = ", ")
    out[paste(who, names(top), sep = "_")] <- sprintf("%.17g", top)
  }
  out
})
finding(report, "X52", function() length(intersect(names(top_not_at_all(GOVERNMENT)), names(top_not_at_all(NEIGHBOURS)))))
finding(report, "C3_6", function() {
  t <- chart_3_6()
  out <- c()
  for (i in names(INCOME)) for (k in names(CARE)) out[paste(INCOME[[i]], k, sep = "_")] <- t[[paste(i, CARE[[k]], sep = "_")]]
  out
})

status <- run_report(report)
if (!interactive()) quit(status = status)
