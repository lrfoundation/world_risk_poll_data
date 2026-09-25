# Reproduce World Risk Poll 2021: A Resilient World? Understanding vulnerability
# in a changing climate.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/core_a_resilient_world/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

DK <- c(98, 99)
DISCRIMINATION <- c("WP22259", "WP22260", "WP22261", "WP22262", "WP22263") # skin, religion, nationality, sex, disability
SERVICES <- c(electricity = "WP22254", water = "WP22255", food = "WP22256",
              medical = "WP22257", telephone = "WP22258")

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
  "Gender", "Education", "Urbanicity", "INCOME_5", "resilience_index",
  "WP20711", "WP20719", "WP22228", "WP22229", "WP22230", "WP22231", "WP22469", "WP22525",
  "WP22232", "WP22240", "WP22241", "WP22242", "WP22243", "WP22244", "WP22245", "WP22247",
  "WP22252", "WP22253", SERVICES, DISCRIMINATION
))

# --- Derived variables ---------------------------------------------------------

recode <- function(x, map) unname(map[as.character(x)])

# Groupings used as keys. CountryIncomeLevel 9 (Venezuela, not classified)
# has no income key, so it drops out of every income breakdown.
d$region <- recode(d$GlobalRegion, c(
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia",
  "9" = "southeastern_asia", "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
))
d$income <- recode(d$CountryIncomeLevel, c("1" = "low_income", "2" = "lower_middle", "3" = "upper_middle", "4" = "high_income"))
d$income3 <- recode(d$CountryIncomeLevel, c("1" = "low_income", "2" = "middle_income", "3" = "middle_income", "4" = "high_income"))
d$income2 <- recode(d$CountryIncomeLevel, c("1" = "low_lower_middle", "2" = "low_lower_middle",
                                            "3" = "upper_middle_high", "4" = "upper_middle_high"))
# Urbanicity: large cities and their suburbs are one group ("large cities/suburbs").
d$urban <- recode(d$Urbanicity, c("1" = "rural", "2" = "small_town", "3" = "large_city", "6" = "large_city"))

# Basic needs (Chart 1.3), as in the Focus On: Risk and Gender pilot.
# 4 = less than a month, weeks not known; 9 = a month or more, months not known.
d$basic_needs <- with(d, case_when(
  WP22228 %in% 1 & WP22229 %in% 1:3 ~ as.numeric(WP22229),
  WP22228 %in% 1 ~ 4,
  WP22228 %in% 2 & WP22230 %in% 1:4 ~ as.numeric(WP22230) + 4,
  WP22228 %in% 2 ~ 9,
  TRUE ~ 98
))

# Government cares: Vietnam (WP22469, "the authorities") and Myanmar (WP22525)
# were asked alternative wordings of WP22231. Merging them reproduces Chart 2.6.
d$gov_cares <- coalesce(d$WP22231, d$WP22469, d$WP22525)

# Any discrimination (Chart 2.5, X20): yes to any of the five types.
# Respondents in the three countries not asked count as "no" (as in the pilot).
d$any_discrimination <- ifelse(rowSums(d[DISCRIMINATION] == 1, na.rm = TRUE) > 0, 1, 2)

# Type of the last disaster (Charts 4.1, 4.2): 0 = no disaster in the past
# five years (including don't know/refused to WP22245); 50 = drought.
d$disaster_type <- ifelse(d$WP22245 %in% 1, d$WP22247, 0)

# --- Helpers -------------------------------------------------------------------

# Some of the values of a named vector.
pick <- function(values, ...) {
  keys <- c(...)
  setNames(unname(values[keys]), keys)
}

# % in each named category of `var` for each `by` group: c("<group>_<category>" = %).
by_category <- function(df, var, categories, by) {
  out <- numeric(0)
  for (name in names(categories)) {
    r <- pct(df, var, categories[[name]], by = by)
    out[paste(names(r), name, sep = "_")] <- r
  }
  out
}

# % with `var` in `codes` for the listed countries, named by ISO3.
country_values <- function(df, var, codes, isos) {
  pick(pct(df, var, codes, by = "COUNTRY_ISO3"), isos)
}

# Country names with gap > threshold, largest first, as "A; B; C".
names_by_gap <- function(gaps, threshold, exclude = character(0)) {
  g <- gaps[!is.na(gaps) & !(names(gaps) %in% exclude)]
  g <- sort(g[g > threshold], decreasing = TRUE)
  paste(names(g), collapse = "; ")
}

# Country-level gap in mean Resilience Index between two groups of `by`.
resilience_gap <- function(df, by, high, low) {
  m_high <- wmean(df[df[[by]] %in% high, ], "resilience_index", by = "Country")
  m_low <- wmean(df[df[[by]] %in% low, ], "resilience_index", by = "Country")
  common <- intersect(names(m_high), names(m_low))
  m_high[common] - m_low[common]
}

YES <- 1

# --- Executive summary ---------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))

# --- Chapter 1: individual- and household-level indicators ---------------------

AGENCY <- list(yes = 1, no = 2, depends = 3, dk = DK)
could_protect <- function() sapply(AGENCY, function(codes) pct(d, "WP22252", codes))
finding(report, "X03", could_protect)
finding(report, "C1_1", could_protect)
finding(report, "X04", function() pct(d, "WP22252", YES, by = "income3"))
finding(report, "X05", function() pct(d, "WP22252", YES, by = "region")[["southern_africa"]])
finding(report, "X06", function() pct(d, "WP22252", YES, by = "region")[["southeastern_asia"]])
finding(report, "C1_2", function() pct(d, "WP22252", YES, by = "region"))

finding(report, "X07", function() pct(d, "basic_needs", 1:4))
finding(report, "X08", function() pct(d, "basic_needs", 1))
finding(report, "X09", function() pick(pct(d, "basic_needs", 1:4, by = "region"), "southern_asia", "northern_africa"))
finding(report, "C1_3", function() {
  by_category(d, "basic_needs", list(
    lt_week = 1, week_to_month = 2:4, month_to_3 = 5:7, `4_plus` = 8, dk = c(9, 98)
  ), by = "region")
})

# Internet access (WP16056) and mobile phone (WP17626) are Gallup World Poll
# items that are not in the public release.
finding(report, "X10", function() {
  g <- merge_gallup(d, "WP16056")
  pct(g, "WP16056", YES, by = "income")
})
finding(report, "C1_4", function() {
  g <- merge_gallup(d, c("WP16056", "WP17626"))
  net <- pct(g, "WP16056", YES, by = "income")
  mob <- pct(g, "WP17626", YES, by = "income")
  c(setNames(net, paste0(names(net), "_internet")), setNames(mob, paste0(names(mob), "_mobile")))
})
finding(report, "C1_5", function() {
  g <- merge_gallup(d, "WP16056")
  r <- pct(g, "WP22252", YES, by = c("income", "WP16056"))
  r <- r[grepl("_(1|2)$", names(r))]
  setNames(r, sub("_1$", "_internet", sub("_2$", "_no_internet", names(r))))
})

PLAN <- pct(d, "WP22253", YES, by = "COUNTRY_ISO3")
PLAN_MAJORITY <- names(PLAN)[PLAN > 50]
finding(report, "X11", function() length(PLAN_MAJORITY))
finding(report, "X12", function() {
  length(unique(d$COUNTRY_ISO3[d$COUNTRY_ISO3 %in% PLAN_MAJORITY & d$region %in% "southeastern_asia"]))
})
finding(report, "X13", function() sum(PLAN >= 70))
finding(report, "C1_6", function() PLAN[PLAN > 50])

# --- Chapter 2: community- and society-level indicators ------------------------

CARES <- list(a_lot = 1, somewhat = 2, not_at_all = 3)
finding(report, "X14", function() sapply(CARES, function(codes) pct(d, "WP22232", codes)))
finding(report, "X15", function() pick(pct(d, "WP22232", YES, by = "income"), "low_income", "high_income"))
finding(report, "C2_1", function() c(pct(d, "WP22232", YES, by = "income"), pct(d, "WP22232", YES, by = "urban")))
finding(report, "X16", function() {
  pick(pct(d, "WP22245", YES, by = "income"), "low_income", "upper_middle", "high_income")
})

# Helped a stranger (WP110) is a Gallup World Poll item (not asked in China).
helped_stranger <- function() merge_gallup(d, "WP110")
finding(report, "X17", function() {
  pick(pct(helped_stranger(), "WP110", YES, by = "region"),
       "latin_america", "northern_america", "northern_western_europe", "eastern_asia")
})
finding(report, "C2_2", function() pct(helped_stranger(), "WP110", YES, by = "region"))
finding(report, "C2_3_median_helped", function() median(pct(helped_stranger(), "WP110", YES, by = "COUNTRY_ISO3")))
finding(report, "C2_3_median_neighbours", function() median(pct(d, "WP22232", YES, by = "COUNTRY_ISO3")))
finding(report, "X18", function() pct(helped_stranger(), "WP110", YES, by = "COUNTRY_ISO3")[["JPN"]])
finding(report, "X19", function() pct(d, "WP22232", YES, by = "COUNTRY_ISO3")[["JPN"]])

# Satisfaction with healthcare (WP97), schools (WP93) and roads (WP92) are
# Gallup World Poll items; 2 = dissatisfied.
INFRASTRUCTURE <- list(
  healthcare = list("WP97", c("VEN", "LBN", "GAB", "AFG", "ZMB", "TGO", "MAR", "MNG", "RUS", "MLI")),
  education = list("WP93", c("VEN", "MLI", "LBN", "AFG", "GAB", "ZWE", "UGA", "IRQ", "MNG", "GIN")),
  roads = list("WP92", c("VEN", "MNG", "SLE", "GAB", "TGO", "GIN", "ZMB", "LBN", "MLI", "ZWE"))
)
finding(report, "T2_1", function() {
  g <- merge_gallup(d, vapply(INFRASTRUCTURE, `[[`, "", 1))
  out <- numeric(0)
  for (key in names(INFRASTRUCTURE)) {
    v <- country_values(g, INFRASTRUCTURE[[key]][[1]], 2, INFRASTRUCTURE[[key]][[2]])
    out[paste(key, names(v), sep = "_")] <- v
  }
  out
})

finding(report, "X20", function() pct(d, "any_discrimination", YES))
FOUR_TYPES <- c(skin = "WP22259", religion = "WP22260", nationality = "WP22261", sex = "WP22262")
finding(report, "X21", function() {
  values <- sapply(FOUR_TYPES, function(v) pct(d, v, YES))
  c(low = min(values), high = max(values))
})
finding(report, "X22", function() pct(d, "WP22263", YES))
finding(report, "X23", function() sapply(FOUR_TYPES[c("nationality", "religion", "sex")], function(v) pct(d, v, YES)))
TYPES <- c(FOUR_TYPES, disability = "WP22263")
finding(report, "C2_4", function() sapply(TYPES, function(v) pct(d, v, YES)))

TOP5 <- list(
  nationality = c("AFG", "ZMB", "CMR", "BOL", "KEN"), religion = c("ZMB", "BRA", "UGA", "CMR", "BOL"),
  sex = c("ZMB", "BOL", "AFG", "USA", "AUS"), skin = c("ZMB", "USA", "BOL", "BRA", "MOZ"),
  disability = c("BGD", "MOZ", "CMR", "COG", "GIN")
)
finding(report, "T2_2", function() {
  out <- numeric(0)
  for (k in names(TOP5)) {
    v <- country_values(d, TYPES[[k]], YES, TOP5[[k]])
    out[paste(k, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "X24", function() {
  sapply(TYPES[c("skin", "nationality", "sex")], function(v) pct(d, v, YES, by = "COUNTRY_ISO3")[["USA"]])
})

ANY_BY_COUNTRY <- pct(d, "any_discrimination", YES, by = "COUNTRY_ISO3")
finding(report, "X25", function() {
  top10 <- names(sort(ANY_BY_COUNTRY, decreasing = TRUE))[1:10]
  length(unique(d$COUNTRY_ISO3[d$COUNTRY_ISO3 %in% top10 & d$CountryIncomeLevel %in% 4]))
})
finding(report, "X26", function() pick(ANY_BY_COUNTRY, "ZMB", "BOL", "CMR", "UGA", "BRA", "USA"))
finding(report, "C2_5", function() {
  c(pick(ANY_BY_COUNTRY, "USA", "AFG", "BRA", "CMR", "UGA", "ZMB", "BOL", "COG", "MOZ", "ZWE"),
    max = max(ANY_BY_COUNTRY))
})

finding(report, "X27", function() sapply(CARES, function(codes) pct(d, "gov_cares", codes)))
finding(report, "X28", function() pick(pct(d, "gov_cares", 3, by = "region"), "central_western_africa", "latin_america"))
finding(report, "C2_6", function() by_category(d, "gov_cares", c(CARES, list(dk = DK)), by = "region"))

GOV_NOT_AT_ALL <- pct(d, "gov_cares", 3, by = "COUNTRY_ISO3")
COUNTRY_REGION <- setNames(d$region, d$COUNTRY_ISO3)[!duplicated(d$COUNTRY_ISO3)]
finding(report, "T2_3", function() {
  pick(GOV_NOT_AT_ALL, "ROU", "IRQ", "HND", "PRY", "BIH", "LBN", "VEN", "SEN", "ALB", "PAN", "NGA", "COL")
})
finding(report, "X29", function() {
  top12 <- names(sort(GOV_NOT_AT_ALL, decreasing = TRUE))[1:12]
  sum(COUNTRY_REGION[top12] == "latin_america")
})
finding(report, "X30", function() {
  over <- COUNTRY_REGION[names(GOV_NOT_AT_ALL)[GOV_NOT_AT_ALL > 50]]
  regions <- c("eastern_europe", "southern_europe", "northern_western_europe")
  setNames(sapply(regions, function(r) sum(over == r)), regions)
})
finding(report, "X31", function() {
  regions <- c("eastern_europe", "southern_europe")
  setNames(sapply(regions, function(r) sum(COUNTRY_REGION == r)), regions)
})

# National Institutions Index: Gallup World Poll index (0-100) built from
# confidence in the military, the judiciary, the national government and
# the honesty of elections. INDEX_NI is a placeholder name; see README.
finding(report, "C2_7", function() wmean(merge_gallup(d, "INDEX_NI"), "INDEX_NI", by = "region"))
finding(report, "C2_8", function() {
  # Scatter with no printed values: country-level correlation between the
  # % saying the government cares 'a lot' or 'somewhat' and the mean index.
  g <- merge_gallup(d, "INDEX_NI")
  x <- pct(g, "gov_cares", c(1, 2), by = "COUNTRY_ISO3")
  y <- wmean(g, "INDEX_NI", by = "COUNTRY_ISO3")
  common <- intersect(names(x), names(y))
  c(corr = cor(x[common], y[common]))
})

# --- Chapter 3: Towards a global Resilience Index -------------------------------

finding(report, "C3_1", function() wmean(d, "resilience_index", by = "region"))
finding(report, "X32", function() {
  r <- wmean(d, "resilience_index", by = "INCOME_5")
  c(bottom = r[["1"]], top = r[["5"]])
})
finding(report, "C3_2", function() {
  sex <- wmean(d, "resilience_index", by = "Gender")
  quintile <- wmean(d, "resilience_index", by = "INCOME_5")
  c(men = sex[["1"]], women = sex[["2"]], wmean(d, "resilience_index", by = "urban"),
    setNames(quintile[as.character(1:5)], paste0("q", 1:5)))
})
finding(report, "X33", function() {
  r <- wmean(d[d$COUNTRY_ISO3 == "AFG", ], "resilience_index", by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})
finding(report, "X34", function() {
  names_by_gap(resilience_gap(d, "Gender", 1, 2), 0.07, exclude = "Afghanistan")
})
finding(report, "X35", function() {
  r <- wmean(d[d$COUNTRY_ISO3 %in% c("ZAF", "NGA"), ], "resilience_index", by = c("COUNTRY_ISO3", "urban"))
  pick(r, "ZAF_large_city", "ZAF_rural", "NGA_large_city", "NGA_rural")
})
finding(report, "X36", function() {
  names_by_gap(resilience_gap(d, "urban", "large_city", "rural"), 0.08 - 1e-9, exclude = c("South Africa", "Nigeria"))
})
finding(report, "X37", function() {
  r <- pct(d[d$COUNTRY_ISO3 %in% c("ZAF", "NGA"), ], "Education", 1, by = c("COUNTRY_ISO3", "urban"))
  pick(r, "NGA_rural", "NGA_large_city", "ZAF_rural", "ZAF_large_city")
})

INCOME_GAP_COUNTRIES <- c("AFG", "EGY", "USA", "BOL", "MEX", "ZMB", "LBN", "EST", "IND", "ECU")
finding(report, "T3_3", function() {
  m <- wmean(d, "resilience_index", by = c("COUNTRY_ISO3", "INCOME_5"))
  out <- numeric(0)
  for (iso in INCOME_GAP_COUNTRIES) {
    lo <- m[[paste0(iso, "_1")]]
    hi <- m[[paste0(iso, "_5")]]
    out[paste0(iso, c("_bottom", "_top", "_difference"))] <- c(lo, hi, hi - lo)
  }
  out
})

finding(report, "X38", function() pct(d, "WP20711", 2))
finding(report, "X39", function() {
  r <- wmean(d, "resilience_index", by = "WP20711")
  c(less_safe = r[["2"]], about_as_safe = r[["3"]], more_safe = r[["1"]])
})
finding(report, "X40", function() {
  r <- pct(d, "WP20711", 2, by = "gov_cares")
  c(not_at_all = r[["3"]], a_lot = r[["1"]])
})
finding(report, "X41", function() {
  r <- pct(d, "WP20711", 2, by = "WP22261")
  c(yes = r[["1"]], no = r[["2"]])
})

# Population = sum of PROJWT among group members with an index score.
low_resilience_group <- function(rows) {
  g <- d[rows & !is.na(d$resilience_index), ]
  c(population = sum(g$PROJWT), score = wmean(g, "resilience_index"))
}
# "Lower income quintiles" = the bottom three quintiles, which reproduces
# the published population size.
finding(report, "X42", function() {
  low_resilience_group(d$COUNTRY_ISO3 == "AFG" & d$Gender == 2 & d$INCOME_5 %in% 1:3)
})
finding(report, "X43", function() {
  r <- pct(d[d$COUNTRY_ISO3 == "AFG", ], "Education", 1, by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})
# Rural = "a rural area or on a farm" (Urbanicity 1); bottom three quintiles.
finding(report, "X44", function() {
  low_resilience_group(d$region == "central_western_africa" & d$Urbanicity %in% 1 &
                         d$Gender == 2 & d$INCOME_5 %in% 1:3)
})
finding(report, "X45", function() {
  r <- pct(d[d$region == "central_western_africa" & d$Urbanicity %in% 1, ], "Education", 1, by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})

# --- Chapter 4: Resilience and natural hazards ---------------------------------

DISASTER_TYPES <- list(flood = 1, hurricane = 2, earthquake = 7, drought = 50, wildfire = 8,
                       thunder = 4, tornado = 3, blizzard = 10, mudslide = 6, volcano = 9, tsunami = 5)
type_pct <- function(keys, df = d) sapply(DISASTER_TYPES[keys], function(codes) pct(df, "disaster_type", codes))

finding(report, "X46", function() pct(d, "WP22245", YES))
finding(report, "X47", function() type_pct(c("flood", "hurricane", "earthquake")))
finding(report, "X48", function() type_pct(c("drought", "wildfire", "thunder")))
finding(report, "C4_1", function() type_pct(names(DISASTER_TYPES)))
finding(report, "X49", function() pick(pct(d, "WP22245", YES, by = "region"), "middle_east", "southeastern_asia"))
finding(report, "X50", function() {
  c(pick(pct(d, "disaster_type", 7, by = "region"), "middle_east"),
    pick(pct(d, "disaster_type", 7, by = "COUNTRY_ISO3"), "IRN", "TUR"))
})
finding(report, "X51", function() {
  type_pct(c("flood", "hurricane", "earthquake"), d[d$region %in% "southeastern_asia", ])
})
finding(report, "C4_2", function() {
  by_category(d, "disaster_type", list(
    flood = 1, hurricane = 2, earthquake = 7, drought = 50, wildfire = 8,
    other = c(3, 4, 5, 6, 9, 10, 11), none = 0
  ), by = "region")
})
finding(report, "X52", function() {
  c(pick(pct(d, "disaster_type", 1, by = "region"), "central_western_africa"),
    pick(pct(d, "disaster_type", 1, by = "COUNTRY_ISO3"), "BFA", "BEN", "SLE", "TGO"))
})

# % who went without each service, by experience of disaster (WP22245 1 = yes, 2 = no).
services_by_disaster <- function(df) {
  out <- numeric(0)
  for (service in names(SERVICES)) {
    r <- pct(df, SERVICES[[service]], YES, by = "WP22245")
    out[paste0(service, c("_disaster", "_no_disaster"))] <- c(r[["1"]], r[["2"]])
  }
  out
}
finding(report, "X53", function() {
  r <- services_by_disaster(d)
  min(r[paste0(names(SERVICES), "_disaster")] - r[paste0(names(SERVICES), "_no_disaster")])
})
finding(report, "C4_3", function() services_by_disaster(d))
finding(report, "C4_4", function() {
  out <- numeric(0)
  for (grp in c("low_lower_middle", "upper_middle_high")) {
    v <- services_by_disaster(d[d$income2 %in% grp, ])
    out[paste(grp, names(v), sep = "_")] <- v
  }
  out
})

finding(report, "X54", function() pct(d, "WP22243", YES))
finding(report, "X55", function() {
  pick(pct(d, "WP22243", YES, by = "region"), "southern_asia", "northern_america", "australia_nz",
       "southeastern_asia", "central_western_africa", "latin_america", "northern_africa", "southern_africa")
})
finding(report, "X56", function() wmean(d, "resilience_index", by = "region")[["southern_asia"]])
finding(report, "C4_5", function() pct(d, "WP22243", YES, by = "region"))
# National government: WP22241 only; Myanmar's alternative wording
# (WP22526, "the government in power") is not merged.
finding(report, "C4_6", function() {
  c(by_category(d, "WP22242", list(hospitals = 1), by = "region"),
    by_category(d, "WP22244", list(local = 1), by = "region"),
    by_category(d, "WP22241", list(national = 1), by = "region"))
})

TRUST_MOST <- list(local_news = 3, weather_service = 1, internet = 7, emergency = 6,
                   disaster_agency = 2, religious = 4, famous = 5)
finding(report, "X57", function() sapply(TRUST_MOST[c("local_news", "weather_service", "internet")], function(codes) pct(d, "WP22240", codes)))
finding(report, "X58", function() pct(d, "WP22240", 4, by = "income")[["low_income"]])
finding(report, "T4_1", function() {
  out <- numeric(0)
  for (source in names(TRUST_MOST)) {
    out[paste0(source, "_all")] <- pct(d, "WP22240", TRUST_MOST[[source]])
    r <- pct(d, "WP22240", TRUST_MOST[[source]], by = "income")
    out[paste(source, names(r), sep = "_")] <- r
  }
  out
})

DISASTER_BY_COUNTRY <- pct(d, "WP22245", YES, by = "Country")
finding(report, "X59", function() paste(names(sort(DISASTER_BY_COUNTRY, decreasing = TRUE))[1:2], collapse = "; "))
finding(report, "C4_7", function() {
  # Scatter with no printed values: country-level correlation between the
  # mean Resilience Index and the % who experienced a disaster.
  r <- wmean(d, "resilience_index", by = "Country")
  common <- intersect(names(r), names(DISASTER_BY_COUNTRY))
  c(corr = cor(r[common], DISASTER_BY_COUNTRY[common]))
})
finding(report, "X60", function() {
  r <- pct(d, "WP20719", c(1, 2), by = "WP22245")
  c(disaster = r[["1"]], no_disaster = r[["2"]])
})
finding(report, "X61", function() {
  r <- pct(d, "WP20719", 1, by = "WP22245")
  c(disaster = r[["1"]], no_disaster = r[["2"]])
})

# % climate change a very serious threat: experienced this type vs everyone else.
very_serious_by_type <- function(codes) {
  dd <- d
  dd$this_type <- ifelse(dd$disaster_type %in% codes, 1, 2)
  r <- pct(dd, "WP20719", 1, by = "this_type")
  c(r[["1"]], r[["2"]])
}
finding(report, "X62", function() setNames(very_serious_by_type(2), c("hurricane", "no_hurricane")))
finding(report, "T4_2", function() {
  r <- pct(d, "WP20719", 1, by = "WP22245")
  out <- c(any_experienced = r[["1"]], any_not = r[["2"]], any_difference = r[["1"]] - r[["2"]])
  for (k in c("drought", "wildfire", "flood", "hurricane", "earthquake")) {
    v <- very_serious_by_type(DISASTER_TYPES[[k]])
    out[paste0(k, c("_experienced", "_not", "_difference"))] <- c(v, v[1] - v[2])
  }
  out
})

# --- Appendix 3: Resilience Index methodology ------------------------------------

finding(report, "X63", function() sum(tapply(!is.na(d$resilience_index), d$COUNTRY_ISO3, sum) == 0))
finding(report, "X64", function() {
  # A country with an index score counts when every respondent is missing
  # the National Institutions Index, government cares or all discrimination items.
  g <- merge_gallup(d, "INDEX_NI")
  per_country <- function(x) tapply(x, g$COUNTRY_ISO3, sum)
  index <- per_country(!is.na(g$resilience_index))
  ni <- per_country(!is.na(g$INDEX_NI))
  gov <- per_country(!is.na(g$gov_cares))
  disc <- per_country(rowSums(!is.na(g[DISCRIMINATION])) > 0)
  keep <- index > 0
  sum(ni[keep] == 0 | gov[keep] == 0 | disc[keep] == 0)
})
finding(report, "A3_1", function() {
  # Histogram on page 61 has no printed values: weighted mean and SD.
  g <- d[!is.na(d$resilience_index), ]
  m <- wmean(g, "resilience_index")
  c(mean = m, sd = sqrt(sum(g$PROJWT * (g$resilience_index - m)^2) / sum(g$PROJWT)))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
