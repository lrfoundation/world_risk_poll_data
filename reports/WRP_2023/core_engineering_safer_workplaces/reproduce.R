# Reproduce World Risk Poll 2024 Report: Engineering safer workplaces (2023 data).
#
# Run from the repository root:
#   Rscript reports/WRP_2023/core_engineering_safer_workplaces/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

EXTERNAL <- file.path(WRP_ROOT, "reports", "external")
GDP_FILE <- file.path(EXTERNAL, "core_engineering_safer_workplaces__worldbank_NY.GDP.PCAP.CD.csv")
MODE_FILE <- file.path(EXTERNAL, "core_engineering_safer_workplaces__wrp_interview_mode.csv")

REGION <- c("1" = "eastern_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
            "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia",
            "9" = "southeastern_asia", "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe",
            "13" = "northern_western_europe", "14" = "southern_europe", "15" = "anz")
RCODE <- setNames(names(REGION), REGION)
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high")
SECTOR <- c("1" = "agriculture", "2" = "fishing", "3" = "manufacturing", "4" = "construction", "5" = "mining",
            "6" = "electricity", "7" = "market_services", "8" = "non_market_services") # WP23340
SCODE <- setNames(names(SECTOR), SECTOR)
SECTOR5 <- c("construction", "agriculture", "market_services", "non_market_services", "manufacturing")
TRAIN <- c("1" = "past2", "2" = "older", "3" = "never")
HARMED <- c(1, 3) # WP22448: 1 = yes, personally; 3 = both
WORRIED <- c(1, 2) # very or somewhat worried

d <- load_wave(2023, c(
  "WPID_RANDOM", "PROJWT", "Country", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
  "Gender", "Age", "AgeGroups4", "Education", "EMP_2010", "INCOME_5", "REGION2_IND",
  "WP20720", "WP20721", "WP20722", "WP20723", "WP22213", "WP20726", "WP22214",
  "WP22442", "WP22443", "WP22444", "WP22445", "WP22446", "WP22447", "WP22448",
  "WP22228", "WP22229", "WP23335", "WP23336", "WP23337", "WP23338", "WP23340"
))
d21 <- load_wave(2021, c("PROJWT", "Country", "COUNTRY_ISO3", "GlobalRegion", "EMP_2010", "WP22214", "WP22448"))
d19 <- load_wave(2019, c("PROJWT", "COUNTRY_ISO3", "EMP_2010", "L19"))

# --- Derived variables ---------------------------------------------------------

# Current workforce: EMP_2010 1-5 (out of the workforce, 6, excluded).
WORKFORCE <- 1:5

# Employment type (Charts 2.9, 3.2): part-time merges codes 3 and 5.
d$emptype <- unname(c("1" = 1, "2" = 2, "3" = 3, "5" = 3, "4" = 4)[as.character(d$EMP_2010)])

# Financial resilience (Chart 2.8): less than a week; one to four weeks; a month or more.
d$fin_res <- case_when(d$WP22229 %in% 1 ~ 1, d$WP22229 %in% c(2, 3) ~ 2, d$WP22228 %in% 2 ~ 3, TRUE ~ NA_real_)

# OSH training: 1 = past two years; 2 = trained, not in the past two years or
# not sure when; 3 = never; 9 = DK/refused (kept in the base).
d$train <- case_when(d$WP23338 %in% 1 ~ 1, d$WP23337 %in% 1 ~ 2, d$WP23337 %in% 2 ~ 3,
                     d$WP23337 %in% c(98, 99) ~ 9, TRUE ~ NA_real_)

wf <- d[d$EMP_2010 %in% WORKFORCE, ]
harmed <- wf[wf$WP22448 %in% HARMED, ] # base for reporting (WP23335)

# 2021 trend figures use each country's 2023 region and income group.
first <- d[!duplicated(d$COUNTRY_ISO3), c("COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel")]
idx <- match(d21$COUNTRY_ISO3, first$COUNTRY_ISO3)
d21$region23 <- ifelse(is.na(idx), d21$GlobalRegion, first$GlobalRegion[idx])
d21$income23 <- first$CountryIncomeLevel[idx]
wf21 <- d21[d21$EMP_2010 %in% WORKFORCE, ]

# 2019: "Have you ever been seriously injured while working?" (L19), asked of the employed.
wf19 <- d19[d19$EMP_2010 %in% WORKFORCE, ]

# --- Helpers -------------------------------------------------------------------

harm <- function(df, by = NULL) pct(df, "WP22448", HARMED, by = by)
reported <- function(df, by = NULL) pct(df, "WP23335", 1, by = by)

# Rename a by-group vector with a code -> key mapping, keeping mapped groups only.
named <- function(v, map) {
  keep <- intersect(names(map), names(v))
  setNames(unname(v[keep]), map[keep])
}

# % trained in the past two years / longer ago / never by group: <group>_<category>.
train_table <- function(df, by, groups) {
  tab <- distribution(df, "train", by = by)
  out <- numeric(0)
  for (g in intersect(names(groups), rownames(tab))) {
    for (cc in intersect(names(TRAIN), colnames(tab))) out[paste(groups[[g]], TRAIN[[cc]], sep = "_")] <- tab[g, cc]
  }
  out
}

country_change <- function() {
  r21 <- harm(wf21, "COUNTRY_ISO3")
  r23 <- harm(wf, "COUNTRY_ISO3")
  iso <- intersect(names(r21)[!is.na(r21)], names(r23)[!is.na(r23)])
  data.frame(iso = iso, r21 = unname(r21[iso]), r23 = unname(r23[iso]), diff = unname(r23[iso] - r21[iso]))
}

country_names <- function() {
  first <- d[!duplicated(d$COUNTRY_ISO3), ]
  setNames(first$Country, first$COUNTRY_ISO3)
}

reg <- function(v, keys) setNames(unname(v[RCODE[keys]]), keys)

# --- Executive summary -------------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() harm(wf))
finding(report, "X04", function() sum(wf$PROJWT[wf$WP22448 %in% HARMED]) / 1e6)
finding(report, "X05", function() {
  r <- harm(wf, "CountryIncomeLevel")
  c(low = r[["1"]], lower_middle = r[["2"]])
})
finding(report, "X06", function() reported(harmed))
finding(report, "X07", function() pct(wf, "train", 3))
finding(report, "X08", function() {
  r <- pct(wf, "train", 3, by = "CountryIncomeLevel")
  c(lower_middle = r[["2"]], low = r[["1"]])
})
finding(report, "X09", function() {
  r <- pct(wf, "train", 1, by = "emptype")
  c(ft_employer = r[["1"]], part_time = r[["3"]])
})
finding(report, "X10", function() {
  ag <- wf[wf$WP23340 %in% as.numeric(SCODE[["agriculture"]]), ]
  c(never = pct(ag, "train", 3), past2 = pct(ag, "train", 1))
})
finding(report, "X11", function() pct(wf[wf$WP23340 %in% as.numeric(SCODE[["fishing"]]), ], "train", 3))

EXPOSURE <- c("4" = "not_harmed", "2" = "know_someone", "1" = "personally", "3" = "both") # WP22448
# The worry-about-work question (WP22214) was asked only of the employed.
finding(report, "X12", function() named(pct(wf, "WP22214", WORRIED, by = "WP22448"), EXPOSURE))

# Chart 4.7 / X13 model: logistic regression of reporting harm (WP23335 yes vs
# no) among the harmed current workforce, on training (never = reference),
# sex, age, education, job sector and log GDP per capita (current US$, 2023).
# Unweighted. Rows missing age or GDP are dropped.
odds_ratios <- function() {
  gdp <- read.csv(GDP_FILE, stringsAsFactors = FALSE)
  gdp <- gdp[gdp$indicator == "NY.GDP.PCAP.CD" & gdp$year == 2023, ]
  m <- harmed[harmed$WP23335 %in% c(1, 2) & harmed$train %in% c(1, 2, 3), ]
  m$reported <- as.integer(m$WP23335 == 1)
  m$gdp <- gdp$value[match(m$COUNTRY_ISO3, gdp$iso3)]
  m <- m[!is.na(m$Age) & !is.na(m$gdp), ]
  m$train_f <- relevel(factor(m$train), ref = "3")
  fit <- glm(reported ~ train_f + factor(Gender) + Age + factor(Education) + factor(WP23340) + log(gdp),
             family = binomial, data = m)
  c(past2 = exp(coef(fit)[["train_f1"]]), older = exp(coef(fit)[["train_f2"]]))
}
finding(report, "X13", odds_ratios)

# --- Chapter 2: Workplace harm ------------------------------------------------------

finding(report, "X14", function() c(adults = harm(d21), workforce = harm(wf21)))
finding(report, "X15", function() length(unique(d21$COUNTRY_ISO3)))
finding(report, "X16", function() pct(wf19, "L19", 1))
finding(report, "X17", function() harm(d))
finding(report, "X18", function() pct(d, "EMP_2010", 6))
# Adds those out of the workforce who last worked within the past two years (WP23336 = 1).
finding(report, "X19", function() harm(d[d$EMP_2010 %in% WORKFORCE | (d$EMP_2010 %in% 6 & d$WP23336 %in% 1), ]))
finding(report, "C2_1", function() c("2019" = pct(wf19, "L19", 1), "2021" = harm(wf21), "2023" = harm(wf)))

mode_groups <- function() {
  t <- country_change()
  modes <- read.csv(MODE_FILE, stringsAsFactors = FALSE)
  t <- merge(t, modes, by.x = "iso", by.y = "COUNTRY_ISO3", all.x = TRUE)
  list(changed = t[t$mode_2021 %in% "TEL" & t$mode_2023 %in% "F2F", ],
       unchanged = t[!is.na(t$mode_2021) & !is.na(t$mode_2023) & t$mode_2021 == t$mode_2023, ])
}
finding(report, "X20", function() nrow(mode_groups()$changed))
finding(report, "X21", function() mean(mode_groups()$changed$diff))
finding(report, "X22", function() nrow(mode_groups()$unchanged))
finding(report, "X23", function() mean(mode_groups()$unchanged$diff))

region_trend <- function(region) {
  c("2023" = harm(wf, "GlobalRegion")[[RCODE[[region]]]], "2021" = harm(wf21, "region23")[[RCODE[[region]]]])
}
finding(report, "X24", function() region_trend("southern_asia"))
finding(report, "X25", function() region_trend("southern_europe"))
finding(report, "X26", function() {
  c("2023" = harm(wf, "COUNTRY_ISO3")[["ITA"]], "2021" = harm(wf21, "COUNTRY_ISO3")[["ITA"]],
    "2019" = pct(wf19[wf19$COUNTRY_ISO3 == "ITA", ], "L19", 1))
})
finding(report, "X27", function() {
  r23 <- harm(wf, "GlobalRegion")
  r21 <- harm(wf21, "region23")
  k <- RCODE[c("northern_africa", "latin_america", "northern_western_europe")]
  min(r21[k] - r23[k])
})
finding(report, "X28", function() reg(harm(wf, "GlobalRegion"), c("anz", "northern_america")))
finding(report, "X29", function() harm(wf, "GlobalRegion")[[RCODE[["eastern_asia"]]]])
finding(report, "X30", function() reg(harm(wf, "GlobalRegion"), c("central_western_africa", "southeastern_asia")))
finding(report, "X31", function() {
  iso <- c("CHN", "TWN", "JPN", "MNG", "HKG", "KOR")
  setNames(unname(harm(wf, "COUNTRY_ISO3")[iso]), iso)
})
finding(report, "C2_2", function() {
  r21 <- harm(wf21, "region23")
  r23 <- harm(wf, "GlobalRegion")
  out <- numeric(0)
  for (code in names(REGION)) {
    out[paste0(REGION[[code]], "_2021")] <- r21[[code]]
    out[paste0(REGION[[code]], "_2023")] <- r23[[code]]
  }
  out
})
finding(report, "X32", function() {
  r23 <- harm(wf, "CountryIncomeLevel")
  r21 <- harm(wf21, "income23")
  c(low = r21[["1"]] - r23[["1"]], lower_middle = r21[["2"]] - r23[["2"]])
})
finding(report, "X33", function() sum(abs(country_change()$diff) >= 10))
finding(report, "C2_3", function() {
  r21 <- harm(wf21, "income23")
  r23 <- harm(wf, "CountryIncomeLevel")
  out <- numeric(0)
  for (code in names(INCOME)) {
    out[paste0(INCOME[[code]], "_2021")] <- r21[[code]]
    out[paste0(INCOME[[code]], "_2023")] <- r23[[code]]
  }
  out
})
finding(report, "T2_1", function() {
  t <- country_change()
  t <- t[abs(t$diff) >= 10, ]
  out <- numeric(0)
  for (i in seq_len(nrow(t))) {
    out[paste0(t$iso[i], "_2021")] <- t$r21[i]
    out[paste0(t$iso[i], "_2023")] <- t$r23[i]
    out[paste0(t$iso[i], "_diff")] <- t$diff[i]
  }
  out
})

AFRICA_LABELLED <- c("MAR", "DZA", "LBY", "EGY", "MRT", "MLI", "NER", "TCD", "NGA", "SLE", "LBR", "GHA",
                     "ETH", "SOM", "KEN", "COD", "UGA", "TZA", "COM", "MDG", "NAM", "ZAF")
finding(report, "C2_4", function() {
  r <- harm(wf[wf$GlobalRegion %in% 1:4, ], "COUNTRY_ISO3")
  c(setNames(unname(r[AFRICA_LABELLED]), AFRICA_LABELLED), legend_max = max(r), legend_min = min(r))
})
finding(report, "X34", function() {
  r <- harm(wf, "COUNTRY_ISO3")
  unname(country_names()[names(r)[which.max(r)]])
})
finding(report, "X35", function() c("2023" = harm(wf, "COUNTRY_ISO3")[["SLE"]], "2021" = harm(wf21, "COUNTRY_ISO3")[["SLE"]]))
finding(report, "X36", function() {
  t <- country_change()
  unname(country_names()[t$iso[which.max(t$diff)]])
})
finding(report, "X37", function() {
  iso <- c("SOM", "TCD", "COM", "COD", "LBR", "UGA")
  setNames(unname(harm(wf, "COUNTRY_ISO3")[iso]), iso)
})
finding(report, "X38", function() c("2023" = pct(wf, "WP22214", WORRIED), "2021" = pct(wf21, "WP22214", WORRIED)))
finding(report, "X39", function() reg(pct(wf, "WP22214", WORRIED, by = "GlobalRegion"), c("southern_asia", "central_western_africa")))
finding(report, "X40", function() {
  r <- sort(harm(wf, "COUNTRY_ISO3"), decreasing = TRUE)
  which(names(r) == "IND")
})
finding(report, "X41", function() c("2023" = harm(wf, "COUNTRY_ISO3")[["IND"]], "2021" = harm(wf21, "COUNTRY_ISO3")[["IND"]]))
finding(report, "X42", function() {
  named(harm(wf[wf$COUNTRY_ISO3 == "IND", ], "REGION2_IND"), c("4" = "north", "1" = "central", "2" = "east", "3" = "west", "5" = "south"))
})
finding(report, "C2_5", function() {
  h <- harm(wf, "GlobalRegion")
  w <- pct(wf, "WP22214", WORRIED, by = "GlobalRegion")
  c(setNames(unname(h[names(REGION)]), paste0(REGION, "_harm")), setNames(unname(w[names(REGION)]), paste0(REGION, "_worry")))
})
finding(report, "C2_6", function() named(pct(wf, "WP22214", WORRIED, by = "WP22448"), EXPOSURE))

RISKS <- list(food = c("WP20720", "WP22442"), water = c("WP20721", "WP22443"), crime = c("WP20722", "WP22444"),
              weather = c("WP20723", "WP22445"), traffic = c("WP22213", "WP22446"),
              mental_health = c("WP20726", "WP22447"), work = c("WP22214", "WP22448"))
finding(report, "X43", function() {
  k <- c("traffic", "weather", "work", "water")
  setNames(sapply(k, function(r) pct(wf, RISKS[[r]][1], WORRIED)), k)
})
# Chart 2.7: scatter with no printed values.
finding(report, "C2_7", function() {
  out <- numeric(0)
  for (r in names(RISKS)) {
    out[paste0(r, "_worry")] <- pct(wf, RISKS[[r]][1], WORRIED)
    out[paste0(r, "_experience")] <- pct(wf, RISKS[[r]][2], HARMED)
  }
  out
})

FIN_RES <- c("1" = "less_week", "2" = "week_month", "3" = "month_plus")
finding(report, "X44", function() {
  r <- harm(wf, "Gender")
  c(men = r[["1"]], women = r[["2"]])
})
finding(report, "X45", function() named(harm(wf, "fin_res"), FIN_RES))
finding(report, "C2_8", function() {
  c(global = harm(wf),
    named(harm(wf, "Gender"), c("1" = "men", "2" = "women")),
    named(harm(wf, "AgeGroups4"), c("1" = "age_15_29", "2" = "age_30_49", "3" = "age_50_64", "4" = "age_65plus")),
    named(harm(wf, "Education"), c("1" = "primary", "2" = "secondary", "3" = "tertiary")),
    named(harm(wf, "fin_res"), FIN_RES))
})
EMPTYPE <- c("1" = "ft_employer", "2" = "ft_self", "3" = "part_time", "4" = "unemployed")
finding(report, "X46", function() named(harm(wf, "emptype"), EMPTYPE))
finding(report, "C2_9", function() named(harm(wf, "emptype"), EMPTYPE))
finding(report, "X47", function() {
  k <- c("fishing", "construction", "mining", "market_services", "non_market_services")
  setNames(unname(harm(wf, "WP23340")[SCODE[k]]), k)
})
finding(report, "C2_10", function() c(global = harm(wf), named(harm(wf, "WP23340"), SECTOR)))
# Chart 2.11: scatter with no printed values.
finding(report, "C2_11", function() {
  out <- numeric(0)
  for (code in names(SECTOR)) {
    s <- wf[wf$WP23340 %in% as.numeric(code), ]
    s$lw <- as.numeric(s$WP22229 %in% 1)
    key <- SECTOR[[code]]
    out[paste0(key, "_harm")] <- harm(s)
    out[paste0(key, "_men")] <- pct(s, "Gender", 1)
    out[paste0(key, "_primary")] <- pct(s, "Education", 1)
    out[paste0(key, "_less_week")] <- pct(s, "lw", 1)
  }
  out
})

harm_sector_by <- function(by, map) {
  r <- harm(wf, c("WP23340", by))
  out <- numeric(0)
  for (s in names(SECTOR)) for (g in names(map)) {
    key <- paste(s, g, sep = "_")
    if (key %in% names(r)) out[paste(SECTOR[[s]], map[[g]], sep = "_")] <- r[[key]]
  }
  out
}
finding(report, "X48", function() {
  r <- harm_sector_by("Gender", c("1" = "men", "2" = "women"))
  r[c("market_services_men", "market_services_women", "non_market_services_men", "non_market_services_women")]
})
finding(report, "X49", function() {
  r <- harm_sector_by("AgeGroups4", c("1" = "15_29", "4" = "65plus"))
  r[c("construction_15_29", "construction_65plus", "agriculture_15_29", "agriculture_65plus")]
})
finding(report, "C2_12", function() {
  r <- harm_sector_by("Gender", c("1" = "men", "2" = "women"))
  r[as.vector(rbind(paste0(SECTOR5, "_women"), paste0(SECTOR5, "_men")))]
})
finding(report, "C2_13", function() {
  r <- harm(wf, c("CountryIncomeLevel", "WP23340"))
  out <- numeric(0)
  for (i in names(INCOME)) for (s in SCODE[SECTOR5]) out[paste(INCOME[[i]], SECTOR[[s]], sep = "_")] <- r[[paste(i, s, sep = "_")]]
  out
})

# --- Chapter 3: Reporting workplace harm ---------------------------------------------

# Chart 3.1: scatter with no printed values.
finding(report, "C3_1", function() {
  h <- harm(wf, "GlobalRegion")
  r <- reported(harmed, "GlobalRegion")
  c(setNames(unname(h[names(REGION)]), paste0(REGION, "_harm")), setNames(unname(r[names(REGION)]), paste0(REGION, "_reported")))
})
finding(report, "X50", function() {
  reg(reported(harmed, "GlobalRegion"), c("anz", "northern_america", "northern_western_europe", "southeastern_asia",
                                          "central_western_africa", "southern_africa", "southern_asia", "northern_africa", "central_asia"))
})
finding(report, "X51", function() named(reported(harmed, "Gender"), c("1" = "men", "2" = "women")))
finding(report, "X52", function() named(reported(harmed, "Education"), c("1" = "primary", "2" = "secondary", "3" = "tertiary")))
finding(report, "X53", function() {
  r <- reported(harmed, "INCOME_5")
  c(min = min(r), max = max(r))
})
finding(report, "X54", function() named(reported(harmed, "AgeGroups4"), c("3" = "age_50_64", "1" = "age_15_29", "2" = "age_30_49")))
finding(report, "X55", function() {
  r <- reported(harmed, c("GlobalRegion", "Gender"))
  out <- numeric(0)
  for (g in c("northern_western_europe", "middle_east", "eastern_europe")) {
    out[paste0(g, "_women")] <- r[[paste(RCODE[[g]], 2, sep = "_")]]
    out[paste0(g, "_men")] <- r[[paste(RCODE[[g]], 1, sep = "_")]]
  }
  out
})
finding(report, "X56", function() {
  r <- reported(harmed, c("GlobalRegion", "AgeGroups4"))
  out <- numeric(0)
  for (g in c("northern_western_europe", "southern_asia", "southern_europe", "eastern_europe")) {
    out[paste0(g, "_15_29")] <- r[[paste(RCODE[[g]], 1, sep = "_")]]
    out[paste0(g, "_30_49")] <- r[[paste(RCODE[[g]], 2, sep = "_")]]
  }
  out
})
REP_EMP <- c("1" = "ft_employer", "3" = "part_time", "2" = "self_employed")
finding(report, "X57", function() named(reported(harmed, "emptype"), REP_EMP))
finding(report, "C3_2", function() named(reported(harmed, "emptype"), REP_EMP))
finding(report, "X58", function() setNames(unname(reported(harmed, "WP23340")[SCODE[SECTOR5]]), SECTOR5))
# Chart 3.3: scatter with no printed values.
finding(report, "C3_3", function() {
  h <- harm(wf, "WP23340")
  r <- reported(harmed, "WP23340")
  c(setNames(unname(h[SCODE[SECTOR5]]), paste0(SECTOR5, "_harm")), setNames(unname(r[SCODE[SECTOR5]]), paste0(SECTOR5, "_reported")))
})

# --- Chapter 4: Occupational safety and health training -------------------------------

finding(report, "X59", function() c(ever = pct(wf, "train", c(1, 2)), past2 = pct(wf, "train", 1)))
finding(report, "C4_1", function() named(distribution(wf, "train"), TRAIN))
finding(report, "X60", function() {
  t <- distribution(wf, "train", by = "CountryIncomeLevel")
  c(past2 = t["4", "1"], older = t["4", "2"])
})
finding(report, "C4_2", function() train_table(wf, "CountryIncomeLevel", INCOME))
finding(report, "X61", function() reg(pct(wf, "train", c(1, 2), by = "GlobalRegion"), c("eastern_europe", "anz")))
finding(report, "C4_3", function() train_table(wf, "GlobalRegion", REGION))

by_country <- function() distribution(wf, "train", by = "COUNTRY_ISO3")
finding(report, "X62", function() {
  top <- names(sort(by_country()[, "1"], decreasing = TRUE))[1:10]
  sum(first$GlobalRegion[match(top, first$COUNTRY_ISO3)] == as.numeric(RCODE[["eastern_europe"]]))
})
finding(report, "X63", function() {
  iso <- c("SEN", "MAR", "TGO", "CIV")
  setNames(unname(by_country()[iso, "3"]), iso)
})
finding(report, "T4_1", function() {
  t <- by_country()
  top <- sort(t[, "1"], decreasing = TRUE)[1:10] # % trained in the past two years
  bottom <- sort(t[, "3"], decreasing = TRUE)[1:10] # % never trained
  c(top, bottom)
})
finding(report, "C4_4", function() {
  c(train_table(wf, "INCOME_5", c("1" = "poorest", "2" = "second", "3" = "middle", "4" = "fourth", "5" = "richest")),
    train_table(wf, "Education", c("1" = "primary", "2" = "secondary", "3" = "tertiary")))
})
finding(report, "C4_5", function() train_table(wf, "WP23340", SECTOR))

construction <- wf[wf$WP23340 %in% as.numeric(SCODE[["construction"]]), ]
finding(report, "X64", function() reg(pct(construction, "train", 1, by = "GlobalRegion"), c("anz", "northern_africa")))
finding(report, "X65", function() reg(harm(construction, "GlobalRegion"), c("anz", "northern_africa")))
finding(report, "C4_6", function() train_table(construction, "GlobalRegion", REGION))
finding(report, "X66", function() named(harm(wf, "train"), TRAIN))
finding(report, "C4_7", odds_ratios)

status <- run_report(report)
if (!interactive()) quit(status = status)
