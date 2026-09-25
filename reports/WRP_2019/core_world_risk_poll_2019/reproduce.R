# Reproduce The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll.
#
# Run from the repository root:
#   Rscript reports/WRP_2019/core_world_risk_poll_2019/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes. One section per chapter of the report.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

# `df` plus any of `columns` it does not have yet, loaded from the 2019 file.
# Every load of the wave has the same rows in the same order.
add_columns <- function(df, columns) {
  new <- setdiff(unique(columns), names(df))
  if (length(new)) cbind(df, load_wave(2019, new)) else df
}


# ==============================================================================
# Part 1: Executive Summary, Introduction, Chapters 1-2
# ==============================================================================

# --- Data ----------------------------------------------------------------------
# Columns used by the report. Later chapters add theirs to this list.

COLUMNS <- c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
  "Gender", "AgeGroups4", "Education", "Urbanicity2", "IncomeFeelings",
  "worry_index_published", "experience_index_published",
  "L1", "L2", "L3_A", "L3_B", "L4A", "L5", "L8A", "L8B", "L13G", "L13H", "L14",
  "L16A", "L16B", "L16C", "L19", "L20D", "L21D", "L27A", "L27B", "L27C"
)
d <- load_wave(2019, COLUMNS)

WORLD_BANK <- read.csv(external_path("core_world_risk_poll_2019__worldbank.csv"), stringsAsFactors = FALSE)

# Freedom in the World 2020 scores. Not redistributed here: see reports/external/README.md.
freedom_house <- function() {
  fh <- read.csv(external_path("core_world_risk_poll_2019__freedom_house.csv"), stringsAsFactors = FALSE)
  fh[!is.na(fh$iso3) & nzchar(fh$iso3), ]
}

# --- Codes -----------------------------------------------------------------------

DK <- c(98, 99)
REGION <- c( # GlobalRegion
  "1" = "east_africa", "2" = "central_west_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "north_america", "7" = "central_asia", "8" = "east_asia",
  "9" = "southeast_asia", "10" = "south_asia", "11" = "middle_east", "12" = "east_europe",
  "13" = "north_west_europe", "14" = "south_europe", "15" = "aus_nz"
)
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # CountryIncomeLevel
SEX <- c("2" = "women", "1" = "men") # Gender
SAFE <- list(more = 1, same = 3, less = 2) # L2
RISK <- list(opp = 1, danger = 2, both = 3, neither = 4, dk = DK) # L1

# --- Derived variables -------------------------------------------------------------

# Safety scale for footnote 34: 1 = more safe, 2 = about as safe, 3 = less safe (DK/refused missing).
d$safety_scale <- unname(c("1" = 1, "3" = 2, "2" = 3)[as.character(d$L2)])

# Greatest sources of risk (L3_A first response, L3_B second response). Global "first or
# second response" figures add the two response shares (mentions()); country, region and
# group figures use the t2_* flags: named the category (or group) first or second.
TOP2_GROUPS <- list(
  road = c(1, 2), health = c(9, 10), crime = 3, financial = c(5, 6),
  environment = c(13, 16), food_water = c(11, 12), political = 7, none = 19
)
for (name in names(TOP2_GROUPS)) {
  codes <- TOP2_GROUPS[[name]]
  d[[paste0("t2_", name)]] <- ifelse(d$L3_A %in% codes | d$L3_B %in% codes, 1, 2)
}
d$second_response <- ifelse(is.na(d$L3_B), 0, d$L3_B) # 0 = not asked the follow-up

# Government Safety Performance Index (Chapter 9, used in the Executive Summary):
# yes = 1, any other answer = 0 on L16A-C, averaged and x 100. Not asked in two countries.
gspi <- d[!is.na(d$L16A), ]
gspi$gspi <- 100 * rowMeans(cbind(gspi$L16A %in% 1, gspi$L16B %in% 1, gspi$L16C %in% 1))

# --- Helpers -------------------------------------------------------------------------

# % in each named category of `var`: c(<name> = %).
shares <- function(df, var, categories, exclude = NULL) {
  tab <- distribution(df, var, exclude = exclude)
  sapply(categories, function(codes) sum(tab[intersect(as.character(codes), names(tab))]))
}

# % in each named category of `var` within each group of `by`: c(<group>_<name> = %).
grid <- function(df, var, categories, by, groups) {
  tab <- distribution(df, var, by = by)
  out <- numeric(0)
  for (code in names(groups)) {
    for (name in names(categories)) {
      cols <- intersect(as.character(categories[[name]]), colnames(tab))
      out[paste(groups[[code]], name, sep = "_")] <- sum(tab[code, cols])
    }
  }
  out
}

# Rename a vector named by group codes: c(<group> = value).
keyed <- function(values, groups) setNames(unname(values[names(groups)]), unname(groups))

by_country <- function(df, var, codes) pct(df, var, codes, by = "COUNTRY_ISO3")

# All country values plus the lowest and highest (the map legend's end points).
world_map <- function(values) c(values, min = min(values), max = max(values))

# ISO3 codes of the n highest (or lowest) countries, named 1..n.
ranked <- function(values, n, lowest = FALSE) {
  setNames(names(sort(values, decreasing = !lowest))[seq_len(n)], seq_len(n))
}

# Global 'first or second response' %: % naming `codes` first plus % naming them second.
mentions <- function(df, codes) {
  w <- df$PROJWT
  100 * (sum(w * (df$L3_A %in% codes)) + sum(w * (df$L3_B %in% codes))) / sum(w)
}

# Adults represented: sum of PROJWT over the rows in `mask`, in whole people.
population <- function(mask) round(sum(d$PROJWT[mask]))

# World Bank indicator by ISO3, for one year or the most recent value up to a year.
world_bank <- function(indicator, year = NULL, latest_upto = NULL) {
  x <- WORLD_BANK[WORLD_BANK$indicator == indicator, ]
  if (!is.null(year)) {
    x <- x[x$year == year, ]
  } else {
    x <- x[x$year <= latest_upto, ]
    x <- x[order(x$iso3, -x$year), ]
    x <- x[!duplicated(x$iso3), ]
  }
  setNames(x$value, x$iso3)
}

# Pearson correlation across the countries present in both series, and the count.
correlation <- function(x, y) {
  iso <- intersect(names(x), names(y))
  ok <- iso[!is.na(x[iso]) & !is.na(y[iso])]
  c(r = cor(x[ok], y[ok]), n = length(ok))
}

# Weighted % by country and sex: list(men = <by ISO3>, women = <by ISO3>).
by_country_sex <- function(df, var, codes) {
  r <- pct(df, var, codes, by = c("COUNTRY_ISO3", "Gender"))
  iso <- sub("_[^_]*$", "", names(r))
  sex <- sub("^.*_", "", names(r))
  list(men = setNames(unname(r[sex == "1"]), iso[sex == "1"]),
       women = setNames(unname(r[sex == "2"]), iso[sex == "2"]))
}

# --- Executive Summary, Preface and Foreword ----------------------------------------

finding(report, "E01", function() nrow(d))
finding(report, "E02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "E03", function() nrow(d))
finding(report, "E04", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "E05", function() nrow(d))
finding(report, "E06", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "E07", function() pct(d, "L3_A", 19))
finding(report, "E08", function() pct(d, "second_response", 19))
finding(report, "E09", function() pct(d, "L14", 5))
finding(report, "E10", function() pct(d[d$CountryIncomeLevel == 1, ], "L13G", 1))
finding(report, "E11", function() pct(d[d$CountryIncomeLevel == 1, ], "L13H", 1))
finding(report, "E12", function() pct(d[d$Gender == 2, ], "L2", 2))

# Violence and harassment at work (L20D risk, L21D experience): asked of workers.
women <- d[d$Gender == 2, ]
women_vh_risk <- by_country(women, "L20D", 1)
women_vh_experience <- by_country(women, "L21D", 1)

finding(report, "E13", function() women_vh_risk[c("MWI", "SWZ", "NPL")])
finding(report, "E14", function() women_vh_risk[c("FIN", "FRA", "SWE", "AUS")])
finding(report, "E15", function() women_vh_experience[["ZMB"]])
finding(report, "E16", function() ranked(women_vh_experience, 1)[[1]])
finding(report, "E17", function() which(names(sort(women_vh_experience, decreasing = TRUE)) == "AUS"))
finding(report, "E18", function() women_vh_experience[["AUS"]])
finding(report, "E19", function() by_country(d[d$Gender == 1, ], "L21D", 1)[["AUS"]])
finding(report, "E20", function() pct(d, "L19", 1))
finding(report, "E21", function() sum(by_country(d, "L19", 1) > 50))
finding(report, "E22", function() pct(d, "L8A", 1))
finding(report, "E23", function() population(d$L8A %in% 1))
finding(report, "E24", function() pct(d, "L8B", 1))
finding(report, "E25", function() population(d$L8B %in% 1))
finding(report, "E26", function() by_country(d, "L8A", 1)[c("LBR", "ZMB", "MOZ")])
finding(report, "E27", function() pct(d, "L4A", 2))
finding(report, "E28", function() {
  users <- d[!is.na(d$L27A), ] # internet users in the past 30 days
  users$any_worry <- ifelse(users$L27A %in% 1 | users$L27B %in% 1 | users$L27C %in% 1, 1, 2)
  pct(users, "any_worry", 1)
})
finding(report, "E29", function() pct(d, "L27B", 1))
finding(report, "E30", function() pct(d, "L27C", 1))
finding(report, "E31", function() by_country(d, "L27C", 1)[c("PRT", "FRA", "ESP", "GBR", "ITA")])
finding(report, "E32", function() pct(d, "L5", c(1, 2)))
finding(report, "E33", function() by_country(d, "L5", 1)[["CHN"]])
finding(report, "E34", function() by_country(d, "L5", 3)[["USA"]])

worry <- wmean(d, "worry_index_published", by = "COUNTRY_ISO3")
experience <- wmean(d, "experience_index_published", by = "COUNTRY_ISO3")
worry_gap <- worry - experience[names(worry)]

finding(report, "E35", function() length(intersect(names(worry)[!is.na(worry)], names(experience)[!is.na(experience)])))
finding(report, "E36", function() ranked(worry_gap, 5))
finding(report, "E37", function() ranked(worry_gap, 1, lowest = TRUE)[[1]])
finding(report, "E38", function() ranked(worry, 5))
finding(report, "E39", function() ranked(experience, 4))

gspi_country <- wmean(gspi, "gspi", by = "COUNTRY_ISO3")
finding(report, "E40", function() 100 * mean(gspi_country < 50))
finding(report, "E41", function() ranked(gspi_country, 4, lowest = TRUE))
finding(report, "E42", function() ranked(gspi_country, 2))

# --- Introduction ------------------------------------------------------------------------

finding(report, "I01", function() length(unique(d$COUNTRY_ISO3)))

# --- Chapter 1: How safe do we feel? --------------------------------------------------------

finding(report, "X1_01", function() pct(d, "L2", 1))
finding(report, "X1_02", function() pct(d, "L2", 2))
finding(report, "X1_03", function() pct(d, "L2", 3))
finding(report, "X1_04", function() pct(d, "L1", 2))
finding(report, "X1_05", function() pct(d, "L1", 1))
finding(report, "X1_06", function() pct(d, "L2", 1))
finding(report, "X1_07", function() pct(d, "L2", 2))
finding(report, "C1_1", function() shares(d, "L2", c(SAFE, list(dk = DK))))
finding(report, "C1_2", function() grid(d, "L2", SAFE, "CountryIncomeLevel", INCOME))
finding(report, "X1_08", function() pct(d[d$CountryIncomeLevel == 3, ], "L2", 1))

# Gallup World Poll WP89: good (1) or bad (2) time to find a job in your area.
high_income_by_job_market <- function() {
  g <- merge_gallup(d[d$CountryIncomeLevel == 4, ], "WP89")
  pct(g, "L2", 2, by = "WP89")
}
finding(report, "X1_09", function() high_income_by_job_market()[["2"]])
finding(report, "X1_10", function() high_income_by_job_market()[["1"]])

upper_middle <- d[d$CountryIncomeLevel == 3, ]
finding(report, "X1_11", function() {
  100 * sum(upper_middle$PROJWT[upper_middle$COUNTRY_ISO3 == "CHN"]) / sum(upper_middle$PROJWT)
})
finding(report, "X1_12", function() length(unique(upper_middle$COUNTRY_ISO3)))
finding(report, "X1_13", function() pct(upper_middle[upper_middle$COUNTRY_ISO3 != "CHN", ], "L2", 1))
finding(report, "C1_3", function() grid(d, "L2", SAFE, "GlobalRegion", REGION))
finding(report, "X1_14", function() pct(d[d$GlobalRegion == 8, ], "L2", 1))
finding(report, "X1_15", function() {
  region <- d[d$GlobalRegion == 4, ]
  100 * sum(region$PROJWT[region$COUNTRY_ISO3 == "ZAF"]) / sum(region$PROJWT)
})

less_safe_country <- by_country(d, "L2", 2)
finding(report, "X1_16", function() less_safe_country[c("ZAF", "NAM", "BWA", "LSO", "SWZ")])
finding(report, "C1_4", function() world_map(less_safe_country))

safety_table <- function(countries) {
  tab <- distribution(d, "L2", by = "COUNTRY_ISO3")
  out <- numeric(0)
  for (iso in countries) for (name in names(SAFE)) out[paste(iso, name, sep = "_")] <- tab[iso, as.character(SAFE[[name]])]
  out
}
finding(report, "T1_1", function() safety_table(c("LBN", "HKG", "AFG", "VEN")))

# Gallup World Poll WP113: feel safe walking alone at night (1 = yes); WP112: confidence
# in the local police (1 = yes, 2 = no); WP31: standard of living getting better (1) or worse (2).
finding(report, "X1_17", function() by_country(merge_gallup(d, "WP113"), "WP113", 1)[["AFG"]])
finding(report, "X1_18", function() ranked(by_country(merge_gallup(d, "WP113"), "WP113", 1), 1, lowest = TRUE)[[1]])
finding(report, "X1_19", function() by_country(merge_gallup(d, "WP112"), "WP112", 1)[["HKG"]])
finding(report, "T1_2", function() safety_table(c("RWA", "CHN", "LAO", "ARE", "ETH")))
finding(report, "X1_20", function() by_country(d, "L2", 1)[["ETH"]])
finding(report, "X1_21", function() by_country(merge_gallup(d, "WP31"), "WP31", 1)[["CHN"]])
finding(report, "X1_22", function() ranked(by_country(merge_gallup(d, "WP31"), "WP31", 1), 1)[[1]])
finding(report, "X1_23", function() pct(d, "L2", 2, by = "Gender")[["2"]])
finding(report, "X1_24", function() pct(d, "L2", 2, by = "Gender")[["1"]])
finding(report, "C1_5", function() {
  world <- keyed(pct(d, "L2", 2, by = "Gender"), SEX)
  names(world) <- paste0("world_", names(world))
  groups <- unlist(lapply(names(INCOME), function(i) setNames(paste(INCOME[[i]], SEX, sep = "_"), paste(i, names(SEX), sep = "_"))))
  c(world, keyed(pct(d, "L2", 2, by = c("CountryIncomeLevel", "Gender")), groups))
})

less_safe_by_sex <- by_country_sex(d, "L2", 2)
finding(report, "X1_25", function() {
  out <- numeric(0)
  for (iso in c("CHL", "USA", "JPN")) {
    out[paste0(iso, "_women")] <- less_safe_by_sex$women[[iso]]
    out[paste0(iso, "_men")] <- less_safe_by_sex$men[[iso]]
  }
  out
})
finding(report, "X1_26", function() {
  high <- unique(d$COUNTRY_ISO3[d$CountryIncomeLevel == 4])
  gap <- less_safe_by_sex$women[high] - less_safe_by_sex$men[high]
  ranked(gap, 1)[[1]]
})
us_less_safe_no_police_confidence <- function(sex) {
  g <- merge_gallup(d[d$COUNTRY_ISO3 == "USA" & d$Gender == sex, ], "WP112")
  pct(g[g$WP112 %in% 2, ], "L2", 2)
}
finding(report, "X1_27", function() us_less_safe_no_police_confidence(2))
finding(report, "X1_28", function() us_less_safe_no_police_confidence(1))
finding(report, "C1_6", function() {
  g <- merge_gallup(d, c("WP31", "WP112"))
  c(grid(g, "L2", SAFE, "WP31", c("1" = "living_better", "2" = "living_worse")),
    grid(g, "L2", SAFE, "WP112", c("1" = "police_yes", "2" = "police_no")))
})

safety_scale_country <- wmean(d, "safety_scale", by = "COUNTRY_ISO3")
finding(report, "X1_29", function() correlation(safety_scale_country, world_bank("NY.GDP.PCAP.CD", year = 2018))[["r"]])
finding(report, "X1_30", function() correlation(safety_scale_country, world_bank("NY.GDP.MKTP.KD.ZG", year = 2018))[["r"]])
finding(report, "X1_31", function() pct(d, "L1", 2))
finding(report, "X1_32", function() pct(d, "L1", 1))
finding(report, "X1_33", function() pct(d, "L1", 3))
finding(report, "X1_34", function() pct(d, "L1", c(4, DK)))
finding(report, "C1_7", function() grid(d, "L1", RISK, "GlobalRegion", REGION))

opportunity_country <- by_country(d, "L1", 1)
# Countries where the rounded % seeing risk as opportunity is 33 or more.
at_least_one_in_three <- names(opportunity_country)[round(opportunity_country) >= 33]
finding(report, "X1_35", function() length(at_least_one_in_three))
finding(report, "X1_36", function() {
  income <- tapply(d$CountryIncomeLevel, d$COUNTRY_ISO3, function(x) x[1])
  sum(income[at_least_one_in_three] %in% c(3, 4))
})
finding(report, "X1_37", function() opportunity_country[c("ARE", "BHR", "KWT", "SAU", "DEU", "SVN", "AUT", "USA")])

# Language of interview (Chart 1.8) is a Gallup World Poll field that is not in the public
# data; GWP_INTERVIEW_LANGUAGE is a placeholder name holding the language (e.g. "Spanish").
LANGUAGES <- c(English = "english", Russian = "russian", Chinese = "chinese", Arabic = "arabic",
               French = "french", Spanish = "spanish")
finding(report, "X1_38", function() {
  g <- merge_gallup(d, "GWP_INTERVIEW_LANGUAGE")
  pct(g[g$GWP_INTERVIEW_LANGUAGE %in% "Spanish", ], "L1", 1)
})
finding(report, "X1_39", function() pct(d[d$GlobalRegion == 5, ], "L1", 1))
finding(report, "X1_40", function() opportunity_country[["ESP"]])
finding(report, "C1_8", function() {
  g <- merge_gallup(d, "GWP_INTERVIEW_LANGUAGE")
  grid(g, "L1", RISK, "GWP_INTERVIEW_LANGUAGE", LANGUAGES)
})
finding(report, "X1_41", function() pct(d, "L1", 1, by = "Gender")[["1"]])
finding(report, "X1_42", function() pct(d, "L1", 1, by = "Gender")[["2"]])
finding(report, "C1_9", function() {
  world <- keyed(pct(d, "L1", 1, by = "CountryIncomeLevel"), INCOME)
  names(world) <- paste0("world_", names(world))
  groups <- unlist(lapply(names(INCOME), function(i) setNames(paste(SEX, INCOME[[i]], sep = "_"), paste(i, names(SEX), sep = "_"))))
  c(world, keyed(pct(d, "L1", 1, by = c("CountryIncomeLevel", "Gender")), groups))
})

opportunity_by_sex <- by_country_sex(d, "L1", 1)
finding(report, "X1_43", function() {
  iso <- names(opportunity_by_sex$men)
  sum(round(opportunity_by_sex$men[iso]) - round(opportunity_by_sex$women[iso]) > 10)
})
finding(report, "X1_44", function() {
  out <- numeric(0)
  for (iso in c("BHR", "AUT", "JPN", "USA")) {
    out[paste0(iso, "_women")] <- opportunity_by_sex$women[[iso]]
    out[paste0(iso, "_men")] <- opportunity_by_sex$men[[iso]]
  }
  out
})
finding(report, "X1_45", function() pct(d, "L1", 1, by = "Education")[["3"]])
finding(report, "X1_46", function() pct(d, "L1", 1, by = "Education")[["1"]])
finding(report, "X1_47", function() pct(d, "L1", 1, by = "IncomeFeelings")[["1"]])
finding(report, "X1_48", function() pct(d, "L1", 1, by = "IncomeFeelings")[["4"]])

EDUCATION <- c("1" = "educ_0_8", "2" = "educ_9_15", "3" = "educ_16plus")
INCOME_FEELINGS <- c("1" = "comfortable", "2" = "getting_by", "3" = "difficult", "4" = "very_difficult")
finding(report, "C1_10", function() {
  c(grid(d, "L1", RISK, "Education", EDUCATION), grid(d, "L1", RISK, "IncomeFeelings", INCOME_FEELINGS))
})

# --- Chapter 2: The sources of greatest risk in people's lives ------------------------------

t2_country <- lapply(setNames(names(TOP2_GROUPS), names(TOP2_GROUPS)), function(n) by_country(d, paste0("t2_", n), 1))

finding(report, "X2_01", function() sum(t2_country$health > 40))
finding(report, "X2_02", function() pct(d, "L3_A", 19))
finding(report, "X2_03", function() pct(d, "second_response", 19))
finding(report, "X2_04", function() pct(d, "L3_A", 19))
finding(report, "X2_05", function() pct(d, "L3_A", DK))
finding(report, "X2_06", function() pct(d, "L3_A", 1))
finding(report, "X2_07", function() pct(d, "L3_A", 3))
finding(report, "X2_08", function() pct(d, "L3_A", 9))
finding(report, "X2_09", function() pct(d, "second_response", c(0, 19, DK)))
finding(report, "X2_10", function() pct(d, "second_response", 1))
finding(report, "X2_11", function() pct(d, "second_response", 3))
finding(report, "X2_12", function() pct(d, "second_response", 9))
finding(report, "X2_13", function() mentions(d, 1))
finding(report, "X2_14", function() mentions(d, 3))
finding(report, "X2_15", function() mentions(d, 9))
finding(report, "X2_16", function() mentions(d, 5))
finding(report, "X2_17", function() mentions(d, 6))

TOP2_CODES <- c( # Chart 2.1 categories (L3_A / L3_B codes)
  none = 19, road = 1, crime = 3, health = 9, other = 18, economy = 6, financial = 5, climate = 16,
  cooking = 4, other_transport = 2, work = 14, politics = 7, food = 12, drugs = 10, pollution = 13,
  mental = 15, water = 11, internet = 8, drowning = 17
)
finding(report, "C2_1", function() sapply(TOP2_CODES, function(code) mentions(d, code)))
finding(report, "X2_18", function() pct(d[d$CountryIncomeLevel == 1, ], "t2_financial", 1))

CHART_2_2 <- c("road", "health", "crime", "financial", "environment", "food_water", "political")
finding(report, "C2_2", function() {
  out <- numeric(0)
  for (name in CHART_2_2) {
    v <- keyed(pct(d, paste0("t2_", name), 1, by = "GlobalRegion"), REGION)
    out[paste(names(v), name, sep = "_")] <- v
  }
  out
})
finding(report, "X2_19", function() population(d$t2_road == 1))
finding(report, "C2_3", function() t2_country$road)
finding(report, "X2_20", function() sum(t2_country$road > 50))
finding(report, "X2_21", function() t2_country$road[c("RWA", "MDG")])
finding(report, "X2_22", function() t2_country$road[["AUS"]])
finding(report, "C2_4", function() {
  ages <- c("1" = "15_29", "2" = "30_49", "3" = "50_64", "4" = "65plus")
  groups <- unlist(lapply(names(SEX), function(s) setNames(paste(SEX[[s]], ages, sep = "_"), paste(s, names(ages), sep = "_"))))
  keyed(pct(d, "t2_road", 1, by = c("Gender", "AgeGroups4")), groups)
})
finding(report, "X2_23", function() {
  keyed(pct(d, "t2_road", 1, by = "IncomeFeelings"), c("1" = "comfortable", "3" = "difficult", "4" = "very_difficult"))
})
finding(report, "X2_24", function() keyed(pct(d, "t2_road", 1, by = "Education"), c("3" = "educ_16plus", "1" = "educ_0_8")))
finding(report, "X2_25", function() keyed(pct(d, "t2_road", 1, by = "Urbanicity2"), c("2" = "urban", "1" = "rural")))
finding(report, "X2_26", function() mentions(d, 3))
finding(report, "X2_27", function() t2_country$crime[["AFG"]])
finding(report, "X2_28", function() t2_country$crime[["BRA"]])
finding(report, "C2_5", function() world_map(t2_country$crime))
finding(report, "X2_29", function() {
  over <- names(t2_country$crime)[t2_country$crime >= 50]
  region <- tapply(d$GlobalRegion, d$COUNTRY_ISO3, function(x) x[1])
  c(n50 = length(over), latam = sum(region[over] == 5), latam_pct = pct(d[d$GlobalRegion == 5, ], "t2_crime", 1))
})
finding(report, "X2_30", function() t2_country$crime[["ZAF"]])
finding(report, "C2_6", function() {
  total <- keyed(pct(d, "t2_crime", 1, by = "GlobalRegion"), REGION)
  names(total) <- paste0(names(total), "_total")
  groups <- unlist(lapply(names(REGION), function(g) setNames(paste(REGION[[g]], SEX, sep = "_"), paste(g, names(SEX), sep = "_"))))
  c(total, keyed(pct(d, "t2_crime", 1, by = c("GlobalRegion", "Gender")), groups))
})
finding(report, "X2_31", function() keyed(pct(d[d$GlobalRegion == 15, ], "t2_crime", 1, by = "Gender"), SEX))
finding(report, "X2_32", function() {
  walk <- by_country_sex(merge_gallup(d, "WP113"), "WP113", 1)
  gap <- walk$men - walk$women[names(walk$men)]
  c(AUS_men = walk$men[["AUS"]], AUS_women = walk$women[["AUS"]], NZL_men = walk$men[["NZL"]],
    NZL_women = walk$women[["NZL"]], AUS_gap = gap[["AUS"]], NZL_gap = gap[["NZL"]], largest = ranked(gap, 1)[[1]])
})

GINI <- world_bank("SI.POV.GINI", latest_upto = 2018)
finding(report, "X2_33", function() correlation(t2_country$crime, GINI)[["r"]])
finding(report, "X2_34", function() correlation(t2_country$crime, GINI)[["n"]])
finding(report, "C2_7", function() {
  # No values are printed in the scatter plot; the labelled countries are returned for reference.
  labelled <- c("ZAF", "BRA", "NGA", "CHN", "MEX", "IND", "USA", "IDN", "GBR", "SVN")
  c(setNames(t2_country$crime[labelled], paste0(labelled, "_pct")), setNames(GINI[labelled], paste0(labelled, "_gini")))
})
finding(report, "C2_8", function() world_map(t2_country$health))
finding(report, "X2_35", function() keyed(pct(d, "t2_health", 1, by = "AgeGroups4"), c("4" = "65plus", "1" = "15_29")))
finding(report, "X2_36", function() keyed(pct(d, "t2_health", 1, by = "Gender"), SEX))
finding(report, "X2_37", function() correlation(t2_country$health, world_bank("SP.DYN.CDRT.IN", year = 2018))[["r"]])
finding(report, "C2_9", function() {
  # No values are printed in the scatter plot; the labelled countries are returned for reference.
  injury <- world_bank("SH.DTH.INJR.ZS", year = 2016)
  labelled <- c("IRQ", "LBY", "AFG", "BRA", "IND", "MEX", "NGA", "CHN", "MMR", "ZAF", "POL", "IDN", "USA", "SRB",
                "GBR", "BGR")
  c(setNames(t2_country$health[labelled], paste0(labelled, "_pct")),
    setNames(injury[labelled], paste0(labelled, "_injury")))
})
finding(report, "X2_38", function() mentions(d, c(5, 6)))
finding(report, "X2_39", function() t2_country$financial[["RWA"]])
finding(report, "X2_40", function() t2_country$financial[["LTU"]])
finding(report, "C2_10", function() t2_country$financial)
finding(report, "X2_41", function() mentions(d, c(13, 16)))
finding(report, "X2_42", function() t2_country$environment[["NPL"]])
finding(report, "C2_11", function() t2_country$environment)
finding(report, "X2_43", function() pct(d, "L5", 1))
finding(report, "X2_44", function() mentions(d, 16))
finding(report, "X2_45", function() mentions(d, 7))
finding(report, "X2_46", function() t2_country$political[c("LBN", "HKG")])
finding(report, "X2_47", function() sum(t2_country$political > 20))
finding(report, "C2_12", function() t2_country$political)
finding(report, "X2_48", function() t2_country$political[c("KOR", "BEL", "USA", "ESP", "CYP")])
finding(report, "X2_49", function() mentions(d, c(11, 12)))
finding(report, "X2_50", function() population(d$t2_food_water == 1))
finding(report, "X2_51", function() mentions(d, 11))
finding(report, "X2_52", function() mentions(d, 12))
finding(report, "C2_13", function() t2_country$food_water)
finding(report, "X2_53", function() t2_country$food_water[c("LUX", "FRA")])
finding(report, "X2_54", function() by_country(d, "L16A", 1)[["FRA"]])
finding(report, "X2_55", function() correlation(t2_country$food_water, world_bank("SH.H2O.BASW.ZS", year = 2017))[["r"]])
finding(report, "X2_56", function() correlation(t2_country$food_water, world_bank("EN.CLC.MDAT.ZS", latest_upto = 2019))[["r"]])
finding(report, "X2_57", function() pct(d, "L3_A", 19))
finding(report, "X2_58", function() pct(d, "second_response", 19))

no_risk_majority <- names(t2_country$none)[t2_country$none > 50]
fh_status <- function() with(freedom_house(), setNames(status, iso3))
finding(report, "X2_59", function() length(no_risk_majority))
finding(report, "X2_60", function() sum(fh_status()[no_risk_majority] %in% "NF"))
finding(report, "X2_61", function() sum(fh_status()[no_risk_majority] %in% "PF"))
finding(report, "C2_14", function() t2_country$none)
finding(report, "X2_62", function() keyed(pct(d, "t2_none", 1, by = "Education"), c("1" = "educ_0_8", "3" = "educ_16plus")))
finding(report, "X2_63", function() {
  correlation(t2_country$none, with(freedom_house(), setNames(total, iso3)))[["r"]]
})


# ==============================================================================
# Part 2: Chapters 3-5
# ==============================================================================

p2_SEX <- c("2" = "women", "1" = "men") # Gender: 1 = Male, 2 = Female
p2_DK <- c(98, 99)
p2_REGIONS <- c( # GlobalRegion codes
  "1" = "east_africa", "2" = "central_west_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "north_america", "7" = "central_asia", "8" = "east_asia", "9" = "southeast_asia",
  "10" = "south_asia", "11" = "middle_east", "12" = "east_europe", "13" = "northwest_europe",
  "14" = "south_europe", "15" = "aus_nz"
)
p2_INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # CountryIncomeLevel
p2_EDU <- c("1" = "edu_0_8", "2" = "edu_9_15", "3" = "edu_16plus") # Education (9 = DK/refused, not charted)
p2_LIKELY <- c(traffic = "L9A", attacked = "L9B", lightning = "L9E", drowning = "L9D", aeroplane = "L9C")
p2_WORRY <- c(food = "L6A", water = "L6B", crime = "L6C", weather = "L6D", power = "L6E",
              appliances = "L6F", mental = "L6G")
p2_HARM <- c(food = "L8A", water = "L8B", crime = "L8C", weather = "L8D", power = "L8E",
             appliances = "L8F", mental = "L8G")
p2_SOURCES <- c(family = "L13A", labels = "L13F", medical = "L13B", news = "L13C", authority = "L13E",
                internet = "L13D", famous = "L13G", religious = "L13H")
p2_TRUST_CODES <- c(family = 1, medical = 2, news = 3, internet = 4, authority = 5, labels = 6,
                    famous = 7, religious = 8) # L14 codes
p2_BAG <- c(neighbour = "L17A", stranger = "L17B", police = "L17C")
p2_OCC <- c(business_owner = 1, vendor = 2, professional = 3, manager = 4, clerical = 5, service = 6,
            construction = 7, farmer = 8, other = 97, dk = 98, refused = 99) # EMP8B codes
p2_RISK_AT_WORK <- c(machinery = "L20A", fire = "L20B", chemicals = "L20C", violence = "L20D", trips = "L20E")
p2_HARM_AT_WORK <- c(machinery = "L21A", fire = "L21B", chemicals = "L21C", violence = "L21D", trips = "L21E")

d <- add_columns(d, unname(c(
  "WPID_RANDOM", "PROJWT", "WGT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "REG_GLOBAL", "Gender",
  "Education", "AgeGroups4", "IncomeFeelings", "worry_index_published", "experience_index_published",
  "L10", "L12", "L14", "L15", "L19", "L22", "L23", "L25", "EMP8B",
  p2_LIKELY, p2_WORRY, p2_HARM, p2_SOURCES, p2_BAG, p2_RISK_AT_WORK, p2_HARM_AT_WORK
)))

# --- Derived variables ---------------------------------------------------------

# Chapter 3. The Worry Index and Experience of Harm Index are published on a
# 0-100 scale; the data holds them on 0-1.
d$p2_worry_100 <- 100 * d$worry_index_published
d$p2_experience_100 <- 100 * d$experience_index_published
# Numeracy (L12): 3 = correct; "incorrect" in the lightning comparison (page 58)
# groups wrong answers with don't know, as the report does on page 53.
d$p2_numeracy <- ifelse(d$L12 %in% 3, 1, ifelse(!is.na(d$L12), 2, NA))
# Likelihood ratings (L9A-E, 0-10): don't know / refused (98, 99) set to missing
# for averages; the Chart 3.3 percentages keep them in the base.
for (p2_v in p2_LIKELY) d[[paste0("p2_", p2_v, "_score")]] <- ifelse(d[[p2_v]] <= 10, d[[p2_v]], NA)
d$p2_likely_mean <- rowMeans(d[paste0("p2_", p2_LIKELY, "_score")], na.rm = TRUE)
d$p2_likely_mean[is.nan(d$p2_likely_mean)] <- NA

# Chapter 4. Social trust score (page 77): very likely = 3, somewhat likely = 2,
# not likely at all = 1, averaged over the three lost-bag questions; respondents
# must answer all three (the police question was not asked in three countries,
# which leaves the 139 countries of footnote 17).
p2_bag <- as.data.frame(lapply(d[p2_BAG], function(x) ifelse(x <= 3, 4 - x, NA)))
d$p2_social_trust <- rowMeans(p2_bag)

# Seat belt laws: WHO Global status report on road safety 2018, Table A7 (see
# README). Countries not in the WHO table count as having no law in Chart 4.6.
# The WHO table is not redistributed here (see reports/external/README.md), so
# the law columns are added to `d` the first time a finding needs them.
p2_add_seatbelt_laws <- function() {
  if ("p2_national_law" %in% names(d)) return(invisible(TRUE))
  p2_who <- read.csv(external_path("core_world_risk_poll_2019__who_seatbelt_laws.csv"), stringsAsFactors = FALSE)
  p2_m <- match(d$COUNTRY_ISO3, p2_who$iso3)
  d$p2_national_law <<- p2_who$national_law[p2_m]
  d$p2_all_occupants <<- p2_who$all_occupants[p2_m]
  d$p2_seatbelt_law <<- ifelse(d$p2_national_law %in% "No", 1, # Chart 4.8: 1 none, 2 partial, 3 full
                        ifelse(d$p2_all_occupants %in% "No", 2, ifelse(d$p2_all_occupants %in% "Yes", 3, NA)))
  invisible(TRUE)
}

# Chapter 5. Workers: employed full or part time, the respondents asked the
# work questions (L19-L21; L22-L25 only of those who work for an employer).
p2_w <- d[!is.na(d$L19), ]
p2_w$n_harm_types <- rowSums(p2_w[p2_HARM_AT_WORK] == 1, na.rm = TRUE) # 0-5 types of harm at work
p2_w$three_plus <- ifelse(p2_w$n_harm_types >= 3, 1, 2)
p2_w$any_risk <- ifelse(rowSums(p2_w[p2_RISK_AT_WORK] == 1, na.rm = TRUE) > 0, 1, 2)
p2_w$low_income <- ifelse(p2_w$CountryIncomeLevel %in% 1, 1, 2)

# --- Helpers -------------------------------------------------------------------

# Rename a vector named by codes to readable keys, dropping unmapped codes.
p2_keyed <- function(values, mapping) {
  keep <- names(values) %in% names(mapping)
  setNames(unname(values[keep]), mapping[names(values)[keep]])
}

# % with `var` in `codes` for each group of `by`, keyed by `mapping`.
p2_pct_by <- function(df, var, codes, by, mapping, exclude = NULL) {
  p2_keyed(pct(df, var, codes, by = by, exclude = exclude), mapping)
}

p2_region_pct <- function(df, var, codes, exclude = NULL) p2_pct_by(df, var, codes, "GlobalRegion", p2_REGIONS, exclude)

# Chart 4.1 / 4.6 layout: c(world = %, low = %, ...).
p2_with_world <- function(df, var, codes) c(world = pct(df, var, codes), p2_pct_by(df, var, codes, "CountryIncomeLevel", p2_INCOME))

p2_sorted_keys <- function(keys) paste(sort(keys, method = "radix"), collapse = ", ")

# Named vector from a list of c(key = value) pieces.
p2_c <- function(...) unlist(list(...))

# =============================================================================
# Chapter 3: The risk perception gap
# =============================================================================

finding(report, "X3_01", function() pct(d, "L12", 3))
finding(report, "X3_02", function() pct(d, "L12", c(1, 2)))
finding(report, "X3_03", function() pct(d, "L12", 98))
finding(report, "X3_04", function() pct(d[d$Education %in% 3, ], "L12", c(1, 2)))
finding(report, "X3_05", function() pct(d[d$Education %in% 3, ], "L12", p2_DK))
finding(report, "X3_06", function() p2_pct_by(d, "L12", 3, "Gender", p2_SEX))

finding(report, "C3_1", function() {
  r <- pct(d, "L12", 3, by = c("Gender", "Education"))
  out <- numeric(0)
  for (s in names(p2_SEX)) for (e in names(p2_EDU)) out[paste(p2_SEX[[s]], p2_EDU[[e]], sep = "_")] <- r[[paste(s, e, sep = "_")]]
  out
})

finding(report, "X3_07", function() p2_region_pct(d, "L12", 3)[c("aus_nz", "north_america", "northwest_europe", "latin_america", "south_asia")])
finding(report, "X3_08", function() p2_region_pct(d, "L12", 3)[c("east_africa", "central_west_africa", "southern_africa")])

finding(report, "X3_09", function() {
  bigger <- p2_region_pct(d, "L12", 1)
  smaller <- p2_region_pct(d, "L12", 2)
  p2_sorted_keys(names(bigger)[bigger <= smaller[names(bigger)]])
})

finding(report, "C3_2", function() {
  tab <- distribution(d, "L12", by = "GlobalRegion")
  cats <- list(same = 3, bigger = 1, smaller = 2, dk = p2_DK)
  out <- numeric(0)
  for (code in names(p2_REGIONS)) for (cat in names(cats)) {
    cols <- intersect(as.character(cats[[cat]]), colnames(tab))
    out[paste(p2_REGIONS[[code]], cat, sep = "_")] <- sum(tab[code, cols])
  }
  out
})

finding(report, "X3_10", function() sapply(p2_LIKELY, function(v) wmean(d, paste0("p2_", v, "_score"))))

finding(report, "C3_3", function() {
  cats <- list(r0 = 0, r1_4 = 1:4, r5 = 5, r6_9 = 6:9, r10 = 10)
  out <- numeric(0)
  for (risk in names(p2_LIKELY)) {
    v <- p2_LIKELY[[risk]]
    for (cat in names(cats)) out[paste(risk, cat, sep = "_")] <- pct(d, v, cats[[cat]])
    out[paste(risk, "mean", sep = "_")] <- wmean(d, paste0("p2_", v, "_score"))
  }
  out
})

finding(report, "X3_11", function() {
  r <- wmean(d, "p2_L9E_score", by = "p2_numeracy")
  c(correct = r[["1"]], incorrect = r[["2"]])
})

finding(report, "C3_4", function() {
  out <- numeric(0)
  for (risk in names(p2_LIKELY)) {
    v <- paste0("p2_", p2_LIKELY[[risk]], "_score")
    out[paste("world", risk, sep = "_")] <- wmean(d, v)
    r <- p2_keyed(wmean(d, v, by = "GlobalRegion"), p2_REGIONS)
    out[paste(names(r), risk, sep = "_")] <- r
  }
  out
})

# Between-country share of the variance (eta squared, %) of each person's mean
# likelihood rating, weighted with the within-country weight WGT.
finding(report, "X3_12", function() {
  g <- d[!is.na(d$p2_likely_mean), ]
  grand <- wmean(g, "p2_likely_mean", weight = "WGT")
  fitted <- wmean(g, "p2_likely_mean", weight = "WGT", by = "COUNTRY_ISO3")[g$COUNTRY_ISO3]
  100 * sum(g$WGT * (fitted - grand)^2) / sum(g$WGT * (g$p2_likely_mean - grand)^2)
})

finding(report, "X3_13", function() sapply(p2_WORRY, function(v) pct(d, v, 1)))

finding(report, "C3_5", function() {
  out <- numeric(0)
  for (risk in names(p2_WORRY)) {
    worried <- pct(d, p2_WORRY[[risk]], 1)
    experienced <- pct(d, p2_HARM[[risk]], 1)
    out[paste0(risk, c("_worried", "_experienced", "_gap"))] <- c(worried, experienced, worried - experienced)
  }
  out
})

finding(report, "X3_14", function() wmean(d, "p2_worry_100"))
finding(report, "X3_15", function() wmean(d, "p2_experience_100"))

p2_worry_region <- function() p2_keyed(wmean(d, "p2_worry_100", by = "GlobalRegion"), p2_REGIONS)
p2_experience_region <- function() p2_keyed(wmean(d, "p2_experience_100", by = "GlobalRegion"), p2_REGIONS)

finding(report, "X3_16", function() {
  worry <- p2_worry_region()
  experience <- p2_experience_region()
  c(southern_africa_worry = worry[["southern_africa"]], latin_america_worry = worry[["latin_america"]],
    southern_africa_experience = experience[["southern_africa"]])
})

finding(report, "C3_6", function() {
  worry <- p2_worry_region()
  experience <- p2_experience_region()
  out <- numeric(0)
  for (region in p2_REGIONS) {
    out[paste0(region, c("_worry", "_experience", "_gap"))] <- c(worry[[region]], experience[[region]],
                                                                 worry[[region]] - experience[[region]])
  }
  out
})

p2_country_indices <- function() {
  worry <- wmean(d, "p2_worry_100", by = "COUNTRY_ISO3")
  data.frame(worry = worry, experience = wmean(d, "p2_experience_100", by = "COUNTRY_ISO3")[names(worry)],
             row.names = names(worry))
}

# Scatter chart with country labels only: no published values to compare.
finding(report, "C3_7", function() {
  c <- p2_country_indices()
  c(setNames(c$worry, paste0(rownames(c), "_worry")), setNames(c$experience, paste0(rownames(c), "_experience")))
})

finding(report, "X3_17", function() {
  c <- p2_country_indices()
  mean(c$worry - c$experience)
})
finding(report, "X3_18", function() {
  c <- p2_country_indices()
  rownames(c)[which.min(c$worry)]
})
finding(report, "X3_19", function() {
  c <- p2_country_indices()["SWE", ]
  c(worry = c$worry, experience = c$experience, gap = c$worry - c$experience)
})

finding(report, "X3_20", function() {
  worry <- p2_keyed(wmean(d, "p2_worry_100", by = "Gender"), p2_SEX)
  experience <- p2_keyed(wmean(d, "p2_experience_100", by = "Gender"), p2_SEX)
  c(worry_women = worry[["women"]], worry_men = worry[["men"]],
    experience_men = experience[["men"]], experience_women = experience[["women"]])
})

finding(report, "X3_21", function() {
  r <- wmean(d, "p2_worry_100", by = c("GlobalRegion", "Gender"))
  regions <- c("6" = "north_america", "15" = "aus_nz", "14" = "south_europe", "4" = "southern_africa", "5" = "latin_america")
  out <- numeric(0)
  for (code in names(regions)) for (s in names(p2_SEX)) {
    out[paste(regions[[code]], p2_SEX[[s]], sep = "_")] <- r[[paste(code, s, sep = "_")]]
  }
  out
})

finding(report, "X3_22", function() {
  r <- wmean(d, "p2_worry_100", by = "IncomeFeelings")
  c(comfortable = r[["1"]], very_difficult = r[["4"]])
})

# =============================================================================
# Chapter 4: Influencing understanding of risk
# =============================================================================

finding(report, "X4_01", function() pct(d, "L10", 1))
finding(report, "X4_02", function() pct(d, "L15", 1))
finding(report, "X4_03", function() sapply(p2_SOURCES, function(v) pct(d, v, 1)))

finding(report, "C4_1", function() {
  out <- numeric(0)
  for (src in names(p2_SOURCES)) {
    r <- p2_with_world(d, p2_SOURCES[[src]], 1)
    out[paste(src, names(r), sep = "_")] <- r
  }
  out
})

finding(report, "X4_04", function() {
  low <- d[d$CountryIncomeLevel %in% 1, ]
  c(famous = pct(low, "L13G", 1), religious = pct(low, "L13H", 1))
})

finding(report, "X4_05", function() {
  p2_region_pct(d, "L13G", 1)[c("east_africa", "central_west_africa", "southern_africa", "south_asia", "southeast_asia")]
})

# Gallup World Poll item WP119 "Is religion an important part of your daily
# life?" (1 = yes, 2 = no); not in the public release.
p2_religion_important <- function() merge_gallup(d, "WP119")
finding(report, "X4_06", function() {
  g <- p2_religion_important()
  pct(g[g$GlobalRegion %in% 1, ], "WP119", 1)
})
finding(report, "X4_07", function() {
  g <- p2_religion_important()
  pct(g[g$REG_GLOBAL %in% 1, ], "WP119", 1) # REG_GLOBAL 1 = European Union
})

finding(report, "C4_2", function() {
  out <- numeric(0)
  for (src in names(p2_SOURCES)) {
    r <- p2_region_pct(d, p2_SOURCES[[src]], 1)
    out[paste(names(r), src, sep = "_")] <- r
  }
  out
})

finding(report, "X4_08", function() {
  srcs <- c("family", "medical", "authority", "famous", "religious")
  sapply(setNames(srcs, srcs), function(s) pct(d, "L14", p2_TRUST_CODES[[s]]))
})

finding(report, "C4_3", function() {
  out <- numeric(0)
  for (src in names(p2_SOURCES)) {
    out[paste0(src, "_use")] <- pct(d, p2_SOURCES[[src]], 1)
    out[paste0(src, "_trust")] <- pct(d, "L14", p2_TRUST_CODES[[src]])
  }
  out
})

finding(report, "C4_4", function() {
  groups <- list(world = d, women = d[d$Gender %in% 2, ], men = d[d$Gender %in% 1, ],
                 edu_0_8 = d[d$Education %in% 1, ], edu_9_15 = d[d$Education %in% 2, ], edu_16plus = d[d$Education %in% 3, ])
  out <- numeric(0)
  for (grp in names(groups)) for (src in c("family", "medical", "authority")) {
    out[paste(grp, src, sep = "_")] <- pct(groups[[grp]], "L14", p2_TRUST_CODES[[src]])
  }
  out
})

finding(report, "X4_09", function() sapply(p2_BAG, function(v) pct(d, v, 1)))
finding(report, "X4_10", function() {
  high <- d[d$CountryIncomeLevel %in% 4, ]
  c(police = pct(high, "L17C", 1), neighbour = pct(high, "L17A", 1))
})

p2_social_trust_by_country <- function() {
  st <- wmean(d, "p2_social_trust", by = "COUNTRY_ISO3")
  ta <- pct(d, "L14", 5, by = "COUNTRY_ISO3")
  keep <- intersect(names(st), names(ta))
  c <- data.frame(social_trust = st[keep], trust_authority = ta[keep], row.names = keep)
  c[complete.cases(c), ]
}

# Scatter chart with country labels only: no published values to compare.
finding(report, "C4_5", function() {
  c <- p2_social_trust_by_country()
  c(setNames(c$social_trust, paste0(rownames(c), "_social_trust")),
    setNames(c$trust_authority, paste0(rownames(c), "_trust_authority")))
})
finding(report, "X4_11", function() {
  c <- p2_social_trust_by_country()
  cor(c$social_trust, c$trust_authority)
})
finding(report, "X4_12", function() nrow(p2_social_trust_by_country()))
finding(report, "X4_13", function() length(unique(d$COUNTRY_ISO3)))

p2_no_law_countries <- function() {
  p2_add_seatbelt_laws()
  pct(d[d$p2_national_law %in% "No", ], "L10", 1, by = "COUNTRY_ISO3")
}
finding(report, "X4_14", function() length(p2_no_law_countries()))
finding(report, "X4_15", function() {
  r <- p2_no_law_countries()
  p2_sorted_keys(names(r)[r > 50])
})
finding(report, "X4_16", function() {
  r <- p2_no_law_countries()
  p2_sorted_keys(names(r)[r < 50])
})
finding(report, "X4_17", function() pct(d, "L10", 2))

finding(report, "C4_6", function() {
  p2_add_seatbelt_laws()
  countries <- d[!duplicated(d$COUNTRY_ISO3), ]
  has_law <- 100 * (countries$p2_national_law %in% "Yes")
  law <- c(world = mean(has_law), p2_keyed(tapply(has_law, countries$CountryIncomeLevel, mean), p2_INCOME))
  wear <- p2_with_world(d, "L10", 1)
  c(setNames(wear, paste0("wear_", names(wear))), setNames(law, paste0("law_", names(law))))
})

finding(report, "X4_18", function() p2_pct_by(d, "L10", 1, "Education", p2_EDU)[c("edu_0_8", "edu_16plus")])

finding(report, "C4_7", function() {
  out <- numeric(0)
  for (code in names(p2_INCOME)) {
    sub <- d[d$CountryIncomeLevel %in% as.numeric(code), ]
    r <- c(p2_pct_by(sub, "L10", 1, "Gender", p2_SEX), p2_pct_by(sub, "L10", 1, "Education", p2_EDU))
    out[paste(p2_INCOME[[code]], names(r), sep = "_")] <- r
  }
  out
})

# Average of the country percentages in each law group (the text: "an average
# of 58% of people"); countries not in the WHO table are left out.
p2_seatbelt_by_law <- function() {
  p2_add_seatbelt_laws()
  country <- pct(d, "L10", 1, by = "COUNTRY_ISO3")
  first <- d[!duplicated(d$COUNTRY_ISO3), ]
  group <- setNames(first$p2_seatbelt_law, first$COUNTRY_ISO3)[names(country)]
  p2_keyed(tapply(country, group, mean), c("1" = "none", "2" = "partial", "3" = "full"))
}
finding(report, "X4_19", p2_seatbelt_by_law)
finding(report, "C4_8", p2_seatbelt_by_law)

finding(report, "X4_20", function() {
  r <- p2_region_pct(d, "L15", 1)
  c(south_europe = r[["south_europe"]], south_asia = r[["south_asia"]], IND = pct(d[d$COUNTRY_ISO3 %in% "IND", ], "L15", 1))
})
finding(report, "X4_21", function() {
  r <- p2_region_pct(d, "L15", 1)
  names(r)[which.min(r)]
})

# =============================================================================
# Chapter 5: Risk at work
# =============================================================================

p2_occupation_shares <- function() p2_keyed(distribution(p2_w, "EMP8B"), setNames(names(p2_OCC), p2_OCC))
finding(report, "X5_01", function() p2_occupation_shares()[c("farmer", "vendor", "manager")])
finding(report, "C5_1", function() p2_occupation_shares()[names(p2_OCC)])

finding(report, "X5_02", function() pct(p2_w, "L19", 1))
finding(report, "X5_03", function() sum(p2_w$PROJWT[p2_w$L19 %in% 1]))

p2_injured_by_occupation <- function(df = p2_w) p2_pct_by(df, "L19", 1, "EMP8B", setNames(names(p2_OCC), p2_OCC))
finding(report, "X5_04", function() p2_injured_by_occupation()[["farmer"]])
finding(report, "X5_05", function() p2_injured_by_occupation()[["construction"]])

p2_violence_risk_by_country <- function() pct(p2_w, "L20D", 1, by = "COUNTRY_ISO3")
finding(report, "X5_06", function() p2_violence_risk_by_country()[["FRA"]])
finding(report, "X5_07", function() p2_region_pct(p2_w, "L20D", 1)[c("northwest_europe", "aus_nz")])

finding(report, "X5_08", function() {
  r <- pct(p2_w, "L8G", 1, by = "L19")
  c(injured = r[["1"]], not_injured = r[["2"]])
})
finding(report, "X5_09", function() pct(d, "L22", 1))
finding(report, "X5_10", function() {
  r <- pct(p2_w, "L19", 1, by = "L25")
  c(difficult = r[["2"]], good = r[["1"]])
})
finding(report, "X5_11", function() p2_pct_by(p2_w, "L25", 1, "Education", p2_EDU)[c("edu_16plus", "edu_0_8")])
finding(report, "X5_12", function() p2_pct_by(p2_w, "L19", 1, "CountryIncomeLevel", p2_INCOME)[c("low", "high")])

p2_injured_by_country <- function() pct(p2_w, "L19", 1, by = "COUNTRY_ISO3")

# Every country's value (the map), plus the legend ends: the lowest and highest
# country values.
finding(report, "C5_2", function() {
  r <- p2_injured_by_country()
  c(r, legend_min = min(r), legend_max = max(r))
})
finding(report, "T5_1", function() {
  r <- p2_injured_by_country()
  sort(r[r > 50], decreasing = TRUE)
})
finding(report, "X5_13", function() sum(p2_injured_by_country() > 50))
finding(report, "X5_14", function() p2_injured_by_country()[["SLE"]])

finding(report, "C5_3", function() {
  p2_injured_by_occupation()[c("farmer", "construction", "business_owner", "vendor", "service", "professional",
                               "manager", "clerical")]
})

finding(report, "C5_4", function() {
  r <- pct(p2_w, "L19", 1, by = c("GlobalRegion", "EMP8B"))
  out <- numeric(0)
  for (code in names(p2_REGIONS)) {
    cc <- r[[paste(code, 7, sep = "_")]]
    f <- r[[paste(code, 8, sep = "_")]]
    out[paste0(p2_REGIONS[[code]], c("_construction", "_farmer", "_gap"))] <- c(cc, f, abs(cc - f))
  }
  out
})

finding(report, "X5_15", function() p2_pct_by(p2_w, "L19", 1, "Gender", p2_SEX))

finding(report, "C5_5", function() {
  out <- numeric(0)
  for (s in names(p2_SEX)) {
    r <- p2_injured_by_occupation(p2_w[p2_w$Gender %in% as.numeric(s), ])
    occ <- c("business_owner", "vendor", "professional", "manager", "clerical", "service", "construction", "farmer")
    out[paste(p2_SEX[[s]], occ, sep = "_")] <- r[occ]
  }
  out
})

finding(report, "X5_16", function() p2_pct_by(p2_w[p2_w$GlobalRegion %in% 10, ], "L19", 1, "Gender", p2_SEX))
# The text describes these as the shares of men and women "who work in the
# region's large agricultural sector"; they are the injury rates among
# Southern Asia's agricultural workers (see README).
finding(report, "X5_17", function() {
  farmers <- p2_w[p2_w$GlobalRegion %in% 10 & p2_w$EMP8B %in% 8, ]
  p2_pct_by(farmers, "L19", 1, "Gender", p2_SEX)
})
finding(report, "X5_18", function() p2_pct_by(p2_w[p2_w$COUNTRY_ISO3 %in% "LKA", ], "L19", 1, "Gender", p2_SEX))
finding(report, "X5_19", function() p2_pct_by(p2_w, "L19", 1, "Education", p2_EDU)[c("edu_16plus", "edu_0_8")])

finding(report, "C5_6", function() {
  r <- pct(p2_w, "L19", 1, by = c("Gender", "Education"))
  out <- numeric(0)
  for (s in names(p2_SEX)) for (e in names(p2_EDU)) out[paste(p2_SEX[[s]], p2_EDU[[e]], sep = "_")] <- r[[paste(s, e, sep = "_")]]
  out
})

finding(report, "X5_20", function() sapply(p2_RISK_AT_WORK, function(v) pct(p2_w, v, 1)))
finding(report, "X5_21", function() {
  r <- pct(p2_w, "any_risk", 1, by = "low_income")
  c(low = r[["1"]], not_low = r[["2"]])
})
finding(report, "X5_22", function() pct(p2_w[p2_w$COUNTRY_ISO3 %in% "BGD", ], "L20B", 1))

# Value of every risk (excluding trips and falls) in each region, and the top
# one(s): the risks whose rounded value equals the rounded maximum.
finding(report, "C5_7", function() {
  risks <- p2_RISK_AT_WORK[names(p2_RISK_AT_WORK) != "trips"]
  t <- sapply(risks, function(v) p2_region_pct(p2_w, v, 1))
  vals <- numeric(0)
  tops <- character(0)
  for (region in rownames(t)) {
    vals[paste(region, colnames(t), sep = "_")] <- t[region, ]
    rounded <- round(t[region, ])
    tops[paste0("top_", region)] <- paste(sort(colnames(t)[rounded == max(rounded)], method = "radix"), collapse = " / ")
  }
  c(vals, tops)
})

finding(report, "X5_23", function() p2_region_pct(p2_w, "L20D", 1)[c("northwest_europe", "aus_nz")])
finding(report, "X5_24", function() p2_pct_by(p2_w[p2_w$COUNTRY_ISO3 %in% "FRA", ], "L20D", 1, "Gender", p2_SEX))

finding(report, "C5_8", function() {
  countries <- c("FRA", "AUS", "FIN", "BEL", "NZL", "SWE", "GBR", "NLD", "IRL", "LUX", "DNK", "NOR", "DEU", "CHE",
                 "AUT", "LTU", "LVA", "EST")
  r <- pct(p2_w, "L20D", 1, by = c("COUNTRY_ISO3", "Gender"))
  allr <- p2_violence_risk_by_country()
  out <- numeric(0)
  for (cc in countries) {
    out[paste0(cc, c("_all", "_women", "_men"))] <- c(allr[[cc]], r[[paste(cc, 2, sep = "_")]], r[[paste(cc, 1, sep = "_")]])
  }
  out
})

finding(report, "X5_25", function() p2_pct_by(p2_w, "L20D", 1, "Gender", p2_SEX))
finding(report, "X5_26", function() {
  r <- pct(p2_w, "L20D", 1, by = c("CountryIncomeLevel", "Gender"))
  c(low_men = r[["1_1"]], low_women = r[["1_2"]], high_women = r[["4_2"]], high_men = r[["4_1"]])
})

finding(report, "C5_9", function() {
  out <- numeric(0)
  for (risk in names(p2_RISK_AT_WORK)) {
    r <- pct(p2_w, p2_RISK_AT_WORK[[risk]], 1, by = c("Gender", "CountryIncomeLevel"))
    for (s in names(p2_SEX)) for (i in names(p2_INCOME)) {
      out[paste(p2_SEX[[s]], p2_INCOME[[i]], risk, sep = "_")] <- r[[paste(s, i, sep = "_")]]
    }
  }
  out
})

finding(report, "C5_10", function() sapply(p2_HARM_AT_WORK, function(v) pct(p2_w, v, 1)))
finding(report, "X5_27", function() pct(p2_w, "L21E", 1))
finding(report, "X5_28", function() p2_pct_by(p2_w, "three_plus", 1, "CountryIncomeLevel", p2_INCOME)[c("low", "high")])
finding(report, "X5_29", function() {
  out <- numeric(0)
  for (k in c("machinery", "fire", "violence")) {
    r <- p2_pct_by(p2_w, p2_HARM_AT_WORK[[k]], 1, "Gender", p2_SEX)
    out[paste0(k, c("_men", "_women"))] <- c(r[["men"]], r[["women"]])
  }
  out
})
finding(report, "X5_30", function() pct(p2_w, "L21D", 1))
finding(report, "X5_31", function() {
  p2_region_pct(p2_w, "L21D", 1)[c("aus_nz", "southern_africa", "central_west_africa", "east_africa", "north_america")]
})
finding(report, "X5_32", function() {
  r <- p2_region_pct(p2_w, "L21D", 1)
  p2_sorted_keys(names(r)[r < 5])
})
finding(report, "C5_11", function() p2_region_pct(p2_w, "L21D", 1))

p2_harm_violence_women_by_country <- function() sort(pct(p2_w[p2_w$Gender %in% 2, ], "L21D", 1, by = "COUNTRY_ISO3"), decreasing = TRUE)
finding(report, "X5_33", function() {
  r <- pct(p2_w, "L21D", 1, by = c("COUNTRY_ISO3", "Gender"))
  c(ZMB_women = r[["ZMB_2"]], AUS_women = r[["AUS_2"]], AUS_men = r[["AUS_1"]])
})
finding(report, "X5_34", function() names(p2_harm_violence_women_by_country())[1])
finding(report, "X5_35", function() match("AUS", names(p2_harm_violence_women_by_country())))

finding(report, "C5_12", function() {
  out <- numeric(0)
  for (k in names(p2_HARM_AT_WORK)) {
    r <- pct(p2_w, p2_HARM_AT_WORK[[k]], 1, by = "AgeGroups4")
    out[paste0(k, c("_age_15_29", "_age_50_64"))] <- c(r[["1"]], r[["3"]])
  }
  out
})

finding(report, "X5_36", function() {
  r <- pct(p2_w, "L8G", 1, by = "n_harm_types")
  c(none = r[["0"]], all_five = r[["5"]])
})
finding(report, "C5_13", function() {
  out <- numeric(0)
  for (k in c("violence", "chemicals", "fire", "machinery")) {
    r <- pct(p2_w, "L8G", 1, by = p2_HARM_AT_WORK[[k]])
    out[paste0(k, c("_yes", "_no"))] <- c(r[["1"]], r[["2"]])
  }
  out
})
finding(report, "X5_37", function() pct(p2_w[p2_w$L21D %in% 1, ], "L8G", 1))

p2_free_to_report_by_country <- function() pct(d, "L22", 1, by = "COUNTRY_ISO3")
finding(report, "X5_38", function() p2_free_to_report_by_country()[c("SEN", "PAK")])
finding(report, "X5_39", function() sum(p2_free_to_report_by_country() < 60))
finding(report, "X5_40", function() {
  r <- p2_region_pct(d, "L22", 1)
  if (any(r < 60)) p2_sorted_keys(names(r)[r < 60]) else "none"
})

# Scatter against the UL Safety Index, with country labels only: no published
# values to compare. Returns the poll side of the chart.
finding(report, "C5_14", p2_free_to_report_by_country)

# Needs the UL Safety Index (safety frameworks), discontinued in April 2020 and
# no longer published. Put it in reports/external/downloaded/ as
# core_world_risk_poll_2019__ul_safety_index.csv (iso3, ul_safety_index); without
# it the finding is reported as EXTERNAL_ONLY.
finding(report, "X5_41", function() {
  ul <- read.csv(external_path("core_world_risk_poll_2019__ul_safety_index.csv"), stringsAsFactors = FALSE)
  r <- p2_free_to_report_by_country()
  keep <- intersect(names(r), ul$iso3[!is.na(ul$ul_safety_index)])
  cor(r[keep], ul$ul_safety_index[match(keep, ul$iso3)])
})

p2_free_to_report_and_gdp <- function() {
  wb <- read.csv(external_path("core_world_risk_poll_2019__worldbank_gdp.csv"),
                 stringsAsFactors = FALSE)
  wb <- wb[wb$indicator == "NY.GDP.PCAP.PP.CD" & wb$year == 2019, ]
  r <- p2_free_to_report_by_country()
  keep <- intersect(names(r), wb$iso3[!is.na(wb$value)])
  data.frame(report = r[keep], log_gdp = log(wb$value[match(keep, wb$iso3)]))
}
finding(report, "X5_42", function() {
  c <- p2_free_to_report_and_gdp()
  cor(c$report, c$log_gdp)
})
finding(report, "X5_43", function() nrow(p2_free_to_report_and_gdp()))

finding(report, "X5_44", function() {
  r <- pct(d, "L22", 1, by = "IncomeFeelings")
  c(comfortable = r[["1"]], difficult = pct(d[d$IncomeFeelings %in% c(3, 4), ], "L22", 1))
})
finding(report, "X5_45", function() {
  r <- distribution(d, "L23")
  c(employer = r[["1"]], government = r[["3"]], union = r[["2"]], nobody = r[["4"]])
})
finding(report, "X5_46", function() pct(d, "L25", 1))
finding(report, "C5_15", function() {
  r <- pct(d, "L25", 1, by = c("Education", "Gender"))
  alle <- pct(d, "L25", 1, by = "Education")
  out <- numeric(0)
  for (e in names(p2_EDU)) {
    out[paste0(p2_EDU[[e]], c("_all", "_women", "_men"))] <- c(alle[[e]], r[[paste(e, 2, sep = "_")]], r[[paste(e, 1, sep = "_")]])
  }
  out
})

# Employee engagement (Chart 5.16 and the text around it) is Gallup's measure,
# asked in the 2019 Gallup World Poll in 108 countries; it is not in the public
# release. GWP_EMPLOYEE_ENGAGEMENT is a placeholder name: 1 = engaged,
# 2 = not engaged, 3 = actively disengaged (see README).
p2_ENGAGEMENT <- "GWP_EMPLOYEE_ENGAGEMENT"
p2_engagement <- function() merge_gallup(d, p2_ENGAGEMENT)

finding(report, "X5_47", function() {
  g <- p2_engagement()
  pct(g[!is.na(g$L22), ], p2_ENGAGEMENT, 1)
})
finding(report, "X5_48", function() {
  r <- pct(p2_engagement(), "L22", 1, by = p2_ENGAGEMENT)
  c(engaged = r[["1"]], disengaged = r[["3"]])
})
finding(report, "X5_49", function() {
  g <- p2_engagement()
  good <- pct(g, "L25", 1, by = p2_ENGAGEMENT)
  difficult <- pct(g, "L25", 2, by = p2_ENGAGEMENT)
  c(engaged_good = good[["1"]], engaged_difficult = difficult[["1"]],
    disengaged_good = good[["3"]], disengaged_difficult = difficult[["3"]])
})
finding(report, "X5_50", function() {
  g <- p2_engagement()
  length(unique(g$COUNTRY_ISO3[!is.na(g[[p2_ENGAGEMENT]])]))
})
finding(report, "C5_16", function() {
  r <- pct(p2_engagement(), "L22", 1, by = c("CountryIncomeLevel", p2_ENGAGEMENT))
  out <- numeric(0)
  for (i in names(p2_INCOME)) {
    out[paste0(p2_INCOME[[i]], c("_engaged", "_disengaged"))] <- c(r[[paste(i, 1, sep = "_")]], r[[paste(i, 3, sep = "_")]])
  }
  out
})


# ==============================================================================
# Part 3: Chapters 6-10 and Appendix 3
# ==============================================================================

p3_DK <- c(98, 99)

# GlobalRegion codes -> keys used in finding ids, and the labels the charts use.
p3_REGIONS <- c(
  "1" = "east_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia",
  "9" = "southeastern_asia", "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
)
p3_REGION_LABELS <- c(
  east_africa = "Eastern Africa", central_western_africa = "Central/Western Africa",
  northern_africa = "Northern Africa", southern_africa = "Southern Africa",
  latin_america = "Latin America & Caribbean", northern_america = "Northern America",
  central_asia = "Central Asia", eastern_asia = "Eastern Asia", southeastern_asia = "Southeastern Asia",
  southern_asia = "Southern Asia", middle_east = "Middle East", eastern_europe = "Eastern Europe",
  northern_western_europe = "Northern/Western Europe", southern_europe = "Southern Europe",
  australia_nz = "Australia & New Zealand"
)
p3_INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = not classified
p3_EDU <- c("1" = "edu_0_8", "2" = "edu_9_15", "3" = "edu_16plus") # 9 = DK/refused
p3_AGE <- c("1" = "age_15_29", "2" = "age_30_49", "3" = "age_50_64", "4" = "age_65plus") # AgeGroups4
p3_SEX <- c("2" = "women", "1" = "men") # Gender

# WHO sub-regions (Appendix 3), for the countries in the 2019 poll. Hong Kong,
# Kosovo, Palestine and Taiwan are not WHO member states and are not listed.
p3_WHO_SUBREGIONS <- c(
  afr_d = "DZA BEN BFA CMR TCD GAB GMB GHA GIN LBR MDG MLI MRT MUS NER NGA SEN SLE TGO",
  afr_e = "BWA COG CIV ETH KEN LSO MWI MOZ NAM RWA ZAF SWZ UGA TZA ZMB ZWE",
  amr_a = "CAN USA",
  amr_b = "ARG BRA CHL COL CRI DOM SLV HND JAM MEX PAN PRY URY VEN",
  amr_d = "BOL ECU GTM NIC PER",
  emr_b = "BHR CYP IRN JOR KWT LBN LBY SAU TUN ARE",
  emr_d = "AFG EGY IRQ MAR PAK YEM",
  eur_a = "AUT BEL HRV DNK FIN FRA DEU GRC IRL ISR ITA LUX MLT NLD NOR PRT SVN ESP SWE CHE GBR",
  eur_b = "ALB ARM AZE BIH BGR GEO KGZ MNE POL ROU SRB SVK TJK MKD TUR TKM UZB",
  eur_c = "BLR EST HUN KAZ LVA LTU MDA RUS UKR",
  sear_b = "IDN LKA THA",
  sear_d = "BGD IND MMR NPL",
  wpr_a = "AUS JPN NZL SGP",
  wpr_b = "KHM CHN LAO MYS MNG PHL KOR VNM"
)
p3_WHO_OF <- unlist(lapply(names(p3_WHO_SUBREGIONS), function(s) {
  isos <- strsplit(p3_WHO_SUBREGIONS[[s]], " ")[[1]]
  setNames(rep(s, length(isos)), isos)
}))

p3_WORK_INJURY <- c("L21A", "L21B", "L21C", "L21D", "L21E") # injury or harm while working, past two years

d <- add_columns(d, c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
  "Gender", "Age", "AgeGroups4", "Education", "IncomeFeelings", "REGION2_USA",
  "L2", "L3_A", "L3_B", "L4A", "L4B", "L4C", "L5", "L6A", "L6B", "L7A", "L7B", "L8A", "L8B", "L8D",
  "L12", "L14", "L16A", "L16B", "L16C", "L26", "L27A", "L27B", "L27C", p3_WORK_INJURY,
  "worry_index_published", "experience_index_published"
))

# --- Derived variables -----------------------------------------------------------

p3_map <- function(x, map) unname(map[as.character(x)])
p3_paste <- function(a, b) ifelse(is.na(a) | is.na(b), NA, paste(a, b, sep = "_"))

# Group keys as strings, so that one helper serves every breakdown.
d$p3_region <- p3_map(d$GlobalRegion, p3_REGIONS)
d$p3_income <- p3_map(d$CountryIncomeLevel, p3_INCOME)
d$p3_edu <- p3_map(d$Education, p3_EDU)
d$p3_age <- p3_map(d$AgeGroups4, p3_AGE)
d$p3_sex <- p3_map(d$Gender, p3_SEX)
d$p3_sex_age <- p3_paste(d$p3_sex, d$p3_age)
d$p3_sex_edu <- p3_paste(d$p3_sex, d$p3_edu)
# Middle income (Chapter 8): lower-middle and upper-middle combined.
d$p3_income3 <- p3_map(d$CountryIncomeLevel, c("1" = "low", "2" = "middle", "3" = "middle", "4" = "high"))
# WHO sub-region (Chart 9.1) and WHO region (sub-regions combined).
d$p3_who_sub <- p3_map(d$COUNTRY_ISO3, p3_WHO_OF)
d$p3_who <- sub("_.*$", "", d$p3_who_sub)

# Numeracy (L12): correct = "10% is the same as 1 out of 10" (code 3); anything
# else, including don't know, is "not correct". Missing where not asked.
d$p3_numeracy <- ifelse(is.na(d$L12), NA, ifelse(d$L12 == 3, 1, 2))
d$p3_numeracy_key <- p3_map(d$p3_numeracy, c("1" = "correct", "2" = "not_correct"))
d$p3_income_numeracy <- p3_paste(d$p3_income, d$p3_numeracy_key)
d$p3_region_numeracy <- p3_paste(d$p3_region, d$p3_numeracy_key)
d$p3_region_sex <- p3_paste(d$p3_region, d$p3_sex)

# U.S. regions (Chart 6.7): REGION2_USA 1 Northeast, 2 Midwest, 3 South, 4 West.
d$p3_us_region <- p3_map(d$REGION2_USA, c("1" = "north_midwest", "2" = "north_midwest", "3" = "south", "4" = "west"))

# Experience of harm from severe weather (Chart 6.8): yes / no; DK and refused are left out.
d$p3_severe_weather <- p3_map(d$L8D, c("1" = "yes", "2" = "no"))

# Food or water among the two biggest risks named (L3_A, L3_B): 11 = water, 12 = food.
d$p3_foodwater_top2 <- ifelse(d$L3_A %in% c(11, 12) | d$L3_B %in% c(11, 12), 1, 2)

# Harm from food or water, and from both, in the past two years.
d$p3_harm_either <- ifelse(d$L8A %in% 1 | d$L8B %in% 1, 1, 2)
d$p3_harm_both <- ifelse(d$L8A %in% 1 & d$L8B %in% 1, 1, 2)

# Government Safety Performance Index (Chapter 9): yes = 1, any other answer
# (no, DK, refused) = 0, averaged over food, water and power lines, x 100.
# Not asked in Saudi Arabia and Turkmenistan.
d$p3_gspi <- ifelse(is.na(d$L16A), NA, 100 * ((d$L16A %in% 1) + (d$L16B %in% 1) + (d$L16C %in% 1)) / 3)

# Work injury (Chapter 10): yes to any of L21A-L21E, among those asked (workers).
d$p3_work_injury <- ifelse(is.na(d$L21A), NA, ifelse(rowSums(d[p3_WORK_INJURY] == 1, na.rm = TRUE) > 0, 1, 2))

# Risk gap (Chapter 10): Worry Index minus Experience Index for each person.
d$p3_risk_gap <- d$worry_index_published - d$experience_index_published

# --- Helpers -------------------------------------------------------------------

# % in each named category of `var` (list(name = codes)), overall or for each
# `by` group: c(name = %) or c("<group>_<name>" = %).
p3_share <- function(df, var, cats, by = NULL) {
  tab <- distribution(df, var, by = by)
  pick <- function(x, codes) sum(x[intersect(as.character(codes), names(x))])
  if (is.null(by)) return(sapply(cats, function(codes) pick(tab, codes)))
  out <- numeric(0)
  for (g in setdiff(rownames(tab), "NA")) { # "NA" = rows with no group
    for (name in names(cats)) out[paste(g, name, sep = "_")] <- pick(tab[g, ], cats[[name]])
  }
  out
}

# % with `var` in `codes` for each `by` group: c(group = %).
p3_pct_by <- function(df, var, codes, by) pct(df, var, codes, by = by)

# % by country (ISO3 names) plus the minimum and maximum across countries (map legends).
p3_country_map <- function(var, codes, df = d) {
  r <- pct(df, var, codes, by = "COUNTRY_ISO3")
  r <- r[!is.na(r)]
  c(r, min = min(r), max = max(r))
}

# Round half up to whole numbers (as the charts print), the same in Python and R.
p3_round <- function(x) floor(x + 0.5)

# Region keys -> labels, in alphabetical (C-locale) order, joined with "; ".
p3_labels <- function(keys) paste(sort(unname(p3_REGION_LABELS[keys]), method = "radix"), collapse = "; ")

p3_country_names <- function(isos) {
  paste(sort(d$Country[match(isos, d$COUNTRY_ISO3)], method = "radix"), collapse = "; ")
}

# Adult population represented (sum of PROJWT) by the rows in `mask`.
p3_adults <- function(mask) sum(d$PROJWT[mask])

p3_country <- function(iso) d[d$COUNTRY_ISO3 %in% iso, ]
p3_prefix <- function(v, prefix) setNames(v, paste(prefix, names(v), sep = "_"))
p3_suffix <- function(v, suffix) setNames(v, paste(names(v), suffix, sep = "_"))

p3_L5 <- list(very = 1, somewhat = 2, not = 3, dk = p3_DK)
p3_L5_3 <- list(very = 1, somewhat = 2, not = 3)
p3_HELP_HARM <- list(help = 1, harm = 2)
p3_HELP_HARM_NONE <- list(help = 1, harm = 2, none = c(3, 4, p3_DK))

# =================================================================================
# Chapter 6: Climate change risk
# =================================================================================

finding(report, "X6_01", function() pct(d, "L5", 1))
finding(report, "X6_02", function() pct(d, "L5", 2))
finding(report, "X6_03", function() pct(d, "L5", 3))
finding(report, "X6_04", function() pct(p3_country("CHN"), "L5", 1))
finding(report, "X6_05", function() pct(p3_country("USA"), "L5", 3))
finding(report, "X6_06", function() pct(d, "L5", p3_DK))
finding(report, "X6_07", function() p3_adults(d$L5 %in% p3_DK))
finding(report, "C6_1", function() p3_share(d, "L5", p3_L5))
finding(report, "C6_2", function() p3_share(d, "L5", list(very = 1, somewhat = 2), by = "p3_region"))
finding(report, "X6_08", function() min(p3_pct_by(d, "L5", c(1, 2), by = "p3_region")))
finding(report, "X6_09", function() p3_pct_by(d, "L5", 1, by = "p3_region")[["southern_europe"]])
finding(report, "X6_10", function() p3_pct_by(d, "L5", 1, by = "p3_region")[["latin_america"]])
finding(report, "X6_11", function() p3_pct_by(d, "L5", 1, by = "p3_edu")[["edu_16plus"]])
finding(report, "X6_12", function() p3_pct_by(d, "L5", 1, by = "p3_edu")[["edu_0_8"]])
finding(report, "C6_3", function() {
  c(p3_prefix(p3_share(d, "L5", p3_L5_3), "global"),
    p3_share(d, "L5", p3_L5_3, by = "p3_edu"), p3_share(d, "L5", p3_L5_3, by = "p3_age"))
})
finding(report, "C6_4", function() p3_pct_by(d, "L5", 1, by = "p3_region_numeracy"))
finding(report, "X6_13", function() p3_pct_by(d, "L5", 1, by = "p3_income")[["high"]])
finding(report, "X6_14", function() p3_pct_by(d, "L5", 1, by = "p3_income")[["low"]])
finding(report, "X6_15", function() p3_pct_by(d, "L5", 1, by = "p3_income")[c("lower_middle", "upper_middle")])
finding(report, "C6_5", function() p3_pct_by(d, "L5", 1, by = "p3_region_sex"))
finding(report, "X6_16", function() {
  r <- p3_pct_by(d[d$p3_region %in% "middle_east", ], "L5", 1, by = "p3_sex")
  r[["women"]] - r[["men"]]
})
finding(report, "X6_17", function() {
  p3_pct_by(d, "L5", 3, by = "p3_region")[c("east_africa", "northern_america", "central_asia", "northern_africa", "southern_asia")]
})
finding(report, "C6_6", function() p3_pct_by(d, "L5", 3, by = "p3_region"))
finding(report, "X6_18", function() pct(p3_country("ETH"), "L5", 3))
finding(report, "X6_19", function() pct(p3_country("ETH"), "Education", 1))
finding(report, "X6_20", function() pct(p3_country("FIN"), "L5", 3))
finding(report, "X6_21", function() pct(d, "L5", p3_DK, by = "COUNTRY_ISO3")[c("LAO", "NPL", "KHM")])
finding(report, "X6_22", function() pct(p3_country("CHN"), "L5", 2))
finding(report, "X6_23", function() pct(p3_country("CHN"), "L5", 3))
finding(report, "X6_24", function() pct(p3_country("CHN"), "L5", p3_DK))
finding(report, "X6_25", function() pct(p3_country("IND"), "L5", 3))
finding(report, "X6_26", function() pct(p3_country("IND"), "L5", 1))
# Population-weighted share (see README): the unweighted mean of country shares is 36%.
finding(report, "X6_27", function() pct(d, "Education", 1))
finding(report, "X6_28", function() length(unique(d$COUNTRY_ISO3)))

p3_us <- function(keys) {
  us <- p3_country("USA")
  us[us$p3_us_region %in% keys, ]
}
finding(report, "X6_29", function() pct(p3_us("south"), "L5", 1))
finding(report, "X6_30", function() pct(p3_us(c("north_midwest", "west")), "L5", 1))
finding(report, "X6_31", function() pct(p3_us("south"), "L8D", 1))
finding(report, "X6_32", function() pct(p3_us(c("north_midwest", "west")), "L8D", 1))
finding(report, "C6_7", function() {
  us <- p3_country("USA")
  c(p3_share(us, "L5", p3_L5_3, by = "p3_us_region"),
    p3_suffix(p3_pct_by(us, "L8D", 1, by = "p3_us_region"), "experienced"))
})
finding(report, "X6_33", function() p3_pct_by(d, "L5", 1, by = "p3_severe_weather")[["yes"]])
finding(report, "X6_34", function() p3_pct_by(d, "L5", 1, by = "p3_severe_weather")[["no"]])
finding(report, "C6_8", function() p3_share(d, "L5", p3_L5, by = "p3_severe_weather"))
finding(report, "X6_35", function() pct(d, "L5", p3_DK))

# Chart 6.9: average predicted probabilities by education from two logistic
# models. The report used a multilevel logistic regression with Gallup World
# Poll items (satisfaction with air and water quality, religion). This version
# uses country fixed effects (see README). Needs the Gallup items.
p3_climate_model <- local({
  cache <- NULL
  function() {
    if (!is.null(cache)) return(cache)
    g <- merge_gallup(d, c("WP93", "WP94", "WP1233"))
    g <- g[g$L5 %in% 1:3 & g$Education %in% 1:3 & g$IncomeFeelings %in% 1:4 & !is.na(g$AgeGroups4) &
      !is.na(g$p3_numeracy) & g$WP93 %in% 1:2 & g$WP94 %in% 1:2 & !is.na(g$WP1233), ]
    g$p3_w <- g$PROJWT / mean(g$PROJWT)
    g$p3_correct <- as.numeric(g$p3_numeracy == 1)
    g$p3_severe <- as.numeric(g$L8D %in% 1)
    g$p3_air_ok <- as.numeric(g$WP93 == 1)
    g$p3_water_ok <- as.numeric(g$WP94 == 1)
    rhs <- paste("factor(Education) + factor(Gender) + factor(AgeGroups4) + factor(IncomeFeelings) + p3_correct",
                 "+ p3_severe + p3_air_ok + p3_water_ok + factor(WP1233) + factor(COUNTRY_ISO3)")
    out <- numeric(0)
    for (outcome in c(very = 1, not = 3)) {
      g$p3_y <- as.numeric(g$L5 == outcome)
      fit <- glm(as.formula(paste("p3_y ~", rhs)), family = quasibinomial(), data = g, weights = p3_w)
      for (level in names(p3_EDU)) {
        p <- predict(fit, newdata = transform(g, Education = as.numeric(level)), type = "response")
        out[paste(p3_EDU[[level]], names(which(c(very = 1, not = 3) == outcome)), sep = "_")] <- 100 * weighted.mean(p, g$p3_w)
      }
    }
    cache <<- out
    out
  }
})
finding(report, "X6_36", function() p3_climate_model()[["edu_16plus_very"]])
finding(report, "C6_9", function() p3_climate_model())
finding(report, "C6_10", function() p3_share(d, "L5", p3_L5_3, by = "p3_sex_age"))
finding(report, "X6_37", function() {
  r <- pct(d[d$CountryIncomeLevel %in% 4, ], "L5", 3, by = "Country")
  names(which.max(r))
})

# =================================================================================
# Chapter 7: Technology-related risk perceptions
# =================================================================================

p3_high <- d[d$CountryIncomeLevel %in% 4, ] # high-income economies

finding(report, "X7_01", function() pct(d, "L4A", 2))
finding(report, "X7_02", function() pct(d, "L4A", 1))
finding(report, "X7_03", function() p3_pct_by(d, "L4A", 1, by = "p3_income")[["low"]])
finding(report, "X7_04", function() p3_pct_by(d, "L4A", 1, by = "p3_income")[["high"]])
finding(report, "X7_05", function() pct(d, "L4B", 1))
finding(report, "X7_06", function() pct(d, "L4B", 2))
finding(report, "X7_07", function() c(nuclear = pct(d, "L4B", 1), ai = pct(d, "L4C", 1)))
finding(report, "X7_08", function() c(nuclear = pct(d, "L4B", 2), ai = pct(d, "L4C", 2)))
finding(report, "C7_1", function() {
  c(p3_prefix(p3_share(d, "L4A", p3_HELP_HARM_NONE), "gm"),
    p3_prefix(p3_share(d, "L4B", p3_HELP_HARM_NONE), "nuclear"),
    p3_prefix(p3_share(d, "L4C", p3_HELP_HARM_NONE), "ai"))
})
finding(report, "C7_2", function() p3_share(d, "L4A", p3_HELP_HARM, by = "p3_region"))
# y-axis of the scatter; the x-axis (Food and Shelter Index) needs Gallup data (X7_09).
finding(report, "C7_3", function() pct(d, "L4A", 1, by = "COUNTRY_ISO3"))

# Country Food and Shelter Index vs % saying GM food will mostly help. Gallup's
# index from WP40 (not enough money for food) and WP43 (not enough money for
# shelter), 1 = yes, 2 = no: each person scores 100 x the share of the two
# items answered "no"; countries are the weighted mean.
p3_food_shelter_correlation <- function() {
  g <- merge_gallup(d, c("WP40", "WP43"))
  g <- g[g$WP40 %in% c(1, 2, p3_DK) & g$WP43 %in% c(1, 2, p3_DK), ]
  g$p3_fsi <- 100 * ((g$WP40 %in% 2) + (g$WP43 %in% 2)) / 2
  fsi <- wmean(g, "p3_fsi", by = "COUNTRY_ISO3")
  help <- pct(d, "L4A", 1, by = "COUNTRY_ISO3")
  common <- intersect(names(fsi), names(help))
  c(r = cor(fsi[common], help[common]), n = length(common))
}
finding(report, "X7_09", function() p3_food_shelter_correlation()[["r"]])
finding(report, "X7_10", function() p3_food_shelter_correlation()[["n"]])
finding(report, "X7_11", function() p3_pct_by(d, "L4A", 1, by = "p3_income")[["low"]])
finding(report, "X7_12", function() p3_pct_by(d, "L4A", 2, by = "p3_income")[["high"]])
finding(report, "X7_13", function() pct(p3_high, "L4A", 2, by = "L6A")[["1"]])
finding(report, "X7_14", function() pct(p3_high, "L4A", 2, by = "L6A")[["3"]])
finding(report, "X7_15", function() p3_pct_by(d, "L4B", 2, by = "p3_region")[["southern_europe"]])
finding(report, "X7_16", function() pct(p3_country("ESP"), "L4B", 2))
finding(report, "X7_17", function() p3_pct_by(d, "L4B", 1, by = "p3_income")[["low"]])
finding(report, "X7_18", function() p3_pct_by(d, "L4B", 2, by = "p3_income")[["low"]])
finding(report, "X7_19", function() p3_pct_by(d, "L4B", 1, by = "p3_income")[["high"]])
finding(report, "X7_20", function() p3_pct_by(d, "L4B", 2, by = "p3_income")[["high"]])
finding(report, "C7_4", function() p3_share(d, "L4B", p3_HELP_HARM, by = "p3_region"))
finding(report, "X7_21", function() p3_pct_by(p3_high, "L4B", 1, by = "p3_edu"))
finding(report, "C7_5", function() p3_share(p3_high, "L4B", p3_HELP_HARM, by = "p3_edu"))
finding(report, "C7_6", function() p3_pct_by(d, "L4B", 1, by = "p3_income_numeracy"))
finding(report, "X7_22", function() p3_pct_by(p3_high, "L4B", 2, by = "p3_sex")[["women"]])
finding(report, "X7_23", function() p3_pct_by(p3_high, "L4B", 1, by = "p3_sex")[["women"]])
finding(report, "X7_24", function() p3_pct_by(p3_high, "L4B", 1, by = "p3_sex")[["men"]])
finding(report, "X7_25", function() p3_pct_by(p3_high, "L4B", 2, by = "p3_sex")[["men"]])
finding(report, "C7_7", function() p3_share(p3_high, "L4B", p3_HELP_HARM, by = "p3_sex_edu"))
finding(report, "X7_26", function() p3_pct_by(d, "L4C", 1, by = "p3_region")[["eastern_asia"]])
finding(report, "X7_27", function() p3_pct_by(d, "L4C", 2, by = "p3_region")[["eastern_asia"]])
finding(report, "X7_28", function() pct(p3_country("CHN"), "L4C", 2))
finding(report, "X7_29", function() names(which.min(pct(d, "L4C", 2, by = "Country"))))
finding(report, "X7_30", function() p3_pct_by(d, "L4C", 2, by = "p3_region")[["southern_europe"]])
finding(report, "X7_31", function() p3_pct_by(d, "L4C", 2, by = "p3_region")[["latin_america"]])
finding(report, "X7_32", function() p3_pct_by(d, "L4C", 2, by = "p3_region")[["northern_america"]])
finding(report, "C7_8", function() p3_share(d, "L4C", p3_HELP_HARM, by = "p3_region"))
# y-axis of the scatter; the x-axis is the Wellcome Global Monitor 2018 Trust in
# Scientists Index (external, not used: the chart prints no values).
finding(report, "C7_9", function() pct(d, "L4C", 2, by = "COUNTRY_ISO3"))
finding(report, "X7_33", function() p3_pct_by(d, "L4C", 1, by = "p3_income")[["high"]])
finding(report, "X7_34", function() p3_pct_by(d, "L4C", 1, by = "p3_income")[["low"]])
finding(report, "X7_35", function() {
  r <- sort(p3_pct_by(d, "L4C", 2, by = "p3_region"), decreasing = TRUE)
  p3_labels(names(r)[1:3])
})
finding(report, "X7_36", function() {
  unname(p3_REGION_LABELS[names(which.max(p3_pct_by(d, "L4C", 1, by = "p3_region")))])
})
finding(report, "C7_10", function() p3_share(d, "L4C", p3_HELP_HARM_NONE, by = "p3_sex_age"))

# =================================================================================
# Chapter 8: Internet-related risk perceptions
# L27A-C were asked only of internet users (L26 = 1); pct() drops the others.
# =================================================================================

finding(report, "X8_01", function() pct(d, "L27B", 1))
finding(report, "X8_02", function() pct(d, "L27C", 1))
finding(report, "X8_03", function() pct(d, "L27A", 1))
finding(report, "X8_04", function() p3_pct_by(d, "L27A", 1, by = "p3_sex")[["women"]])
finding(report, "X8_05", function() p3_pct_by(d, "L27A", 1, by = "p3_sex")[["men"]])
finding(report, "X8_06", function() p3_pct_by(d, "L27A", 1, by = "p3_age")[["age_15_29"]])
finding(report, "X8_07", function() p3_pct_by(d, "L27A", 1, by = "p3_age")[["age_65plus"]])
finding(report, "X8_08", function() pct(d, "L26", 1))
finding(report, "X8_09", function() p3_pct_by(d, "L26", 1, by = "p3_region")[["northern_america"]])
finding(report, "X8_10", function() p3_pct_by(d, "L26", 1, by = "p3_region")[["east_africa"]])
finding(report, "X8_11", function() p3_pct_by(d, "L26", 1, by = "p3_region")[["southern_asia"]])
finding(report, "C8_1", function() p3_country_map("L26", 1))

finding(report, "C8_2", function() {
  r <- c(p3_pct_by(d, "L26", 1, by = c("p3_sex", "p3_age")), p3_pct_by(d, "L26", 1, by = c("p3_sex", "p3_edu")))
  r[as.vector(t(outer(c("women", "men"), c(p3_AGE, p3_EDU), paste, sep = "_")))]
})
finding(report, "X8_12", function() sum(table(d$COUNTRY_ISO3[!is.na(d$L27A)]) < 100))
finding(report, "C8_3", function() {
  cats <- list(yes = 1, no = 2, dk = p3_DK)
  c(p3_prefix(p3_share(d, "L27A", cats), "bullying"), p3_prefix(p3_share(d, "L27B", cats), "false_info"),
    p3_prefix(p3_share(d, "L27C", cats), "fraud"))
})
finding(report, "C8_4", function() p3_country_map("L27B", 1))

# Country % of internet users worried about false information vs the World Bank
# GINI index (SI.POV.GINI): each country's latest estimate from 2018 or earlier,
# the latest available when the report retrieved it (May 2020).
p3_gini_correlation <- function() {
  gini <- read.csv(external_path("core_world_risk_poll_2019__worldbank_SI.POV.GINI.csv"))
  gini <- gini[gini$year <= 2018 & !is.na(gini$value), ]
  gini <- gini[order(gini$iso3, -gini$year), ]
  gini <- gini[!duplicated(gini$iso3), ]
  gini <- setNames(gini$value, gini$iso3)
  worry <- pct(d, "L27B", 1, by = "COUNTRY_ISO3")
  common <- intersect(names(worry), names(gini))
  c(r = cor(worry[common], gini[common]), n = length(common))
}
finding(report, "X8_13", function() p3_gini_correlation()[["r"]])
finding(report, "X8_14", function() p3_gini_correlation()[["n"]])
finding(report, "C8_5", function() {
  c(p3_prefix(p3_pct_by(d, "L27B", 1, by = "p3_age"), "false_info"),
    p3_prefix(p3_pct_by(d, "L27C", 1, by = "p3_age"), "fraud"),
    p3_prefix(p3_pct_by(d, "L27A", 1, by = "p3_age"), "bullying"))
})
finding(report, "X8_15", function() min(p3_pct_by(d, "L27B", 1, by = "p3_age")))
finding(report, "X8_16", function() p3_pct_by(d, "L27A", 1, by = "p3_income3")[["low"]])
finding(report, "X8_17", function() p3_pct_by(d, "L27A", 1, by = "p3_income3")[["middle"]])
finding(report, "X8_18", function() p3_pct_by(d, "L27A", 1, by = "p3_income3")[["high"]])
# Scatter with no printed values: % worried about online bullying and mean age
# of internet users, by country.
finding(report, "C8_6", function() {
  users <- d[!is.na(d$L27A), ]
  c(p3_suffix(pct(users, "L27A", 1, by = "COUNTRY_ISO3"), "bullying"),
    p3_suffix(wmean(users, "Age", by = "COUNTRY_ISO3"), "age"))
})
finding(report, "C8_7", function() {
  r <- c(p3_pct_by(d, "L27C", 1, by = c("p3_sex", "p3_edu")), p3_pct_by(d, "L27C", 1, by = c("p3_sex", "p3_age")))
  r[as.vector(t(outer(c("women", "men"), c(p3_EDU, p3_AGE), paste, sep = "_")))]
})
finding(report, "X8_19", function() pct(d, "L27C", 1, by = "COUNTRY_ISO3")[c("PRT", "FRA", "ESP", "GBR", "ITA")])
finding(report, "C8_8", function() p3_country_map("L27C", 1))

# =================================================================================
# Chapter 9: Food and water risk
# =================================================================================

finding(report, "X9_01", function() pct(d, "L8A", 1))
finding(report, "X9_02", function() pct(d, "L8B", 1))
finding(report, "X9_03", function() pct(d, "p3_foodwater_top2", 1))
finding(report, "X9_04", function() p3_pct_by(d, "L16A", 2, by = "p3_region")[["eastern_europe"]])
finding(report, "X9_05", function() pct(d[!is.na(d$L8A), ], "p3_harm_either", 1))
finding(report, "X9_06", function() p3_adults(d$L8A %in% 1))
finding(report, "X9_07", function() pct(d[!is.na(d$L8A), ], "p3_harm_both", 1))
finding(report, "X9_08", function() {
  r <- sort(p3_pct_by(d, "L8A", 1, by = "p3_who"), decreasing = TRUE)
  which(names(r) == "sear")
})
finding(report, "C9_1", function() p3_pct_by(d, "L8A", 1, by = "p3_who_sub"))
finding(report, "X9_09", function() pct(d, "L6A", c(1, 2)))
finding(report, "X9_10", function() pct(d, "L6B", c(1, 2)))
finding(report, "X9_11", function() pct(d, "L7A", c(1, 2)))
finding(report, "X9_12", function() pct(d, "L7B", c(1, 2)))
finding(report, "C9_2", function() {
  c(p3_suffix(p3_pct_by(d, "L6A", 1, by = "p3_income"), "food"),
    p3_suffix(p3_pct_by(d, "L6B", 1, by = "p3_income"), "water"))
})
finding(report, "C9_3", function() {
  c(p3_prefix(p3_suffix(p3_pct_by(d, "L7A", 1, by = "p3_income"), "likely"), "food"),
    p3_prefix(p3_suffix(p3_pct_by(d, "L8A", 1, by = "p3_income"), "experienced"), "food"),
    p3_prefix(p3_suffix(p3_pct_by(d, "L7B", 1, by = "p3_income"), "likely"), "water"),
    p3_prefix(p3_suffix(p3_pct_by(d, "L8B", 1, by = "p3_income"), "experienced"), "water"))
})

p3_food_worry <- function() p3_pct_by(d, "L6A", 1, by = "p3_region")
p3_food_harm <- function() p3_pct_by(d, "L8A", 1, by = "p3_region")[names(p3_food_worry())]
# X9_13 and X9_14 use the rounded chart values: unrounded, the gap is 4.9 points
# in Eastern Asia, 4.8 in the Middle East and 4.6 in Eastern Africa.
finding(report, "X9_13", function() {
  gap <- p3_round(p3_food_worry()) - p3_round(p3_food_harm())
  p3_labels(names(gap)[gap >= 5])
})
finding(report, "X9_14", function() {
  gap <- p3_round(p3_food_harm()) - p3_round(p3_food_worry())
  p3_labels(names(gap)[gap >= 5])
})
finding(report, "X9_15", function() unname(p3_REGION_LABELS[names(sort(p3_food_worry(), decreasing = TRUE))[1]]))
finding(report, "X9_16", function() unname(p3_REGION_LABELS[names(sort(p3_food_worry(), decreasing = TRUE))[2]]))
finding(report, "X9_17", function() p3_food_harm()[["east_africa"]] - p3_food_worry()[["east_africa"]])
finding(report, "X9_18", function() p3_food_harm()[["east_africa"]])
finding(report, "X9_19", function() p3_food_worry()[["east_africa"]])
finding(report, "C9_4", function() c(p3_suffix(p3_food_worry(), "worried"), p3_suffix(p3_food_harm(), "experienced")))
finding(report, "X9_20", function() pct(d, "L14", 1))
finding(report, "X9_21", function() pct(d, "L14", 2))
finding(report, "X9_22", function() pct(d, "L14", 5))
finding(report, "C9_5", function() {
  cats <- list(family = 1, medical = 2, agency = 5)
  c(p3_share(d, "L14", cats, by = "p3_edu"), p3_share(d, "L14", cats, by = "p3_sex_age"))
})
finding(report, "X9_23", function() pct(d, "L16B", 1))
finding(report, "X9_24", function() pct(d, "L16A", 1))
finding(report, "X9_25", function() p3_pct_by(d, "L16A", 2, by = "p3_region")[["northern_america"]])
finding(report, "X9_26", function() p3_pct_by(d, "L16A", 2, by = "p3_region")[["northern_western_europe"]])
finding(report, "X9_27", function() pct(p3_country("FRA"), "L16A", 2))
finding(report, "C9_6", function() p3_country_map("L16A", 2))

# Rows with the Gallup World Poll item WP139, confidence in the national
# government (1 = yes, 2 = no; DK and refused stay in the base).
p3_confidence_government <- function() merge_gallup(d, "WP139")
finding(report, "X9_28", function() {
  g <- p3_confidence_government()
  pct(g[g$COUNTRY_ISO3 %in% "FRA", ], "WP139", 1)
})
finding(report, "X9_29", function() p3_pct_by(d, "L16A", 2, by = "p3_region")[c("latin_america", "southern_europe", "middle_east")])
finding(report, "X9_30", function() p3_pct_by(d, "L16A", 1, by = "p3_region")[["eastern_europe"]])
finding(report, "X9_31", function() p3_pct_by(d[!is.na(d$L8A), ], "p3_harm_either", 1, by = "p3_region")[["eastern_europe"]])
finding(report, "X9_32", function() {
  g <- p3_confidence_government()
  median(pct(g[g$p3_region %in% "eastern_europe", ], "WP139", 1, by = "COUNTRY_ISO3"))
})
finding(report, "X9_33", function() {
  g <- p3_confidence_government()
  pct(g[g$p3_region %in% "eastern_europe", ], "L16A", 1, by = "WP139")[["1"]]
})
finding(report, "X9_34", function() {
  g <- p3_confidence_government()
  pct(g[g$p3_region %in% "eastern_europe", ], "L16A", 1, by = "WP139")[["2"]]
})
# Scatter with no printed values: y-axis (% government does a good job on food
# safety) for Eastern European countries and for regions. The x-axis is
# confidence in the national government (Gallup WP139).
finding(report, "C9_7", function() {
  c(pct(d[d$p3_region %in% "eastern_europe", ], "L16A", 1, by = "COUNTRY_ISO3"), p3_pct_by(d, "L16A", 1, by = "p3_region"))
})
finding(report, "X9_35", function() pct(d, "L16A", 1, by = "COUNTRY_ISO3")[c("UKR", "ROU")])
finding(report, "X9_36", function() p3_country_names(names(sort(pct(d, "L16A", 1, by = "COUNTRY_ISO3")))[1:2]))
finding(report, "X9_37", function() pct(p3_confidence_government(), "WP139", 1, by = "COUNTRY_ISO3")[c("UKR", "ROU")])
finding(report, "X9_38", function() p3_pct_by(d, "L16B", 1, by = "p3_region")[["northern_africa"]])
finding(report, "X9_39", function() p3_pct_by(d, "L16B", 1, by = "p3_region")[["eastern_europe"]])
finding(report, "X9_40", function() {
  r <- p3_pct_by(d, "L16B", 1, by = "p3_region")
  p3_labels(names(r)[r < 50])
})
finding(report, "X9_41", function() pct(d, "L16B", 1, by = "COUNTRY_ISO3")[c("TUN", "MAR")])
finding(report, "C9_8", function() p3_country_map("L16B", 2))
finding(report, "X9_42", function() pct(p3_country("UKR"), "L16B", 1))
finding(report, "X9_43", function() pct(p3_country("RUS"), "L16B", 1))

p3_gspi_by_country <- function() wmean(d, "p3_gspi", by = "COUNTRY_ISO3")
finding(report, "X9_44", function() length(p3_gspi_by_country()))
finding(report, "X9_45", function() median(p3_gspi_by_country()))
finding(report, "X9_46", function() sum(p3_gspi_by_country() < 50))
finding(report, "X9_47", function() sum(p3_gspi_by_country() >= 75))
finding(report, "X9_48", function() p3_gspi_by_country()[c("SGP", "ARE")])
finding(report, "X9_49", function() {
  g <- p3_confidence_government()
  pct(g[g$COUNTRY_ISO3 %in% "HRV", ], "WP139", 1)
})
finding(report, "X9_50", function() {
  asked <- tapply(!is.na(d$L16A), d$COUNTRY_ISO3, sum)
  p3_country_names(names(asked)[asked == 0])
})
finding(report, "C9_9", function() p3_gspi_by_country())

# =================================================================================
# Chapter 10: Forecasting risk
# Only the recorded 2019 values can be computed; the 2020-2021 forecasts come from
# models with external predictors (see README). The report's 127 forecast
# countries are not listed, so all 142 countries are used.
# =================================================================================

finding(report, "X10_01", function() pct(d, "L2", 2))
finding(report, "X10_02", function() 100 * wmean(d, "experience_index_published"))
finding(report, "X10_03", function() pct(d, "p3_work_injury", 1))
finding(report, "X10_04", function() sum(d$PROJWT))
finding(report, "X10_05", function() p3_pct_by(d, "L2", 2, by = "p3_income")[["high"]])
finding(report, "X10_06", function() p3_pct_by(d, "L2", 2, by = "p3_income")[["low"]])
finding(report, "X10_07", function() p3_pct_by(d, "L2", 2, by = "p3_region")[["northern_america"]])
finding(report, "X10_08", function() p3_pct_by(d, "L2", 2, by = "p3_region")[["southern_europe"]])
finding(report, "X10_09", function() p3_pct_by(d, "L2", 2, by = "p3_region")[["latin_america"]])
finding(report, "C10_2", function() {
  c(harm_2019 = 100 * wmean(d, "experience_index_published"),
    worry_2019 = 100 * wmean(d, "worry_index_published"),
    gap_2019 = 100 * wmean(d, "p3_risk_gap"),
    less_safe_2019 = pct(d, "L2", 2),
    injuries_2019 = pct(d, "p3_work_injury", 1))
})
finding(report, "C10_3", function() p3_suffix(p3_pct_by(d, "L2", 2, by = "p3_income"), "2019"))
finding(report, "C10_4", function() p3_suffix(p3_pct_by(d, "L2", 2, by = "p3_region"), "2019"))

# =================================================================================
# Appendix 3: Regions
# =================================================================================

finding(report, "A3", function() {
  n <- table(d$p3_region[!duplicated(d$COUNTRY_ISO3)])
  c(setNames(as.numeric(n), names(n)), total = sum(n))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
