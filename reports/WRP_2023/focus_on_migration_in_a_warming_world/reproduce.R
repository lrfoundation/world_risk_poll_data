# Reproduce World Risk Poll 2024 Focus On: Migration in a warming world.
#
# Run from the repository root:
#   Rscript reports/WRP_2023/focus_on_migration_in_a_warming_world/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

DK <- c(98, 99) # don't know, refused: kept in the base
CLIMATE <- "WP20719" # 1 = very serious, 2 = somewhat serious, 3 = not a threat (2019: L5)
RISK <- "WP22331" # greatest source of risk to safety in daily life, coded (2019: L3_A)
MIGRATE <- "WP1325" # Gallup: 1 = would like to move permanently to another country, 2 = continue living here
DESTINATION <- "WP3120" # Gallup: country the respondent would like to move to (Gallup country code, as WP5)
GALLUP <- c(MIGRATE, DESTINATION)
# Greatest-risk codes: financial (not having enough money) and the general economy, and
# climate change or severe weather. 2019 has no separate climate code: 16 also covers
# earthquakes and other non-weather disasters.
RISK_CODES <- list(
  "2019" = list(climate = 16),
  "2021" = list(financial = 9, economy = 10, climate = 19),
  "2023" = list(financial = 9, economy = 10, climate = 19)
)
REGIONS <- c( # GlobalRegion codes -> keys
  "1" = "eastern_africa", "2" = "cw_africa", "3" = "northern_africa", "4" = "southern_africa", "5" = "latam",
  "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
  "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
  "14" = "southern_europe", "15" = "anz"
)
# Chart 10 groups Africa, Latin America and Eastern Europe as "Other" (10 categories).
OTHER <- c("eastern_africa", "cw_africa", "northern_africa", "southern_africa", "latam", "eastern_europe")
LOW <- 1; LOWER_MIDDLE <- 2; UPPER_MIDDLE <- 3; HIGH <- 4 # CountryIncomeLevel

# ND-GAIN Country Index, 2024 release: overall score (0-100), readiness and
# vulnerability (0-1). Not redistributed here; see README for the download.
NDGAIN <- "focus_on_migration_in_a_warming_world__ndgain_scores.csv"
NDGAIN_YEAR <- 2022
ND_MEASURES <- c("gain", "readiness", "vulnerability")

COLS <- c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "CountryIncomeLevel", "INCOME_5", "WP22228", "WP22229",
          RISK, CLIMATE)
d21 <- load_wave(2021, COLS); d21$Year <- 2021
d23 <- load_wave(2023, COLS); d23$Year <- 2023
d19 <- load_wave(2019, c("COUNTRY_ISO3", "PROJWT", "L3_A", "L5")); d19$Year <- 2019
names(d19)[names(d19) == "L3_A"] <- RISK
names(d19)[names(d19) == "L5"] <- CLIMATE

# --- Derived variables ---------------------------------------------------------

# Basic needs without income (Chart 1): WP22228 (less than a month / a month
# or more) with the follow-up WP22229 (weeks). 1 = less than a week, 2 = less
# than a month but a week or more (including don't know on the follow-up),
# 3 = don't know/refused, 4 = a month or more.
needs <- function(df) {
  ifelse(df$WP22229 %in% 1, 1,
    ifelse(df$WP22228 %in% 1, 2, ifelse(df$WP22228 %in% DK, 3, ifelse(df$WP22228 %in% 2, 4, NA))))
}
d21$needs <- needs(d21)
d23$needs <- needs(d23)
BY_YEAR <- list("2019" = d19, "2021" = d21, "2023" = d23)

# The blended file (Chapters 3-5): 2021 and 2023 respondents pooled, weighted
# by PROJWT. WPID_RANDOM does not repeat across the two waves.
b <- bind_rows(d21, d23)
# climate3: 1 very, 2 somewhat, 3 not a threat (DK/refused -> missing).
b$climate3 <- ifelse(b[[CLIMATE]] %in% 1:3, b[[CLIMATE]], NA)
# threat: 1 = a threat (very or somewhat serious), 2 = not a threat (Charts 8, 10).
b$threat <- c(1, 1, 2)[b$climate3]
# very_not: 1 = very serious, 2 = not a threat; somewhat serious left out (Chapter 5).
b$very_not <- c(1, NA, 2)[b$climate3]
# fin: 1 = less than a month, 2 = a month or more (DK/refused -> missing).
b$fin <- ifelse(b$WP22228 %in% 1:2, b$WP22228, NA)

# Destination lookup: Gallup country code (WP5) -> ISO3 and GlobalRegion, from
# every wave of the poll (148 countries; each country keeps its 2023 region).
# WP3120 is assumed to use the same country codes; destinations outside the
# poll's countries, and don't know/refused, are left out.
lookup <- bind_rows(lapply(c(2023, 2025, 2021, 2019), function(y) {
  unique(load_wave(y, c("WP5", "COUNTRY_ISO3", "GlobalRegion")))
}))
lookup <- lookup[!duplicated(lookup$WP5), ]
DEST_ISO3 <- setNames(lookup$COUNTRY_ISO3, lookup$WP5)
DEST_REGION <- setNames(unname(REGIONS[as.character(lookup$GlobalRegion)]), lookup$WP5)

# --- Helpers -------------------------------------------------------------------

# % naming a greatest-risk category in `year` (all countries surveyed that year).
risk <- function(year, key) pct(BY_YEAR[[as.character(year)]], RISK, RISK_CODES[[as.character(year)]][[key]])

.cache <- new.env()
cached <- function(name, fn) {
  if (is.null(.cache[[name]])) .cache[[name]] <- fn()
  .cache[[name]]
}

# Blended respondents who would like to move, with their destination region and ISO3.
migrants <- function() cached("migrants", function() {
  g <- merge_gallup(b, GALLUP)
  m <- g[g[[MIGRATE]] %in% 1, ]
  key <- as.character(m[[DESTINATION]])
  m$dest_region <- unname(DEST_REGION[key])
  m$dest_iso3 <- unname(DEST_ISO3[key])
  m$dest10 <- ifelse(m$dest_region %in% OTHER, "other", m$dest_region)
  m[!is.na(m$dest_region), ]
})

# Migrants with the ND-GAIN gaps (destination minus origin) for each measure.
ndgain_gaps <- function() cached("ndgain", function() {
  m <- migrants()
  nd <- read.csv(external_path(NDGAIN))
  nd <- nd[nd$year == NDGAIN_YEAR, ]
  for (x in ND_MEASURES) {
    v <- setNames(nd[[x]], nd$ISO3)
    m[[paste0("gap_", x)]] <- unname(v[m$dest_iso3] - v[m$COUNTRY_ISO3])
  }
  m[stats::complete.cases(m[paste0("gap_", ND_MEASURES)]), ]
})

# % of each group's destinations in each category (rows sum to 100): c('<group>_<cat>' = %).
shares <- function(m, group, groups, cat = "dest_region") {
  t <- distribution(m[!is.na(m[[group]]), ], cat, by = group)
  grid <- expand.grid(r = rownames(t), c = colnames(t), stringsAsFactors = FALSE)
  setNames(as.vector(t), paste(groups[grid$r], grid$c, sep = "_"))
}

# Chi-square, df, Cramer's V and adjusted standardised residuals of `group` by
# `cat`. Counts are weighted by PROJWT rescaled to the sample size.
crosstab_tests <- function(m, group, groups, cat = "dest_region") {
  m <- m[!is.na(m[[group]]) & !is.na(m[[cat]]), ]
  w <- m$PROJWT * nrow(m) / sum(m$PROJWT)
  obs <- tapply(w, list(m[[group]], m[[cat]]), sum)
  obs[is.na(obs)] <- 0
  n <- sum(obs)
  row <- rowSums(obs); col <- colSums(obs)
  exp <- outer(row, col) / n
  chi2 <- sum((obs - exp)^2 / exp)
  k <- min(dim(obs)) - 1
  adj <- (obs - exp) / sqrt(exp * outer(1 - row / n, 1 - col / n))
  grid <- expand.grid(r = rownames(obs), c = colnames(obs), stringsAsFactors = FALSE)
  c(chi2 = chi2, df = (nrow(obs) - 1) * (ncol(obs) - 1), cramers_v = sqrt(chi2 / (n * k)),
    setNames(as.vector(adj), paste("resid", groups[grid$r], grid$c, sep = "_")))
}

# Survey-weighted linear regression of `y` on `terms` (a named list of
# numeric vectors). PROJWT weights; linearisation (sandwich) standard errors
# for a design with weights only (HC0 x n/(n-1), as survey::svyglm), p-values
# from t(n - p). Returns a data frame with coef and p, one row per term.
svy_lm <- function(m, y, terms) {
  X <- cbind(const = 1, as.matrix(as.data.frame(lapply(terms, as.numeric))))
  w <- m$PROJWT
  fit <- glm(m[[y]] ~ X - 1, family = gaussian(), weights = w)
  beta <- setNames(coef(fit), colnames(X))
  e <- m[[y]] - as.vector(X %*% beta)
  bread <- solve(crossprod(X, w * X))
  meat <- crossprod(X * (w * e))
  n <- nrow(X); p <- ncol(X)
  se <- sqrt(diag(bread %*% meat %*% bread) * n / (n - 1))
  data.frame(coef = beta, p = 2 * pt(abs(beta / se), n - p, lower.tail = FALSE), row.names = colnames(X))
}

# 0/1 columns for each of `levels` of `s` (the reference level is left out).
dummies <- function(s, levels, prefix) {
  setNames(lapply(levels, function(lv) as.numeric(s == lv)), paste0(prefix, levels))
}

# Chart 14 model: income group, income quintile, climate concern, financial
# resilience. Sample: very serious or not a threat, a financial resilience
# answer, a classified income group and an income quintile. With
# `interaction`, very serious (reference: not a threat) is interacted with the
# income group, so the income-group coefficients are those for people who do
# not see climate change as a threat.
income_model <- function(m, interaction) {
  m <- m[!is.na(m$very_not) & !is.na(m$fin) & m$CountryIncomeLevel %in% 1:4 & !is.na(m$INCOME_5), ]
  terms <- c(dummies(m$CountryIncomeLevel, c(LOWER_MIDDLE, UPPER_MIDDLE, HIGH), "income"),
             dummies(m$INCOME_5, 2:5, "quintile"),
             list(month_or_more = as.numeric(m$fin == 2)))
  if (interaction) {
    very <- as.numeric(m$very_not == 1)
    terms$very_serious <- very
    for (lv in c(LOWER_MIDDLE, UPPER_MIDDLE, HIGH)) {
      terms[[paste0("very_serious_x_income", lv)]] <- very * (m$CountryIncomeLevel == lv)
    }
  } else {
    terms$not_a_threat <- as.numeric(m$very_not == 2)
  }
  svy_lm(m, "gap_gain", terms)
}

# --- Key findings and introduction (pages 2-3) -------------------------------------------

finding(report, "X01", function() {
  # Rank among the substantive categories (codes 1-21, leaving out other,
  # nothing, DK and refused), with financial (9) and the general economy (10)
  # combined.
  share <- distribution(d23, RISK)
  share <- share[as.numeric(names(share)) %in% 1:21]
  combined <- sum(share[c("9", "10")])
  1 + sum(share[!names(share) %in% c("9", "10")] > combined)
})
finding(report, "X02", function() pct(d23, "needs", 1:2))
finding(report, "X03", function() risk(2023, "climate"))
finding(report, "X04", function() {
  years <- c(2019, 2021, 2023)
  years[which.max(sapply(years, risk, key = "climate"))]
})
finding(report, "X05", function() {
  g <- merge_gallup(b[!is.na(b$climate3), ], MIGRATE)
  pct(g[g$climate3 == 1, ], MIGRATE, 1) / pct(g[g$climate3 %in% 2:3, ], MIGRATE, 1)
})
finding(report, "X06", function() length(unique(d23$COUNTRY_ISO3)))

# --- 2.1 Economic insecurity (page 4) -----------------------------------------------------

finding(report, "X07", function() pct(d23, "needs", 1))
finding(report, "X08", function() pct(d21, "needs", 1))
finding(report, "X09", function() pct(d23, "needs", 2))
finding(report, "X10", function() pct(d21, "needs", 2))
finding(report, "X11", function() pct(d21, "needs", 4))
finding(report, "X12", function() pct(d23, "needs", 4))
finding(report, "X13", function() risk(2021, "financial"))
finding(report, "X14", function() risk(2023, "financial"))
finding(report, "X15", function() risk(2021, "economy"))
finding(report, "X16", function() risk(2023, "economy"))
finding(report, "X17", function() pct(d23, RISK, c(RISK_CODES[["2023"]]$financial, RISK_CODES[["2023"]]$economy)))

finding(report, "C2_1", function() {
  keys <- c("1" = "week", "2" = "month", "3" = "dk", "4" = "more")
  out <- c()
  for (y in c("2021", "2023")) {
    v <- distribution(BY_YEAR[[y]], "needs")
    out <- c(out, setNames(v, paste(keys[names(v)], y, sep = "_")))
  }
  out
})
finding(report, "C2_2", function() {
  c(personal_finances_2021 = risk(2021, "financial"), personal_finances_2023 = risk(2023, "financial"),
    economy_2021 = risk(2021, "economy"), economy_2023 = risk(2023, "economy"))
})

# --- 2.2 Climate risk (page 5) --------------------------------------------------------------

finding(report, "X18", function() pct(d19, CLIMATE, 1))
finding(report, "X19", function() pct(d21, CLIMATE, 1))
finding(report, "X20", function() pct(d23, CLIMATE, 1))
finding(report, "X21", function() pct(d19, CLIMATE, 2))
finding(report, "X22", function() pct(d23, CLIMATE, 2))
finding(report, "X23", function() pct(d19, CLIMATE, DK))
finding(report, "X24", function() pct(d23, CLIMATE, DK))
finding(report, "X25", function() pct(d19, CLIMATE, 3))
finding(report, "X26", function() pct(d23, CLIMATE, 3))
finding(report, "X27", function() risk(2019, "climate"))
finding(report, "X28", function() risk(2021, "climate"))

finding(report, "C2_3", function() {
  cats <- list(very = 1, somewhat = 2, dk = DK, not = 3)
  out <- c()
  for (k in names(cats)) for (y in c("2019", "2021", "2023")) {
    out[paste(k, y, sep = "_")] <- pct(BY_YEAR[[y]], CLIMATE, cats[[k]])
  }
  out
})
finding(report, "C2_4", function() c("2021" = risk(2021, "climate"), "2023" = risk(2023, "climate")))

# --- 3. Who wants to leave (pages 6-7): Gallup WP1325 ------------------------------------

CLIMATE3 <- c("1" = "very", "2" = "somewhat", "3" = "not")
FIN <- c("1" = "less", "2" = "more")

migrate_by <- function(group, groups) {
  g <- merge_gallup(b[!is.na(b[[group]]), ], MIGRATE)
  r <- pct(g, MIGRATE, 1, by = group)
  setNames(r, groups[names(r)])
}

chart7_values <- function() {
  g <- merge_gallup(b[!is.na(b$climate3) & !is.na(b$fin), ], MIGRATE)
  r <- pct(g, MIGRATE, 1, by = c("climate3", "fin"))
  parts <- strsplit(names(r), "_")
  setNames(r, sapply(parts, function(p) paste(CLIMATE3[p[1]], FIN[p[2]], sep = "_")))
}

finding(report, "C3_5", function() migrate_by("climate3", CLIMATE3))
finding(report, "X29", function() migrate_by("climate3", CLIMATE3)[["very"]])
finding(report, "X30", function() {
  g <- merge_gallup(b[b$climate3 %in% 2:3, ], MIGRATE)
  pct(g, MIGRATE, 1)
})
finding(report, "X31", function() {
  g <- merge_gallup(b[!is.na(b$climate3), ], MIGRATE)
  min(pct(g, MIGRATE, 2, by = "climate3"))
})
finding(report, "X32", function() migrate_by("fin", FIN)[["more"]])
finding(report, "X33", function() migrate_by("fin", FIN)[["less"]])
finding(report, "C3_6", function() migrate_by("fin", FIN))
finding(report, "C3_7", function() chart7_values())
finding(report, "X34", function() chart7_values()[["very_more"]])
finding(report, "X35", function() chart7_values()[["very_less"]])
finding(report, "X36", function() chart7_values()[["not_more"]])
finding(report, "X37", function() chart7_values()[["not_less"]])
finding(report, "X38", function() {
  v <- chart7_values()
  v[["not_less"]] / v[["not_more"]]
})

# --- 4. Where people want to go (pages 9-11): Gallup WP1325 and WP3120 --------------------

THREAT <- c("1" = "threat", "2" = "not")
# Chart 10 groups: financial resilience x climate concern.
GROUP4 <- c("1" = "less_threat", "2" = "less_not", "3" = "more_threat", "4" = "more_not")

chart8_values <- function() cached("chart8", function() {
  m <- migrants()
  c(shares(m, "threat", THREAT), crosstab_tests(m, "threat", THREAT))
})
chart9_values <- function() cached("chart9", function() {
  m <- migrants()
  c(shares(m, "fin", FIN), crosstab_tests(m, "fin", FIN))
})
chart10_values <- function() cached("chart10", function() {
  m <- migrants()
  m$group4 <- (m$fin - 1) * 2 + m$threat
  c(shares(m, "group4", GROUP4, "dest10"), crosstab_tests(m, "group4", GROUP4, "dest10"))
})
getv <- function(v, key) if (key %in% names(v)) v[[key]] else 0

finding(report, "C4_8", function() chart8_values())
text_finding <- function(id, values, key) {
  force(values); force(key) # bind now: the loops below reuse `x`
  finding(report, id, function() values()[[key]])
}
text_finding("X39", chart8_values, "threat_northern_america")
text_finding("X40", chart8_values, "not_northern_america")
finding(report, "X41", function() {
  v <- chart8_values()
  v[["threat_northern_america"]] - v[["not_northern_america"]]
})
finding(report, "X42", function() {
  v <- chart8_values()
  gaps <- sapply(REGIONS, function(r) abs(getv(v, paste0("threat_", r)) - getv(v, paste0("not_", r))))
  unname(REGIONS[which.max(gaps)])
})
finding(report, "X43", function() {
  v <- chart8_values()
  falls <- sapply(REGIONS, function(r) getv(v, paste0("not_", r)) - getv(v, paste0("threat_", r)))
  unname(REGIONS[which.max(falls)])
})
text_finding("X44", chart8_values, "not_middle_east")
text_finding("X45", chart8_values, "threat_middle_east")
text_finding("X46", chart8_values, "threat_nw_europe")
text_finding("X47", chart8_values, "not_nw_europe")
text_finding("X48", chart8_values, "not_southeastern_asia")
text_finding("X49", chart8_values, "threat_southeastern_asia")
text_finding("X50", chart8_values, "threat_anz")
text_finding("X51", chart8_values, "not_anz")

finding(report, "C4_9", function() chart9_values())
for (x in list(c("X52", "more_nw_europe"), c("X53", "less_nw_europe"), c("X54", "more_anz"), c("X55", "less_anz"),
               c("X56", "more_middle_east"), c("X57", "less_middle_east"), c("X58", "less_southern_asia"),
               c("X59", "more_southern_asia"), c("X60", "more_northern_america"),
               c("X61", "less_northern_america"))) {
  text_finding(x[1], chart9_values, x[2])
}

finding(report, "C4_10", function() chart10_values())
for (x in list(c("X62", "less_not_middle_east"), c("X63", "less_not_southeastern_asia"),
               c("X64", "less_threat_middle_east"), c("X65", "less_threat_southeastern_asia"),
               c("X66", "less_not_northern_america"), c("X67", "less_threat_northern_america"))) {
  text_finding(x[1], chart10_values, x[2])
}
finding(report, "X68", function() {
  v <- chart10_values()
  v[["less_threat_northern_america"]] - v[["less_not_northern_america"]]
})
for (x in list(c("X69", "less_not_nw_europe"), c("X70", "less_threat_nw_europe"), c("X71", "more_not_nw_europe"),
               c("X72", "more_threat_nw_europe"), c("X73", "more_threat_northern_america"),
               c("X74", "more_not_northern_america"), c("X75", "more_not_anz"), c("X76", "more_threat_anz"),
               c("X77", "more_not_middle_east"), c("X78", "more_threat_middle_east"),
               c("X79", "more_not_southeastern_asia"), c("X80", "more_threat_southeastern_asia"))) {
  text_finding(x[1], chart10_values, x[2])
}

# --- 5. ND-GAIN gaps (pages 12-16): Gallup WP1325, WP3120 and ND-GAIN -----------------------

VERY_NOT <- c("1" = "very", "2" = "not")

# Mean ND-GAIN gaps by group: c('<measure>_<group>' = mean).
nd_means <- function(group, groups) {
  m <- ndgain_gaps()
  m <- m[!is.na(m[[group]]), ]
  out <- c()
  for (x in ND_MEASURES) {
    r <- wmean(m, paste0("gap_", x), by = group)
    out <- c(out, setNames(r, paste(x, groups[names(r)], sep = "_")))
  }
  out
}
chart11_values <- function() cached("chart11", function() nd_means("very_not", VERY_NOT))
chart12_values <- function() cached("chart12", function() nd_means("fin", FIN))
chart13_values <- function() cached("chart13", function() {
  m <- ndgain_gaps()
  m <- m[!is.na(m$very_not) & !is.na(m$fin), ]
  out <- c()
  for (x in ND_MEASURES) {
    r <- wmean(m, paste0("gap_", x), by = c("very_not", "fin"))
    parts <- strsplit(names(r), "_")
    out <- c(out, setNames(r, sapply(parts, function(p) paste(x, VERY_NOT[p[1]], FIN[p[2]], sep = "_"))))
  }
  out
})

model11 <- function() cached("model11", function() {
  m <- ndgain_gaps()
  m <- m[!is.na(m$very_not), ]
  svy_lm(m, "gap_gain", list(not_a_threat = m$very_not == 2))
})
model12 <- function() cached("model12", function() {
  m <- ndgain_gaps()
  m <- m[!is.na(m$fin), ]
  svy_lm(m, "gap_gain", list(month_or_more = m$fin == 2))
})
model13 <- function() cached("model13", function() {
  m <- ndgain_gaps()
  m <- m[!is.na(m$very_not) & !is.na(m$fin), ]
  not_ <- as.numeric(m$very_not == 2); more <- as.numeric(m$fin == 2)
  svy_lm(m, "gap_gain", list(not_a_threat = not_, month_or_more = more, interaction = not_ * more))
})
model14_text <- function() cached("model14", function() income_model(ndgain_gaps(), interaction = TRUE))

without_gain <- function(v) v[!startsWith(names(v), "gain")]

finding(report, "C5_11a", function() {
  v <- chart11_values()
  c(very = v[["gain_very"]], not = v[["gain_not"]])
})
finding(report, "C5_11b", function() without_gain(chart11_values()))
text_finding("X81", chart11_values, "gain_very")
text_finding("X82", chart11_values, "gain_not")
finding(report, "X83", function() {
  v <- chart11_values()
  v[["gain_very"]] - v[["gain_not"]]
})
finding(report, "X84", function() model11()["not_a_threat", "coef"])
finding(report, "X85", function() model11()["not_a_threat", "p"])
for (x in list(c("X86", "readiness_very"), c("X87", "readiness_not"), c("X88", "vulnerability_very"),
               c("X89", "vulnerability_not"))) {
  text_finding(x[1], chart11_values, x[2])
}

finding(report, "C5_12a", function() {
  v <- chart12_values()
  c(less = v[["gain_less"]], more = v[["gain_more"]], p = model12()["month_or_more", "p"])
})
finding(report, "C5_12b", function() without_gain(chart12_values()))
text_finding("X90", chart12_values, "gain_less")
text_finding("X91", chart12_values, "gain_more")
finding(report, "X92", function() {
  v <- chart12_values()
  v[["gain_less"]] - v[["gain_more"]]
})
finding(report, "X93", function() model12()["month_or_more", "coef"])
finding(report, "X94", function() model12()["month_or_more", "p"])
for (x in list(c("X95", "readiness_less"), c("X96", "readiness_more"), c("X97", "vulnerability_less"),
               c("X98", "vulnerability_more"))) {
  text_finding(x[1], chart12_values, x[2])
}

finding(report, "C5_13a", function() {
  v <- chart13_values()
  v <- v[startsWith(names(v), "gain_")]
  setNames(v, sub("^gain_", "", names(v)))
})
finding(report, "C5_13b", function() without_gain(chart13_values()))
text_finding("X99", chart13_values, "gain_very_less")
text_finding("X100", chart13_values, "gain_not_more")
finding(report, "X101", function() model13()["interaction", "coef"])
finding(report, "X102", function() model13()["interaction", "p"])
for (x in list(c("X103", "readiness_very_less"), c("X104", "readiness_not_less"), c("X105", "readiness_very_more"),
               c("X106", "readiness_not_more"), c("X108", "vulnerability_very_less"))) {
  text_finding(x[1], chart13_values, x[2])
}
finding(report, "X107", function() {
  v <- chart13_values()
  groups <- c("very_less", "very_more", "not_less", "not_more")
  groups[which.max(v[paste0("readiness_", groups)])]
})
other_vulnerability <- function() {
  v <- chart13_values()
  v[paste0("vulnerability_", c("very_more", "not_less", "not_more"))]
}
finding(report, "X109", function() max(other_vulnerability()))
finding(report, "X110", function() min(other_vulnerability()))

finding(report, "C5_14", function() {
  # No values are printed on the chart: coefficients of the main-effects model.
  r <- income_model(ndgain_gaps(), interaction = FALSE)
  setNames(r$coef, rownames(r))[rownames(r) != "const"]
})
finding(report, "X111", function() model14_text()[paste0("income", LOWER_MIDDLE), "coef"])
finding(report, "X112", function() model14_text()[paste0("income", UPPER_MIDDLE), "coef"])
finding(report, "X113", function() model14_text()[paste0("income", HIGH), "coef"])
finding(report, "X114", function() model14_text()[paste0("very_serious_x_income", UPPER_MIDDLE), "coef"])
finding(report, "X115", function() model14_text()[paste0("very_serious_x_income", UPPER_MIDDLE), "p"])

status <- run_report(report)
if (!interactive()) quit(status = status)
