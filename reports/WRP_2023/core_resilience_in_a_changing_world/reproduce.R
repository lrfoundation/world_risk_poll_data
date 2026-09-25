# Reproduce World Risk Poll 2024 Report: Resilience in a Changing World.
#
# Run from the repository root:
#   Rscript reports/WRP_2023/core_resilience_in_a_changing_world/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

REGIONS <- c(
  "1" = "east_africa", "2" = "central_western_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "north_america", "7" = "central_asia", "8" = "east_asia", "9" = "southeast_asia",
  "10" = "south_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "northern_western_europe",
  "14" = "southern_europe", "15" = "anz"
)
INCOME <- c("4" = "high", "3" = "upper_middle", "2" = "lower_middle", "1" = "low") # CountryIncomeLevel
DIMS <- c(index = "ri", individual = "idv", household = "hhl", community = "com", societal = "soc")
WARNING_SOURCES <- c(internet = "WP22248", government = "WP22249", radio = "WP22250", community = "WP22251")
DISCRIMINATION <- c("WP22259", "WP22260", "WP22261", "WP22262", "WP22263")
RESILIENCE <- c("resilience_index_100", "resilience_idv", "resilience_hhl", "resilience_com", "resilience_soc")
COMMON <- c(
  "WPID_RANDOM", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel", "PROJWT", "WGT",
  "Gender", "AgeGroups3", "AgeGroups4", "Education", "Urbanicity", "EMP_2010", "INCOME_5", RESILIENCE,
  "WP22247", unname(WARNING_SOURCES), "WP22252", "WP22228", "WP22229", DISCRIMINATION,
  "REGION_PAK", "REGION_NZL"
)

d23 <- load_wave(2023, c(COMMON, "WP23344", "WP23345", "WP20719"))
d21 <- load_wave(2021, c(COMMON, "WP22245", "WP22253"))

# --- Derived variables ---------------------------------------------------------

# The same questions under their 2021 and 2023 names: experienced a disaster in
# the past five years, and a household disaster plan known by all members.
names(d23)[match(c("WP23344", "WP23345"), names(d23))] <- c("disaster", "plan")
names(d21)[match(c("WP22245", "WP22253"), names(d21))] <- c("disaster", "plan")

# Region and income group: the report classifies countries by their 2023
# region and income group in both years (Iran moves from the Middle East to
# Southern Asia; seven countries change income group).
first_by_country <- function(d, var) tapply(d[[var]], d$COUNTRY_ISO3, function(x) x[1])
REGION_2023 <- first_by_country(d23, "GlobalRegion")
INCOME_2023 <- first_by_country(d23, "CountryIncomeLevel")

prepare <- function(d) {
  # Resilience Index and its four dimensions on the published 0-100 scale.
  d$ri <- d$resilience_index_100
  d$idv <- 100 * d$resilience_idv
  d$hhl <- 100 * d$resilience_hhl
  d$com <- 100 * d$resilience_com
  d$soc <- 100 * d$resilience_soc
  r <- unname(REGION_2023[d$COUNTRY_ISO3])
  d$region <- ifelse(is.na(r), d$GlobalRegion, r)
  i <- unname(INCOME_2023[d$COUNTRY_ISO3])
  d$income <- ifelse(is.na(i), d$CountryIncomeLevel, i)

  # Early warning (Chapter 3), among those who experienced a disaster:
  # 1 = yes to at least one source; 2 = no to at least one and yes to none;
  # missing if no substantive answer (yes/no) to any source.
  src <- as.matrix(d[WARNING_SOURCES])
  any_yes <- rowSums(src == 1, na.rm = TRUE) > 0
  any_no <- rowSums(src == 2, na.rm = TRUE) > 0
  d$warned <- ifelse(any_yes, 1, ifelse(any_no, 2, NA))

  # Financial resilience: 1 = less than a week; 2 = a week to a month
  # (includes DK on the weeks follow-up); 3 = a month or more.
  d$fin <- with(d, case_when(
    WP22228 %in% 1 & WP22229 %in% 1 ~ 1,
    WP22228 %in% 1 ~ 2,
    WP22228 %in% 2 ~ 3,
    TRUE ~ NA_real_
  ))

  # Employment (Chart 4.1): 1 = full time for an employer; 2 = in the
  # workforce but not; 3 = out of the workforce.
  d$emp <- unname(c("1" = 1, "2" = 2, "3" = 2, "4" = 2, "5" = 2, "6" = 3)[as.character(d$EMP_2010)])

  # Any discrimination (Chart 2.11): yes to any of the five types, among
  # respondents asked at least one of them (DK/refused kept in the base).
  asked <- rowSums(!is.na(d[DISCRIMINATION])) > 0
  any_yes <- rowSums(as.matrix(d[DISCRIMINATION]) == 1, na.rm = TRUE) > 0
  d$any_discrimination <- ifelse(asked, ifelse(any_yes, 1, 2), NA)

  # Disaster type among everyone asked whether they experienced a disaster.
  d$flood <- ifelse(is.na(d$disaster), NA, ifelse(d$WP22247 %in% 1, 1, 2))
  d$earthquake <- ifelse(is.na(d$disaster), NA, ifelse(d$WP22247 %in% 7, 1, 2))
  d
}
d23 <- prepare(d23)
d21 <- prepare(d21)

ew23 <- d23[!is.na(d23$warned), ] # experienced a disaster, substantive answer on warnings
ew21 <- d21[!is.na(d21$warned), ]
exp23 <- d23[d23$disaster %in% 1, ] # experienced a disaster in the past five years
exp21 <- d21[d21$disaster %in% 1, ]

BOTH <- countries_in_all(c(2021, 2023)) # the 120 countries measured in both years

# --- Helpers -------------------------------------------------------------------

# Resilience Index and dimension scores (0-100) by group: a matrix with one
# row per group and one column per DIMS name.
scores <- function(df, by) {
  cols <- lapply(DIMS, function(v) wmean(df, v, by = by))
  keys <- sort(unique(unlist(lapply(cols, names))))
  out <- sapply(cols, function(x) unname(x[keys]))
  if (!is.matrix(out)) out <- matrix(out, nrow = 1, dimnames = list(NULL, names(DIMS)))
  rownames(out) <- keys
  out
}

S23 <- scores(d23, "COUNTRY_ISO3")
S21 <- scores(d21, "COUNTRY_ISO3")
CHANGE <- S23[BOTH, ] - S21[BOTH, ] # country change 2021-2023, 120 countries

# A change that rounds to four points or more is significant (|change| >= 3.5).
significant <- function(dim) {
  ch <- CHANGE[, dim]
  ch <- ch[!is.na(ch)]
  c(increase = sum(ch >= 3.5), decrease = sum(ch <= -3.5), no_change = sum(abs(ch) < 3.5))
}

change_chart <- function(dim, isos) {
  out <- c()
  for (iso in isos) {
    out[paste0(iso, "_2021")] <- S21[iso, dim]
    out[paste0(iso, "_2023")] <- S23[iso, dim]
    out[paste0(iso, "_change")] <- S23[iso, dim] - S21[iso, dim]
  }
  out
}

by_region <- function(x) {
  x <- x[names(x) %in% names(REGIONS)]
  setNames(unname(x), REGIONS[names(x)])
}

country_pct <- function(df, var, codes) pct(df, var, codes, by = "COUNTRY_ISO3")

# Pearson correlation over countries with both values.
corr <- function(x, y) {
  k <- intersect(names(x)[!is.na(x)], names(y)[!is.na(y)])
  cor(unname(x[k]), unname(y[k]))
}

# Country change 2021-2023 in the % giving `codes` (common countries).
country_change <- function(var, codes) {
  setNames(unname(country_pct(d23, var, codes)[BOTH] - country_pct(d21, var, codes)[BOTH]), BOTH)
}

# Resilience Index of group `high` minus group `low` of `var`, by country.
gap_by_country <- function(df, var, high, low) {
  a <- wmean(df[df[[var]] %in% high, ], "ri", by = "COUNTRY_ISO3")
  b <- wmean(df[df[[var]] %in% low, ], "ri", by = "COUNTRY_ISO3")
  k <- intersect(names(a), names(b))
  a[k] - b[k]
}

index_change <- function(iso, dim = "index") unname(CHANGE[iso, dim])

# --- Executive summary -----------------------------------------------------------

finding(report, "X01", function() nrow(d23))
finding(report, "X02", function() length(unique(d23$COUNTRY_ISO3)))
finding(report, "X03", function() length(BOTH))
finding(report, "X04", function() wmean(d23, "ri"))
finding(report, "X05", function() wmean(d21, "ri"))
finding(report, "X06", function() unname(significant("index")["no_change"]))
finding(report, "X07", function() unname(significant("index")["decrease"]))
finding(report, "X08", function() unname(significant("index")["increase"]))
finding(report, "X09", function() unname(significant("individual")["decrease"]))
finding(report, "X10", function() pct(d21, "WP22252", 2))
finding(report, "X11", function() pct(d23, "WP22252", 2))
finding(report, "X12", function() pct(ew23, "warned", 2))
finding(report, "X13", function() pct(ew21, "warned", 2))

# Gallup World Poll mobile phone ownership (placeholder name; see README):
# 1 = has a mobile phone that can access the internet, 2 = has one that cannot
# (or does not know), 3 = no mobile phone.
mobile_phone <- function(df) merge_gallup(df, "GWP_MOBILE_PHONE")
finding(report, "X14", function() pct(mobile_phone(ew23[ew23$warned == 2, ]), "GWP_MOBILE_PHONE", c(1, 2)))
finding(report, "X15", function() pct(d23, "disaster", 1))
finding(report, "X16", function() pct(d21, "disaster", 1))
countries_planning_trend <- function() sum(!is.na(country_change("disaster", 1)) & !is.na(country_change("plan", 1)))
finding(report, "X17", countries_planning_trend)

# --- Chapter 2: The state of global resilience -------------------------------------

finding(report, "X18", function() wmean(d21, "ri"))
finding(report, "X19", function() wmean(d23, "ri"))
finding(report, "X20", function() unname(significant("index")["decrease"]))
finding(report, "X21", function() unname(significant("index")["increase"]))
finding(report, "X22", function() wmean(d23[d23$region == 8, ], "ri") - wmean(d21[d21$region == 8, ], "ri"))
finding(report, "C2_1", function() {
  out <- c()
  for (year in c("2021", "2023")) {
    r <- by_region(wmean(if (year == "2021") d21 else d23, "ri", by = "region"))
    out[paste0(names(r), "_", year)] <- r
  }
  out
})
finding(report, "X23", function() length(unique(d21$COUNTRY_ISO3)))
finding(report, "X24", function() length(unique(d23$COUNTRY_ISO3)))
finding(report, "X25", function() length(BOTH))
finding(report, "X26", function() unname(significant("index")["no_change"]))

# 95% margin of error (points) for a 50% proportion, with the Kish design effect of WGT.
margin_of_error <- function(df) {
  sapply(split(df$WGT, df$COUNTRY_ISO3), function(w) {
    n <- length(w)
    deff <- n * sum(w^2) / sum(w)^2
    196 * sqrt(0.25 * deff / n)
  })
}
finding(report, "X27", function() mean(margin_of_error(d23)))
finding(report, "C2_2", function() significant("index"))
finding(report, "X28", function() sum(!is.na(CHANGE[, "index"])))
finding(report, "C2_3", function() change_chart("index", c("BGR", "ECU", "HRV", "MAR", "MKD", "LAO", "POL", "EGY", "SRB", "SVK")))
finding(report, "C2_4", function() change_chart("index", c("DZA", "GAB", "BFA", "RUS", "SLV", "KGZ", "THA", "UKR", "MLI", "LBN")))
finding(report, "X29", function() index_change("BGR"))
finding(report, "X30", function() index_change("ECU"))
finding(report, "X31", function() index_change("MAR"))
finding(report, "X32", function() index_change("DZA"))
finding(report, "X33", function() index_change("GAB"))
finding(report, "X34", function() min(CHANGE[c("BFA", "RUS", "KGZ", "UKR"), "index"]))
finding(report, "X35", function() index_change("MLI"))
finding(report, "X36", function() index_change("LBN"))
finding(report, "X37", function() S23["KWT", "index"])
finding(report, "X38", function() S23["VNM", "index"])
finding(report, "X39", function() index_change("UZB"))
finding(report, "X40", function() S23["AFG", "index"])
finding(report, "X41", function() index_change("AFG"))
finding(report, "X42", function() index_change("ECU"))
finding(report, "X43", function() S23["CHN", "index"])
rank_2023 <- function(iso, dim = "index") unname(rank(-S23[, dim], na.last = "keep")[iso])
finding(report, "X44", function() rank_2023("KWT"))
finding(report, "X45", function() rank_2023("VNM"))
# Chart 2.5 shows every country's 2023 score as an unlabelled dot: no
# published values to compare.
finding(report, "C2_5", function() {
  x <- S23[, "index"]
  x[!is.na(x)]
})
finding(report, "C2_6", function() {
  out <- c()
  for (dim in names(DIMS)) {
    s <- significant(dim)
    out[paste0(dim, "_increase")] <- s[["increase"]]
    out[paste0(dim, "_decrease")] <- s[["decrease"]]
  }
  out
})
finding(report, "X46", function() unname(significant("individual")["decrease"]))
finding(report, "X47", function() unname(significant("index")["decrease"]))
finding(report, "X48", function() unname(significant("individual")["no_change"]))
finding(report, "X49", function() unname(significant("individual")["increase"]))
finding(report, "X50", function() unname(significant("index")["increase"]))
finding(report, "X51", function() unname(significant("index")["decrease"]))
finding(report, "X52", function() index_change("BGR", "individual"))
finding(report, "X53", function() index_change("POL", "individual"))
finding(report, "X54", function() index_change("MAR", "individual"))
finding(report, "X55", function() index_change("HRV", "individual"))
finding(report, "C2_7", function() change_chart("individual", c("DZA", "CHN", "LBN", "KGZ", "PRY", "SRB", "HRV", "MAR", "POL", "BGR")))
finding(report, "X56", function() pct(d23, "WP22252", 2))
finding(report, "X57", function() pct(d21, "WP22252", 2))
finding(report, "X58", function() unname(significant("household")["no_change"]))
finding(report, "X59", function() unname(significant("household")["decrease"]))
finding(report, "X60", function() unname(significant("household")["increase"]))
finding(report, "C2_8", function() change_chart("household", c("DZA", "UZB", "TGO", "KGZ", "NIC", "MYS", "BGR", "MKD", "MAR", "BGD")))
finding(report, "X61", function() unname(significant("community")["decrease"]))
finding(report, "X62", function() unname(significant("community")["increase"]))
finding(report, "C2_9", function() change_chart("community", c("THA", "SLV", "MMR", "LBN", "ZMB", "CYP", "ECU", "NZL", "LTU", "HRV")))
by_income <- function(x) {
  x <- x[names(x) %in% names(INCOME)]
  setNames(unname(x), INCOME[names(x)])
}
finding(report, "X63", function() {
  out <- c()
  for (year in c("2021", "2023")) {
    r <- by_income(wmean(if (year == "2021") d21 else d23, "com", by = "income"))
    out[paste0(names(r), "_", year)] <- r
  }
  out
})
finding(report, "X64", function() unname(significant("societal")["no_change"]))
finding(report, "X65", function() unname(significant("societal")["decrease"]))
finding(report, "X66", function() unname(significant("societal")["increase"]))
finding(report, "C2_10", function() change_chart("societal", c("GAB", "THA", "MLI", "UKR", "BFA", "SLE", "ECU", "LAO", "EGY", "JOR")))
finding(report, "X67", function() index_change("BRA", "societal"))

# Gallup World Poll: local economic conditions getting better (1) or worse
# (2); placeholder name, see README.
local_economy <- function() merge_gallup(d23, "GWP_LOCAL_ECONOMY")
finding(report, "X68", function() unname(pct(local_economy(), "GWP_LOCAL_ECONOMY", 1, by = "COUNTRY_ISO3")["BRA"]))
finding(report, "X69", function() {
  g7_brics <- c("CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA", "BRA", "RUS", "IND", "CHN", "ZAF")
  s <- pct(local_economy(), "GWP_LOCAL_ECONOMY", 1, by = "COUNTRY_ISO3")[g7_brics]
  d23$Country[d23$COUNTRY_ISO3 == names(which.max(s))][1]
})

discrimination_by_income <- function() {
  out <- c()
  for (year in c("2021", "2023")) {
    d <- if (year == "2021") d21 else d23
    out[paste0("total_", year)] <- pct(d, "any_discrimination", 1)
    r <- by_income(pct(d, "any_discrimination", 1, by = "income"))
    out[paste0(names(r), "_", year)] <- r
  }
  out
}
finding(report, "C2_11", discrimination_by_income)
finding(report, "X70", function() {
  r <- discrimination_by_income()
  c("2021" = r[["total_2021"]], "2023" = r[["total_2023"]])
})
finding(report, "X71", function() {
  r <- discrimination_by_income()
  r[!startsWith(names(r), "total")]
})
DISC23 <- country_pct(d23, "any_discrimination", 1)
finding(report, "X72", function() {
  d21c <- country_pct(d21, "any_discrimination", 1)
  isos <- c("USA", "SGP", "BEL", "KOR", "SVN", "EST", "CAN", "LVA")
  min(DISC23[isos] - d21c[isos])
})
finding(report, "X73", function() DISC23[c("USA", "TCD", "AFG", "LBR")])
finding(report, "X74", function() unname(rank(-DISC23)["USA"]))
finding(report, "X75", function() {
  usa <- d23[d23$COUNTRY_ISO3 == "USA", ]
  sapply(c(nationality = "WP22261", gender = "WP22262", skin = "WP22259", disability = "WP22263"),
         function(v) pct(usa, v, 1))
})
finding(report, "X76", function() corr(CHANGE[, "individual"], CHANGE[, "household"]))
finding(report, "X77", function() corr(CHANGE[, "community"], CHANGE[, "societal"]))

# Table 2.2: country names as printed where they differ from the data's names.
REPORT_NAMES <- c(TWN = "Taiwan, PoC", COD = "Democratic Republic of the Congo", CIV = "Côte d'Ivoire")
NAMES <- first_by_country(d23, "Country")
report_name <- function(iso) if (iso %in% names(REPORT_NAMES)) REPORT_NAMES[[iso]] else NAMES[[iso]]

# Countries ordered from highest to lowest 2023 score on `dim`.
ranking <- function(dim) {
  x <- S23[, dim]
  names(sort(x[!is.na(x)], decreasing = TRUE))
}
finding(report, "T2_2", function() {
  out <- c()
  for (dim in c("individual", "household", "community", "societal")) {
    o <- ranking(dim)
    for (k in 1:10) {
      out[paste0(dim, "_top_", k)] <- report_name(o[k])
      out[paste0(dim, "_bottom_", k)] <- report_name(o[length(o) - k + 1])
    }
  }
  out
})
# Per country: number of dimensions in the top 10, and in the bottom 10.
extremes_count <- function() {
  top <- setNames(rep(0, nrow(S23)), rownames(S23))
  bottom <- top
  for (dim in c("individual", "household", "community", "societal")) {
    o <- ranking(dim)
    n <- length(o)
    top[o[1:10]] <- top[o[1:10]] + 1
    bottom[o[(n - 9):n]] <- bottom[o[(n - 9):n]] + 1
  }
  list(top = top, bottom = bottom)
}
finding(report, "X78", function() {
  e <- extremes_count()
  c(KWT = e$top[["KWT"]], AFG = e$bottom[["AFG"]], YEM = e$bottom[["YEM"]])
})
# Top and bottom counted separately (Niger is in the bottom 10 twice and the
# top 10 once, see README).
finding(report, "X79", function() {
  e <- extremes_count()
  others <- !names(e$top) %in% c("KWT", "AFG", "YEM")
  sum(((e$top > 2) | (e$bottom > 2))[others])
})

# --- Chapter 3: Early warnings ----------------------------------------------------

finding(report, "X80", function() pct(ew23, "warned", 1))
finding(report, "X81", function() pct(ew23, "warned", 2))
finding(report, "X82", function() pct(ew21, "warned", 1))
finding(report, "X83", function() pct(ew21, "warned", 2))
EW4ALL_IN_POLL <- c("MOZ", "MUS", "KHM", "BGD", "LAO", "MDG", "SOM", "UGA", "COM", "LBR", "GTM", "ECU", "NPL",
                    "NER", "TCD", "TJK", "ETH") # Early Warnings for All priority countries shown in Chart 3.1
finding(report, "X84", function() sum(EW4ALL_IN_POLL %in% d23$COUNTRY_ISO3))
finding(report, "C3_1", function() country_pct(ew23, "warned", 1)[EW4ALL_IN_POLL])
finding(report, "X85", function() {
  hazards <- list(earthquake = c(7, 2), mudslide = c(6, 2), heatwave = c(51, 1), hurricane = c(2, 1),
                  blizzard = c(10, 1), tornado = c(3, 1), flood = c(1, 1)) # WP22247 code, warned answer
  sapply(hazards, function(h) pct(ew23[ew23$WP22247 %in% h[1], ], "warned", h[2]))
})
finding(report, "X86", function() {
  out <- c()
  for (key in c("radio", "government", "internet")) {
    out[paste0(key, "_2023")] <- pct(exp23, WARNING_SOURCES[[key]], 1)
    out[paste0(key, "_2021")] <- pct(exp21, WARNING_SOURCES[[key]], 1)
  }
  out
})
finding(report, "C3_2", function() {
  out <- c()
  for (key in names(WARNING_SOURCES)) {
    out[paste0(key, "_2021")] <- pct(exp21, WARNING_SOURCES[[key]], 1)
    out[paste0(key, "_2023")] <- pct(exp23, WARNING_SOURCES[[key]], 1)
  }
  out
})
AGE4 <- c("1" = "15_29", "2" = "30_49", "3" = "50_64", "4" = "65plus")
finding(report, "C3_3", function() {
  out <- c()
  for (year in c("2021", "2023")) {
    r <- pct(if (year == "2021") exp21 else exp23, "WP22248", 1, by = "AgeGroups4")
    out[paste0(AGE4[names(r)], "_", year)] <- r
  }
  out
})
finding(report, "X87", function() {
  r <- pct(exp23, "WP22248", 1, by = "AgeGroups4")
  c("15_29" = r[["1"]], "65plus" = r[["4"]])
})
finding(report, "X88", function() pct(merge_gallup(d23, "GWP_INTERNET_ACCESS"), "GWP_INTERNET_ACCESS", 1))
finding(report, "X89", function() pct(ew23, "warned", 1))

# % at least one warning and % no warning, by group.
warned_by <- function(var, labels, df = ew23) {
  w <- pct(df, "warned", 1, by = var)
  n <- pct(df, "warned", 2, by = var)
  out <- c()
  for (code in names(labels)) {
    out[paste0(labels[[code]], "_warned")] <- w[[code]]
    out[paste0(labels[[code]], "_none")] <- n[[code]]
  }
  out
}
EDUCATION <- c("1" = "primary", "2" = "secondary", "3" = "tertiary")
FIN <- c("1" = "less_week", "2" = "week_month", "3" = "month_plus")
finding(report, "C3_4", function() warned_by("region", REGIONS))
finding(report, "C3_5", function() warned_by("Education", EDUCATION))
finding(report, "X90", function() {
  r <- pct(ew23, "warned", 1, by = "Education")
  setNames(unname(r[names(EDUCATION)]), EDUCATION)
})
finding(report, "C3_6", function() warned_by("fin", FIN))
finding(report, "X91", function() {
  r <- pct(ew23, "warned", 1, by = "fin")
  c(month_plus = r[["3"]], less_week = r[["1"]])
})
# Gallup's degree of urbanisation (placeholder name; see README):
# 1 = rural areas, 2 = towns and semi-dense areas, 3 = cities.
finding(report, "C3_7", function() {
  warned_by("GWP_DEGURBA", c("1" = "rural", "2" = "towns", "3" = "cities"), merge_gallup(ew23, "GWP_DEGURBA"))
})
finding(report, "X92", function() {
  r <- pct(ew23, "warned", 1, by = "Gender")
  c(men = r[["1"]], women = r[["2"]])
})
finding(report, "X93", function() pct(mobile_phone(ew23[ew23$warned == 2, ]), "GWP_MOBILE_PHONE", c(1, 2)))
finding(report, "X94", function() {
  g <- mobile_phone(d23)
  c(internet = pct(g, "GWP_MOBILE_PHONE", 1), no_internet = pct(g, "GWP_MOBILE_PHONE", 2),
    none = pct(g, "GWP_MOBILE_PHONE", 3))
})
finding(report, "X95", function() {
  r <- pct(mobile_phone(ew23), "GWP_MOBILE_PHONE", 1, by = "warned")
  c(warned = r[["1"]], none = r[["2"]])
})
finding(report, "C3_8", function() {
  g <- mobile_phone(ew23)
  out <- c()
  for (code in c("1", "2")) {
    sub <- g[g$warned == as.numeric(code), ]
    label <- c("1" = "warned", "2" = "none")[[code]]
    for (phone in c("1", "2", "3")) {
      key <- c("1" = "internet", "2" = "no_internet", "3" = "none")[[phone]]
      out[paste0(label, "_", key)] <- pct(sub, "GWP_MOBILE_PHONE", as.numeric(phone))
    }
  }
  out
})
finding(report, "C3_9", function() {
  s <- scores(ew23, "warned")
  out <- c()
  for (dim in names(DIMS)) {
    out[paste0(dim, "_warned")] <- s["1", dim]
    out[paste0(dim, "_none")] <- s["2", dim]
  }
  out
})

# --- Chapter 4: What makes people more resilient? ----------------------------------------

# World Bank indicators, 2020-2023 (snapshot in reports/external; see README).
WB <- NULL
world_bank <- function() {
  if (is.null(WB)) WB <<- read.csv(external_path("core_resilience_in_a_changing_world__worldbank.csv"), stringsAsFactors = FALSE)
  WB
}
# World Bank indicator by ISO3 for one year.
wb <- function(indicator, year) {
  w <- world_bank()
  s <- w[w$indicator == indicator & w$year == year, ]
  setNames(s$value, s$iso3)
}

# Gaussian GLM weighted by PROJWT (= weighted least squares) of the Resilience
# Index on personal characteristics, region and country economic indicators
# (World Bank, 2023). Reference groups: out of the workforce, aged 50+, male,
# poorest 20%, rural, Eastern Africa.
resilience_model <- local({
  fit <- NULL
  function() {
    if (is.null(fit)) {
      m <- d23[c("ri", "EMP_2010", "AgeGroups3", "Gender", "INCOME_5", "Urbanicity", "GlobalRegion", "COUNTRY_ISO3", "PROJWT")]
      m$log_gdp_pc <- log(unname(wb("NY.GDP.PCAP.CD", 2023)[m$COUNTRY_ISO3]))
      m$gdp_growth <- unname(wb("NY.GDP.MKTP.KD.ZG", 2023)[m$COUNTRY_ISO3])
      m$inflation <- unname(wb("FP.CPI.TOTL.ZG", 2023)[m$COUNTRY_ISO3])
      m <- m[complete.cases(m), ]
      m$EMP_2010 <- relevel(factor(m$EMP_2010), ref = "6")
      m$AgeGroups3 <- relevel(factor(m$AgeGroups3), ref = "3")
      fit <<- coef(glm(ri ~ EMP_2010 + AgeGroups3 + factor(Gender) + factor(INCOME_5) + factor(Urbanicity) +
                         factor(GlobalRegion) + log_gdp_pc + gdp_growth + inflation,
                       data = m, weights = PROJWT, family = gaussian()))
    }
    fit
  }
})
finding(report, "X96", function() resilience_model()[["EMP_20101"]])
finding(report, "X97", function() gap_by_country(d23, "emp", 1, 3)[["AFG"]])
finding(report, "X98", function() {
  r <- pct(d23[d23$COUNTRY_ISO3 == "AFG", ], "emp", 3, by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})
finding(report, "X99", function() gap_by_country(d23, "emp", 1, 3)[c("COM", "CHN")])
EMP <- c("1" = "ft_employer", "2" = "other_workforce", "3" = "out_workforce")
finding(report, "C4_1", function() {
  s <- scores(d23, "emp")
  out <- c()
  for (code in names(EMP)) {
    for (dim in c("individual", "household", "community", "societal")) out[paste0(EMP[[code]], "_", dim)] <- s[code, dim]
  }
  out
})
finding(report, "X100", function() {
  out <- c()
  for (year in c("2023", "2021")) {
    r <- pct(if (year == "2021") d21 else d23, "WP22252", 2, by = "emp")
    out[paste0(c("out_", "other_", "ft_"), year)] <- c(r[["3"]], r[["2"]], r[["1"]])
  }
  out
})
quintile_gaps <- function() {
  list(poorest = wmean(d23[d23$INCOME_5 %in% 1, ], "ri", by = "region"),
       richest = wmean(d23[d23$INCOME_5 %in% 5, ], "ri", by = "region"))
}
finding(report, "T4_1", function() {
  q <- quintile_gaps()
  out <- c()
  for (code in names(REGIONS)) {
    key <- REGIONS[[code]]
    out[paste0(key, "_poorest")] <- q$poorest[[code]]
    out[paste0(key, "_richest")] <- q$richest[[code]]
    out[paste0(key, "_gap")] <- q$richest[[code]] - q$poorest[[code]]
  }
  out
})
finding(report, "X101", function() {
  q <- quintile_gaps()
  codes <- c(east_asia = "8", north_africa = "3", southern_europe = "14")
  sapply(codes, function(code) q$richest[[code]] - q$poorest[[code]])
})
finding(report, "X102", function() resilience_model()[["AgeGroups31"]])
finding(report, "X103", function() resilience_model()[["AgeGroups32"]])
finding(report, "X104", function() gap_by_country(d23, "AgeGroups4", 1, 4)[c("MYS", "LKA", "PHL")])
GENDER_GAP <- gap_by_country(d23, "Gender", 1, 2) # men minus women
finding(report, "X105", function() {
  men <- round(wmean(d23[d23$Gender == 1, ], "ri", by = "COUNTRY_ISO3"))
  women <- round(wmean(d23[d23$Gender == 2, ], "ri", by = "COUNTRY_ISO3"))
  k <- intersect(names(men), names(women))
  sum(women[k] > men[k])
})
finding(report, "X106", function() GENDER_GAP[c("AFG", "PAK", "CZE", "KOR")])
finding(report, "T4_2", function() {
  out <- c()
  for (iso in c("UKR", "RUS", "BFA", "MLI", "MMR", "AFG", "ECU")) {
    for (dim in names(DIMS)) {
      out[paste0(iso, "_", dim, "_2023")] <- S23[iso, dim]
      out[paste0(iso, "_", dim, "_2021")] <- S21[iso, dim]
    }
  }
  out
})
finding(report, "X107", function() index_change("AFG", "societal"))
finding(report, "X108", function() {
  g23 <- wb("NY.GDP.MKTP.KD.ZG", 2023)
  g21 <- wb("NY.GDP.MKTP.KD.ZG", 2021)
  k <- intersect(names(g23), names(g21))
  corr(CHANGE[, "community"], g23[k] - g21[k])
})
finding(report, "X109", function() corr(country_change("WP22228", 2), CHANGE[, "individual"]))
finding(report, "C4_2", function() {
  s <- scores(d23, "fin")
  out <- c()
  for (code in names(FIN)) for (dim in names(DIMS)) out[paste0(FIN[[code]], "_", dim)] <- s[code, dim]
  out
})

# --- Chapter 5: Natural hazards and resilience ----------------------------------------------

finding(report, "X110", function() c("2023" = pct(d23, "disaster", 1), "2021" = pct(d21, "disaster", 1)))
finding(report, "X111", function() c(flood = pct(exp23, "WP22247", 1), hurricane = pct(exp23, "WP22247", 2),
                                      earthquake = pct(exp23, "WP22247", 7)))
finding(report, "X112", function() c("2023" = pct(d23, "flood", 1), "2021" = pct(d21, "flood", 1)))
DISASTER_REGION <- list("2021" = by_region(pct(d21, "disaster", 1, by = "region")),
                        "2023" = by_region(pct(d23, "disaster", 1, by = "region")))
finding(report, "X113", function() DISASTER_REGION[["2023"]][["anz"]])
country_disaster <- function(iso, d) pct(d[d$COUNTRY_ISO3 == iso, ], "disaster", 1)
finding(report, "X114", function() {
  c(NZL_2023 = country_disaster("NZL", d23), NZL_2021 = country_disaster("NZL", d21),
    AUS_2023 = country_disaster("AUS", d23), AUS_2021 = country_disaster("AUS", d21))
})
finding(report, "X115", function() {
  sapply(c(southern_africa = "southern_africa", central_asia = "central_asia"),
         function(k) DISASTER_REGION[["2023"]][[k]] - DISASTER_REGION[["2021"]][[k]])
})
finding(report, "X116", function() c("2023" = country_disaster("UKR", d23), "2021" = country_disaster("UKR", d21)))
finding(report, "C5_1", function() {
  out <- c()
  for (year in names(DISASTER_REGION)) out[paste0(names(DISASTER_REGION[[year]]), "_", year)] <- DISASTER_REGION[[year]]
  out
})
finding(report, "X117", function() {
  r <- pct(d23, "WP22252", 1, by = "disaster")
  c(exp = r[["1"]], noexp = r[["2"]])
})
finding(report, "X118", function() {
  r <- pct(d23, "plan", 1, by = "disaster")
  c(exp = r[["1"]], noexp = r[["2"]])
})
finding(report, "X119", countries_planning_trend)
finding(report, "X120", function() corr(country_change("disaster", 1), country_change("plan", 1)))
finding(report, "X121", function() country_change("plan", 1)[["MAR"]])
# Scatter without data labels: no published values to compare.
finding(report, "C5_2", function() {
  e <- country_change("disaster", 1)
  p <- country_change("plan", 1)
  k <- names(e)[!is.na(e) & !is.na(p)]
  c(setNames(e[k], paste0(k, "_experience")), setNames(p[k], paste0(k, "_planning")))
})
finding(report, "X122", function() corr(country_change("disaster", 1), country_change("WP22252", 1)))
finding(report, "X123", function() corr(pct(d23, "plan", 1, by = "region"), pct(d23, "WP22252", 1, by = "region")))
# Scatters without data labels: no published values to compare.
finding(report, "C5_3", function() {
  plan <- by_region(pct(d23, "plan", 1, by = "region"))
  agency <- by_region(pct(d23, "WP22252", 1, by = "region"))
  c(setNames(plan, paste0(names(plan), "_plan")), setNames(agency, paste0(names(agency), "_agency")))
})
finding(report, "C5_4", function() {
  plan <- country_pct(d23, "plan", 1)
  agency <- country_pct(d23, "WP22252", 1)
  c(setNames(plan, paste0(names(plan), "_plan")), setNames(agency, paste0(names(agency), "_agency")))
})
by_sex <- function(var, codes) {
  r <- pct(d23, var, codes, by = "Gender")
  c(men = r[["1"]], women = r[["2"]])
}
finding(report, "X124", function() by_sex("WP22252", 1))
finding(report, "X125", function() by_sex("plan", 1))
finding(report, "X126", function() by_sex("WP22228", 2))
finding(report, "X127", function() {
  r <- pct(d23, "WP20719", 1, by = "disaster")
  c(exp = r[["1"]], noexp = r[["2"]])
})
CLIMATE_BY_TYPE <- pct(exp23, "WP20719", 1, by = "WP22247")
finding(report, "X128", function() {
  codes <- c(earthquake = "7", hurricane = "2", flood = "1", heatwave = "51", mudslide = "6")
  sapply(codes, function(code) CLIMATE_BY_TYPE[[code]])
})
finding(report, "X129", function() CLIMATE_BY_TYPE[["6"]] / CLIMATE_BY_TYPE[["51"]])

MAR23 <- d23[d23$COUNTRY_ISO3 == "MAR", ]
MAR21 <- d21[d21$COUNTRY_ISO3 == "MAR", ]
finding(report, "X130", function() {
  c(change = index_change("MAR"), "2023" = S23["MAR", "index"],
    individual = index_change("MAR", "individual"), household = index_change("MAR", "household"))
})
finding(report, "X131", function() {
  m21 <- MAR21[MAR21$disaster %in% 1, ]
  c("2021" = pct(MAR21, "disaster", 1), flood = pct(m21, "WP22247", 1), drought = pct(m21, "WP22247", 50),
    wildfire = pct(m21, "WP22247", 8), "2023" = pct(MAR23, "disaster", 1),
    earthquake = pct(MAR23[MAR23$disaster %in% 1, ], "WP22247", 7), earthquake_all = pct(MAR23, "earthquake", 1))
})
finding(report, "X132", function() {
  r <- wmean(MAR23, "ri", by = "disaster")
  c(exp = r[["1"]], noexp = r[["2"]])
})
finding(report, "C5_5", function() {
  out <- c()
  for (dim in names(DIMS)) {
    out[paste0(dim, "_2021")] <- S21["MAR", dim]
    out[paste0(dim, "_2023")] <- S23["MAR", dim]
  }
  out
})
finding(report, "X133", function() {
  r <- pct(MAR23, "WP22252", 1, by = "disaster")
  c("2023" = pct(MAR23, "WP22252", 1), "2021" = pct(MAR21, "WP22252", 1), exp = r[["1"]], noexp = r[["2"]])
})
finding(report, "X134", function() c("2023" = pct(MAR23, "plan", 1), "2021" = pct(MAR21, "plan", 1)))
# Gallup World Poll WP108: donated money to a charity in the past month (1 = yes).
finding(report, "X135", function() pct(merge_gallup(MAR23, "WP108"), "WP108", 1))

PAK23 <- d23[d23$COUNTRY_ISO3 == "PAK", ]
PAK21 <- d21[d21$COUNTRY_ISO3 == "PAK", ]
NZL23 <- d23[d23$COUNTRY_ISO3 == "NZL", ]
NZL21 <- d21[d21$COUNTRY_ISO3 == "NZL", ]
finding(report, "X136", function() c("2023" = pct(PAK23, "disaster", 1), "2021" = pct(PAK21, "disaster", 1)))
finding(report, "X137", function() c("2023" = pct(PAK23, "flood", 1), "2021" = pct(PAK21, "flood", 1)))
finding(report, "X138", function() c("2023" = pct(NZL23, "disaster", 1), "2021" = pct(NZL21, "disaster", 1)))
finding(report, "X139", function() pct(NZL23, "flood", 1))
PAK_REGIONS <- c("1" = "sindh", "2" = "punjab", "3" = "kp") # REGION_PAK
NZL_REGIONS <- c("2" = "auckland", "9" = "wellington", "14" = "canterbury") # REGION_NZL
finding(report, "X140", function() {
  r <- pct(PAK23, "flood", 1, by = "REGION_PAK")
  setNames(unname(r[names(PAK_REGIONS)]), PAK_REGIONS)
})
finding(report, "X141", function() pct(NZL23, "flood", 1, by = "REGION_NZL")[["2"]])
regional_changes <- function(new, old, var, regions) {
  ch <- scores(new, var)[names(regions), ] - scores(old, var)[names(regions), ]
  out <- c()
  for (code in names(regions)) for (dim in names(DIMS)) out[paste0(regions[[code]], "_", dim)] <- ch[code, dim]
  out
}
finding(report, "X142", function() {
  r <- regional_changes(PAK23, PAK21, "REGION_PAK", PAK_REGIONS)
  c(community = r[["kp_community"]], societal = r[["kp_societal"]])
})
finding(report, "C5_6", function() regional_changes(PAK23, PAK21, "REGION_PAK", PAK_REGIONS))
finding(report, "X143", function() {
  r <- regional_changes(NZL23, NZL21, "REGION_NZL", NZL_REGIONS)
  c(community = r[["auckland_community"]], societal = r[["auckland_societal"]])
})
finding(report, "C5_7", function() regional_changes(NZL23, NZL21, "REGION_NZL", NZL_REGIONS))

# --- Appendices -----------------------------------------------------------------------------

# Needs the Gallup national institutions items (placeholder name; see README):
# countries where any societal item was not asked at all.
finding(report, "X144", function() {
  g <- merge_gallup(d23, "GWP_NATIONAL_INSTITUTIONS")
  items <- c(DISCRIMINATION, "GWP_NATIONAL_INSTITUTIONS")
  asked <- sapply(split(g[items], g$COUNTRY_ISO3), function(x) all(colSums(!is.na(x)) > 0))
  sum(!asked)
})
finding(report, "X145", function() sum(is.na(S23[, "societal"])))
finding(report, "TA_2", function() {
  moe <- margin_of_error(d23)
  out <- c()
  for (iso in rownames(S23)) {
    out[paste0(iso, "_moe")] <- moe[[iso]]
    for (dim in names(DIMS)) if (!is.na(S23[iso, dim])) out[paste0(iso, "_", dim)] <- S23[iso, dim]
  }
  out
})

status <- run_report(report)
if (!interactive()) quit(status = status)
