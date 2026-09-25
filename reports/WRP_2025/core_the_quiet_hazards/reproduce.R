# Reproduce World Risk Poll 2026: The quiet hazards: How everyday risk shapes daily life.
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_the_quiet_hazards/reproduce.R
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

# Worry (1 very, 2 somewhat, 3 not) and harm (1 personally, 2 know someone,
# 3 both, 4 no) items. Same names in 2021-2025; 2025 adds the last three.
WORRY <- c(traffic = "WP22213", severe_weather = "WP20723", crime = "WP20722", food = "WP20720",
           mental_health = "WP20726", work = "WP22214", water = "WP20721",
           prolonged_weather = "WP24174", wildfires = "WP24173", air = "WP24175")
HARM <- c(traffic = "WP22446", severe_weather = "WP22445", crime = "WP22444", food = "WP22442",
          mental_health = "WP22447", work = "WP22448", water = "WP22443",
          prolonged_weather = "WP24177", wildfires = "WP24176", air = "WP24178")
WORRY_2019 <- c(severe_weather = "L6D", crime = "L6C", food = "L6A", mental_health = "L6G", water = "L6B")
NEW_2025 <- c("prolonged_weather", "wildfires", "air")
WEATHER <- c("prolonged_weather", "severe_weather", "wildfires", "air")
RISK_LABEL <- c(traffic = "Traffic/roadside accidents", severe_weather = "Severe weather events",
                crime = "Violent crime", food = "Food you eat", mental_health = "Mental health issues",
                work = "Work you do", water = "Water you drink",
                prolonged_weather = "Severe prolonged weather events", wildfires = "Wildfires",
                air = "The air you breathe")
WORRIED <- c(1, 2)
HARMED <- c(1, 3)
DK <- c(98, 99)
WORKFORCE <- 1:5 # EMP_2010: employed full/part time, self-employed or unemployed

REGION <- c("1" = "east_africa", "2" = "cw_africa", "3" = "north_africa", "4" = "southern_africa", "5" = "latam",
            "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
            "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
            "14" = "southern_europe", "15" = "anz")
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = not classified
US_REGION <- c("1" = "northeast", "2" = "midwest", "3" = "south", "4" = "west") # REGION2_USA
HOURS <- c("1" = "lt15", "2" = "h15_29", "3" = "h30_39", "4" = "h40_49", "5" = "h50plus") # Gallup EMP_WORK_HOURS
LE <- c("1" = "thriving", "2" = "struggling", "3" = "suffering")

# Top-of-mind risk (WP22331) labels used in Table 1.1; 98 = don't know or refused.
TOP_LABEL <- c("1" = "Road-related accidents", "2" = "Other transport", "3" = "Crime/violence", "4" = "War/terrorism",
               "5" = "Personal health", "6" = "Drugs, alcohol, smoking", "7" = "COVID-19", "8" = "Mental health",
               "9" = "Financial", "10" = "Economy", "11" = "Politics", "12" = "Technology", "13" = "Water",
               "14" = "Unsafe food", "15" = "Hunger", "16" = "Household accidents", "17" = "Work", "18" = "Pollution",
               "19" = "Climate change/severe weather", "20" = "Non-weather disasters", "21" = "Drowning",
               "22" = "Other", "23" = "Nothing", "98" = "Don't know")

BASE <- c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "WGT", "GlobalRegion", "CountryIncomeLevel", "EMP_2010")
OLD <- setdiff(names(WORRY), NEW_2025)
d25 <- load_wave(2025, unname(c(BASE, "Age", "Gender", "Education", "Urbanicity", "INCOME_5", "WP22331", "WP22252",
                                "WP22228", "WP20719", "REGION2_USA", "worry_index_published", WORRY, HARM)))
# Trends use the countries surveyed in 2025 in every wave.
C25 <- unique(d25$COUNTRY_ISO3)
d23 <- load_wave(2023, unname(c(BASE, "WP22331", WORRY[OLD], HARM[OLD])))
d21 <- load_wave(2021, unname(c(BASE, "WP22331", WORRY[OLD], HARM[OLD])))
d19 <- load_wave(2019, unname(c(BASE, "L3_A", "L19", WORRY_2019)))
d23 <- d23[d23$COUNTRY_ISO3 %in% C25, ]
d21 <- d21[d21$COUNTRY_ISO3 %in% C25, ]
d19 <- d19[d19$COUNTRY_ISO3 %in% C25, ]
WAVES <- list("2019" = d19, "2021" = d21, "2023" = d23, "2025" = d25)

# --- Derived variables -----------------------------------------------------------

# Top-of-mind risk with don't know and refused together (the report's "Don't know").
d25$top_risk <- ifelse(d25$WP22331 %in% 99, 98, d25$WP22331)

# Experience of Harm Index (0-100): share of the 10 harm items answered
# "personally" or "both", for respondents with no don't know or refused answer.
H <- as.matrix(d25[unname(HARM)])
any_dk <- rowSums(H == 98 | H == 99, na.rm = TRUE) > 0
d25$ehi <- ifelse(any_dk, NA, 100 * rowSums(H == 1 | H == 3, na.rm = TRUE) / 10)
# Worry Index (0-100): LRF's published 2025 index.
d25$wi <- 100 * d25$worry_index_published
# Number of the four weather-related hazards personally experienced (footnote ii, p. 26).
HW <- as.matrix(d25[unname(HARM[WEATHER])])
d25$n_weather <- rowSums(HW == 1 | HW == 3, na.rm = TRUE)
d25$us_region <- ifelse(is.na(d25$REGION2_USA), NA, US_REGION[as.character(d25$REGION2_USA)])
WAVES[["2025"]] <- d25

# Current workforce (harm at work); the worry-about-work question is asked only of the employed.
wf <- lapply(WAVES, function(d) d[d$EMP_2010 %in% WORKFORCE, ])

# --- Helpers ---------------------------------------------------------------------

# Round half up to a whole number, as printed (same rule as reproduce.py).
r0 <- function(x) floor(x + 0.5 + 1e-9)

# Sum of the rounded % in each of `codes`: how the report builds 'worried'
# (very + somewhat) and 'personally experienced' (personally + both).
rsum <- function(df, var, codes, by = NULL) {
  if (!is.null(by)) df <- df[stats::complete.cases(df[by]), , drop = FALSE]
  t <- distribution(df, var, by = by)
  if (is.null(by)) {
    return(sum(vapply(codes, function(c) {
      v <- t[as.character(c)]
      if (is.na(v)) 0 else r0(v)
    }, numeric(1))))
  }
  out <- setNames(rep(0, nrow(t)), rownames(t))
  for (c in codes) if (as.character(c) %in% colnames(t)) out <- out + r0(t[, as.character(c)])
  out
}

worried <- function(df, key, by = NULL) rsum(df, WORRY[[key]], WORRIED, by)

# % personally harmed (rounded sum); work among the current workforce.
harmed <- function(y, key, by = NULL) {
  y <- as.character(y)
  rsum(if (key == "work") wf[[y]] else WAVES[[y]], HARM[[key]], HARMED, by)
}
harmed_df <- function(df, key, by = NULL) {
  base <- if (key == "work") df[df$EMP_2010 %in% WORKFORCE, ] else df
  rsum(base, HARM[[key]], HARMED, by)
}
top_risk <- function(df, codes, by = NULL) pct(df, "WP22331", codes, by = by)

# Rename a by-group result with readable keys, dropping unknown groups.
keyed <- function(v, keys) {
  v <- v[names(v) %in% names(keys)]
  setNames(unname(v), unname(keys[names(v)]))
}

# Table 1.1: the three highest-ranked categories on rounded %, tied ones grouped.
top_three <- function(df) {
  shares <- distribution(df, "top_risk")
  rounded <- r0(shares)
  levels <- sort(unique(rounded), decreasing = TRUE)[1:3]
  lapply(levels, function(r) {
    members <- names(shares)[rounded == r]
    list(value = max(shares[members]), label = paste(sort(unname(TOP_LABEL[members]), method = "radix"), collapse = ", "))
  })
}
table_1_1 <- function() {
  regs <- sort(unique(d25$GlobalRegion))
  setNames(lapply(regs, function(r) top_three(d25[d25$GlobalRegion == r, ])), REGION[as.character(regs)])
}

# Gallup Life Evaluation Index groups from the Cantril ladder (WP16 now, WP18 in
# five years): 1 thriving (7+ and 8+), 3 suffering (both 4 or below), 2 struggling.
life_evaluation <- function(df) {
  g <- merge_gallup(df, c("WP16", "WP18"))
  now <- ifelse(g$WP16 <= 10, g$WP16, NA)
  fut <- ifelse(g$WP18 <= 10, g$WP18, NA)
  g$life_eval <- ifelse(is.na(now) | is.na(fut), NA,
                        ifelse(now >= 7 & fut >= 8, 1, ifelse(now <= 4 & fut <= 4, 3, 2)))
  g
}

# Gallup EMP_WORK_HOURS: 1 <15, 2 15-29, 3 30-39, 4 40-49, 5 50+ hours a week (98 no answer).
hours <- function(df) {
  g <- merge_gallup(df, "EMP_WORK_HOURS")
  g$hours <- ifelse(g$EMP_WORK_HOURS <= 5, g$EMP_WORK_HOURS, NA)
  g
}

# A snapshot in reports/external/ (see README); missing files give EXTERNAL_ONLY.
external <- function(name) read.csv(external_path(sprintf("core_the_quiet_hazards__%s.csv", name)), stringsAsFactors = FALSE)

# Split "a_b" group keys from a two-variable `by`.
split_key <- function(k, i) vapply(strsplit(k, "_", fixed = TRUE), `[`, character(1), i)

# --- Executive summary and front matter ------------------------------------------

finding(report, "X01", function() nrow(d25))
finding(report, "X02", function() length(unique(d25$COUNTRY_ISO3)))
finding(report, "X03", function() harmed(2025, "work"))
finding(report, "X04", function() harmed(2023, "work"))
finding(report, "X05", function() harmed(2021, "work"))
finding(report, "X06", function() harmed(2025, "food"))
finding(report, "X07", function() harmed(2025, "water"))
finding(report, "X08", function() top_risk(d25, 1))
finding(report, "X09", function() top_risk(d25, 5))
finding(report, "X10", function() top_risk(d25, 3))
finding(report, "X11", function() length(unique(d25$GlobalRegion)))
finding(report, "X12", function() {
  length(unique(vapply(table_1_1(), function(t) paste(vapply(t, `[[`, character(1), "label"), collapse = " | "), character(1))))
})
finding(report, "X13", function() harmed(2025, "prolonged_weather"))
finding(report, "X14", function() harmed(2025, "severe_weather"))
finding(report, "X15", function() harmed(2025, "air"))
finding(report, "X16", function() harmed(2025, "wildfires"))
finding(report, "X17", function() pct(d25, WORRY[["air"]], 3))

# The 10 countries with the highest % personally harmed (unrounded).
top10_harm <- function(key) head(sort(pct(d25, HARM[[key]], HARMED, by = "COUNTRY_ISO3"), decreasing = TRUE), 10)
finding(report, "X18", function() length(intersect(names(top10_harm("severe_weather")), names(top10_harm("prolonged_weather")))))

# --- Chapter 1: Top risks to safety -----------------------------------------------

finding(report, "X19", function() r0(top_risk(d25, 1)) - r0(top_risk(d23, 1)))
finding(report, "X20", function() top_risk(d25, DK))
finding(report, "X21", function() top_risk(d23, DK))
finding(report, "X22", function() top_risk(d21, DK))
finding(report, "X23", function() r0(top_risk(d25, DK)) - r0(top_risk(d23, DK)))
finding(report, "X24", function() top_risk(d21[d21$COUNTRY_ISO3 == "IND", ], DK))
finding(report, "X25", function() top_risk(d23[d23$COUNTRY_ISO3 == "IND", ], DK))
finding(report, "X26", function() top_risk(d25[d25$COUNTRY_ISO3 == "IND", ], DK))
finding(report, "X27", function() top_risk(d23, 1))
finding(report, "X28", function() top_risk(d21, 1))
finding(report, "X29", function() pct(d19, "L3_A", 1)) # 2019 first answer; code 1 = road-related accidents
finding(report, "X30", function() top_risk(d25, 10))
finding(report, "X31", function() top_risk(d25, 19))
finding(report, "X32", function() top_risk(d25, 9))
finding(report, "X33", function() top_risk(d25, 4))
finding(report, "X34", function() top_risk(d25, 99))
finding(report, "X35", function() top_risk(d25, 98))
finding(report, "X36", function() top_risk(d25[d25$WP22252 %in% 2, ], DK))
finding(report, "X37", function() top_risk(d25[d25$WP22252 %in% 1, ], DK))

road_by_region <- function(y) keyed(top_risk(WAVES[[as.character(y)]], 1, by = "GlobalRegion"), REGION)
finding(report, "X38", function() road_by_region(2025)[["anz"]])
finding(report, "X39", function() road_by_region(2025)[["northern_america"]])
road_region_change <- function(region) r0(road_by_region(2025)[[region]]) - r0(road_by_region(2023)[[region]])
finding(report, "X40", function() road_region_change("northern_america"))
finding(report, "X41", function() road_region_change("eastern_asia"))
finding(report, "X42", function() road_region_change("southern_asia"))
finding(report, "X43", function() sum(vapply(table_1_1(), function(t) any(grepl("Road-related", vapply(t, `[[`, character(1), "label"))), logical(1))))
finding(report, "X44", function() sum(vapply(table_1_1(), function(t) t[[1]]$label == "Road-related accidents", logical(1))))
finding(report, "X45", function() sum(vapply(table_1_1(), function(t) grepl("Personal health", t[[2]]$label), logical(1))))
region_top_risk <- function(region, codes) keyed(top_risk(d25, codes, by = "GlobalRegion"), REGION)[[region]]
finding(report, "X46", function() region_top_risk("eastern_asia", 19))
finding(report, "X47", function() region_top_risk("eastern_europe", 4))
finding(report, "X48", function() region_top_risk("anz", 8))
finding(report, "X49", function() region_top_risk("northern_america", 11))

CHART_1_1 <- list(dk = DK, road = 1, health = 5, crime = 3, economy = 10, climate = 19, nothing = 23,
                  financial = 9, other = 22, war = 4, work = 17, technology = 12, environment = 18)
finding(report, "C1_1", function() {
  out <- numeric(0)
  for (key in names(CHART_1_1)) {
    v <- top_risk(d25, CHART_1_1[[key]])
    out[key] <- v
    out[paste0(key, "_change")] <- r0(v) - r0(top_risk(d23, CHART_1_1[[key]])) # rounded, as printed
  }
  out
})
finding(report, "C1_2", function() {
  out <- numeric(0)
  for (y in c(2021, 2023, 2025)) {
    v <- road_by_region(y)
    out[paste(names(v), y, sep = "_")] <- v
  }
  out
})
finding(report, "T1_1", function() {
  tt <- table_1_1()
  out <- numeric(0)
  for (reg in names(tt)) for (i in 1:3) out[paste(reg, i, sep = "_")] <- tt[[reg]][[i]]$value
  out
})
finding(report, "T1_1", function() {
  tt <- table_1_1()
  out <- character(0)
  for (reg in names(tt)) for (i in 1:3) out[paste(reg, i, "risk", sep = "_")] <- tt[[reg]][[i]]$label
  out
})

finding(report, "X50", function() r0(top_risk(d25, 3)) - r0(top_risk(d23, 3)))
crime_latam <- function(y) keyed(top_risk(WAVES[[as.character(y)]], 3, by = "GlobalRegion"), REGION)[["latam"]]
finding(report, "X51", function() crime_latam(2025))
finding(report, "X52", function() crime_latam(2023))
finding(report, "X53", function() r0(crime_latam(2025)) - r0(crime_latam(2023)))
finding(report, "C1_3", function() {
  out <- numeric(0)
  for (y in c(2021, 2023, 2025)) {
    out[paste0("latam_", y)] <- crime_latam(y)
    out[paste0("global_", y)] <- top_risk(WAVES[[as.character(y)]], 3)
  }
  out
})

# Table 1.2: the 13 largest national falls in % naming crime and violence, 2023-2025.
crime_declines <- function() {
  a <- top_risk(d23, 3, by = "COUNTRY_ISO3")
  b <- top_risk(d25, 3, by = "COUNTRY_ISO3")
  iso <- intersect(names(a), names(b))
  t <- data.frame(iso = iso, y2023 = a[iso], y2025 = b[iso])
  t$gap <- t$y2023 - t$y2025
  head(t[order(-t$gap), ], 13)
}
finding(report, "T1_2", function() {
  t <- crime_declines()
  out <- numeric(0)
  for (i in seq_len(nrow(t))) {
    out[paste0(t$iso[i], "_2023")] <- t$y2023[i]
    out[paste0(t$iso[i], "_2025")] <- t$y2025[i]
    out[paste0(t$iso[i], "_gap")] <- r0(t$y2023[i]) - r0(t$y2025[i]) # rounded figures, as printed
  }
  out
})
finding(report, "T1_2", function() c(countries = paste(sort(crime_declines()$iso, method = "radix"), collapse = " ")))

region_of <- function(d) {
  first <- d[!duplicated(d$COUNTRY_ISO3), ]
  setNames(first$GlobalRegion, first$COUNTRY_ISO3)
}
finding(report, "X54", function() sum(region_of(d25)[crime_declines()$iso] == 5))
latam_in_top10_crime <- function(d) {
  top <- head(sort(top_risk(d, 3, by = "COUNTRY_ISO3"), decreasing = TRUE), 10)
  sum(region_of(d)[names(top)] == 5)
}
finding(report, "X55", function() latam_in_top10_crime(d25))
finding(report, "X56", function() latam_in_top10_crime(d23))
finding(report, "X57", function() top_risk(d25, 3, by = "COUNTRY_ISO3")[c("ECU", "CHL", "CRI", "MEX", "PER", "COL", "ARG")])

CHART_1_4 <- list(road = 1, health = 5, economy = c(9, 10)) # economy includes financial
finding(report, "C1_4", function() {
  g <- life_evaluation(d25)
  out <- numeric(0)
  for (risk in names(CHART_1_4)) {
    r <- pct(g, "WP22331", CHART_1_4[[risk]], by = c("CountryIncomeLevel", "life_eval"))
    inc <- split_key(names(r), 1)
    le <- split_key(names(r), 2)
    keep <- inc %in% names(INCOME) & le %in% names(LE)
    out[paste(INCOME[inc[keep]], risk, LE[le[keep]], sep = "_")] <- r[keep]
  }
  out
})
finding(report, "X58", function() {
  g <- life_evaluation(d25)
  pct(g[g$CountryIncomeLevel %in% 2 & g$life_eval %in% 3, ], "WP22331", c(9, 10))
})

# --- Chapter 2: Trends in everyday risk --------------------------------------------

finding(report, "X59", function() sum(vapply(names(WORRY), function(k) worried(d25, k) >= 50, logical(1))))
finding(report, "X60", function() worried(d25, "work"))
# Chart 2.1 is a scatter with no printed values: worry and personal harm for the 10 risks.
finding(report, "C2_1", function() {
  c(setNames(vapply(names(WORRY), function(k) worried(d25, k), numeric(1)), paste0("worry_", names(WORRY))),
    setNames(vapply(names(HARM), function(k) harmed(2025, k), numeric(1)), paste0("harm_", names(HARM))))
})

# Table 2.1: % worried / % personally harmed, unrounded, by region.
ratios <- function() {
  m <- sapply(names(WORRY), function(k) {
    w <- pct(d25, WORRY[[k]], WORRIED, by = "GlobalRegion")
    h <- pct(if (k == "work") wf[["2025"]] else d25, HARM[[k]], HARMED, by = "GlobalRegion")
    w[names(REGION)] / h[names(REGION)]
  })
  rownames(m) <- REGION
  m
}
finding(report, "T2_1", function() {
  m <- ratios()
  c(setNames(apply(m, 1, max), paste0(rownames(m), "_max")), setNames(apply(m, 1, min), paste0(rownames(m), "_min")))
})
finding(report, "T2_1", function() {
  m <- ratios()
  c(setNames(unname(RISK_LABEL[colnames(m)[apply(m, 1, which.max)]]), paste0(rownames(m), "_max_risk")),
    setNames(unname(RISK_LABEL[colnames(m)[apply(m, 1, which.min)]]), paste0(rownames(m), "_min_risk")))
})
finding(report, "X61", function() {
  m <- ratios()
  sum(colnames(m)[apply(m, 1, which.max)] == "wildfires")
})
finding(report, "X62", function() {
  max(vapply(c("traffic", "crime", "food", "work"), function(k) abs(pct(d25, WORRY[[k]], WORRIED) - pct(d23, WORRY[[k]], WORRIED)), numeric(1)))
})

worry_trend <- function(key, y) {
  if (y == 2019) return(if (key %in% names(WORRY_2019)) rsum(d19, WORRY_2019[[key]], WORRIED) else NA)
  if (y < 2025 && key %in% NEW_2025) return(NA)
  worried(WAVES[[as.character(y)]], key)
}
finding(report, "X63", function() worry_trend("severe_weather", 2025) - worry_trend("severe_weather", 2023))
finding(report, "X64", function() worry_trend("water", 2025) - worry_trend("water", 2023))
finding(report, "X65", function() worried(d25, "prolonged_weather"))
finding(report, "X66", function() {
  w <- vapply(names(WORRY), function(k) worried(d25, k), numeric(1))
  1 + sum(w > w[["prolonged_weather"]])
})
finding(report, "X67", function() worried(d25, "wildfires"))
finding(report, "X68", function() worried(d25, "air"))
finding(report, "X69", function() worried(d25, "severe_weather"))
finding(report, "C2_2", function() {
  out <- numeric(0)
  for (key in names(WORRY)) for (y in c(2019, 2021, 2023, 2025)) {
    v <- worry_trend(key, y)
    if (!is.na(v)) out[paste(key, y, sep = "_")] <- v
  }
  out
})
finding(report, "X70", function() harmed(2023, "severe_weather"))
finding(report, "X71", function() harmed(2021, "severe_weather"))
finding(report, "X72", function() harmed(2025, "traffic"))
finding(report, "X73", function() harmed(2025, "crime"))
finding(report, "C2_3", function() {
  out <- numeric(0)
  for (k in names(HARM)) for (y in c(2021, 2023, 2025)) {
    if (y == 2025 || !(k %in% NEW_2025)) out[paste(k, y, sep = "_")] <- harmed(y, k)
  }
  out
})

country_ehi <- function() wmean(d25, "ehi", by = "COUNTRY_ISO3")
finding(report, "X74", function() sum(country_ehi() >= 20))
finding(report, "X75", function() {
  e <- country_ehi()
  min(e[e >= 20])
})
finding(report, "X76", function() wmean(d25, "ehi", weight = "WGT")) # within-country weight; PROJWT gives 13.9
# Chart 2.4 is a scatter with no printed values: country Worry and Experience of Harm Index.
finding(report, "C2_4", function() {
  wi <- wmean(d25, "wi", by = "COUNTRY_ISO3")
  e <- country_ehi()
  c(setNames(wi, paste0(names(wi), "_worry")), setNames(e, paste0(names(e), "_experience")))
})

SIX <- c("CHN", "IND", "PHL", "TCD", "COM", "SOM")
# Chart 2.5: % personally harmed (rounded sum) for each risk in the six countries.
six_profiles <- function() {
  d <- d25[d25$COUNTRY_ISO3 %in% SIX, ]
  sapply(names(HARM), function(k) harmed_df(d, k, by = "COUNTRY_ISO3")[SIX])
}
finding(report, "C2_5", function() {
  p <- six_profiles()
  rownames(p) <- SIX
  glob <- c(severe_weather = harmed(2025, "severe_weather"), prolonged_weather = harmed(2025, "prolonged_weather"))
  c(CHN_severe_weather = p["CHN", "severe_weather"], CHN_work = p["CHN", "work"],
    IND_min = min(p["IND", ]), IND_max = max(p["IND", ]),
    PHL_severe_weather = p["PHL", "severe_weather"], PHL_prolonged_weather = p["PHL", "prolonged_weather"],
    TCD_severe_weather = p["TCD", "severe_weather"], COM_mental_health = p["COM", "mental_health"],
    COM_prolonged_weather = p["COM", "prolonged_weather"], SOM_work = p["SOM", "work"],
    PHL_vs_global = min(p["PHL", names(glob)] / glob))
})
finding(report, "C2_5", function() {
  p <- six_profiles()
  rownames(p) <- SIX
  c(highest_work = SIX[which.max(p[, "work"])], highest_mental = SIX[which.max(p[, "mental_health"])])
})

know_someone <- function(key) pct(if (key == "work") wf[["2025"]] else d25, HARM[[key]], 2)
finding(report, "C2_6", function() {
  out <- numeric(0)
  for (k in names(HARM)) {
    out[paste0(k, "_personal")] <- harmed(2025, k)
    out[paste0(k, "_know")] <- know_someone(k)
  }
  out
})
finding(report, "X77", function() know_someone("prolonged_weather"))
finding(report, "X78", function() know_someone("traffic"))
finding(report, "X79", function() r0(know_someone("traffic")) / harmed(2025, "traffic"))
finding(report, "X80", function() wmean(d25[d25$CountryIncomeLevel %in% 2, ], "ehi"))
finding(report, "C2_7", function() {
  g <- life_evaluation(d25)
  e <- wmean(g, "ehi", by = c("CountryIncomeLevel", "life_eval"))
  w <- wmean(g, "wi", by = c("CountryIncomeLevel", "life_eval"))
  out <- numeric(0)
  for (k in names(e)) {
    inc <- split_key(k, 1)
    le <- split_key(k, 2)
    if (inc %in% names(INCOME) && le %in% names(LE)) {
      key <- paste(INCOME[[inc]], LE[[le]], sep = "_")
      out[paste0(key, "_experience")] <- e[[k]]
      out[paste0(key, "_worry")] <- w[[k]]
      out[paste0(key, "_gap")] <- r0(w[[k]]) - r0(e[[k]])
    }
  }
  out
})

# --- Chapter 3: Workplace harm ----------------------------------------------------

finding(report, "X81", function() {
  w <- wf[["2025"]]
  sum(w$PROJWT * (w$WP22448 %in% HARMED)) / 1e6
})
finding(report, "C3_1", function() {
  # 2019: ever seriously injured while working (asked of the employed)
  c("2019" = pct(d19, "L19", 1), "2021" = harmed(2021, "work"), "2023" = harmed(2023, "work"), "2025" = harmed(2025, "work"))
})
work_harm_by <- function(var, keys) keyed(harmed(2025, "work", by = var), keys)
finding(report, "C3_2", function() {
  c(work_harm_by("Education", c("1" = "primary", "2" = "secondary", "3" = "tertiary")),
    work_harm_by("WP22228", c("1" = "lt_month", "2" = "month_plus")))
})
finding(report, "X82", function() work_harm_by("WP22228", c("1" = "x"))[["x"]])
finding(report, "X83", function() work_harm_by("WP22228", c("2" = "x"))[["x"]])
finding(report, "X84", function() work_harm_by("Education", c("1" = "x"))[["x"]])
finding(report, "X85", function() work_harm_by("Education", c("2" = "x"))[["x"]])
finding(report, "X86", function() work_harm_by("Education", c("3" = "x"))[["x"]])

work_by_income <- function() {
  list(experience = keyed(harmed(2025, "work", by = "CountryIncomeLevel"), INCOME),
       worry = keyed(worried(d25, "work", by = "CountryIncomeLevel"), INCOME))
}
finding(report, "C3_3", function() {
  x <- work_by_income()
  out <- numeric(0)
  for (inc in INCOME) {
    out[paste0(inc, "_experience")] <- x$experience[[inc]]
    out[paste0(inc, "_worry")] <- x$worry[[inc]]
    out[paste0(inc, "_gap")] <- x$worry[[inc]] - x$experience[[inc]]
  }
  out
})
work_income_value <- function(inc, what) {
  x <- work_by_income()
  if (what == "gap") x$worry[[inc]] - x$experience[[inc]] else x[[what]][[inc]]
}
for (spec in list(c("X87", "low", "experience"), c("X88", "low", "worry"), c("X89", "low", "gap"),
                  c("X90", "lower_middle", "experience"), c("X91", "upper_middle", "experience"),
                  c("X92", "lower_middle", "worry"), c("X93", "upper_middle", "worry"),
                  c("X94", "high", "experience"), c("X95", "high", "worry"), c("X96", "high", "gap"))) {
  local({
    s <- spec
    finding(report, s[1], function() work_income_value(s[2], s[3]))
  })
}
finding(report, "X97", function() pct(d25, "EMP_2010", 6))
finding(report, "X98", function() pct(d25, "EMP_2010", WORKFORCE))

work_harm_region <- function(y) keyed(harmed(y, "work", by = "GlobalRegion"), REGION)
finding(report, "X99", function() work_harm_region(2023)[["eastern_asia"]])
finding(report, "X100", function() work_harm_region(2025)[["eastern_asia"]])
finding(report, "X101", function() work_harm_region(2023)[["nw_europe"]])
finding(report, "X102", function() work_harm_region(2025)[["nw_europe"]])
finding(report, "X103", function() {
  a <- work_harm_region(2021)
  b <- work_harm_region(2025)
  sum(b > a[names(b)])
})
finding(report, "X104", function() {
  a <- work_harm_region(2023)
  b <- work_harm_region(2025)
  r <- c("southern_asia", "southeastern_asia", "southern_africa", "middle_east", "anz", "northern_america")
  setNames(b[r] - a[r], r)
})
finding(report, "C3_4", function() {
  out <- numeric(0)
  for (y in c(2021, 2023, 2025)) {
    v <- work_harm_region(y)
    out[paste(names(v), y, sep = "_")] <- v
  }
  out
})

# % harmed (workforce) or worried (employees) by hours band, as rounded sums.
hours_by <- function(df, what, by = "hours") {
  if (what == "experience") rsum(df[df$EMP_2010 %in% WORKFORCE, ], "WP22448", HARMED, by = by)
  else rsum(df, "WP22214", WORRIED, by = by)
}
finding(report, "C3_5", function() {
  g <- hours(d25)
  out <- numeric(0)
  for (scope in c("global", "high")) {
    df <- if (scope == "global") g else g[g$CountryIncomeLevel %in% 4, ]
    for (what in c("experience", "worry")) {
      v <- hours_by(df, what)
      out[paste(scope, what, HOURS[names(v)], sep = "_")] <- v
    }
  }
  out
})
high_income_hours <- function(what) {
  g <- hours(d25)
  hours_by(g[g$CountryIncomeLevel %in% 4, ], what)
}
finding(report, "X105", function() min(high_income_hours("worry")[c("1", "2", "3", "4")]))
finding(report, "X106", function() max(high_income_hours("worry")[c("1", "2", "3", "4")]))
finding(report, "X107", function() high_income_hours("worry")[["5"]])
finding(report, "X108", function() high_income_hours("experience")[["5"]])
finding(report, "X109", function() {
  g <- hours(d25)
  w <- g[g$EMP_2010 %in% WORKFORCE, ]
  out <- vapply(c("4", "5", "3", "2", "1"), function(h) pct(w, "hours", as.numeric(h)), numeric(1))
  names(out) <- HOURS[names(out)]
  c(out, h40plus = rsum(w, "hours", c(4, 5)))
})
finding(report, "X110", function() {
  g <- hours(d25)
  w <- g[g$CountryIncomeLevel %in% 4 & g$EMP_2010 %in% WORKFORCE, ]
  r <- pct(w, "INCOME_5", 5, by = "hours")
  setNames(r[c("5", "3", "1")], HOURS[c("5", "3", "1")])
})

# Logistic regressions of worry about harm at work, employees in high-income
# countries. Unweighted. Hours band reference 40-49; model 2 adds worry about
# mental health issues (reference: not worried). Same specification as Python.
work_worry_models <- function() {
  g <- hours(d25)
  m <- g[g$CountryIncomeLevel %in% 4 & g$WP22214 %in% 1:3, ]
  m$worried <- as.numeric(m$WP22214 %in% WORRIED)
  m$Education[m$Education %in% 9] <- NA
  m$Urbanicity[m$Urbanicity %in% 9] <- NA
  m$Gender[!(m$Gender %in% 1:2)] <- NA
  m$mental <- ifelse(m$WP20726 %in% 1:3, m$WP20726, NA)
  m$hours_f <- relevel(factor(m$hours), ref = "4")
  m$mental_f <- relevel(factor(m$mental), ref = "3")
  f1 <- worried ~ hours_f + Age + factor(Gender) + factor(Education) + factor(INCOME_5) + factor(EMP_2010) + factor(Urbanicity)
  m1 <- glm(f1, family = binomial, data = m[stats::complete.cases(m[c("hours", "Age", "Gender", "Education", "INCOME_5", "Urbanicity")]), ])
  m2 <- glm(update(f1, . ~ . + mental_f), family = binomial,
            data = m[stats::complete.cases(m[c("hours", "Age", "Gender", "Education", "INCOME_5", "Urbanicity", "mental")]), ])
  list(coef(m1), coef(m2))
}
odds_pct <- function(b) 100 * (exp(b) - 1)
finding(report, "X111", function() odds_pct(work_worry_models()[[1]][["hours_f5"]]))
finding(report, "X112", function() odds_pct(-work_worry_models()[[1]][["hours_f1"]]))
finding(report, "X113", function() odds_pct(work_worry_models()[[2]][["mental_f2"]]))
finding(report, "X114", function() odds_pct(work_worry_models()[[2]][["mental_f1"]]))

hi_worry_wellbeing_hours <- function() {
  g <- life_evaluation(hours(d25))
  g <- g[g$CountryIncomeLevel %in% 4, ]
  g$thriving <- ifelse(g$life_eval %in% 1, 1, ifelse(g$life_eval %in% 2:3, 2, NA))
  rsum(g, "WP22214", WORRIED, by = c("thriving", "hours"))
}
finding(report, "C3_6", function() {
  r <- hi_worry_wellbeing_hours()
  t <- split_key(names(r), 1)
  h <- split_key(names(r), 2)
  setNames(r, paste(ifelse(t == "1", "thriving", "not_thriving"), HOURS[h], sep = "_"))
})
finding(report, "X115", function() hi_worry_wellbeing_hours()[["2_5"]])
finding(report, "X116", function() hi_worry_wellbeing_hours()[["1_5"]])

# --- Chapter 4: Weather-related risks ----------------------------------------------

finding(report, "C4_1", function() {
  out <- numeric(0)
  for (k in WEATHER) {
    out[paste0(k, "_very")] <- pct(d25, WORRY[[k]], 1)
    out[paste0(k, "_somewhat")] <- pct(d25, WORRY[[k]], 2)
    out[paste0(k, "_not")] <- pct(d25, WORRY[[k]], 3)
  }
  out
})
finding(report, "X117", function() {
  c(any = pct(d25, "n_weather", 1:4), one = pct(d25, "n_weather", 1), two = pct(d25, "n_weather", 2),
    three = pct(d25, "n_weather", 3), four = pct(d25, "n_weather", 4))
})

PROXIMITY <- c("4" = "no", "2" = "know", "1" = "personal", "3" = "both") # harm answer groups
# % very (1) or somewhat (2) worried by harm answer; worry DK stays in the base.
worry_by_proximity <- function(key, level) keyed(pct(d25, WORRY[[key]], level, by = HARM[[key]]), PROXIMITY)
finding(report, "C4_2", function() {
  out <- numeric(0)
  for (k in WEATHER) for (lvl in c("very", "somewhat")) {
    v <- worry_by_proximity(k, if (lvl == "very") 1 else 2)
    out[paste(k, names(v), lvl, sep = "_")] <- v
  }
  out
})
finding(report, "X118", function() worry_by_proximity("wildfires", 1)[["personal"]])
finding(report, "X119", function() worry_by_proximity("prolonged_weather", 1)[["personal"]])
finding(report, "X120", function() worry_by_proximity("wildfires", 2)[["personal"]])
finding(report, "X121", function() worry_by_proximity("prolonged_weather", 2)[["personal"]])
finding(report, "X122", function() worry_by_proximity("wildfires", 1)[["both"]])
finding(report, "X123", function() worry_by_proximity("prolonged_weather", 1)[["both"]])
finding(report, "C4_3", function() {
  out <- numeric(0)
  for (k in WEATHER) {
    v <- keyed(harmed(2025, k, by = "CountryIncomeLevel"), INCOME)
    out[paste(k, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "X124", function() {
  vapply(setNames(WEATHER, WEATHER), function(k) keyed(harmed(2025, k, by = "CountryIncomeLevel"), INCOME)[["high"]], numeric(1))
})

# Countries with at least 2% of land burned in 2025 (GWIS snapshot), with harm and worry.
wildfire_countries <- function() {
  gw <- external("gwis_burned_area")
  burned <- setNames(gw$burned_pct, gw$iso3)
  harm <- pct(d25, HARM[["wildfires"]], HARMED, by = "COUNTRY_ISO3")
  worry <- pct(d25, WORRY[["wildfires"]], WORRIED, by = "COUNTRY_ISO3")
  t <- data.frame(iso = names(harm), harm = harm, worry = worry[names(harm)], burned = burned[names(harm)])
  t[!is.na(t$burned) & t$burned >= 2, ]
}
finding(report, "X125", function() nrow(wildfire_countries()))
finding(report, "X126", function() {
  t <- wildfire_countries()
  cor(t$harm, t$worry)
})
# Chart 4.4 is a scatter with no printed values.
finding(report, "C4_4", function() {
  t <- wildfire_countries()
  c(setNames(t$harm, paste0(t$iso, "_harm")), setNames(t$worry, paste0(t$iso, "_worry")))
})

wildfire_worry_by_country <- function() worried(d25, "wildfires", by = "COUNTRY_ISO3")
top13_wildfire <- function() {
  rs <- wildfire_worry_by_country()
  names(rs)[rs >= sort(rs, decreasing = TRUE)[13]] # top 13, ties kept
}
finding(report, "C4_5", function() {
  top <- top13_wildfire()
  t <- distribution(d25[d25$COUNTRY_ISO3 %in% top, ], WORRY[["wildfires"]], by = "COUNTRY_ISO3")
  c(setNames(t[top, "1"], paste0(top, "_very")), setNames(t[top, "2"], paste0(top, "_somewhat")))
})
finding(report, "C4_5", function() c(countries = paste(sort(top13_wildfire(), method = "radix"), collapse = " ")))
finding(report, "X127", function() wildfire_worry_by_country()[c("GRC", "PRT", "MNG", "CYP", "TUR", "MWI", "KOR", "BRA", "PHL", "BOL")])
finding(report, "X128", function() wildfire_worry_by_country()[["USA"]])
finding(report, "X129", function() {
  rs <- wildfire_worry_by_country()
  sum(rs >= rs[["USA"]]) # last place among countries tied on the rounded figure
})
us_worry <- function(key) worried(d25[d25$COUNTRY_ISO3 == "USA", ], key, by = "us_region")
finding(report, "X130", function() us_worry("wildfires")[["west"]])
finding(report, "X131", function() us_worry("wildfires")[["northeast"]])
finding(report, "X132", function() us_worry("wildfires")[["south"]])
finding(report, "X133", function() us_worry("wildfires")[["midwest"]])
finding(report, "X134", function() {
  w <- us_worry("wildfires")
  w[["west"]] / max(w[names(w) != "west"])
})
finding(report, "C4_6", function() {
  out <- numeric(0)
  for (k in WEATHER) {
    v <- us_worry(k)
    out[paste(k, names(v), sep = "_")] <- v
  }
  out
})

# Chart 4.7 is a scatter with no printed values. Needs the Gallup item "In the
# city or area where you live, are you satisfied or dissatisfied with the
# quality of air?" (placeholder name; 1 = satisfied).
finding(report, "C4_7", function() {
  g <- merge_gallup(d25, "GWP_AIR_QUALITY_SATISFACTION")
  s <- pct(g, "GWP_AIR_QUALITY_SATISFACTION", 1, by = "COUNTRY_ISO3")
  w <- pct(g, WORRY[["air"]], WORRIED, by = "COUNTRY_ISO3")
  c(setNames(s, paste0(names(s), "_satisfied")), setNames(w, paste0(names(w), "_worry")))
})

DEGURBA <- c("1" = "cities", "2" = "towns", "3" = "rural") # placeholder Gallup degree-of-urbanisation item
air_worry_by_degurba <- function(by) {
  g <- merge_gallup(d25, "GWP_DEGURBA")
  rsum(g, WORRY[["air"]], WORRIED, by = c(by, "GWP_DEGURBA"))
}
finding(report, "C4_8", function() {
  r <- air_worry_by_degurba("GlobalRegion")
  reg <- split_key(names(r), 1)
  u <- split_key(names(r), 2)
  keep <- reg %in% names(REGION) & u %in% names(DEGURBA)
  setNames(r[keep], paste(REGION[reg[keep]], DEGURBA[u[keep]], sep = "_"))
})
urban_rural_gaps <- function() {
  r <- air_worry_by_degurba("COUNTRY_ISO3")
  iso <- split_key(names(r), 1)
  u <- split_key(names(r), 2)
  t <- data.frame(iso = sort(unique(iso), method = "radix"))
  for (k in names(DEGURBA)) t[[k]] <- r[paste(t$iso, k, sep = "_")]
  t$gap <- t[["1"]] - t[["3"]]
  t <- t[!is.na(t$gap), ]
  head(t[order(-t$gap, t$iso, method = "radix"), ], 10) # ties: ISO3 order
}
BALKANS <- c("ALB", "BIH", "BGR", "HRV", "GRC", "XKX", "MNE", "MKD", "SRB", "SVN")
finding(report, "X135", function() sum(region_of(d25)[urban_rural_gaps()$iso] == 7))
finding(report, "X136", function() sum(urban_rural_gaps()$iso %in% BALKANS))
finding(report, "T4_1", function() {
  t <- urban_rural_gaps()
  out <- numeric(0)
  for (i in seq_len(nrow(t))) for (k in names(DEGURBA)) out[paste(t$iso[i], DEGURBA[[k]], sep = "_")] <- t[[k]][i]
  out
})

# Chart 4.9: country-level harm and worry by how far PM2.5 exceeds the WHO guideline (5 ug/m3).
pm25_bands <- function() {
  pm <- external("worldbank_pm25")
  pm <- setNames(pm$value, pm$iso3)
  e <- pct(d25, HARM[["air"]], HARMED, by = "COUNTRY_ISO3")
  t <- data.frame(experience = e, worry = pct(d25, WORRY[["air"]], WORRIED, by = "COUNTRY_ISO3")[names(e)],
                  ratio = pm[names(e)] / 5)
  t <- t[stats::complete.cases(t), ]
  t$band <- cut(t$ratio, c(0, 2, 3, 5, 7, Inf), right = FALSE, labels = c("lt2x", "x2_3", "x3_5", "x5_7", "x7plus"))
  t
}
finding(report, "C4_9", function() {
  t <- pm25_bands()
  out <- numeric(0)
  for (m in c("experience", "worry")) {
    med <- tapply(t[[m]], t$band, median)
    med <- med[!is.na(med)]
    out[paste(m, names(med), sep = "_")] <- med
  }
  out
})
finding(report, "X137", function() {
  t <- pm25_bands()
  median(t$experience[t$band %in% c("x2_3", "x3_5", "x5_7")])
})

finding(report, "T4_2", function() {
  out <- numeric(0)
  for (k in c("severe_weather", "prolonged_weather")) {
    top <- names(top10_harm(k))
    rs <- harmed_df(d25[d25$COUNTRY_ISO3 %in% top, ], k, by = "COUNTRY_ISO3")
    out[paste(k, names(rs), sep = "_")] <- rs
  }
  out
})
finding(report, "T4_2", function() {
  ks <- c("severe_weather", "prolonged_weather")
  setNames(vapply(ks, function(k) paste(sort(names(top10_harm(k)), method = "radix"), collapse = " "), character(1)), paste0(ks, "_top10"))
})
finding(report, "X138", function() harmed_df(d25[d25$COUNTRY_ISO3 == "PHL", ], "severe_weather"))
finding(report, "X139", function() pct(d25, WORRY[["prolonged_weather"]], 1))
finding(report, "X140", function() pct(d25, WORRY[["prolonged_weather"]], 2))
no_threat_top5 <- function() head(sort(pct(d25, "WP20719", 3, by = "COUNTRY_ISO3"), decreasing = TRUE), 5)
finding(report, "X141", function() unname(tail(no_threat_top5(), 1)))
finding(report, "X142", function() sum(names(no_threat_top5()) %in% c("BHR", "SAU", "ARE")))

least_worried_prolonged <- function() {
  rs <- worried(d25, "prolonged_weather", by = "COUNTRY_ISO3")
  iso <- names(rs)
  head(iso[order(rs, iso, method = "radix")], 10) # ties: ISO3 order
}
finding(report, "C4_10", function() {
  t <- distribution(d25, WORRY[["prolonged_weather"]], by = "COUNTRY_ISO3")
  g <- distribution(d25, WORRY[["prolonged_weather"]])
  top <- least_worried_prolonged()
  c(global_very = g[["1"]], global_somewhat = g[["2"]],
    setNames(t[top, "1"], paste0(top, "_very")), setNames(t[top, "2"], paste0(top, "_somewhat")))
})
finding(report, "C4_10", function() c(countries = paste(sort(least_worried_prolonged(), method = "radix"), collapse = " ")))

status <- run_report(report)
if (!interactive()) quit(status = status)
