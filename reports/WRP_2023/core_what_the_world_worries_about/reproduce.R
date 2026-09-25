# Reproduce World Risk Poll 2024 report: What the World Worries About.
#
# Run from the repository root:
#   Rscript reports/WRP_2023/core_what_the_world_worries_about/reproduce.R
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
  "1" = "east_africa", "2" = "cw_africa", "3" = "north_africa", "4" = "south_africa", "5" = "latam",
  "6" = "north_america", "7" = "central_asia", "8" = "east_asia", "9" = "se_asia", "10" = "south_asia",
  "11" = "middle_east", "12" = "east_europe", "13" = "nw_europe", "14" = "south_europe", "15" = "anz"
)
# Risk -> 2019 worry item, 2021/2023 worry item, 2021/2023 experience item.
# Traffic and work were not asked in 2019; 2019 experience items are not used.
RISKS <- list(
  food = c("L6A", "WP20720", "WP22442"), water = c("L6B", "WP20721", "WP22443"),
  crime = c("L6C", "WP20722", "WP22444"), weather = c("L6D", "WP20723", "WP22445"),
  traffic = c(NA, "WP22213", "WP22446"), mental = c("L6G", "WP20726", "WP22447"),
  work = c(NA, "WP22214", "WP22448")
)
# Greatest source of risk (open question, coded): the codes differ in 2019.
ROAD <- 1
CLIMATE <- c("2019" = 16, "2021" = 19, "2023" = 19) # 2019: "climate change, natural disasters or weather-related events"
CRIME <- 3
HEALTH <- 5
WORRIED <- c(1, 2) # very or somewhat worried
PERSONAL <- c(1, 3) # experience: "yes, personally" or "both"
EXPERIENCE <- c(none = 4, know = 2, personal = 1, both = 3) # experience codes in chart order
DK <- c(98, 99)

# Round half up to a whole number (the same rule in reproduce.py).
rnd <- function(x) floor(x + 0.5)

# --- Data ------------------------------------------------------------------------------

# Common names across waves: safe, top_risk, climate, worry_<risk>, exp_<risk>.
harmonise <- function(df, year) {
  old <- if (year == 2019) c("L2", "L3_A", "L5") else c("WP20711", "WP22331", "WP20719")
  new <- c("safe", "top_risk", "climate")
  for (risk in names(RISKS)) {
    items <- RISKS[[risk]]
    if (year == 2019) {
      if (!is.na(items[1])) { old <- c(old, items[1]); new <- c(new, paste0("worry_", risk)) }
    } else {
      old <- c(old, items[2], items[3]); new <- c(new, paste0("worry_", risk), paste0("exp_", risk))
    }
  }
  names(df)[match(old, names(df))] <- new
  df
}

ITEMS_2123 <- unlist(lapply(RISKS, function(x) x[2:3]), use.names = FALSE)
d23 <- harmonise(load_wave(2023, c(
  "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT", "Age", "Gender", "Education",
  "Urbanicity", "WP20711", "WP22331", "WP20719", ITEMS_2123, "WP22232", "WP22228", "WP23344",
  "WP22247", "WP23342", "Q4_mean", "Q5_mean", "Q4_mean_projwt_byusertime", "Q5_mean_projwt_byusertime",
  "WPID_RANDOM"
)), 2023)
d21 <- harmonise(load_wave(2021, c("COUNTRY_ISO3", "PROJWT", "WP20711", "WP22331", "WP20719", ITEMS_2123,
                                   "WP22245", "WP22247")), 2021)
d19 <- harmonise(load_wave(2019, c("COUNTRY_ISO3", "PROJWT", "L2", "L3_A", "L5",
                                   na.omit(sapply(RISKS, `[`, 1)))), 2019)
N_COUNTRIES <- c("2019" = length(unique(d19$COUNTRY_ISO3)), "2021" = length(unique(d21$COUNTRY_ISO3)),
                 "2023" = length(unique(d23$COUNTRY_ISO3)))

# --- Derived variables -----------------------------------------------------------------

# Trends (report footnote ii, page 7): earlier waves use only the countries surveyed
# in 2023 (137 in 2019, 120 in 2021), and every country keeps its 2023 region.
# Iran is Middle East in the 2019 and 2021 files and Southern Asia in 2023; the
# 2023 region reproduces Table 3.1 and the Chart 2.2 changes.
REGION_2023 <- tapply(d23$GlobalRegion, d23$COUNTRY_ISO3, function(x) x[1])
d23$region <- d23$GlobalRegion
d21 <- d21[d21$COUNTRY_ISO3 %in% names(REGION_2023), ]
d19 <- d19[d19$COUNTRY_ISO3 %in% names(REGION_2023), ]
d21$region <- unname(REGION_2023[d21$COUNTRY_ISO3])
d19$region <- unname(REGION_2023[d19$COUNTRY_ISO3])

# Climate change threat with refused merged into don't know (charts label this
# "Don't know/Refused"): 1 very, 2 somewhat, 3 not a threat, 98 DK/refused.
d19$climate_dkr <- ifelse(d19$climate %in% 99, 98, d19$climate)
d21$climate_dkr <- ifelse(d21$climate %in% 99, 98, d21$climate)
d23$climate_dkr <- ifelse(d23$climate %in% 99, 98, d23$climate)

# PROJWT rescaled within each country so that the valid cases carry the country's
# whole population. This is how the 2023 file's Q4_mean_projwt_byusertime /
# Q5_mean_projwt_byusertime are built; it is applied to 2021 in the same way.
valid_case_weight <- function(df, ok) {
  total <- ave(df$PROJWT, df$COUNTRY_ISO3, FUN = sum)
  valid <- ave(ifelse(ok, df$PROJWT, 0), df$COUNTRY_ISO3, FUN = sum)
  ifelse(ok, df$PROJWT * total / valid, NA)
}

# Worry and Experience of Harm indices (Charts 4.6-4.8), 0-100: the simple mean of
# the seven items, not the Rasch-weighted worry_index_published /
# experience_index_published.
# 2023: the file's "Worried Mean" (Q4_mean) and "Experienced Mean" (Q5_mean) with
# their own projection weights.
d23$worry_idx <- 100 * d23$Q4_mean
d23$exp_idx <- 100 * d23$Q5_mean
d23$w_worry_idx <- d23$Q4_mean_projwt_byusertime
d23$w_exp_idx <- d23$Q5_mean_projwt_byusertime
# 2021: rebuilt with the rules that reproduce Q4_mean and Q5_mean exactly in 2023.
# Worry: very 2, somewhat 1, not 0, summed over the items asked and divided by 7
# (work, asked only of workers, counts 0 when not asked); missing if any asked item
# is DK/refused. Experience: share of the seven items personally experienced;
# missing if any item is DK/refused.
WORRY_COLS <- paste0("worry_", names(RISKS))
EXP_COLS <- paste0("exp_", names(RISKS))
wm <- as.matrix(d21[WORRY_COLS])
score <- ifelse(wm %in% 1, 2, ifelse(wm %in% 2, 1, 0))
dim(score) <- dim(wm)
any_dk <- rowSums(matrix(wm %in% DK, nrow = nrow(wm))) > 0
d21$worry_idx <- ifelse(any_dk, NA, 100 * rowSums(score) / 14)
em <- as.matrix(d21[EXP_COLS])
exp_ok <- rowSums(is.na(em)) == 0 & rowSums(matrix(em %in% DK, nrow = nrow(em))) == 0
d21$exp_idx <- ifelse(exp_ok, 100 * rowMeans(matrix(em %in% PERSONAL, nrow = nrow(em))), NA)
d21$w_worry_idx <- valid_case_weight(d21, !is.na(d21$worry_idx))
d21$w_exp_idx <- valid_case_weight(d21, !is.na(d21$exp_idx))
rm(wm, score, any_dk, em, exp_ok)

WAVE <- list("2019" = d19, "2021" = d21, "2023" = d23)

# --- Helpers ---------------------------------------------------------------------------

# % by 2023 region, named by region.
by_region <- function(df, var, codes, ...) {
  r <- pct(df, var, codes, by = "region", ...)
  setNames(unname(r), REGIONS[names(r)])
}

country <- function(df, var, codes, ...) pct(df, var, codes, by = "COUNTRY_ISO3", ...)

# ISO3 codes of the n largest values, sorted alphabetically, as one string.
top <- function(x, n) paste(sort(names(sort(x, decreasing = TRUE))[seq_len(n)]), collapse = "; ")

prefix <- function(x, p) setNames(x, paste0(p, names(x)))
suffix <- function(x, s) setNames(x, paste0(names(x), s))

# % very, somewhat, not a threat, DK/refused and combined (very + somewhat).
threat_shares <- function(df, by = NULL) {
  t <- distribution(df, "climate_dkr", by = by)
  if (is.null(by)) t <- matrix(t, nrow = 1, dimnames = list("All", names(t)))
  out <- data.frame(very = t[, "1"], somewhat = t[, "2"], not = t[, "3"], dk = t[, "98"], row.names = rownames(t))
  out$combined <- out$very + out$somewhat
  out$combined_rounded <- rnd(out$very) + rnd(out$somewhat) # "based on rounded numbers"
  out
}

# --- Executive summary --------------------------------------------------------------------

finding(report, "X01", function() nrow(d23))
finding(report, "X02", function() N_COUNTRIES[["2023"]])
finding(report, "X03", function() pct(d23, "climate", c(1, 2)))
finding(report, "X05", function() pct(d23, "top_risk", ROAD))
finding(report, "X06", function() pct(d21, "top_risk", ROAD))
finding(report, "X07", function() pct(d19, "top_risk", ROAD))
finding(report, "X08", function() pct(d23, "safe", 1))
finding(report, "X09", function() pct(d23, "safe", 3))
finding(report, "X10", function() pct(d23, "safe", 2))
finding(report, "X11", function() pct(d19, "worry_mental", WORRIED))
finding(report, "X12", function() pct(d21, "worry_mental", WORRIED))
finding(report, "X13", function() pct(d23, "worry_mental", WORRIED))

# --- Chapter 2: road-related accidents -------------------------------------------------------

finding(report, "X14", function() pct(d23, "top_risk", CRIME))
finding(report, "X15", function() pct(d23, "top_risk", HEALTH))
finding(report, "X16", function() pct(d23, "top_risk", CLIMATE[["2023"]]))
finding(report, "X17", function() pct(d21, "top_risk", CLIMATE[["2021"]]))
finding(report, "X18", function() pct(d19, "top_risk", CLIMATE[["2019"]]))

TOP_RISKS <- list( # Chart 2.1: WP22331 codes (same in 2021 and 2023)
  road = 1, crime = 3, health = 5, dk = 98, nothing = 23, economy = 10,
  climate = 19, financial = 9, other = 22, war = 4
)
finding(report, "C2_1", function() {
  out <- numeric(0)
  for (key in names(TOP_RISKS)) {
    now <- pct(d23, "top_risk", TOP_RISKS[[key]])
    out[key] <- now
    out[paste0(key, "_chg")] <- now - pct(d21, "top_risk", TOP_RISKS[[key]]) # unrounded change vs 2021
  }
  out
})

finding(report, "X19", function() pct(d23, "top_risk", ROAD, by = "CountryIncomeLevel")[["4"]])
finding(report, "X20", function() pct(d23, "top_risk", ROAD, by = "CountryIncomeLevel")[["1"]])
for (x in list(c("X21", "anz"), c("X22", "north_america"), c("X23", "se_asia"), c("X24", "central_asia"), c("X25", "south_africa"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() by_region(d23, "top_risk", ROAD)[[key]])
  })
}
finding(report, "X26", function() pct(d23, "top_risk", ROAD) - pct(d23, "top_risk", HEALTH))

finding(report, "C2_2", function() {
  now <- by_region(d23, "top_risk", ROAD)
  before <- by_region(d21, "top_risk", ROAD)[names(now)]
  c(now, suffix(now - before, "_chg"))
})

finding(report, "C2_3", function() {
  out <- numeric(0)
  for (risk in names(RISKS)) {
    t <- distribution(d23, paste0("worry_", risk))
    out[paste0(risk, "_very")] <- t[["1"]]
    out[paste0(risk, "_somewhat")] <- t[["2"]]
    out[paste0(risk, "_total")] <- t[["1"]] + t[["2"]]
  }
  out
})

# Chart 2.4 is a scatter plot with no printed values; X42-X45 are the values quoted in the text.
finding(report, "C2_4", function() {
  c(suffix(by_region(d23, "worry_traffic", WORRIED), "_worry"), suffix(by_region(d23, "exp_traffic", PERSONAL), "_experience"))
})

finding(report, "X27", function() pct(d23, "worry_traffic", WORRIED))
finding(report, "X28", function() pct(d23, "worry_traffic", 1))
finding(report, "X29", function() pct(d23, "worry_traffic", 2))
finding(report, "X30", function() pct(d23, "worry_traffic", WORRIED) - pct(d21, "worry_traffic", WORRIED))
finding(report, "X31", function() pct(d21, "worry_traffic", WORRIED))
for (x in list(c("X32", "weather"), c("X33", "crime"), c("X34", "food"), c("X35", "water"), c("X36", "work"))) {
  local({
    risk <- x[2]
    finding(report, x[1], function() pct(d23, paste0("worry_", risk), WORRIED))
  })
}
finding(report, "X37", function() pct(d23, "exp_traffic", PERSONAL))
finding(report, "X38", function() pct(d23, "exp_traffic", 2))
finding(report, "X39", function() pct(d23, "exp_traffic", c(1, 2, 3)))
finding(report, "X40", function() pct(d21, "exp_traffic", PERSONAL))
finding(report, "X41", function() pct(d21, "exp_traffic", 2))
finding(report, "X42", function() by_region(d23, "worry_traffic", WORRIED)[["latam"]])
finding(report, "X43", function() by_region(d23, "exp_traffic", PERSONAL)[["latam"]])
finding(report, "X44", function() by_region(d23, "exp_traffic", PERSONAL)[["nw_europe"]])
finding(report, "X45", function() by_region(d23, "worry_traffic", WORRIED)[["nw_europe"]])

# Country % worried about / personally harmed by traffic accidents, 2021 and 2023,
# for the 120 countries surveyed in both waves.
TRAFFIC_CHANGES <- local({
  w21 <- country(d21, "worry_traffic", WORRIED)
  w23 <- country(d23, "worry_traffic", WORRIED)
  e21 <- country(d21, "exp_traffic", PERSONAL)
  e23 <- country(d23, "exp_traffic", PERSONAL)
  iso <- sort(intersect(names(w21), names(w23)))
  t <- data.frame(worry_2021 = w21[iso], worry_2023 = w23[iso], experience_2021 = e21[iso],
                  experience_2023 = e23[iso], row.names = iso)
  for (block in c("worry", "experience")) {
    t[[paste0(block, "_chg")]] <- t[[paste0(block, "_2023")]] - t[[paste0(block, "_2021")]]
    t[[paste0(block, "_chg_rounded")]] <- rnd(t[[paste0(block, "_2023")]]) - rnd(t[[paste0(block, "_2021")]])
  }
  t
})
traffic_country_changes <- function() TRAFFIC_CHANGES

# Changes of 4 points or more between country figures rounded to whole numbers
# (unrounded changes give 12/15 and 26/29).
countries_changing_4_points <- function() {
  t <- traffic_country_changes()
  out <- numeric(0)
  for (block in c("experience", "worry")) {
    out[paste0(block, "_decrease")] <- sum(t[[paste0(block, "_chg_rounded")]] <= -4)
    out[paste0(block, "_increase")] <- sum(t[[paste0(block, "_chg_rounded")]] >= 4)
  }
  out
}
finding(report, "C2_5", countries_changing_4_points)
finding(report, "X46", function() countries_changing_4_points()[["experience_increase"]])
finding(report, "X47", function() countries_changing_4_points()[["experience_decrease"]])

# 95% margin of error for a 50% estimate with the Kish design effect of WGT.
finding(report, "X48", function() {
  n <- tapply(d23$WGT, d23$COUNTRY_ISO3, length)
  deff <- n * tapply(d23$WGT^2, d23$COUNTRY_ISO3, sum) / tapply(d23$WGT, d23$COUNTRY_ISO3, sum)^2
  mean(100 * 1.96 * sqrt(deff * 0.25 / n))
})

C2_6_COUNTRIES <- list(worry = c("ITA", "ARE", "FRA", "CHN", "VNM", "SLE", "THA", "HRV", "MDA", "POL"),
                       experience = c("CHN", "SLE", "PAN", "TUR", "USA", "CMR", "BRA", "THA", "MLI", "ZMB"))
finding(report, "C2_6", function() {
  t <- traffic_country_changes()
  out <- numeric(0)
  for (block in names(C2_6_COUNTRIES)) {
    for (iso in C2_6_COUNTRIES[[block]]) {
      for (s in c("2021", "2023", "chg")) out[paste(block, iso, s, sep = "_")] <- t[iso, paste(block, s, sep = "_")]
    }
  }
  out
})
for (block in c("worry", "experience")) {
  local({
    b <- block
    chg <- function() setNames(traffic_country_changes()[[paste0(b, "_chg")]], rownames(traffic_country_changes()))
    finding(report, paste0("C2_6_", b, "_up_top5"), function() top(chg(), 5))
    finding(report, paste0("C2_6_", b, "_down_top5"), function() top(-chg(), 5))
  })
}
finding(report, "X49", function() traffic_country_changes()["CHN", "experience_chg"])
finding(report, "X50", function() traffic_country_changes()["SLE", "experience_chg"])
finding(report, "X51", function() traffic_country_changes()["SLE", "worry_chg"])

traffic_worry_by_experience <- function() {
  t <- distribution(d23, "worry_traffic", by = "exp_traffic")
  out <- numeric(0)
  for (key in names(EXPERIENCE)) {
    code <- as.character(EXPERIENCE[[key]])
    out[paste0(key, "_very")] <- t[code, "1"]
    out[paste0(key, "_somewhat")] <- t[code, "2"]
    out[paste0(key, "_total")] <- t[code, "1"] + t[code, "2"]
  }
  out
}
finding(report, "C2_7", traffic_worry_by_experience)
for (x in list(c("X52", "none_total"), c("X53", "none_very"), c("X54", "none_somewhat"), c("X55", "know_total"),
               c("X56", "personal_total"), c("X57", "both_total"), c("X58", "personal_very"), c("X59", "know_very"),
               c("X60", "both_very"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() traffic_worry_by_experience()[[key]])
  })
}

top_risk_by_experience <- function(code, exp_var) {
  r <- pct(d23, "top_risk", code, by = exp_var)
  setNames(unname(r[as.character(EXPERIENCE)]), names(EXPERIENCE))
}
finding(report, "C2_8", function() top_risk_by_experience(ROAD, "exp_traffic"))
finding(report, "C2_9", function() top_risk_by_experience(CLIMATE[["2023"]], "exp_weather"))
finding(report, "C2_10", function() top_risk_by_experience(CRIME, "exp_crime"))
for (x in list(c("X61", "none"), c("X62", "know"), c("X63", "personal"), c("X64", "both"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() top_risk_by_experience(ROAD, "exp_traffic")[[key]])
  })
}
for (x in list(c("X65", "none"), c("X66", "know"), c("X67", "personal"), c("X68", "both"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() top_risk_by_experience(CLIMATE[["2023"]], "exp_weather")[[key]])
  })
}

# Needs the Gallup World Poll item "In the city or area where you live, are you
# satisfied or dissatisfied with the roads and highways?" (placeholder name
# GWP_ROADS_SATISFACTION: 1 = satisfied, 2 = dissatisfied). Pearson correlation of
# the country figures (Chart 2.11).
roads_correlation <- function(outcome, codes) {
  g <- merge_gallup(d23[c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", outcome)], "GWP_ROADS_SATISFACTION")
  sat <- country(g, "GWP_ROADS_SATISFACTION", 1)
  y <- country(g, outcome, codes)
  iso <- intersect(names(sat), names(y))
  cor(sat[iso], y[iso])
}
finding(report, "X69", function() roads_correlation("worry_traffic", WORRIED))
finding(report, "X70", function() roads_correlation("exp_traffic", PERSONAL))

# --- Chapter 3: climate change ---------------------------------------------------------------

finding(report, "X71", function() pct(d21, "WP22245", 1))
finding(report, "X72", function() pct(d23, "WP23344", 1))
# Flood/heavy rain (WP22247 code 1) as a share of all adults: those not asked the
# type question (no disaster) count as not experiencing a flood.
flood_share <- function(df, asked) {
  100 * sum(df$PROJWT[df$WP22247 %in% 1]) / sum(df$PROJWT[!is.na(df[[asked]])])
}
finding(report, "X73", function() flood_share(d21, "WP22245"))
finding(report, "X74", function() flood_share(d23, "WP23344"))

THREAT_TREND <- local({
  out <- numeric(0)
  for (year in names(WAVE)) {
    s <- threat_shares(WAVE[[year]])
    for (key in c("very", "somewhat", "not", "dk")) out[paste(key, year, sep = "_")] <- s[1, key]
  }
  out
})
threat_trend <- function() THREAT_TREND
finding(report, "C3_2", threat_trend)
for (x in list(c("X75", "very_2019"), c("X76", "somewhat_2019"), c("X77", "not_2019"), c("X78", "dk_2019"),
               c("X80", "very_2021"), c("X81", "very_2023"), c("X83", "somewhat_2021"), c("X84", "somewhat_2023"),
               c("X89", "not_2023"), c("X90", "dk_2023"), c("X92", "dk_2021"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() threat_trend()[[key]])
  })
}
finding(report, "X79", function() threat_trend()[["very_2021"]] - threat_trend()[["very_2023"]])
finding(report, "X82", function() threat_trend()[["somewhat_2023"]] - threat_trend()[["somewhat_2021"]])
finding(report, "X85", function() pct(d23, "climate", c(1, 2)) - pct(d21, "climate", c(1, 2)))
finding(report, "X86", function() pct(d21, "climate", c(1, 2)))
finding(report, "X87", function() pct(d19, "climate", c(1, 2)))
finding(report, "X88", function() threat_trend()[["not_2023"]] - threat_trend()[["not_2021"]])
finding(report, "X91", function() threat_trend()[["dk_2021"]] - threat_trend()[["dk_2023"]])

THREAT_BY_REGION <- lapply(WAVE, function(df) {
  t <- threat_shares(df, by = "region")
  rownames(t) <- REGIONS[rownames(t)]
  t
})
threat_by_region <- function(year) THREAT_BY_REGION[[as.character(year)]]

finding(report, "C3_3", function() {
  t <- threat_by_region(2023)
  out <- numeric(0)
  for (key in rownames(t)) {
    for (part in c("very", "somewhat", "dk", "not")) out[paste(key, part, sep = "_")] <- t[key, part]
    out[paste0(key, "_combined")] <- t[key, "combined_rounded"]
  }
  out
})
for (x in list(c("X93", "south_europe", "combined_rounded"), c("X94", "nw_europe", "combined_rounded"),
               c("X95", "latam", "very"), c("X98", "north_america", "very"), c("X99", "north_america", "not"),
               c("X100", "south_asia", "not"), c("X101", "middle_east", "not"), c("X102", "se_asia", "dk"),
               c("X103", "cw_africa", "dk"), c("X104", "south_africa", "dk"))) {
  local({
    key <- x[2]
    part <- x[3]
    finding(report, x[1], function() threat_by_region(2023)[key, part])
  })
}
finding(report, "X96", function() {
  t <- threat_by_region(2023)
  which(rownames(t)[order(-t$combined_rounded, -t$combined)] == "east_asia")
})
finding(report, "X97", function() country(d23, "climate", 2)[["CHN"]])

# Table 3.1: differences of the rounded 2019 and 2023 regional figures.
region_change_2019_2023 <- function() {
  a <- threat_by_region(2019)
  b <- threat_by_region(2023)
  a <- a[rownames(b), ]
  out <- data.frame(row.names = rownames(b))
  for (part in c("very", "somewhat", "not", "dk")) out[[part]] <- rnd(b[[part]]) - rnd(a[[part]])
  out$combined <- b$combined_rounded - a$combined_rounded
  out
}
finding(report, "T3_1", function() {
  t <- region_change_2019_2023()
  out <- numeric(0)
  for (key in rownames(t)) for (part in c("very", "somewhat", "not", "dk")) out[paste(key, part, sep = "_")] <- t[key, part]
  out
})
for (x in list(c("X105", "north_africa", "very"), c("X110", "south_europe", "very"), c("X111", "south_europe", "somewhat"),
               c("X112", "anz", "combined"), c("X113", "anz", "not"), c("X114", "anz", "dk"), c("X115", "east_europe", "very"))) {
  local({
    key <- x[2]
    part <- x[3]
    finding(report, x[1], function() region_change_2019_2023()[key, part])
  })
}
finding(report, "X106", function() threat_by_region(2019)["north_africa", "very"])
finding(report, "X107", function() threat_by_region(2023)["north_africa", "very"])
finding(report, "X108", function() threat_by_region(2019)["south_europe", "combined_rounded"])
finding(report, "X109", function() threat_by_region(2023)["south_europe", "combined_rounded"])

china_and_rest <- function(year) {
  df <- WAVE[[as.character(year)]]
  df$china <- ifelse(df$COUNTRY_ISO3 == "CHN", "china", "rest")
  threat_shares(df, by = "china")
}
finding(report, "C3_4", function() {
  out <- numeric(0)
  for (who in c("china", "rest")) for (year in names(WAVE)) out[paste(who, year, sep = "_")] <- china_and_rest(year)[who, "combined_rounded"]
  out
})
for (x in list(c("X116", "china", "2023"), c("X117", "china", "2021"), c("X118", "china", "2019"),
               c("X119", "rest", "2023"), c("X120", "rest", "2019"), c("X121", "rest", "2021"))) {
  local({
    who <- x[2]
    year <- x[3]
    finding(report, x[1], function() china_and_rest(year)[who, "combined_rounded"])
  })
}
for (x in list(c("X122", "2021"), c("X123", "2019"), c("X124", "2023"))) {
  local({
    year <- x[2]
    finding(report, x[1], function() country(WAVE[[year]], "climate", 98)[["CHN"]]) # don't know only
  })
}

THREAT_BY_COUNTRY <- local({
  t <- threat_shares(d23, by = "COUNTRY_ISO3")
  t$dk_only <- country(d23, "climate", 98)[rownames(t)]
  t$no_opinion <- t$dk # don't know or refused
  t
})
threat_by_country <- function() THREAT_BY_COUNTRY

C3_5_COUNTRIES <- c("ESP", "DEU", "AUT", "GEO", "KOR", "ITA", "JPN", "LUX", "GBR", "IRL")
finding(report, "C3_5", function() {
  t <- threat_by_country()
  out <- numeric(0)
  for (iso in C3_5_COUNTRIES) {
    out[paste0(iso, "_very")] <- t[iso, "very"]
    out[paste0(iso, "_somewhat")] <- t[iso, "somewhat"]
    out[paste0(iso, "_total")] <- t[iso, "combined_rounded"]
  }
  out
})
# Ranked on the sum of the rounded figures, ties broken on the unrounded sum.
finding(report, "C3_5_top10", function() {
  t <- threat_by_country()
  paste(sort(rownames(t)[order(-t$combined_rounded, -t$combined)][1:10]), collapse = "; ")
})
finding(report, "X125", function() threat_by_country()["ESP", "combined_rounded"])

C3_6_COUNTRIES <- c("SAU", "ETH", "ARE", "ISR", "IRQ", "MLI", "BHR", "JOR", "EST", "IND")
finding(report, "C3_6", function() setNames(threat_by_country()[C3_6_COUNTRIES, "not"], C3_6_COUNTRIES))
finding(report, "C3_6_top10", function() top(setNames(threat_by_country()$not, rownames(threat_by_country())), 10))
for (x in list(c("X126", "SAU", "not"), c("X127", "SAU", "very"), c("X129", "ETH", "not"), c("X130", "ETH", "very"),
               c("X131", "ISR", "not"), c("X134", "MMR", "no_opinion"), c("X135", "LBY", "no_opinion"),
               c("X136", "SAU", "dk_only"))) {
  local({
    iso <- x[2]
    part <- x[3]
    finding(report, x[1], function() threat_by_country()[iso, part])
  })
}
finding(report, "X128", function() threat_by_country()["SAU", "not"] / threat_by_country()["SAU", "very"])
finding(report, "X132", function() country(d19, "climate", 3)[["ISR"]])
finding(report, "X133", function() country(d21, "climate", 3)[["ISR"]])

C3_7_COUNTRIES <- c("MMR", "LBY", "MAR", "LAO", "IDN", "NAM", "NGA", "COD", "YEM", "SAU")
finding(report, "C3_7", function() setNames(threat_by_country()[C3_7_COUNTRIES, "dk_only"], C3_7_COUNTRIES))
finding(report, "C3_7_top10", function() top(setNames(threat_by_country()$dk_only, rownames(threat_by_country())), 10))

# Model (Charts 3.8, 3.9 and pages 19-20). The report fits a multi-level model of
# saying climate change is a very serious threat. Here: a logistic regression (glm,
# binomial, logit link) with country fixed effects in place of the country random
# intercepts, so region and country income level are absorbed.
# Outcome: 1 = very serious threat, 0 = any other answer (DK/refused included).
# Covariates: worry about severe weather (ref. not worried), education (ref.
# primary), male, urbanicity (ref. rural area or farm; the report's "city" is a
# large city), age (years), neighbours care about you (WP22232) and could cover
# basic needs for a month (WP22228). Weights: WGT, rescaled to mean 1.
# Cases with DK/refused on a covariate are dropped. If GALLUP_WP_PATH is set, the
# two Gallup World Poll controls the report names are added: feelings about
# household income (WP2319) and not enough money for food (WP40).
model_data <- function() {
  m <- d23[d23$worry_weather %in% 1:3 & d23$Education %in% 1:3 & d23$Urbanicity %in% c(1, 2, 3, 6) &
             !is.na(d23$Age) & d23$WP22232 %in% 1:3 & d23$WP22228 %in% 1:2, ]
  m$very <- as.numeric(m$climate %in% 1)
  m$worry <- factor(c("very", "somewhat", "not")[m$worry_weather], levels = c("not", "somewhat", "very"))
  m$edu <- factor(c("primary", "secondary", "tertiary")[m$Education], levels = c("primary", "secondary", "tertiary"))
  m$male <- as.numeric(m$Gender %in% 1)
  m$urban <- factor(unname(c("1" = "rural", "2" = "town", "3" = "city", "6" = "suburb")[as.character(m$Urbanicity)]),
                    levels = c("rural", "town", "city", "suburb"))
  m$w <- m$WGT / mean(m$WGT)
  m
}

CLIMATE_MODEL <- NULL
climate_model <- function() {
  if (!is.null(CLIMATE_MODEL)) return(CLIMATE_MODEL)
  m <- model_data()
  formula <- very ~ worry + edu + male + urban + Age + factor(WP22232) + factor(WP22228) + factor(COUNTRY_ISO3)
  g <- tryCatch(merge_gallup(m, c("WP2319", "WP40")), gallup_data_required = function(e) NULL)
  if (!is.null(g)) {
    m <- g[g$WP2319 %in% 1:4 & g$WP40 %in% 1:2, ]
    m$w <- m$WGT / mean(m$WGT)
    formula <- update(formula, . ~ . + factor(WP2319) + factor(WP40))
  }
  fit <- suppressWarnings(glm(formula, data = m, weights = w, family = binomial(),
                              control = glm.control(epsilon = 1e-12, maxit = 100),
                              model = FALSE, x = FALSE, y = FALSE))
  odds <- exp(coef(fit))
  CLIMATE_MODEL <<- c(very = odds[["worryvery"]], somewhat = odds[["worrysomewhat"]],
                      tertiary = odds[["edutertiary"]], secondary = odds[["edusecondary"]],
                      male = odds[["male"]], city = odds[["urbancity"]])
  CLIMATE_MODEL
}
finding(report, "C3_8", function() climate_model()[c("very", "somewhat")])
finding(report, "C3_9", function() climate_model()[c("tertiary", "secondary")])
for (x in list(c("X04", "very"), c("X137", "somewhat"), c("X138", "tertiary"), c("X139", "secondary"),
               c("X140", "male"), c("X141", "city"))) {
  local({
    key <- x[2]
    finding(report, x[1], function() climate_model()[[key]])
  })
}

# Needs the Gallup World Poll item "In this country, are you satisfied or
# dissatisfied with the efforts to preserve the environment?" (placeholder name
# GWP_ENVIRONMENT_SATISFACTION: 1 = satisfied, 2 = dissatisfied).
environment_satisfaction <- function(code) {
  g <- merge_gallup(d23[c("WPID_RANDOM", "PROJWT", "climate")], "GWP_ENVIRONMENT_SATISFACTION")
  pct(g, "GWP_ENVIRONMENT_SATISFACTION", 1, by = "climate")[[as.character(code)]]
}
finding(report, "X142", function() environment_satisfaction(1))
finding(report, "X143", function() environment_satisfaction(3))
finding(report, "X144", function() environment_satisfaction(98))
finding(report, "X145", function() pct(d23, "WP23342", 1, by = "climate")[["1"]])
finding(report, "X146", function() pct(d23, "WP23342", 1, by = "climate")[["3"]])

# --- Chapter 4: global trends ----------------------------------------------------------------

SAFE <- list(less = 2, about = 3, more = 1)
finding(report, "C4_1", function() {
  out <- numeric(0)
  for (year in names(WAVE)) for (key in names(SAFE)) out[paste(key, year, sep = "_")] <- pct(WAVE[[year]], "safe", SAFE[[key]])
  out
})
finding(report, "X147", function() pct(d21, "safe", 2))
finding(report, "X148", function() pct(d21, "safe", 1))
finding(report, "X149", function() N_COUNTRIES[["2021"]])
finding(report, "X150", function() length(unique(d19$COUNTRY_ISO3))) # 2019 countries also surveyed in 2023

finding(report, "C4_2", function() {
  out <- numeric(0)
  for (part in names(SAFE)) out <- c(out, suffix(by_region(d23, "safe", SAFE[[part]]), paste0("_", part)))
  out
})

# Chart 4.3 is a scatter plot with no printed values: change 2019-2023 in feeling less and more safe.
safety_change_by_region <- function() {
  out <- numeric(0)
  for (part in c("less", "more")) {
    now <- by_region(d23, "safe", SAFE[[part]])
    before <- by_region(d19, "safe", SAFE[[part]])[names(now)]
    out <- c(out, suffix(now - before, paste0("_", part, "_chg")))
  }
  out
}
finding(report, "C4_3", safety_change_by_region)
finding(report, "X151", function() by_region(d23, "safe", 1)[["east_asia"]])
finding(report, "X152", function() safety_change_by_region()[["north_america_less_chg"]])
finding(report, "X153", function() safety_change_by_region()[["east_europe_less_chg"]])
finding(report, "X154", function() country(d19, "safe", 2)[["USA"]])
finding(report, "X155", function() country(d23, "safe", 2)[["USA"]])

finding(report, "C4_4", function() {
  out <- numeric(0)
  for (risk in names(RISKS)) {
    for (year in names(WAVE)) {
      if (year == "2019" && is.na(RISKS[[risk]][1])) next # not asked in 2019
      out[paste(risk, year, sep = "_")] <- pct(WAVE[[year]], paste0("worry_", risk), WORRIED)
    }
  }
  out
})
finding(report, "C4_5", function() {
  out <- numeric(0)
  for (risk in names(RISKS)) for (year in c("2021", "2023")) out[paste(risk, year, sep = "_")] <- pct(WAVE[[year]], paste0("exp_", risk), PERSONAL)
  out
})
finding(report, "X156", function() pct(d23, "exp_traffic", PERSONAL) - pct(d21, "exp_traffic", PERSONAL))
finding(report, "X157", function() pct(d23, "exp_weather", PERSONAL) - pct(d21, "exp_weather", PERSONAL))

index_by_region <- function(df, var) {
  r <- wmean(df, var, weight = paste0("w_", var), by = "region")
  setNames(unname(r), REGIONS[names(r)])
}
finding(report, "C4_6", function() {
  c(suffix(index_by_region(d21, "worry_idx"), "_2021"), suffix(index_by_region(d23, "worry_idx"), "_2023"))
})
finding(report, "C4_7", function() {
  c(suffix(index_by_region(d21, "exp_idx"), "_2021"), suffix(index_by_region(d23, "exp_idx"), "_2023"))
})
finding(report, "C4_8", function() {
  c(suffix(index_by_region(d23, "exp_idx"), "_experience"), suffix(index_by_region(d23, "worry_idx"), "_worry"))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
