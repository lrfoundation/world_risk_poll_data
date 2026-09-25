# Reproduce World Risk Poll 2024: A World of Waste.
#
# Run from the repository root:
#   Rscript reports/WRP_2023/core_a_world_of_waste/reproduce.R
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
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "Gender",
  "AgeGroups4", "Education", "INCOME_5", "WP20719", "WP23341", "WP23342", "WP23343",
  "REGION_IND", "REGION_BRA"
))

INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = Venezuela, not classified
REGION <- c(
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
  "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "northern_western_europe",
  "14" = "southern_europe", "15" = "australia_nz"
)
AGE <- c("1" = "15_29", "2" = "30_49", "3" = "50_64", "4" = "65plus") # AgeGroups4
SEX <- c("2" = "women", "1" = "men") # Gender
EDUCATION <- c("1" = "primary", "2" = "secondary", "3" = "tertiary")
CLIMATE <- c("1" = "very", "2" = "somewhat", "3" = "not") # WP20719: climate change a threat to the country
URBAN <- c("1" = "cities", "2" = "towns", "3" = "rural") # degree of urbanisation (Gallup item, see below)
QUINTILE <- c("1" = "q1", "2" = "q2", "3" = "q3", "4" = "q4", "5" = "q5") # INCOME_5
EUROPE <- c(12, 13, 14)
ASIA <- c(7, 8, 9, 10)
AFRICA <- c(1, 2, 3, 4)
SUB_SAHARAN_AFRICA <- c(1, 2, 4)

# --- Derived variables ---------------------------------------------------------

# Material (WP23341): 1 plastic, 2 food, 3 cardboard/paper, 4 cans/metal,
# 5 household dust/leaves/mud, 6 ash, 7 glass, 8 other, 98/99 DK/refused.
d$food_green <- as.numeric(d$WP23341 %in% c(2, 5)) # food and green waste
d$dry <- as.numeric(d$WP23341 %in% c(1, 3, 4, 7)) # dry recyclables

# Disposal (WP23343): 1 household burns it, 2 government collects it,
# 3 community group, 4 private company, 5 household takes it to the tip,
# 6 household throws it outside, 96 other, 98/99 DK/refused.
# Collected ('controlled disposal') = government, community group or private company.
d$collected <- as.numeric(d$WP23343 %in% c(2, 3, 4))
d$burns <- as.numeric(d$WP23343 %in% 1)

# Separation (WP23342): 1 yes, 2 no, 3 sometimes, 98/99 DK/refused.
d$separated <- as.numeric(d$WP23342 %in% 1)

# Waste behaviour quadrant (Chapter 6): 'separated' is yes only, 'collected' is
# any organised collection; everything else is 'not'.
d$quadrant <- with(d, case_when(
  collected == 1 & separated == 1 ~ 1, collected == 1 ~ 2, separated == 1 ~ 3, TRUE ~ 4
))
QUADRANT <- c("1" = "both", "2" = "collected_only", "3" = "separated_only", "4" = "neither")

# Main disposal method for Chart 4.3: burning vs dumping vs the tip vs all
# collection combined (the chart note).
d$main_method <- with(d, case_when(
  WP23343 %in% 1 ~ 1, WP23343 %in% 6 ~ 2, WP23343 %in% 5 ~ 3, collected == 1 ~ 4, TRUE ~ 9
))

# Eastern Europe as the report's text uses it (pages 12 and 33): the
# GlobalRegion plus the Western Balkans and Georgia.
EASTERN_EUROPE_WIDE <- sort(union(unique(d$COUNTRY_ISO3[d$GlobalRegion %in% 12]),
                                  c("ALB", "BIH", "MKD", "MNE", "SRB", "GEO")))

COUNTRY_REGION <- tapply(d$GlobalRegion, d$COUNTRY_ISO3, function(x) x[1])
COUNTRY_INCOME <- tapply(d$CountryIncomeLevel, d$COUNTRY_ISO3, function(x) x[1])

ind <- d[d$COUNTRY_ISO3 == "IND", ]
bra <- d[d$COUNTRY_ISO3 == "BRA", ]

INDIA_STATES <- c( # REGION_IND codes shown on the Chart 5.8 map
  "1" = "andhra_pradesh", "3" = "assam", "4" = "bihar", "6" = "chhattisgarh", "7" = "delhi", "9" = "gujarat",
  "10" = "haryana", "11" = "himachal_pradesh", "13" = "jharkhand", "14" = "karnataka", "15" = "kerala",
  "16" = "madhya_pradesh", "17" = "maharashtra", "22" = "odisha", "24" = "punjab", "25" = "rajasthan",
  "27" = "tamil_nadu", "29" = "uttar_pradesh", "30" = "uttarakhand", "31" = "west_bengal", "32" = "telangana"
)
BRAZIL_STATES <- c( # REGION_BRA codes shown on the Chart 5.11 map
  "13" = "amazonas", "15" = "para", "17" = "tocantins", "21" = "maranhao", "23" = "ceara",
  "24" = "rio_grande_do_norte", "25" = "paraiba", "26" = "pernambuco", "27" = "alagoas", "28" = "sergipe",
  "29" = "bahia", "31" = "minas_gerais", "33" = "rio_de_janeiro", "35" = "sao_paulo", "41" = "parana",
  "42" = "santa_catarina", "43" = "rio_grande_do_sul", "50" = "mato_grosso_do_sul", "52" = "goias",
  "53" = "federal_district", "54" = "espirito_santo", "55" = "amapa", "56" = "rondonia"
)

# --- Gallup World Poll item ------------------------------------------------------
# Every urban-rural figure uses the degree of urbanisation (cities / towns and
# semi-dense areas / rural areas), a Gallup World Poll item that is not in the
# public release. GWP_DEGURBA is a placeholder name, coded 1 = cities,
# 2 = towns and semi-dense areas, 3 = rural areas (see README).

.cache <- new.env()
urban <- function() {
  if (is.null(.cache$urban)) .cache$urban <- merge_gallup(d, "GWP_DEGURBA")
  .cache$urban
}

# --- Helpers -------------------------------------------------------------------

# Rename a pct(..., by = ...) result: c(<prefix><names_map[code]> = value).
named <- function(x, names_map, prefix = "") {
  keep <- names(x) %in% names(names_map)
  setNames(unname(x[keep]), paste0(prefix, names_map[names(x)[keep]]))
}

# % by two groups, names '<name1>_<name2>'.
by2 <- function(df, var, codes, g1, names1, g2, names2) {
  r <- pct(df, var, codes, by = c(g1, g2))
  a <- sub("_.*$", "", names(r))
  b <- sub("^[^_]*_", "", names(r))
  keep <- a %in% names(names1) & b %in% names(names2)
  setNames(unname(r[keep]), paste(names1[a[keep]], names2[b[keep]], sep = "_"))
}

# % by country (ISO3). Within a country PROJWT is proportional to WGT.
country <- function(var, codes, df = d) pct(df, var, codes, by = "COUNTRY_ISO3")

# ISO3 codes of the n highest values, sorted alphabetically, as text.
top <- function(x, n) paste(sort(names(sort(x, decreasing = TRUE))[seq_len(n)]), collapse = "; ")

top_names <- function(x, n) names(sort(x, decreasing = TRUE))[seq_len(n)]

rank_of <- function(x, key) sum(x > x[[key]]) + 1

# Men minus women, % with `var` = 1, by `group`.
sex_gap <- function(var, group) {
  men <- pct(d[d$Gender == 1, ], var, 1, by = group)
  women <- pct(d[d$Gender == 2, ], var, 1, by = group)
  men - women[names(men)]
}

# --- Executive summary ------------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() pct(d, "WP23341", c(1, 2)))
finding(report, "X04", function() pct(d, "WP23341", 1))
finding(report, "X05", function() pct(d, "WP23341", 2))
finding(report, "X06", function() pct(d, "WP23342", 1))
finding(report, "X07", function() pct(d, "WP23342", 1, by = "CountryIncomeLevel")[["4"]])
finding(report, "X08", function() pct(d, "WP23342", 1, by = "CountryIncomeLevel")[["1"]])
finding(report, "X09", function() pct(d, "WP23343", 2))
finding(report, "X10", function() {
  u <- urban()
  pct(u[u$CountryIncomeLevel == 1, ], "collected", 1, by = "GWP_DEGURBA")[["1"]]
})
finding(report, "X11", function() {
  u <- urban()
  pct(u[u$CountryIncomeLevel == 1, ], "collected", 1, by = "GWP_DEGURBA")[["3"]]
})
finding(report, "X12", function() pct(d, "WP23343", c(1, 5, 6)))
finding(report, "X13", function() pct(d, "WP23343", 1))
finding(report, "X14", function() pct(d, "WP23343", 1, by = "GlobalRegion")[["2"]])
finding(report, "X15", function() pct(d, "WP23343", 1, by = "GlobalRegion")[["1"]])
finding(report, "X16", function() country("burns", 1)[["IDN"]])
finding(report, "X17", function() country("burns", 1)[["IDN"]])
finding(report, "X18", function() pct(d, "quadrant", 1))
finding(report, "X19", function() pct(d, "quadrant", c(2, 3)))
finding(report, "X20", function() pct(d, "quadrant", 1, by = "CountryIncomeLevel")[["4"]])
finding(report, "X21", function() pct(d, "quadrant", 1, by = "CountryIncomeLevel")[["1"]])
finding(report, "X22", function() pct(d, "quadrant", 4, by = "CountryIncomeLevel")[["1"]])

# --- Chapter 2: The material world --------------------------------------------------

finding(report, "X23", function() pct(d, "WP23341", 5))
finding(report, "X24", function() pct(d, "WP23341", 3))
finding(report, "X25", function() pct(d, "WP23341", 4))
finding(report, "X26", function() pct(d, "WP23341", 6))
finding(report, "X27", function() pct(d, "WP23341", 7))
finding(report, "X28", function() pct(d, "WP23341", 8))

MATERIALS <- list(plastic = 1, food = 2, dust = 5, cardboard = 3, cans = 4, other = 8, ash = 6, glass = 7)
finding(report, "C2_1", function() sapply(MATERIALS, function(codes) pct(d, "WP23341", codes)))
finding(report, "C2_2", function() {
  groups <- list(plastic = 1, food = 2, cardboard = 3, dust = 5, other = c(4, 6, 7, 8, 98, 99))
  out <- numeric(0)
  for (name in names(groups)) {
    v <- named(pct(d, "WP23341", groups[[name]], by = "CountryIncomeLevel"), INCOME)
    out <- c(out, setNames(v, paste(names(v), name, sep = "_")))
  }
  out
})
finding(report, "X29", function() pct(d, "WP23341", 1, by = "CountryIncomeLevel")[["4"]])
finding(report, "X30", function() {
  p <- pct(d, "WP23341", 1, by = "CountryIncomeLevel")
  f <- pct(d, "WP23341", 2, by = "CountryIncomeLevel")
  c(upper_middle_plastic = p[["3"]], upper_middle_food = f[["3"]],
    lower_middle_plastic = p[["2"]], lower_middle_food = f[["2"]])
})
finding(report, "X31", function() pct(d, "WP23341", 1, by = "CountryIncomeLevel")[["1"]])
finding(report, "X32", function() pct(d, "WP23341", 2, by = "CountryIncomeLevel")[["4"]])
finding(report, "X33", function() named(pct(d, "WP23341", 2, by = "CountryIncomeLevel"), INCOME[1:3]))
finding(report, "X34", function() {
  r <- pct(d, "WP23341", 5, by = "CountryIncomeLevel")
  r[["1"]] / r[["4"]]
})
finding(report, "C2_3", function() {
  c(named(pct(d, "food_green", 1, by = "CountryIncomeLevel"), INCOME, "food_green_"),
    named(pct(d, "dry", 1, by = "CountryIncomeLevel"), INCOME, "dry_"))
})
finding(report, "X35", function() pct(d, "food_green", 1))
finding(report, "C2_4", function() {
  c(named(pct(d, "food_green", 1, by = "GlobalRegion"), REGION, "food_green_"),
    named(pct(d, "dry", 1, by = "GlobalRegion"), REGION, "dry_"))
})
finding(report, "X36", function() {
  sum(pct(d, "food_green", 1, by = "GlobalRegion") > pct(d, "dry", 1, by = "GlobalRegion"))
})
finding(report, "X37", function() {
  named(pct(d, "dry", 1, by = "GlobalRegion"), REGION)[c("northern_western_europe", "southern_europe", "australia_nz", "northern_america")]
})
finding(report, "X38", function() {
  top10 <- top_names(country("WP23341", 1), 10)
  c(europe = sum(COUNTRY_REGION[top10] %in% EUROPE),
    southeastern_asia = sum(COUNTRY_REGION[top10] %in% 9),
    lower_middle = sum(COUNTRY_INCOME[top10] %in% 2))
})

TABLE_2_1 <- list( # material: codes and the countries printed in Table 2.1
  plastic = list(1, c("SVN", "CZE", "SWZ", "SLV", "NLD", "BEL", "KHM", "ITA", "MMR", "IDN")),
  food = list(2, c("COD", "CIV", "GAB", "MAR", "LBN", "KWT", "PAK", "AZE", "MYS", "ISR")),
  dust = list(5, c("ETH", "AFG", "SLE", "MWI", "NER", "ZWE", "BFA", "TCD", "ZMB", "MLI")),
  cardboard = list(3, c("ISL", "SWE", "USA", "GBR", "IRL", "CAN", "TWN", "AUT", "AUS", "HRV"))
)
finding(report, "T2_1", function() {
  out <- c()
  for (name in names(TABLE_2_1)) {
    r <- country("WP23341", TABLE_2_1[[name]][[1]])
    printed <- TABLE_2_1[[name]][[2]]
    out <- c(out, setNames(r[printed], paste(name, printed, sep = "_")))
    out[paste0(name, "_top10")] <- top(r, 10)
  }
  out
})
finding(report, "X39", function() {
  f <- country("WP23341", 2)
  u <- country("WP23341", 5)
  c(food_COD = f[["COD"]], food_CIV = f[["CIV"]], food_GAB = f[["GAB"]], dust_AFG = u[["AFG"]])
})
finding(report, "X40", function() named(pct(d, "dry", 1, by = "Gender"), SEX))
finding(report, "X41", function() {
  # Either gap: men minus women for dry recyclables, or women minus men for
  # food and green waste (Eastern Europe: 4.9 and 5.4 points).
  dry <- sex_gap("dry", "GlobalRegion")
  food_green <- -sex_gap("food_green", "GlobalRegion")
  sapply(c(eastern_asia = "8", central_asia = "7", eastern_europe = "12"),
         function(k) as.numeric(max(dry[[k]], food_green[[k]]) > 5))
})
finding(report, "C2_5", function() {
  fg <- pct(d, "food_green", 1, by = "Gender")
  dr <- pct(d, "dry", 1, by = "Gender")
  c(women_food_green = fg[["2"]], women_dry = dr[["2"]], men_food_green = fg[["1"]], men_dry = dr[["1"]])
})
# "Differences of 10 percentage points or more" (page 12) are gaps that round
# to 10 or more: Ukraine (9.9) and Kyrgyzstan (9.6) are in the report's list.
finding(report, "X42", function() {
  g <- sex_gap("dry", "COUNTRY_ISO3")
  hit <- names(g)[g >= 9.5]
  c(count = length(hit), countries = paste(sort(hit), collapse = "; "))
})
finding(report, "X43", function() {
  g <- -sex_gap("dry", "COUNTRY_ISO3")
  hit <- names(g)[g >= 9.5]
  c(count = length(hit), countries = paste(sort(hit), collapse = "; "))
})
finding(report, "C2_6", function() by2(d, "dry", 1, "CountryIncomeLevel", INCOME, "AgeGroups4", AGE))

# % with `var` = 1 aged 15-29 and 65+, by country. Countries with fewer than
# 100 respondents in either age group are left out, which reproduces the
# country list in Chart 3.4 (Saudi Arabia has three respondents aged 65+).
MIN_AGE_BASE <- 100
age_gap <- function(var) {
  young <- pct(d[d$AgeGroups4 %in% 1, ], var, 1, by = "COUNTRY_ISO3")
  old <- pct(d[d$AgeGroups4 %in% 4, ], var, 1, by = "COUNTRY_ISO3")
  n_young <- table(d$COUNTRY_ISO3[d$AgeGroups4 %in% 1])
  n_old <- table(d$COUNTRY_ISO3[d$AgeGroups4 %in% 4])
  keep <- intersect(names(n_young)[n_young >= MIN_AGE_BASE], names(n_old)[n_old >= MIN_AGE_BASE])
  keep <- sort(intersect(keep, intersect(names(young), names(old))))
  list(young = young[keep], old = old[keep])
}

finding(report, "T2_2", function() {
  a <- age_gap("dry")
  gap <- a$young - a$old # ranking uses the unrounded gap
  out <- c()
  for (iso in c("BGR", "TWN", "MUS", "SVK", "PRT")) {
    # The printed gap is the difference of the rounded figures.
    out[paste0(iso, "_15_29")] <- a$young[[iso]]
    out[paste0(iso, "_65plus")] <- a$old[[iso]]
    out[paste0(iso, "_gap")] <- round(a$young[[iso]]) - round(a$old[[iso]])
  }
  out["top5"] <- top(gap, 5)
  out
})
finding(report, "X44", function() {
  a <- age_gap("dry")
  sum((a$young - a$old) > 25)
})
finding(report, "C2_7", function() by2(d, "dry", 1, "CountryIncomeLevel", INCOME, "Education", EDUCATION))
finding(report, "X45", function() named(pct(urban(), "dry", 1, by = "GWP_DEGURBA"), c("1" = "cities", "3" = "rural")))
finding(report, "X46", function() {
  u <- urban()
  named(pct(u[u$CountryIncomeLevel == 1, ], "dry", 1, by = "GWP_DEGURBA"), c("1" = "cities", "3" = "rural"))
})

# --- Chapter 3: Dividing lines in waste separation ----------------------------------

SEPARATION <- list(yes = 1, sometimes = 3, no = 2)

# pct() of each separation answer by `group`, names '<group name>_<answer>'.
separation_by <- function(df, group, names_map) {
  out <- numeric(0)
  for (s in names(SEPARATION)) {
    v <- named(pct(df, "WP23342", SEPARATION[[s]], by = group), names_map)
    out <- c(out, setNames(v, paste(names(v), s, sep = "_")))
  }
  out
}

finding(report, "X47", function() pct(d, "WP23342", 2))
finding(report, "X48", function() pct(d, "WP23342", 3))
finding(report, "C3_1", function() {
  c(setNames(sapply(SEPARATION, function(codes) pct(d, "WP23342", codes)), paste0("global_", names(SEPARATION))),
    separation_by(d, "GlobalRegion", REGION))
})
finding(report, "X49", function() {
  named(pct(d, "WP23342", 1, by = "GlobalRegion"), REGION)[c("australia_nz", "northern_western_europe")]
})
finding(report, "X50", function() {
  named(pct(d, "WP23342", 1, by = "GlobalRegion"), REGION)[c(
    "eastern_asia", "southeastern_asia", "central_asia", "southern_asia", "southern_africa", "central_western_africa"
  )]
})
finding(report, "X51", function() country("WP23342", 3)[["CHN"]])
finding(report, "X52", function() pct(d[d$COUNTRY_ISO3 != "CHN", ], "WP23342", 3))
finding(report, "X53", function() pct(d[d$GlobalRegion == 8 & d$COUNTRY_ISO3 != "CHN", ], "WP23342", 1))
finding(report, "C3_2", function() separation_by(d, "CountryIncomeLevel", INCOME))
finding(report, "X54", function() {
  r <- pct(d, "WP23342", 1, by = "CountryIncomeLevel")
  r[["4"]] / r[["1"]]
})
finding(report, "X55", function() {
  r <- pct(d, "WP23342", 1, by = "CountryIncomeLevel")
  c(upper_middle = r[["3"]], lower_middle = r[["2"]])
})

TABLE_3_1 <- list(yes = c("KOR", "ISL", "BEL", "ITA", "SVN", "MLT", "TWN", "CZE", "LUX", "SWE"),
                  no = c("GAB", "CIV", "XKX", "TGO", "CMR", "BEN", "LBR", "COG", "MNE", "ALB"))
finding(report, "T3_1", function() {
  out <- c()
  for (s in names(TABLE_3_1)) {
    r <- country("WP23342", SEPARATION[[s]])
    out <- c(out, setNames(r[TABLE_3_1[[s]]], paste(s, TABLE_3_1[[s]], sep = "_")))
    out[paste0(s, "_top10")] <- top(r, 10)
  }
  out
})
finding(report, "X56", function() {
  top10 <- top_names(country("WP23342", 1), 10)
  sum(COUNTRY_REGION[top10] %in% c(EUROPE, 8))
})
finding(report, "X57", function() {
  top10 <- top_names(country("WP23342", 2), 10)
  c(sub_saharan_africa = sum(COUNTRY_REGION[top10] %in% SUB_SAHARAN_AFRICA),
    eastern_europe = sum(top10 %in% EASTERN_EUROPE_WIDE))
})
finding(report, "X58", function() {
  yes <- pct(d, "WP23342", 1, by = "AgeGroups4")
  c(`15_29_yes` = yes[["1"]], `15_29_no` = pct(d, "WP23342", 2, by = "AgeGroups4")[["1"]], `65plus_yes` = yes[["4"]])
})
finding(report, "C3_3", function() separation_by(d, "AgeGroups4", AGE))

CHART_3_4 <- c("BRA", "GRC", "ARG", "URY", "VEN", "PER", "PHL", "DOM", "SLV", "HRV", "COL", "CRI", "BGR", "PAN", "CHL")
finding(report, "C3_4", function() {
  a <- age_gap("separated")
  gap <- a$old - a$young # ranking uses the unrounded gap
  out <- c()
  for (iso in CHART_3_4) {
    # The printed gap is the difference of the rounded figures.
    out[paste0(iso, "_15_29")] <- a$young[[iso]]
    out[paste0(iso, "_65plus")] <- a$old[[iso]]
    out[paste0(iso, "_gap")] <- round(a$old[[iso]]) - round(a$young[[iso]])
  }
  means <- pct(d, "separated", 1, by = "AgeGroups4")
  out["mean_15_29"] <- means[["1"]]
  out["mean_65plus"] <- means[["4"]]
  out["top15"] <- top(gap, 15)
  out
})
finding(report, "X59", function() {
  c(latin_america = pct(d, "WP23342", 1, by = "GlobalRegion")[["5"]], global = pct(d, "WP23342", 1))
})
finding(report, "X60", function() {
  a <- age_gap("separated")
  sum(COUNTRY_REGION[top_names(a$old - a$young, 15)] %in% 5)
})
finding(report, "X61", function() {
  r <- by2(d, "separated", 1, "CountryIncomeLevel", INCOME, "Gender", SEX)
  c(named(pct(d, "WP23342", 1, by = "Gender"), SEX), r[grepl("^(upper|lower)_middle", names(r))])
})
finding(report, "C3_5", function() separation_by(d, "Gender", SEX))
finding(report, "X62", function() {
  sep <- by2(d, "separated", 1, "GlobalRegion", REGION, "Gender", SEX)
  dry <- by2(d, "dry", 1, "GlobalRegion", REGION, "Gender", SEX)
  out <- c()
  for (region in c("northern_america", "southern_asia")) {
    for (sex in c("women", "men")) {
      out[paste(region, "sep", sex, sep = "_")] <- sep[[paste(region, sex, sep = "_")]]
      out[paste(region, "dry", sex, sep = "_")] <- dry[[paste(region, sex, sep = "_")]]
    }
  }
  out
})
finding(report, "X63", function() named(pct(d, "WP23342", 1, by = "Education"), EDUCATION))
finding(report, "X64", function() named(pct(d, "WP23342", 1, by = "WP20719"), CLIMATE))
finding(report, "X65", function() named(pct(d[d$CountryIncomeLevel == 4, ], "WP23342", 1, by = "WP20719"), CLIMATE))
finding(report, "C3_6", function() by2(d, "separated", 1, "CountryIncomeLevel", INCOME, "WP20719", CLIMATE))

# --- Chapter 4: The open burning of household waste -----------------------------------

METHODS <- list(government = 2, landfill = 5, burns = 1, street = 6, community = 3, private = 4, other = 96)
finding(report, "C4_1", function() sapply(METHODS, function(codes) pct(d, "WP23343", codes)))
finding(report, "X66", function() {
  others <- sapply(c(1, 3, 4, 5, 6, 96), function(code) pct(d, "WP23343", code))
  pct(d, "WP23343", 2) / max(others)
})
finding(report, "X67", function() pct(d, "WP23343", c(1, 5, 6)))
finding(report, "X68", function() pct(d, "WP23343", 6))
finding(report, "X69", function() pct(d, "collected", 1))
finding(report, "X70", function() {
  shares <- sapply(1:6, function(code) pct(d, "WP23343", code))
  sum(shares > shares[1]) + 1
})
finding(report, "X71", function() pct(d, "WP23343", 5))
finding(report, "X72", function() named(pct(d, "burns", 1, by = "CountryIncomeLevel"), INCOME))
finding(report, "X73", function() max(pct(d, "burns", 1, by = "GlobalRegion")[c("12", "13", "14", "15")]))
finding(report, "C4_2", function() c(named(pct(d, "burns", 1, by = "GlobalRegion"), REGION), global = pct(d, "burns", 1)))

# Countries where burning is the most common of the four methods (Chart 4.3),
# compared on shares rounded to whole numbers: Benin burns 29.3% and takes
# 28.7% to the tip (29% each) and is not in the chart.
burning_most_common <- function() {
  shares <- sapply(c(burn = 1, dump = 2, tip = 3, collected = 4), function(code) country("main_method", code))
  shares <- round(shares)
  rownames(shares)[shares[, "burn"] > pmax(shares[, "dump"], shares[, "tip"], shares[, "collected"])]
}
finding(report, "X74", function() sum(country("burns", 1) > 50))
finding(report, "X75", function() length(burning_most_common()))
finding(report, "X76", function() sum(!(COUNTRY_REGION[burning_most_common()] %in% c(AFRICA, ASIA))))
finding(report, "C4_3", function() {
  r <- country("burns", 1)
  most <- burning_most_common()
  c(r[most], global = pct(d, "burns", 1), countries = paste(sort(most), collapse = "; "))
})

country_rates <- function() {
  data.frame(collected = country("collected", 1), burns = country("burns", 1),
             separated = country("separated", 1), dry = country("dry", 1))
}
finding(report, "X77", function() {
  rates <- country_rates()
  cor(rates$collected, rates$burns)
})
finding(report, "C4_4", function() {
  # Scatter plot: no values are printed, so these have nothing to compare with.
  rates <- country_rates()
  c(setNames(rates$collected, paste0(rownames(rates), "_collected")),
    setNames(rates$burns, paste0(rownames(rates), "_burns")))
})
finding(report, "X78", function() {
  r <- country("burns", 1)
  c(SWZ = r[["SWZ"]], rank = rank_of(r, "SWZ"))
})
finding(report, "X79", function() country("burns", 1)[["SWZ"]])

# --- Chapter 5: Controlled disposal: an urban-rural divide -----------------------------

finding(report, "C5_1", function() c(named(pct(d, "collected", 1, by = "GlobalRegion"), REGION), global = pct(d, "collected", 1)))
finding(report, "X80", function() {
  named(pct(d, "collected", 1, by = "GlobalRegion"), REGION)[c(
    "eastern_asia", "middle_east", "central_asia", "northern_africa", "southern_africa"
  )]
})
finding(report, "X81", function() sum(pct(d, "collected", 1, by = "GlobalRegion") < 50))
finding(report, "X82", function() {
  named(pct(d, "collected", 1, by = "GlobalRegion"), REGION)[c(
    "southeastern_asia", "southern_asia", "eastern_asia", "central_asia", "central_western_africa", "eastern_africa"
  )]
})
finding(report, "X83", function() named(pct(d, "collected", 1, by = "CountryIncomeLevel"), INCOME))

collected_income_urban <- function() by2(urban(), "collected", 1, "CountryIncomeLevel", INCOME, "GWP_DEGURBA", URBAN)
finding(report, "X84", function() {
  r <- collected_income_urban()
  r[!startsWith(names(r), "low_") | names(r) == "low_towns"]
})
finding(report, "X85", function() {
  u <- urban()
  by2(u[u$COUNTRY_ISO3 %in% c("AUT", "DNK"), ], "collected", 1, "COUNTRY_ISO3", c(AUT = "AUT", DNK = "DNK"),
      "GWP_DEGURBA", URBAN)
})
finding(report, "C5_2", function() {
  c(collected_income_urban(), named(pct(urban(), "collected", 1, by = "GWP_DEGURBA"), URBAN, "mean_"))
})

region_urban_gap <- function() {
  u <- urban()
  list(cities = pct(u[u$GWP_DEGURBA %in% 1, ], "collected", 1, by = "GlobalRegion"),
       rural = pct(u[u$GWP_DEGURBA %in% 3, ], "collected", 1, by = "GlobalRegion"))
}
finding(report, "X86", function() {
  g <- region_urban_gap()
  values <- c(g$cities[as.character(EUROPE)], g$rural[as.character(EUROPE)])
  as.numeric(min(values) >= 79.5 && max(values) < 90.5)
})
finding(report, "X87", function() {
  g <- region_urban_gap()
  c(australia_nz = g$cities[["15"]] - g$rural[["15"]], northern_america = g$cities[["6"]] - g$rural[["6"]])
})
finding(report, "X88", function() {
  g <- region_urban_gap()
  c(southern_africa = as.numeric(g$cities[["4"]] - g$rural[["4"]] > 50),
    eastern_africa = as.numeric(g$cities[["1"]] - g$rural[["1"]] > 50))
})
finding(report, "C5_3", function() {
  g <- region_urban_gap()
  out <- c()
  for (code in names(REGION)) {
    name <- REGION[[code]]
    out[paste0(name, "_rural")] <- g$rural[[code]]
    out[paste0(name, "_cities")] <- g$cities[[code]]
    out[paste0(name, "_gap")] <- round(g$cities[[code]]) - round(g$rural[[code]]) # from the rounded figures
  }
  means <- pct(urban(), "collected", 1, by = "GWP_DEGURBA")
  c(out, mean_rural = means[["3"]], mean_cities = means[["1"]])
})

country_urban_gap <- function() {
  u <- urban()
  cities <- pct(u[u$GWP_DEGURBA %in% 1, ], "collected", 1, by = "COUNTRY_ISO3")
  rural <- pct(u[u$GWP_DEGURBA %in% 3, ], "collected", 1, by = "COUNTRY_ISO3")
  keep <- intersect(names(cities), names(rural))
  list(cities = cities[keep], rural = rural[keep])
}
finding(report, "X89", function() {
  # Gaps as printed in Chart 5.4: differences of the rounded figures.
  g <- country_urban_gap()
  sum((round(g$cities) - round(g$rural)) >= 60)
})
CHART_5_4 <- c("KHM", "SEN", "NPL", "NIC", "PRY", "TZA", "BOL", "MNG", "MLI", "GTM", "KGZ", "HND", "IRQ", "GHA", "NAM")
finding(report, "C5_4", function() {
  g <- country_urban_gap()
  out <- c()
  for (iso in CHART_5_4) {
    out[paste0(iso, "_rural")] <- g$rural[[iso]]
    out[paste0(iso, "_cities")] <- g$cities[[iso]]
    out[paste0(iso, "_gap")] <- round(g$cities[[iso]]) - round(g$rural[[iso]]) # from the rounded figures
  }
  means <- pct(urban(), "collected", 1, by = "GWP_DEGURBA")
  out["mean_rural"] <- means[["3"]]
  out["mean_cities"] <- means[["1"]]
  out["top15"] <- top(g$cities - g$rural, 15)
  out
})

india_urban <- function() {
  u <- urban()
  u[u$COUNTRY_ISO3 == "IND", ]
}
suffix <- function(s) setNames(paste(URBAN, s, sep = "_"), names(URBAN))
finding(report, "X90", function() {
  u <- india_urban()
  cc <- named(pct(u, "collected", 1, by = "GWP_DEGURBA"), URBAN)
  b <- named(pct(u, "burns", 1, by = "GWP_DEGURBA"), URBAN)
  c(cities_collected = cc[["cities"]], cities_burns = b[["cities"]], towns_collected = cc[["towns"]],
    rural_collected = cc[["rural"]], rural_burns = b[["rural"]], towns_burns = b[["towns"]])
})
finding(report, "C5_5", function() {
  u <- india_urban()
  c(named(pct(u, "burns", 1, by = "GWP_DEGURBA"), suffix("burns")),
    named(pct(u, "collected", 1, by = "GWP_DEGURBA"), suffix("collected")))
})
finding(report, "X91", function() pct(ind[ind$burns == 1, ], "separated", 0))
finding(report, "C5_6", function() {
  # % whose main waste is plastic, among households that burn / have their
  # waste collected (the reading that fits the text; see README).
  u <- india_urban()
  c(named(pct(u[u$burns == 1, ], "WP23341", 1, by = "GWP_DEGURBA"), suffix("burns")),
    named(pct(u[u$collected == 1, ], "WP23341", 1, by = "GWP_DEGURBA"), suffix("collected")))
})
finding(report, "C5_7", function() by2(india_urban(), "burns", 1, "GWP_DEGURBA", URBAN, "INCOME_5", QUINTILE))
finding(report, "C5_8", function() named(pct(ind, "burns", 1, by = "REGION_IND"), INDIA_STATES))
finding(report, "X92", function() {
  s <- pct(ind, "burns", 1, by = "REGION_IND")
  r <- named(s, INDIA_STATES)
  c(delhi = r[["delhi"]], assam = r[["assam"]], assam_rank = rank_of(s, "3"))
})
finding(report, "X93", function() {
  # Needs the Gallup World Poll item on satisfaction with air quality where
  # the respondent lives (placeholder name; 2 = dissatisfied assumed).
  g <- merge_gallup(ind, "GWP_AIR_QUALITY_SATISFACTION")
  g$delhi <- ifelse(g$REGION_IND %in% 7, 1, 2)
  r <- pct(g, "GWP_AIR_QUALITY_SATISFACTION", 2, by = "delhi")
  c(delhi = r[["1"]], rest = r[["2"]])
})

brazil_urban <- function() {
  u <- urban()
  u[u$COUNTRY_ISO3 == "BRA", ]
}
finding(report, "X94", function() named(pct(brazil_urban(), "burns", 1, by = "GWP_DEGURBA"), URBAN))
finding(report, "X95", function() {
  u <- brazil_urban()
  r <- pct(u[u$GWP_DEGURBA %in% 3, ], "burns", 1, by = "INCOME_5")
  c(rural_q1 = r[["1"]], rural_q5 = r[["5"]])
})
finding(report, "C5_9", function() {
  u <- brazil_urban()
  c(named(pct(u, "burns", 1, by = "GWP_DEGURBA"), suffix("burns")),
    named(pct(u, "collected", 1, by = "GWP_DEGURBA"), suffix("collected")))
})
finding(report, "C5_10", function() by2(brazil_urban(), "burns", 1, "GWP_DEGURBA", URBAN, "INCOME_5", QUINTILE))
finding(report, "C5_11", function() named(pct(bra, "burns", 1, by = "REGION_BRA"), BRAZIL_STATES))
finding(report, "X96", function() {
  r <- named(pct(bra, "burns", 1, by = "REGION_BRA"), BRAZIL_STATES)
  c(maranhao = r[["maranhao"]], para = r[["para"]])
})

# --- Chapter 6: Global household waste: further analysis --------------------------------

finding(report, "X97", function() {
  sapply(c(collected_only = 2, separated_only = 3, neither = 4), function(code) pct(d, "quadrant", code))
})
finding(report, "X98", function() {
  q <- lapply(1:4, function(code) pct(d, "quadrant", code, by = "CountryIncomeLevel"))
  c(upper_middle_both = q[[1]][["3"]], upper_middle_collected_only = q[[2]][["3"]],
    lower_middle_separated_only = q[[3]][["2"]], lower_middle_neither = q[[4]][["2"]])
})
finding(report, "C6_1", function() {
  out <- c()
  for (code in names(QUADRANT)) {
    q <- QUADRANT[[code]]
    out[paste0("global_", q)] <- pct(d, "quadrant", as.numeric(code))
    v <- named(pct(d, "quadrant", as.numeric(code), by = "CountryIncomeLevel"), INCOME)
    out <- c(out, setNames(v, paste(names(v), q, sep = "_")))
  }
  out
})
finding(report, "X99", function() {
  r <- sort(country("quadrant", 2), decreasing = TRUE)
  c(eastern_europe = sum(names(r)[1:10] %in% EASTERN_EUROPE_WIDE),
    top5_eastern_europe = sum(names(r)[1:5] %in% EASTERN_EUROPE_WIDE),
    top5_over_two_thirds = as.numeric(all(r[1:5] > 200 / 3)))
})
TABLE_6_1 <- c("XKX", "MNE", "BGR", "BIH", "SRB", "KWT", "PSE", "MKD", "GEO", "CHL")
TABLE_6_2 <- c("LKA", "NPL", "BGD", "MWI", "UGA", "TJK", "SWE", "KHM", "KEN", "HND")
finding(report, "T6_1", function() {
  r <- country("quadrant", 2)
  c(r[TABLE_6_1], top10 = top(r, 10))
})
finding(report, "T6_2", function() {
  r <- country("quadrant", 3)
  c(r[TABLE_6_2], top10 = top(r, 10))
})
finding(report, "X100", function() country("quadrant", 3)[c("LKA", "NPL", "BGD", "IND")])
finding(report, "X101", function() {
  s <- d[d$quadrant == 3, ]
  burns <- pct(s, "WP23343", 1, by = "CountryIncomeLevel")
  c(global_landfill = pct(s, "WP23343", 5), global_burns = pct(s, "WP23343", 1),
    low_burns = burns[["1"]], lower_middle_burns = burns[["2"]])
})
finding(report, "C6_2", function() {
  # Bubble chart: no values are printed, so these have nothing to compare
  # with. Also returns the country-level correlation between separation and
  # collection within each income group.
  rates <- country_rates()
  out <- c()
  for (m in c("collected", "separated", "dry")) out <- c(out, setNames(rates[[m]], paste(rownames(rates), m, sep = "_")))
  for (code in names(INCOME)) {
    r <- rates[COUNTRY_INCOME[rownames(rates)] %in% as.numeric(code), ]
    out[paste0("corr_", INCOME[[code]])] <- cor(r$collected, r$separated)
  }
  out
})

status <- run_report(report)
if (!interactive()) quit(status = status)
