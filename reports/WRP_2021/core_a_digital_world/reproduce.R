# Reproduce World Risk Poll 2021: A Digital World.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/core_a_digital_world/reproduce.R
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
REGIONS <- c( # GlobalRegion code -> key
  "1" = "east_africa", "2" = "central_west_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "north_america", "7" = "central_asia", "8" = "east_asia",
  "9" = "southeast_asia", "10" = "south_asia", "11" = "middle_east", "12" = "east_europe",
  "13" = "north_west_europe", "14" = "south_europe", "15" = "aus_nz"
)
REGION_NAMES <- c( # as printed in the report
  "1" = "Eastern Africa", "2" = "Central/Western Africa", "3" = "Northern Africa", "4" = "Southern Africa",
  "5" = "Latin America & Caribbean", "6" = "Northern America", "7" = "Central Asia", "8" = "Eastern Asia",
  "9" = "Southeastern Asia", "10" = "Southern Asia", "11" = "Middle East", "12" = "Eastern Europe",
  "13" = "Northern/Western Europe", "14" = "Southern Europe", "15" = "Australia & New Zealand"
)
EDUCATION <- c("1" = "primary", "2" = "secondary", "3" = "post_secondary") # 9 = DK/refused
AGE <- c("1" = "15_29", "2" = "30_49", "3" = "50_64", "4" = "65plus") # AgeGroups4
INCOME_FEELINGS <- c("1" = "comfortable", "2" = "getting_by", "3" = "difficult", "4" = "very_difficult")
AI <- list(help = 1, harm = 2, no_opinion = 3, neither = 4, dk = DK) # WP22227
WORRY <- list(very = 1, somewhat = 2, not = 3, dk = DK)

# Gallup World Poll items that are not in the public release (see README).
INTERNET_ACCESS <- "WP16056" # 'Do you have access to the internet in any way...?' 1 = yes, 2 = no
RELIGION <- "WP119" # 'Is religion an important part of your daily life?' 1 = yes, 2 = no
CONFIDENCE <- "WP139" # confidence in the national government: 1 = yes, 2 = no

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "Gender", "Country", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
  "Education", "AgeGroups4", "IncomeFeelings", "INCOME_5",
  "WP22222", "WP22223", "WP22224", "WP22225", "WP22468", "WP22524", "WP22226", "WP22227",
  "WP22259", "WP22260", "WP22261", "WP22262", "WP22263", "WP22252"
))
d19 <- load_wave(2019, c("PROJWT", "COUNTRY_ISO3", "AgeGroups4", "L26", "L4C"))

# --- Derived variables ---------------------------------------------------------

# Worry that the government will use personal information: Tajikistan and
# Vietnam were asked about "the authorities" (WP22468) and Myanmar about "the
# government in power" (WP22524) instead of WP22224.
d$gov_worry <- coalesce(as.numeric(d$WP22224), as.numeric(d$WP22468), as.numeric(d$WP22524))

# Discrimination in Chapter 1: skin colour, ethnic group/nationality or gender.
# 1 = yes to any, 2 = everyone else who was asked; NA where none was asked.
DISC3 <- c("WP22259", "WP22261", "WP22262")
d$disc3 <- ifelse(rowSums(d[DISC3] == 1, na.rm = TRUE) > 0, 1, 2)
d$disc3[rowSums(!is.na(d[DISC3])) == 0] <- NA

# Forms of discrimination in Chapter 3: 0, 1 or 2 (= two or more) of five
# forms; NA where none was asked.
DISC5 <- c("WP22259", "WP22260", "WP22261", "WP22262", "WP22263")
d$n_disc <- pmin(rowSums(d[DISC5] == 1, na.rm = TRUE), 2)
d$n_disc[rowSums(!is.na(d[DISC5])) == 0] <- NA

# Age under 50 vs 50 and over (text, Chapter 3).
d$under_50 <- ifelse(d$AgeGroups4 %in% 1:2, 1, ifelse(d$AgeGroups4 %in% 3:4, 2, NA))

# Internet users: used the internet in the past 30 days.
iu <- d[d$WP22222 %in% 1, ]

# Trends: the 119 countries surveyed in both waves; each country's 2021
# World Bank income group is used in both years.
BOTH <- countries_in_all(c(2019, 2021))
income_2021 <- tapply(d$CountryIncomeLevel, d$COUNTRY_ISO3, function(x) x[1])
trend <- rbind(
  data.frame(PROJWT = d19$PROJWT, COUNTRY_ISO3 = d19$COUNTRY_ISO3, AgeGroups4 = as.numeric(d19$AgeGroups4),
             internet = as.numeric(d19$L26), ai = as.numeric(d19$L4C), year = 2019),
  data.frame(PROJWT = d$PROJWT, COUNTRY_ISO3 = d$COUNTRY_ISO3, AgeGroups4 = as.numeric(d$AgeGroups4),
             internet = as.numeric(d$WP22222), ai = as.numeric(d$WP22227), year = 2021)
)
trend <- trend[trend$COUNTRY_ISO3 %in% BOTH, ]
trend$income <- as.numeric(income_2021[trend$COUNTRY_ISO3])

# External data for Chart 3.3: World Justice Project Rule of Law Index 2021. Not
# redistributed here: python reports/external/fetch_external.py wjp downloads it.
WJP <- "core_a_digital_world__wjp_rule_of_law_index_2021.csv"

# --- Helpers -------------------------------------------------------------------

# % in each named category of `var`: c(<name> = %) without `by`, or
# c("<group key>_<name>" = %) with `by` (`keys` maps group codes to keys).
answers <- function(df, var, categories, by = NULL, keys = NULL, exclude = NULL) {
  tab <- distribution(df, var, by = by, exclude = exclude)
  if (is.null(by)) {
    return(sapply(categories, function(codes) sum(tab[intersect(as.character(codes), names(tab))])))
  }
  out <- numeric(0)
  for (code in names(keys)) {
    if (!code %in% rownames(tab)) next
    for (name in names(categories)) {
      cols <- intersect(as.character(categories[[name]]), colnames(tab))
      out[paste(keys[[code]], name, sep = "_")] <- sum(tab[code, cols])
    }
  }
  out
}

# Rename a vector named by codes with readable keys (codes not in `keys` dropped).
keyed <- function(x, keys) {
  k <- intersect(names(keys), names(x))
  setNames(unname(x[k]), unname(keys[k]))
}

prefix <- function(x, p) setNames(x, paste(p, names(x), sep = "_"))

round_half_up <- function(x) floor(x + 0.5)

# Mostly help / mostly harm from the rounded percentages, as the report does.
ratio_rounded <- function(help, harm) round_half_up(help) / round_half_up(harm)

SEXES <- c("2" = "women", "1" = "men")

# --- Executive summary and Chapter 1: Artificial intelligence ---------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() pct(d, "WP22227", 1))
finding(report, "X04", function() pct(d, "WP22227", 2))
finding(report, "X05", function() pct(d, "WP22227", c(3, DK)))
finding(report, "X06", function() pct(d, "WP22227", 3))
finding(report, "X07", function() pct(d, "WP22227", DK))
finding(report, "X08", function() keyed(pct(d, "WP22227", 1, by = "Gender"), SEXES))
finding(report, "X09", function() keyed(pct(d, "WP22227", 2, by = "Gender"), SEXES))
finding(report, "X10", function() keyed(pct(trend, "ai", 1, by = "year"), c("2019" = "2019", "2021" = "2021")))
finding(report, "X11", function() keyed(pct(trend, "ai", 2, by = "year"), c("2019" = "2019", "2021" = "2021")))

finding(report, "C1_1", function() {
  c(prefix(answers(d, "WP22227", AI), "world"), answers(d, "WP22227", AI, by = "Gender", keys = SEXES))
})

finding(report, "X12", function() {
  e <- d[d$GlobalRegion %in% 8, ]
  c(help = pct(e, "WP22227", 1), harm = pct(e, "WP22227", 2))
})
finding(report, "X13", function() {
  e <- d[d$GlobalRegion %in% 8, ]
  ratio_rounded(pct(e, "WP22227", 1), pct(e, "WP22227", 2))
})
finding(report, "X14", function() {
  e <- d[d$GlobalRegion %in% 1, ]
  c(harm = pct(e, "WP22227", 2), help = pct(e, "WP22227", 1))
})
finding(report, "X15", function() {
  r <- pct(d[d$COUNTRY_ISO3 %in% c("TZA", "KEN", "UGA"), ], "WP22227", 2, by = "COUNTRY_ISO3")
  r[c("TZA", "KEN", "UGA")]
})
finding(report, "X16", function() {
  max(pct(d[d$COUNTRY_ISO3 %in% c("TZA", "KEN", "UGA"), ], "WP22227", 1, by = "COUNTRY_ISO3"))
})

ai_by_region <- function() {
  out <- answers(d, "WP22227", AI, by = "GlobalRegion", keys = REGIONS)
  for (key in REGIONS) {
    out[paste0(key, "_ratio")] <- ratio_rounded(out[[paste0(key, "_help")]], out[[paste0(key, "_harm")]])
  }
  out
}
finding(report, "C1_2", ai_by_region)
finding(report, "M1_1", function() {
  out <- ai_by_region()
  setNames(out[paste0(REGIONS, "_ratio")], REGIONS)
})

finding(report, "X17", function() {
  x <- d[d$COUNTRY_ISO3 == "CHN", ]
  c(help = pct(x, "WP22227", 1), harm = pct(x, "WP22227", 2))
})

finding(report, "T1_1", function() {
  tab <- distribution(d, "WP22227", by = "COUNTRY_ISO3")
  out <- numeric(0)
  for (iso in c("KOR", "JPN", "FIN", "SWE", "CHN", "DEU", "NOR", "EST", "DNK", "ISL")) {
    row <- tab[iso, ]
    out[paste0(iso, "_help")] <- row[["1"]]
    out[paste0(iso, "_harm")] <- row[["2"]]
    out[paste0(iso, "_net")] <- row[["1"]] - row[["2"]]
    out[paste0(iso, "_no_opinion_dk")] <- sum(row[intersect(c("3", "98", "99"), names(row))])
  }
  out
})

ACCESS <- c("1" = "access", "2" = "no_access")

finding(report, "X18", function() {
  g <- merge_gallup(d, INTERNET_ACCESS)
  keyed(pct(g, "WP22227", 1, by = INTERNET_ACCESS), ACCESS)
})
finding(report, "X19", function() pct(d[d$Education %in% 1, ], "WP22227", 1))
finding(report, "X20", function() {
  g <- merge_gallup(d[d$Education %in% 1, ], INTERNET_ACCESS)
  pct(g[g[[INTERNET_ACCESS]] %in% 1, ], "WP22227", 1)
})
finding(report, "C1_3", function() {
  g <- merge_gallup(d, INTERNET_ACCESS)
  answers(g, "WP22227", AI, by = INTERNET_ACCESS, keys = ACCESS)
})

finding(report, "X21", function() {
  u <- d[d$COUNTRY_ISO3 == "USA", ]
  c(help = pct(u, "WP22227", 1), harm = pct(u, "WP22227", 2))
})

RELIGIOUS <- c("1" = "important", "2" = "not_important")

finding(report, "X22", function() {
  g <- merge_gallup(d, RELIGION)
  c(USA = pct(g[g$COUNTRY_ISO3 == "USA", ], RELIGION, 1),
    north_west_europe = pct(g[g$GlobalRegion %in% 13, ], RELIGION, 1),
    east_asia = pct(g[g$GlobalRegion %in% 8, ], RELIGION, 1))
})
finding(report, "X23", function() {
  g <- merge_gallup(d[d$COUNTRY_ISO3 == "USA", ], RELIGION)
  keyed(pct(g, "WP22227", 1, by = RELIGION), RELIGIOUS)
})
finding(report, "X24", function() {
  g <- merge_gallup(d, RELIGION)
  answers(g, "WP22227", list(help = 1, harm = 2), by = RELIGION, keys = RELIGIOUS)
})
finding(report, "C1_4", function() {
  g <- merge_gallup(d, RELIGION)
  answers(g, "WP22227", AI, by = RELIGION, keys = RELIGIOUS)
})
finding(report, "X25", function() {
  g <- merge_gallup(d[d$Education %in% 3, ], c(RELIGION, INTERNET_ACCESS))
  keyed(pct(g[g[[INTERNET_ACCESS]] %in% 1, ], "WP22227", 1, by = RELIGION), RELIGIOUS)
})

DISCRIMINATED <- c("1" = "experienced", "2" = "not_experienced")

finding(report, "X26", function() {
  e <- d[d$disc3 %in% 1, ]
  c(help = pct(e, "WP22227", 1), harm = pct(e, "WP22227", 2))
})
finding(report, "X27", function() {
  n <- d[d$disc3 %in% 2, ]
  c(help = pct(n, "WP22227", 1), harm = pct(n, "WP22227", 2))
})
finding(report, "X28", function() keyed(pct(d, "WP22227", c(3, DK), by = "disc3"), DISCRIMINATED))
finding(report, "C1_5", function() answers(d, "WP22227", AI, by = "disc3", keys = DISCRIMINATED))
finding(report, "X29", function() {
  r <- pct(d, "WP22227", 2, by = c("COUNTRY_ISO3", "disc3"))
  isos <- unique(sub("_[0-9]+$", "", names(r)))
  gaps <- r[paste0(isos, "_1")] - r[paste0(isos, "_2")]
  sum(gaps >= 10, na.rm = TRUE)
})
finding(report, "C1_6", function() {
  r <- pct(d[d$COUNTRY_ISO3 %in% c("DNK", "NOR", "SWE"), ], "WP22227", 2, by = c("COUNTRY_ISO3", "disc3"))
  names(r) <- paste(sub("_[0-9]+$", "", names(r)), DISCRIMINATED[sub("^.*_", "", names(r))], sep = "_")
  r
})

CAR <- list(yes = 1, no = 2, dk = DK) # WP22226

finding(report, "X30", function() c(yes = pct(d, "WP22226", 1), no = pct(d, "WP22226", 2)))
finding(report, "C1_7", function() answers(d, "WP22226", CAR))
finding(report, "X31", function() max(pct(d, "WP22226", 1, by = "COUNTRY_ISO3")))
finding(report, "X32", function() {
  r <- pct(d, "WP22226", 1, by = "COUNTRY_ISO3")
  d$Country[match(names(which.max(r)), d$COUNTRY_ISO3)]
})
finding(report, "X33", function() keyed(pct(d[d$COUNTRY_ISO3 == "AFG", ], "WP22226", 1, by = "Gender"), c("1" = "men", "2" = "women")))
finding(report, "T1_2", function() {
  pct(d, "WP22226", 1, by = "COUNTRY_ISO3")[c("DNK", "ARE", "AFG", "ITA", "ESP", "KGZ", "SWE", "SAU", "IRN", "NPL")]
})
finding(report, "X34", function() keyed(pct(d, "WP22226", 1, by = "Education"), EDUCATION))

car_safe_by_access_education <- function() {
  g <- merge_gallup(d, INTERNET_ACCESS)
  pct(g, "WP22226", 1, by = c(INTERNET_ACCESS, "Education"))
}
finding(report, "X35", function() {
  r <- car_safe_by_access_education()
  min(sapply(names(EDUCATION), function(e) r[[paste0("1_", e)]] - r[[paste0("2_", e)]]))
})
finding(report, "C1_8_world", function() keyed(pct(d, "WP22226", 1, by = "Education"), EDUCATION))
finding(report, "C1_8_internet", function() {
  r <- car_safe_by_access_education()
  setNames(r[paste0("1_", names(EDUCATION))], EDUCATION)
})
finding(report, "C1_8_no_internet", function() {
  r <- car_safe_by_access_education()
  setNames(r[paste0("2_", names(EDUCATION))], EDUCATION)
})

# --- Chapter 2: Global internet use -------------------------------------------------

INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high")
YEARS <- c("2019" = "2019", "2021" = "2021")
internet_trend <- function(df) keyed(pct(df, "internet", 1, by = "year"), YEARS)

finding(report, "X36", function() length(BOTH))
finding(report, "X37", function() internet_trend(trend))
finding(report, "X38", function() internet_trend(trend[trend$income %in% 2, ]))
finding(report, "X39", function() internet_trend(trend[trend$income %in% 3, ]))
finding(report, "X40", function() internet_trend(trend[trend$income %in% 1, ]))
finding(report, "X41", function() keyed(pct(d, "WP22222", 1, by = "GlobalRegion"), REGIONS[c("10", "1", "2")]))
finding(report, "X42", function() keyed(pct(d, "WP22222", 1, by = "Education"), EDUCATION))
finding(report, "X43", function() keyed(pct(d, "WP22222", 1, by = "Gender"), c("1" = "men", "2" = "women")))

internet_gender_gap_by_region <- function() {
  r <- pct(d, "WP22222", 1, by = c("GlobalRegion", "Gender"))
  codes <- names(REGIONS)
  setNames(r[paste0(codes, "_1")] - r[paste0(codes, "_2")], codes)
}
finding(report, "X44", function() unname(REGION_NAMES[names(which.max(internet_gender_gap_by_region()))]))
finding(report, "X45", function() internet_gender_gap_by_region()[["10"]])
finding(report, "X46", function() {
  pct(d[d$GlobalRegion %in% 10 & d$Gender %in% 2 & d$Education %in% 1, ], "WP22222", 1)
})
finding(report, "X47", function() internet_trend(trend[trend$AgeGroups4 %in% 4, ]))

finding(report, "C2_1", function() {
  r <- pct(trend, "internet", 1, by = c("income", "year"))
  out <- prefix(internet_trend(trend), "world")
  for (code in names(INCOME)) {
    for (year in c("2019", "2021")) out[paste(INCOME[[code]], year, sep = "_")] <- r[[paste(code, year, sep = "_")]]
  }
  out
})
finding(report, "C2_2", function() keyed(pct(d, "WP22222", 1, by = "GlobalRegion"), REGIONS))
finding(report, "X48", function() keyed(pct(d, "Education", 1, by = "GlobalRegion"), REGIONS[c("10", "2", "1", "8", "3")]))
finding(report, "X49", function() sum(pct(d, "Education", 1, by = "GlobalRegion") > 50))
finding(report, "X50", function() {
  keyed(pct(d[d$Education %in% 1, ], "WP22222", 1, by = "GlobalRegion"), REGIONS[c("10", "1", "2")])
})
finding(report, "C2_3", function() {
  r <- pct(d, "WP22222", 1, by = c("GlobalRegion", "Education"))
  out <- prefix(keyed(pct(d, "WP22222", 1, by = "Education"), EDUCATION), "world")
  for (g in c("10", "2", "1")) {
    for (e in names(EDUCATION)) out[paste(REGIONS[[g]], EDUCATION[[e]], sep = "_")] <- r[[paste(g, e, sep = "_")]]
  }
  out
})
finding(report, "X51", function() keyed(pct(d, "WP22222", 1, by = "INCOME_5"), c("1" = "lowest", "5" = "highest")))
finding(report, "X52", function() keyed(pct(d[d$GlobalRegion %in% 10, ], "WP22222", 1, by = "Gender"), c("1" = "men", "2" = "women")))
finding(report, "X53", function() {
  r <- pct(d[!d$GlobalRegion %in% 10, ], "WP22222", 1, by = "Gender")
  r[["1"]] - r[["2"]]
})
finding(report, "X54", function() keyed(pct(d[!d$GlobalRegion %in% 10, ], "WP22222", 1, by = "Gender"), c("1" = "men", "2" = "women")))
finding(report, "X55", function() keyed(pct(d[d$GlobalRegion %in% 10, ], "Education", 1, by = "Gender"), SEXES))
finding(report, "X56", function() {
  keyed(pct(d[d$GlobalRegion %in% 10 & d$Education %in% 2, ], "WP22222", 1, by = "Gender"), c("1" = "men", "2" = "women"))
})
finding(report, "X57", function() {
  pct(d[d$GlobalRegion %in% 10 & d$Gender %in% 1 & d$Education %in% 1, ], "WP22222", 1)
})
finding(report, "X58", function() keyed(pct(d, "WP22222", 1, by = "AgeGroups4"), c("1" = "15_29", "4" = "65plus")))
finding(report, "X59", function() {
  r <- pct(trend, "internet", 1, by = c("AgeGroups4", "year"))
  ages <- c("4" = "65plus", "1" = "15_29", "2" = "30_49")
  setNames(sapply(names(ages), function(a) r[[paste0(a, "_2021")]] - r[[paste0(a, "_2019")]]), ages)
})
finding(report, "C2_4", function() {
  r <- pct(trend, "internet", 1, by = c("AgeGroups4", "year"))
  out <- numeric(0)
  for (a in names(AGE)) {
    for (year in c("2019", "2021")) out[paste(AGE[[a]], year, sep = "_")] <- r[[paste(a, year, sep = "_")]]
  }
  out
})
finding(report, "X60", function() {
  g <- merge_gallup(d[d$CountryIncomeLevel %in% 1, ], INTERNET_ACCESS)
  keyed(pct(g, "WP22252", 1, by = INTERNET_ACCESS), ACCESS)
})

# --- Chapter 3: Online data ----------------------------------------------------------

finding(report, "X61", function() pct(iu, "WP22223", c(1, 2)))
finding(report, "X62", function() pct(iu, "WP22225", c(1, 2)))
finding(report, "X63", function() pct(iu, "WP22225", c(1, 2)))
finding(report, "X64", function() pct(iu, "gov_worry", c(1, 2)))
finding(report, "X65", function() sum(pct(iu, "WP22223", 1, by = "GlobalRegion") > 50))
finding(report, "X66", function() keyed(pct(iu, "WP22223", 1, by = "GlobalRegion"), REGIONS[c("2", "9", "4", "5", "1")]))
finding(report, "C3_1", function() {
  c(prefix(answers(iu, "WP22223", WORRY), "stolen"),
    prefix(answers(iu, "WP22225", WORRY), "companies"),
    prefix(answers(iu, "gov_worry", WORRY), "government"))
})
finding(report, "C3_2", function() answers(iu, "WP22223", WORRY, by = "GlobalRegion", keys = REGIONS))
finding(report, "C3_3", function() {
  # No values are printed on the chart: the correlation across countries is
  # reported for reference only (see README).
  wjp <- read.csv(external_path(WJP), stringsAsFactors = FALSE)
  very <- pct(iu, "WP22223", 1, by = "COUNTRY_ISO3")
  very <- very[!is.na(very)]
  m <- merge(data.frame(iso3 = names(very), very = unname(very)), wjp, by = "iso3")
  c(correlation = cor(m$very, m$wjp_rule_of_law_index_2021), n_countries = nrow(m))
})
finding(report, "X67", function() keyed(pct(iu, "WP22223", 1, by = "Gender"), SEXES))
finding(report, "X68", function() keyed(pct(iu, "WP22223", 1, by = "Education"), EDUCATION))
finding(report, "X69", function() {
  c(under_50 = pct(iu, "WP22223", 1, by = "under_50")[["1"]],
    `65plus` = pct(iu, "WP22223", 1, by = "AgeGroups4")[["4"]])
})
finding(report, "X70", function() {
  keyed(pct(iu, "WP22223", 1, by = "IncomeFeelings"), c("1" = "comfortable", "4" = "very_difficult"))
})
finding(report, "C3_4", function() {
  c(keyed(pct(iu, "WP22223", 1, by = "AgeGroups4"), AGE),
    keyed(pct(iu, "WP22223", 1, by = "IncomeFeelings"), INCOME_FEELINGS))
})
finding(report, "C3_5", function() {
  comp <- pct(iu, "WP22225", 1, by = "GlobalRegion")
  gov <- pct(iu, "gov_worry", 1, by = "GlobalRegion")
  out <- numeric(0)
  for (code in names(REGIONS)) {
    out[paste0(REGIONS[[code]], "_companies")] <- comp[[code]]
    out[paste0(REGIONS[[code]], "_government")] <- gov[[code]]
  }
  out
})

CONFIDENT <- c("1" = "confidence", "2" = "no_confidence")

finding(report, "X71", function() {
  g <- merge_gallup(iu, CONFIDENCE)
  keyed(pct(g, "gov_worry", 1, by = CONFIDENCE), CONFIDENT)
})
finding(report, "C3_6", function() {
  g <- merge_gallup(iu, CONFIDENCE)
  isos <- c("MUS", "TUR", "POL", "HND", "SLV", "GRC", "USA", "JPN", "HKG", "IRN")
  r <- pct(g[g$COUNTRY_ISO3 %in% isos, ], "gov_worry", 1, by = c("COUNTRY_ISO3", CONFIDENCE))
  out <- numeric(0)
  for (iso in isos) {
    for (code in names(CONFIDENT)) out[paste(iso, CONFIDENT[[code]], sep = "_")] <- r[[paste(iso, code, sep = "_")]]
  }
  out
})

# Chart 3.7 and the text on page 34: the companies series leaves don't know and
# refused out of the base (this reproduces all four bars); the government series
# keeps them in, like every other chart.
finding(report, "X72", function() {
  v <- iu[iu$IncomeFeelings %in% 4, ]
  c(government = pct(v, "gov_worry", 1), companies = pct(v, "WP22225", 1, exclude = DK))
})
finding(report, "C3_7", function() {
  comp <- pct(iu, "WP22225", 1, by = "IncomeFeelings", exclude = DK)
  gov <- pct(iu, "gov_worry", 1, by = "IncomeFeelings")
  out <- numeric(0)
  for (code in names(INCOME_FEELINGS)) {
    out[paste0(INCOME_FEELINGS[[code]], "_companies")] <- comp[[code]]
    out[paste0(INCOME_FEELINGS[[code]], "_government")] <- gov[[code]]
  }
  out
})
finding(report, "C3_8", function() {
  forms <- c("0" = "none", "1" = "one", "2" = "two_plus")
  c(prefix(keyed(pct(iu, "WP22223", 1, by = "n_disc"), forms), "stolen"),
    prefix(keyed(pct(iu, "WP22225", 1, by = "n_disc"), forms), "companies"),
    prefix(keyed(pct(iu, "gov_worry", 1, by = "n_disc"), forms), "government"))
})
finding(report, "X73", function() {
  v <- iu[iu$n_disc %in% c(1, 2) & iu$IncomeFeelings %in% 4, ]
  c(stolen = pct(v, "WP22223", 1), government = pct(v, "gov_worry", 1))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
