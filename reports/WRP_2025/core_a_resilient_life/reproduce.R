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

# The Resilience Index and its four dimensions: the released 0-1 scores, used x 100.
DIMS <- c(index = "resilience_index", individual = "resilience_idv", household = "resilience_hhl",
          community = "resilience_com", societal = "resilience_soc")
FOUR <- c("individual", "household", "community", "societal")
REGION <- c("1" = "east_africa", "2" = "cw_africa", "3" = "north_africa", "4" = "southern_africa", "5" = "latam",
            "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
            "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
            "14" = "southern_europe", "15" = "anz")
AFRICA <- c("north_africa", "southern_africa", "cw_africa", "east_africa")
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = not classified
LE <- c("1" = "thriving", "2" = "struggling", "3" = "suffering")
CARE <- c("1" = "a_lot", "2" = "somewhat", "3" = "not_at_all")
WHO <- c(government = "gov", neighbours = "WP22232")
DISC <- c(skin = "WP22259", religion = "WP22260", nationality = "WP22261", gender = "WP22262",
          disability = "WP22263")
PLAN <- c("2021" = "WP22253", "2023" = "WP23345", "2025" = "WP23345") # household disaster plan known to all
# Harm in the past two years (1 personally, 2 someone you know, 3 both, 4 no), page 1.
HARM <- c(prolonged_weather = "WP24177", severe_weather = "WP22445", traffic = "WP22446", food = "WP22442",
          water = "WP22443", mental_health = "WP22447", crime = "WP22444")
DK <- c(98, 99)
SIX <- c("GRC", "NZL", "AUS", "NLD", "EST", "FRA") # Chart 1.6
# Country names as printed in Table 3.1 (others use the release's Country name).
NAME <- c(COM = "Comoros", BOL = "Bolivia", PER = "Peru", PAN = "Panama", ROU = "Romania", PRY = "Paraguay",
          COL = "Colombia", HND = "Honduras", MDG = "Madagascar", GRC = "Greece",
          HKG = "Hong Kong (S.A.R. of China)", GAB = "Gabon", RUS = "Russia", ECU = "Ecuador", MEX = "Mexico",
          COG = "Republic of Congo")

BASE <- c("WPID_RANDOM", "COUNTRY_ISO3", "Country", "PROJWT", "GlobalRegion", "CountryIncomeLevel", unname(DIMS),
          "WP22231", "WP22232", "WP22252", "WP22228", unname(DISC))
d25 <- load_wave(2025, c(BASE, "WP22231_ALL", "WP23345", unname(HARM)))
d23 <- load_wave(2023, c(BASE, "WP22231_ALL", "WP23345"))
d21 <- load_wave(2021, c(BASE, "WP22525", "WP22469", "WP22253"))
d19 <- load_wave(2019, c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion")) # Gallup items only

# --- Derived variables -----------------------------------------------------------

prep <- function(d, y) {
  for (k in names(DIMS)) d[[k]] <- 100 * d[[DIMS[[k]]]] # 0-100, as printed
  d$plan <- d[[PLAN[[as.character(y)]]]]
  d
}
d25 <- prep(d25, 2025)
d23 <- prep(d23, 2023)
d21 <- prep(d21, 2021)
# Government cares about you: the combined version that adds Myanmar's and
# Vietnam's own wording (WP22231_ALL in 2023 and 2025; built the same way for 2021).
d25$gov <- d25$WP22231_ALL
d23$gov <- d23$WP22231_ALL
d21$gov <- dplyr::coalesce(d21$WP22231, d21$WP22525, d21$WP22469)

# Every country in each wave (country-level changes) and, for global and
# regional trends, the countries surveyed in 2025, as the report does.
C25 <- unique(d25$COUNTRY_ISO3)
ALL <- list("2021" = d21, "2023" = d23, "2025" = d25)
TREND <- lapply(ALL, function(d) d[d$COUNTRY_ISO3 %in% C25, ])

# --- Helpers ---------------------------------------------------------------------

# Round half up to a whole number, as printed (same rule as reproduce.py).
r0 <- function(x) floor(x + 0.5 + 1e-9)
# Difference of two figures rounded as printed: how the report states its changes.
rdiff <- function(a, b) r0(a) - r0(b)

# Rename a by-group result with readable keys, dropping unknown groups.
keyed <- function(v, keys) {
  v <- v[names(v) %in% names(keys)]
  setNames(unname(v), unname(keys[names(v)]))
}
country <- function(df, iso) df[df$COUNTRY_ISO3 == iso, , drop = FALSE]
country_means <- function(df, k) wmean(df, k, by = "COUNTRY_ISO3")
country_pct <- function(df, var, codes, exclude = NULL) pct(df, var, codes, by = "COUNTRY_ISO3", exclude = exclude)
# Rank countries, 1 = highest (ties share the best rank).
ranks <- function(v, ascending = FALSE) {
  v <- v[!is.na(v)]
  rank(if (ascending) v else -v, ties.method = "min")
}
# Sum of the rounded % in each of `codes` ('personally' + 'both', as in The quiet hazards).
rsum <- function(df, var, codes) {
  t <- distribution(df, var)
  sum(vapply(codes, function(c) if (as.character(c) %in% names(t)) r0(t[[as.character(c)]]) else 0, numeric(1)))
}
# Split "a_b" group keys from a two-variable `by`.
split_key <- function(k, i) vapply(strsplit(k, "_", fixed = TRUE), `[`, character(1), i)

.cache <- new.env()
cached <- function(key, fn) {
  if (is.null(.cache[[key]])) .cache[[key]] <- fn()
  .cache[[key]]
}

# 2025 respondents with Gallup's Life Evaluation Index (WP16 now, WP18 in five years).
# life_eval: 1 thriving (now 7+ and future 8+), 3 suffering (both 4 or below),
# 2 struggling (everyone else with valid answers). ladder: WP16, 0-10.
wellbeing <- function() cached("wellbeing", function() {
  g <- merge_gallup(d25, c("WP16", "WP18"))
  now <- ifelse(g$WP16 <= 10, g$WP16, NA)
  fut <- ifelse(g$WP18 <= 10, g$WP18, NA)
  g$ladder <- now
  g$life_eval <- ifelse(is.na(now) | is.na(fut), NA,
                        ifelse(now >= 7 & fut >= 8, 1, ifelse(now <= 4 & fut <= 4, 3, 2)))
  g$thriving <- ifelse(is.na(g$life_eval), NA, 100 * (g$life_eval == 1))
  g
})

# One wave with a Gallup yes/no item (1 = yes) as a 0/100 variable `yes`.
gallup_wave <- function(year, item) cached(paste(year, item), function() {
  d <- if (year == 2019) d19 else ALL[[as.character(year)]]
  g <- merge_gallup(d, item)
  g$yes <- ifelse(is.na(g[[item]]), NA, 100 * (g[[item]] == 1))
  g
})

# Gallup WP16056: access to the internet in any way (1 = yes); countries surveyed in 2025.
internet <- function(year) {
  g <- gallup_wave(year, "WP16056")
  g[g$COUNTRY_ISO3 %in% C25, ]
}

# Change in country % who could protect themselves (WP22252 = yes), 2023 to 2025.
agency_change <- function() {
  a23 <- country_pct(d23, "WP22252", 1)
  a25 <- country_pct(d25, "WP22252", 1)
  common <- intersect(names(a23), names(a25))
  a25[common] - a23[common]
}
# A change counts as 10 points or more when it rounds to 10 or more.
big <- function(change) r0(change) >= 10

# Regional Index change 2023 to 2025 (difference of the rounded Table 1.2 scores).
region_change <- function() {
  a <- keyed(wmean(TREND[["2023"]], "index", by = "GlobalRegion"), REGION)
  b <- keyed(wmean(TREND[["2025"]], "index", by = "GlobalRegion"), REGION)
  rdiff(b, a[names(b)])
}

# Country change in a dimension (difference of rounded scores), for `isos` or every
# country with a score in both waves.
country_change <- function(k, y0 = "2021", y1 = "2025", isos = NULL) {
  a <- country_means(ALL[[y0]], k)
  b <- country_means(ALL[[y1]], k)
  a <- a[!is.na(a)]
  b <- b[!is.na(b)]
  if (is.null(isos)) isos <- sort(intersect(names(a), names(b)))
  setNames(rdiff(b[isos], a[isos]), isos)
}

# Country % 'not at all' minus % 'a lot', rounded: counts of gaps of 10+ points either way.
care_gaps <- function(who) {
  t <- distribution(d25, WHO[[who]], by = "COUNTRY_ISO3")
  gap <- r0(t[, "3"] - t[, "1"])
  c(a_lot_higher = sum(gap <= -10), under_10 = sum(gap > -10 & gap < 10), not_at_all_higher = sum(gap >= 10))
}

# Table 3.1: rows of (countries, unrounded %) for the 10 highest % 'not at all'.
# The last row holds every remaining country with the same printed value.
top10 <- function(who) {
  s <- sort(country_pct(d25, WHO[[who]], 3), decreasing = TRUE)
  rows <- lapply(1:9, function(i) list(isos = names(s)[i], value = unname(s[i])))
  rest <- names(s)[10:length(s)]
  last <- rest[r0(s[rest]) == r0(s[10])]
  c(rows, list(list(isos = last, value = unname(s[10]))))
}
country_name <- function(iso) {
  if (iso %in% names(NAME)) NAME[[iso]] else d25$Country[d25$COUNTRY_ISO3 == iso][1]
}

# Global (or by-group) mean of a 0-100 measure over the trend countries.
gm <- function(y, k, by = NULL) wmean(TREND[[as.character(y)]], k, by = by)

# --- Front matter and executive summary -------------------------------------------

finding(report, "X01", function() nrow(d25))
finding(report, "X02", function() length(unique(d25$COUNTRY_ISO3)))
finding(report, "X03", function() c(government = pct(d25, "gov", 1), neighbours = pct(d25, "WP22232", 1)))
finding(report, "X04", function() gm(2025, "index"))
finding(report, "X05", function() rdiff(gm(2025, "index"), gm(2023, "index")))
finding(report, "X06", function() rdiff(gm(2025, "index"), gm(2021, "index")))
finding(report, "X07", function() gm(2021, "index"))
finding(report, "X08", function() gm(2025, "individual"))
finding(report, "X09", function() rdiff(gm(2025, "individual"), gm(2023, "individual")))
finding(report, "X10", function() rdiff(gm(2023, "individual"), gm(2021, "individual")))
finding(report, "X11", function() gm(2021, "individual"))
finding(report, "X12", function() gm(2023, "individual"))
finding(report, "X13", function() gm(2025, "household"))
finding(report, "X14", function() rdiff(gm(2025, "household"), gm(2023, "household")))
finding(report, "X15", function() gm(2025, "community"))
finding(report, "X16", function() rdiff(gm(2025, "community"), gm(2023, "community")))
finding(report, "X17", function() sum(big(agency_change())))
finding(report, "X18", function() sum(big(-agency_change())))
finding(report, "X19", function() sum(big(-agency_change())[c("IND", "PAK", "IDN")]))
finding(report, "X20", function() gm(2025, "societal"))
finding(report, "X21", function() gm(2023, "societal"))
finding(report, "X22", function() gm(2021, "societal"))
finding(report, "X23", function() country_change("societal", isos = SIX))
finding(report, "X24", function() region_change()[c(AFRICA, "latam")])
finding(report, "X25", function() {
  rk <- rank(-region_change(), ties.method = "min")
  sum(rk[AFRICA] <= 4)
})
finding(report, "X26", function() country_change("household", isos = c("DZA", "NGA", "KEN", "EGY", "UGA")))

table_1_3 <- function() {
  out <- c()
  for (y in c(2019, 2025)) {
    g <- internet(y)
    r <- keyed(wmean(g, "yes", by = "GlobalRegion"), REGION)
    r <- r[names(r) %in% AFRICA]
    out <- c(out, setNames(r, paste0(names(r), "_", y)), setNames(wmean(g, "yes"), paste0("global_", y)))
  }
  out
}
finding(report, "X27", function() {
  t <- table_1_3()
  k <- c("north_africa", "cw_africa", "southern_africa")
  setNames(rdiff(t[paste0(k, "_2025")], t[paste0(k, "_2019")]), k)
})

by_life_eval <- function(k) keyed(wmean(wellbeing(), k, by = "life_eval"), LE)
finding(report, "X28", function() by_life_eval("index"))
finding(report, "X29", function() by_life_eval("individual"))
finding(report, "X30", function() {
  t <- by_life_eval("individual")
  unname(t["thriving"] / t["suffering"])
})
finding(report, "X31", function() {
  g <- wellbeing()
  keyed(wmean(g[!is.na(g$ladder) & g$ladder <= 2, ], "index", by = "CountryIncomeLevel"), INCOME)
})

# Chart 2.3: Resilience Index by present life rating and income group ("low_0" ...).
chart_2_3 <- function() {
  t <- wmean(wellbeing(), "index", by = c("CountryIncomeLevel", "ladder"))
  inc <- split_key(names(t), 1)
  keep <- inc %in% names(INCOME)
  setNames(unname(t[keep]), paste0(INCOME[inc[keep]], "_", split_key(names(t)[keep], 2)))
}
finding(report, "X32", function() {
  t <- chart_2_3()
  sum(vapply(INCOME, function(inc) t[[paste0(inc, "_10")]] < t[[paste0(inc, "_9")]], logical(1)))
})

care <- function(df, who) keyed(distribution(df, WHO[[who]]), CARE)
finding(report, "X33", function() care(d25, "government"))
finding(report, "X34", function() rdiff(care(TREND[["2025"]], "government")[["not_at_all"]],
                                        care(TREND[["2021"]], "government")[["not_at_all"]]))
finding(report, "X35", function() {
  a <- care(TREND[["2021"]], "neighbours")
  b <- care(TREND[["2025"]], "neighbours")
  c(a_lot_2025 = b[["a_lot"]], not_at_all_2025 = b[["not_at_all"]], not_at_all_2021 = a[["not_at_all"]],
    a_lot_2021 = a[["a_lot"]], somewhat_2021 = a[["somewhat"]], somewhat_2025 = b[["somewhat"]])
})
finding(report, "X36", function() {
  sum(vapply(TREND, function(d) {
    t <- care(d, "government")
    t[["not_at_all"]] > t[["a_lot"]]
  }, logical(1)))
})
finding(report, "X37", function() care_gaps("government")[["not_at_all_higher"]])
finding(report, "X38", function() care_gaps("government")[["a_lot_higher"]])
finding(report, "X39", function() keyed(pct(d25, "gov", 3, by = "CountryIncomeLevel"), INCOME))
finding(report, "X40", function() pct(d25[d25$CountryIncomeLevel %in% c(2, 3), ], "gov", 3))

# Household resilience by income group and neighbours' care ("low_a_lot" ...).
household_by_neighbour_care <- function() {
  t <- wmean(d25, "household", by = c("CountryIncomeLevel", "WP22232"))
  inc <- split_key(names(t), 1)
  cr <- split_key(names(t), 2)
  keep <- inc %in% names(INCOME) & cr %in% names(CARE)
  setNames(unname(t[keep]), paste0(INCOME[inc[keep]], "_", CARE[cr[keep]]))
}
household_care_gaps <- function() {
  t <- household_by_neighbour_care()
  vapply(INCOME, function(inc) rdiff(t[[paste0(inc, "_a_lot")]], t[[paste0(inc, "_not_at_all")]]), numeric(1)) |>
    setNames(unname(INCOME))
}
finding(report, "X41", household_care_gaps)
finding(report, "X42", function() {
  g <- country_pct(d25, "gov", 3)
  n <- country_pct(d25, "WP22232", 3)
  common <- intersect(names(g), names(n))
  cor(g[common], n[common])
})

# --- Chapter 1 ---------------------------------------------------------------------

finding(report, "X43", function() sum(vapply(ALL, function(d) sum(stats::complete.cases(d[FOUR])), numeric(1))))
finding(report, "X44", function() vapply(HARM, function(v) rsum(d25, v, c(1, 3)), numeric(1)))

finding(report, "C1_1", function() {
  out <- c()
  for (k in names(DIMS)) for (y in names(TREND)) out[paste0(k, "_", y)] <- gm(y, k)
  out
})

by_income <- function(k) keyed(wmean(d25, k, by = "CountryIncomeLevel"), INCOME)
finding(report, "C1_2", function() {
  out <- c()
  for (k in names(DIMS)) {
    v <- by_income(k)
    out[paste0(k, "_", names(v))] <- v
  }
  out
})
finding(report, "X45", function() by_income("index"))
finding(report, "X46", function() by_income("individual"))
finding(report, "X47", function() rdiff(by_income("individual")[["high"]], by_income("individual")[["upper_middle"]]))
finding(report, "X48", function() {
  v <- by_income("individual")
  c(lower_middle = v[["high"]] / v[["lower_middle"]], low = v[["high"]] / v[["low"]])
})
finding(report, "X49", function() by_income("household"))
finding(report, "X50", function() by_income("community"))
finding(report, "X51", function() by_income("societal"))

finding(report, "T1_2", function() {
  out <- c()
  for (y in names(TREND)) {
    v <- keyed(gm(y, "index", by = "GlobalRegion"), REGION)
    out[paste0(names(v), "_", y)] <- v
  }
  out
})
finding(report, "X52", function() region_change()[c("southern_asia", "eastern_asia")])
finding(report, "X53", function() sum(region_change() <= -2))
finding(report, "X54", function() country_change("individual", isos = c("POL", "SVK", "HRV", "BGR", "BIH")))
finding(report, "X55", function() {
  a <- wmean(country(d21, "MAR"), "individual")
  b <- wmean(country(d25, "MAR"), "individual")
  c("change" = rdiff(b, a), "2021" = a, "2025" = b)
})
finding(report, "X56", function() {
  ch <- country_change("individual")
  sum(ch < ch[["POL"]])
})
finding(report, "X57", function() {
  a <- country_pct(d21, "WP22252", 1)
  b <- country_pct(d25, "WP22252", 1)
  isos <- c("SVK", "BGR", "HRV", "POL", "BIH")
  setNames(rdiff(b[isos], a[isos]), isos)
})
# Line charts with no printed values (Charts 1.3 to 1.6): written to output/ only.
country_lines <- function(isos, dims) {
  out <- c()
  for (i in isos) for (k in dims) for (y in names(ALL)) {
    key <- if (length(dims) > 1) paste0(k, "_", y) else paste0(i, "_", y)
    out[key] <- wmean(country(ALL[[y]], i), k)
  }
  out
}
finding(report, "C1_3", function() country_lines(c("POL", "SVK", "HRV", "BGR", "BIH"), "individual"))
finding(report, "X58", function() c(DZA = wmean(country(d25, "DZA"), "household"),
                                    EGY = wmean(country(d25, "EGY"), "household")))
finding(report, "C1_4", function() country_lines(c("DZA", "NGA", "KEN", "EGY", "UGA"), "household"))
finding(report, "X59", function() {
  # % who could cover basic needs for a month or more; don't know and refused excluded.
  a <- country_pct(d21, "WP22228", 2, exclude = DK)
  b <- country_pct(d25, "WP22228", 2, exclude = DK)
  isos <- c("DZA", "EGY", "UGA", "KEN", "NGA")
  setNames(rdiff(b[isos], a[isos]), isos)
})
finding(report, "X60", function() {
  a <- country_pct(d21, "plan", 1, exclude = DK)
  b <- country_pct(d25, "plan", 1, exclude = DK)
  isos <- c("DZA", "KEN")
  setNames(rdiff(b[isos], a[isos]), isos)
})
finding(report, "T1_3", table_1_3)
finding(report, "X61", function() vapply(ALL, function(d) wmean(country(d, "UKR"), "community"), numeric(1)))
finding(report, "X62", function() wmean(country(d25, "UKR"), "individual"))
finding(report, "X63", function() vapply(ALL, function(d) pct(country(d, "UKR"), "WP22232", c(1, 2)), numeric(1)))
finding(report, "C1_5", function() country_lines("UKR", names(DIMS)))
finding(report, "C1_6", function() country_lines(SIX, "societal"))

finding(report, "X64", function() {
  a <- country_pct(d21[d21$COUNTRY_ISO3 %in% SIX, ], "gov", c(1, 2))
  b <- country_pct(d25[d25$COUNTRY_ISO3 %in% SIX, ], "gov", c(1, 2))
  sum(b[SIX] < a[SIX])
})
confidence_fell <- function(item, isos) {
  a <- wmean(gallup_wave(2021, item), "yes", by = "COUNTRY_ISO3")
  b <- wmean(gallup_wave(2025, item), "yes", by = "COUNTRY_ISO3")
  sum(b[isos] < a[isos])
}
finding(report, "X65", function() confidence_fell("WP139", SIX))
finding(report, "X66", function() confidence_fell("WP137", c("AUS", "GRC", "NZL", "NLD")))
finding(report, "X67", function() confidence_fell("WP138", c("AUS", "GRC")))
finding(report, "X68", function() {
  sum(vapply(c("skin", "gender", "disability"), function(k) {
    pct(country(d25, "AUS"), DISC[[k]], 1) > pct(country(d21, "AUS"), DISC[[k]], 1)
  }, logical(1)))
})

dim_ranks <- function(k) ranks(country_means(d25, k))
finding(report, "X69", function() vapply(c("individual", "household", "community"), function(k) wmean(country(d25, "USA"), k), numeric(1)))
finding(report, "X70", function() c(SWE = wmean(country(d25, "SWE"), "individual"),
                                    VNM = wmean(country(d25, "VNM"), "household")))
us_ranks <- function() vapply(FOUR, function(k) unname(dim_ranks(k)["USA"]), numeric(1))
finding(report, "X71", us_ranks)
finding(report, "C1_7", us_ranks)
finding(report, "X72", function() length(dim_ranks("societal")))
finding(report, "X73", function() 100 * dim_ranks("community")[["USA"]] / length(dim_ranks("community")))
finding(report, "X74", function() {
  r <- lapply(FOUR, dim_ranks)
  isos <- Reduce(intersect, lapply(r, names))
  m <- sapply(r, function(v) v[isos])
  colnames(m) <- FOUR
  split <- m[, "societal"] - pmin(m[, "individual"], m[, "household"])
  unname(rank(-split, ties.method = "min")[isos == "USA"])
})

us_confidence <- function(item, year = 2025) wmean(country(gallup_wave(year, item), "USA"), "yes")
# Position from the bottom (or top) as % of countries.
bottom_share <- function(v, iso = "USA") {
  r <- ranks(v, ascending = TRUE)
  100 * r[[iso]] / length(r)
}
top_share <- function(v, iso = "USA") {
  r <- ranks(v)
  100 * r[[iso]] / length(r)
}
finding(report, "X75", function() c(national_government = us_confidence("WP139"), judiciary = us_confidence("WP138")))
finding(report, "X76", function() {
  c(national_government = bottom_share(wmean(gallup_wave(2025, "WP139"), "yes", by = "COUNTRY_ISO3")),
    judiciary = bottom_share(wmean(gallup_wave(2025, "WP138"), "yes", by = "COUNTRY_ISO3")))
})
finding(report, "X77", function() pct(country(d25, "USA"), "gov", 1))
finding(report, "X78", function() bottom_share(country_pct(d25, "gov", 1)))
finding(report, "X79", function() vapply(DISC[c("religion", "disability", "skin", "nationality", "gender")],
                                         function(v) pct(country(d25, "USA"), v, 1), numeric(1)))
finding(report, "X80", function() vapply(DISC[c("religion", "disability")],
                                         function(v) top_share(country_pct(d25, v, 1)), numeric(1)))
finding(report, "X81", function() vapply(DISC[c("skin", "nationality", "gender")],
                                         function(v) unname(ranks(country_pct(d25, v, 1))["USA"]), numeric(1)))
finding(report, "X82", function() {
  a <- us_confidence("WP137", 2019)
  b <- us_confidence("WP137", 2025)
  c("2025" = b, "2019" = a, "change" = rdiff(b, a))
})

# --- Chapter 2 (Gallup Life Evaluation Index) ----------------------------------------

finding(report, "X83", function() {
  vapply(FOUR, function(k) {
    t <- by_life_eval(k)
    rdiff(t[["thriving"]], t[["suffering"]])
  }, numeric(1))
})
finding(report, "X84", function() {
  t <- by_life_eval("index")
  rdiff(t[["thriving"]], t[["suffering"]])
})
chart_2_1_values <- function() {
  t <- wmean(wellbeing(), "index", by = c("CountryIncomeLevel", "life_eval"))
  inc <- split_key(names(t), 1)
  keep <- inc %in% names(INCOME)
  out <- setNames(unname(t[keep]), paste0(INCOME[inc[keep]], "_", LE[split_key(names(t)[keep], 2)]))
  g <- by_life_eval("index")
  c(out, setNames(g, paste0("global_", names(g))))
}
finding(report, "C2_1", chart_2_1_values)
finding(report, "X85", function() {
  t <- chart_2_1_values()
  min(vapply(INCOME, function(inc) rdiff(t[[paste0(inc, "_thriving")]], t[[paste0(inc, "_suffering")]]), numeric(1)))
})
country_wellbeing <- function() {
  g <- wellbeing()
  th <- wmean(g, "thriving", by = "COUNTRY_ISO3")
  ix <- wmean(g, "index", by = "COUNTRY_ISO3")
  isos <- sort(union(names(th), names(ix)))
  data.frame(iso = isos, thriving = unname(th[isos]), index = unname(ix[isos]))
}
finding(report, "C2_2", function() {  # scatter with no printed values: written to output/ only
  t <- country_wellbeing()
  c(setNames(t$thriving, paste0("thriving_", t$iso)), setNames(t$index, paste0("index_", t$iso)))
})
finding(report, "X86", function() {
  t <- country_wellbeing()
  t <- t[stats::complete.cases(t), ]
  cor(t$thriving, t$index)
})
finding(report, "X87", function() median(country_wellbeing()$thriving, na.rm = TRUE))
finding(report, "X88", function() median(country_means(d25, "index"), na.rm = TRUE))
finding(report, "C2_3", chart_2_3)  # line chart with no printed values: written to output/ only
finding(report, "C2_4", function() {
  out <- c()
  for (k in FOUR) {
    v <- by_life_eval(k)
    out[paste0(k, "_", names(v))] <- v
  }
  out
})
finding(report, "X89", function() by_life_eval("household"))
finding(report, "C2_5", function() {
  g <- wellbeing()
  g <- g[!is.na(g$life_eval) & g$life_eval == 3, ]
  out <- c()
  for (k in FOUR) {
    v <- keyed(wmean(g, k, by = "CountryIncomeLevel"), INCOME)
    out[paste0(names(v), "_", k)] <- v
  }
  out
})

# --- Chapter 3 ---------------------------------------------------------------------

finding(report, "X90", function() {
  t <- distribution(d25, "gov") # WP22231_ALL: 99 = don't know or refused
  c(not_at_all = t[["3"]], dk = t[["99"]], somewhat = t[["2"]], a_lot = t[["1"]])
})
finding(report, "X91", function() {
  a <- care(TREND[["2021"]], "government")
  b <- care(TREND[["2025"]], "government")
  c(a_lot_2021 = a[["a_lot"]], a_lot_change = rdiff(b[["a_lot"]], a[["a_lot"]]),
    somewhat_2021 = a[["somewhat"]], somewhat_change = rdiff(b[["somewhat"]], a[["somewhat"]]))
})
finding(report, "C3_1", function() {  # 2023 is plotted but not labelled: written to output/ only
  out <- c()
  for (who in names(WHO)) for (y in names(TREND)) {
    v <- care(TREND[[y]], who)
    out[paste0(who, "_", y, "_", names(v))] <- v
  }
  out
})
finding(report, "X92", function() c(government_under_10 = care_gaps("government")[["under_10"]],
                                    neighbours_not_at_all_higher = care_gaps("neighbours")[["not_at_all_higher"]],
                                    neighbours_a_lot_higher = care_gaps("neighbours")[["a_lot_higher"]]))
finding(report, "C3_2", function() {
  out <- c()
  for (who in names(WHO)) {
    v <- care_gaps(who)
    out[paste0(who, "_", names(v))] <- v
  }
  out
})
finding(report, "X93", function() keyed(pct(d25, "WP22232", 3, by = "CountryIncomeLevel"), INCOME))
finding(report, "C3_3", function() {
  out <- c()
  for (who in names(WHO)) {
    v <- keyed(pct(d25, WHO[[who]], 3, by = "CountryIncomeLevel"), INCOME)
    out[paste0(who, "_", names(v))] <- v
  }
  out
})
finding(report, "C3_4", function() keyed(wmean(wellbeing(), "thriving", by = "CountryIncomeLevel"), INCOME))

by_region <- function(who) keyed(pct(d25, WHO[[who]], 3, by = "GlobalRegion"), REGION)
finding(report, "X94", function() {
  pairs <- list(c("government", "northern_america"), c("government", "cw_africa"), c("neighbours", "eastern_europe"),
                c("neighbours", "latam"), c("government", "eastern_asia"), c("government", "central_asia"),
                c("neighbours", "southeastern_asia"))
  setNames(vapply(pairs, function(p) by_region(p[1])[[p[2]]], numeric(1)),
           vapply(pairs, paste, character(1), collapse = "_"))
})
finding(report, "C3_5", function() {
  out <- c()
  for (who in names(WHO)) {
    v <- by_region(who)
    out[paste0(who, "_", names(v))] <- v
  }
  out
})
finding(report, "T3_1", function() {
  keys <- c()
  vals <- c()
  for (who in names(WHO)) {
    rows <- top10(who)
    for (i in seq_along(rows)) {
      nm <- sort(vapply(rows[[i]]$isos, country_name, character(1)), method = "radix")
      keys <- c(keys, paste0(who, "_", i, "_country"), paste0(who, "_", i, "_value"))
      vals <- c(vals, paste(nm, collapse = ", "), sprintf("%.17g", rows[[i]]$value))
    }
  }
  setNames(vals, keys)
})
both_lists <- function() {
  listed <- lapply(names(WHO), function(who) unlist(lapply(top10(who), `[[`, "isos")))
  sort(intersect(listed[[1]], listed[[2]]))
}
finding(report, "X95", function() length(both_lists()))
finding(report, "X96", function() {
  r <- d25$GlobalRegion[match(both_lists(), d25$COUNTRY_ISO3)]
  sum(r == 5)
})
finding(report, "X97", function() min(country_pct(d25, "gov", 3)[both_lists()]))
finding(report, "X98", function() min(country_pct(d25, "WP22232", 3)[both_lists()]))
finding(report, "X99", function() c(government_PAN = country_pct(d25, "gov", 3)[["PAN"]],
                                    government_PRY = country_pct(d25, "gov", 3)[["PRY"]],
                                    neighbours_ECU = country_pct(d25, "WP22232", 3)[["ECU"]],
                                    neighbours_MEX = country_pct(d25, "WP22232", 3)[["MEX"]]))
finding(report, "C3_6", household_by_neighbour_care)
finding(report, "X100", function() max(household_care_gaps()))

quit(status = run_report(report))
