# Reproduce World Risk Poll 2026: After the storm: How disasters reshape resilience and trust.
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_after_the_storm/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes. Estimates are weighted least squares with
# PROJWT and HC1 standard errors (95% intervals: estimate +/- 1.96 SE).

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

# --- Variables -------------------------------------------------------------------

DIMS <- c(index = "resilience_index_100", societal = "resilience_soc", community = "resilience_com",
          household = "resilience_hhl", individual = "resilience_idv")
CARES <- "WP22231"       # government cares about you and your wellbeing: 1 a lot
NEIGHBOURS <- "WP22232"  # neighbours care about you and your wellbeing: 1 a lot
PROTECT <- "WP22252"     # could protect yourself and your family in a future disaster: 1 yes
EXPOSURE <- c("2021" = "WP22245", "2023" = "WP23344", "2025" = "WP24213")
TYPE <- c("2023" = "WP22247", "2025" = "WP24180")  # 1 flood, 2 tropical storm, 7 earthquake
PREPARED <- c("2021" = "WP22241", "2025" = "WP24198")
LOCAL_PREPARED <- "WP24199"
WORRY <- "worry_index_published"
CONFIDENCE <- "WP139"    # Gallup World Poll: confidence in national government (1 = yes)
PSU <- "WP12259"         # Gallup World Poll: primary sampling unit
STRATA <- "WP12258"      # Gallup World Poll: stratum
MEASURES <- c("index", "societal", "community", "household", "individual", "confidence", "cares", "neighbours", "protect")
Z <- 1.96

CASES <- c("MAR", "ECU", "MOZ", "NZL", "TUR", "PAK", "ZAF")
MONTHS <- c(MAR = 1, ECU = 5, MOZ = 6, NZL = 7, TUR = 10, PAK = 14, ZAF = 22)
CONF_CASES <- c("ECU", "MOZ", "NZL", "TUR", "ZAF")
RECOVERY <- c("MAR", "TUR", "NZL")
OTHERS <- c("THA", "PHL", "LBN")

# Region variable for each case and wave; NA = not public, taken from the Gallup item in GALLUP_REGION.
REGION_VAR <- list(
  MAR = c("2021" = "REGION_MAR", "2023" = "REGION3_MAR", "2025" = "REGION3_MAR"),
  ECU = c("2021" = "REGION_ECU", "2023" = "REGION_ECU"),
  MOZ = c("2021" = "REGION_MOZ", "2023" = "REGION_MOZ"),
  NZL = c("2021" = "REGION_NZL", "2023" = "REGION_NZL", "2025" = NA),
  TUR = c("2021" = "REGION3_TUR", "2023" = "REGION3_TUR", "2025" = "REGION3_TUR"),
  PAK = c("2021" = "REGION_PAK", "2023" = "REGION_PAK"),
  ZAF = c("2021" = NA, "2023" = "REGION_ZAF", "2025" = "REGION_ZAF")
)
GALLUP_REGION <- c(NZL = "REGION_NZL", ZAF = "REGION_ZAF")
AFFECTED <- list(MAR = 7, ECU = c(6, 8), MOZ = c(4, 8, 10), NZL = c(1, 2), TUR = c(6, 11), PAK = 1, ZAF = 4)
ALSO_REACHED <- list(TUR = 12, NZL = c(3, 4, 5, 6))

MAR_PROVINCES <- list("1" = c(54, 57, 58, 59, 60, 61, 68, 72), "2" = c(27, 28, 29, 30, 31, 32, 66, 75),
                      "3" = c(45, 46, 48, 50, 51, 52, 53, 55, 56), "4" = c(17, 18, 37, 38, 39, 40, 70),
                      "5" = c(20, 43, 44, 49, 67), "6" = c(19, 21, 33, 34, 35, 36, 41, 63, 64),
                      "7" = c(22, 23, 24, 25, 26, 42, 65, 71), "8" = c(13, 16, 47, 62, 73), "9" = c(9, 10, 11, 12, 14, 15),
                      "10" = c(5, 7, 8, 69), "11" = c(3, 4, 6, 74), "12" = c(1, 2))
MAR_PROVINCE_REGION <- unlist(lapply(names(MAR_PROVINCES), function(r) setNames(rep(as.numeric(r), length(MAR_PROVINCES[[r]])),
                                                                                 MAR_PROVINCES[[r]])))
MAR_REGIONS <- c("1" = "tanger", "2" = "oriental", "3" = "fes_meknes", "4" = "rabat", "5" = "beni_mellal",
                 "6" = "casablanca_settat", "7" = "marrakech_safi", "8" = "draa", "9" = "souss_massa", "10" = "guelmim",
                 "11" = "laayoune", "12" = "dakhla")
TUR_REGIONS <- c("1" = "istanbul", "2" = "west_marmara", "3" = "aegean", "4" = "east_marmara", "5" = "west_anatolia",
                 "6" = "mediterranean", "7" = "central_anatolia", "8" = "west_black_sea", "9" = "east_black_sea",
                 "10" = "ne_anatolia", "11" = "cea", "12" = "southeast_anatolia")
NZL_REGIONS <- c("1" = "northland", "2" = "auckland", "3" = "waikato", "4" = "bay_of_plenty", "5" = "east_cape",
                 "6" = "hawkes_bay", "7" = "taranaki", "8" = "manawatu", "9" = "wellington", "10" = "tasman", "11" = "nelson",
                 "12" = "marlborough", "13" = "west_coast", "14" = "canterbury", "15" = "otago", "16" = "southland")
ZAF_REGIONS <- c("1" = "Eastern Cape", "2" = "Free State", "3" = "Gauteng", "4" = "KwaZulu-Natal", "5" = "Limpopo",
                 "6" = "Mpumalanga", "7" = "North West", "8" = "Northern Cape", "9" = "Western Cape")
TUR_AFFECTED_UNITS <- c(12, 13, 22)  # TR62 Adana, TR63 Hatay, TRB1 Malatya
TUR_NO_2023 <- c(13, 24, 25)         # TR63 Hatay, TRC1 Gaziantep, TRC2 Sanliurfa
TR62 <- 12; TR63 <- 13; TRC3 <- 26
NZ_HAWKES_BAY <- 6; SE_ANATOLIA <- 12
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high")

# --- Data ------------------------------------------------------------------------

BASE <- c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", unname(DIMS), CARES, NEIGHBOURS, PROTECT)
WAVE_COLS <- list(
  "2021" = c(EXPOSURE[["2021"]], PREPARED[["2021"]], "REGION_MAR", "REGION_ECU", "REGION_MOZ", "REGION_NZL", "REGION3_TUR",
             "REGION_TUR", "REGION_PAK"),
  "2023" = c(EXPOSURE[["2023"]], TYPE[["2023"]], "REGION3_MAR", "REGION_ECU", "REGION_MOZ", "REGION_NZL", "REGION3_TUR",
             "REGION_TUR", "REGION_PAK", "REGION_ZAF"),
  "2025" = c(EXPOSURE[["2025"]], TYPE[["2025"]], PREPARED[["2025"]], LOCAL_PREPARED, WORRY, "REGION3_MAR", "REGION3_TUR",
             "REGION_ZAF")
)

yes100 <- function(x, code = 1) ifelse(is.na(x), NA_real_, 100 * (x == code))

QUESTIONS <- c(cares = CARES, neighbours = NEIGHBOURS, protect = PROTECT)

prepare <- function(d) {
  for (k in names(DIMS)) d[[k]] <- if (k == "index") d[[DIMS[[k]]]] else 100 * d[[DIMS[[k]]]]
  for (k in names(QUESTIONS)) if (QUESTIONS[[k]] %in% names(d)) d[[k]] <- yes100(d[[QUESTIONS[[k]]]])
  d
}

WAVE <- list()
for (y in names(WAVE_COLS)) {
  d <- load_wave(as.numeric(y), c(BASE, WAVE_COLS[[y]]))
  d <- prepare(d[d$COUNTRY_ISO3 %in% c(CASES, OTHERS), ])
  d$wave <- as.numeric(y)
  d$exposure <- yes100(d[[EXPOSURE[[y]]]])
  if (y %in% names(PREPARED)) d$prepared <- yes100(d[[PREPARED[[y]]]])
  if (y == "2025") {
    d$local_prepared <- yes100(d[[LOCAL_PREPARED]])
    d$worry <- 100 * d[[WORRY]]
  }
  WAVE[[y]] <- d
}

r0 <- function(x) floor(x + 0.5 + 1e-9)
num <- function(x) sprintf("%.17g", x)
country <- function(year, iso) { d <- WAVE[[as.character(year)]]; d[d$COUNTRY_ISO3 == iso, ] }
mean_w <- function(d, y) { d <- d[!is.na(d[[y]]), ]; sum(d[[y]] * d$PROJWT) / sum(d$PROJWT) }

# Respondents of one case study, with `region`, `A` (1 = affected region) and `wave`. Region
# don't know / refused are left out, except Morocco 2021, where they stay in the rest of the country.
case_data <- function(iso, years) {
  frames <- lapply(years, function(year) {
    d <- country(year, iso)
    var <- REGION_VAR[[iso]][[as.character(year)]]
    if (is.na(var)) {
      var <- GALLUP_REGION[[iso]]
      d <- merge_gallup(d, var)
    }
    if (iso == "MAR" && year == 2021) {
      d$region <- unname(MAR_PROVINCE_REGION[as.character(d[[var]])])
    } else {
      d$region <- d[[var]]
      d <- d[!is.na(d$region) & !(d$region %in% c(98, 99)), ]
    }
    d$A <- as.integer(d$region %in% AFFECTED[[iso]])
    d
  })
  as.data.frame(bind_rows(frames))
}

with_confidence <- function(d) {
  d <- merge_gallup(d, CONFIDENCE)
  d$confidence <- yes100(d[[CONFIDENCE]])
  d
}

# --- Estimation ------------------------------------------------------------------

# Weighted least squares; HC1 variance, or CR1 when `cluster` is given.
wls <- function(y, X, w, cluster = NULL) {
  XtW <- t(X * w)
  bread <- solve(XtW %*% X)
  b <- as.vector(bread %*% (XtW %*% y))
  u <- X * as.vector(w * (y - X %*% b))
  n <- nrow(X); k <- ncol(X)
  if (is.null(cluster)) {
    V <- bread %*% crossprod(u) %*% bread * n / (n - k)
  } else {
    cl <- as.character(cluster)
    cl[is.na(cl)] <- "NA"  # a missing region is its own cluster
    S <- rowsum(u, cl)
    G <- nrow(S)
    V <- bread %*% crossprod(S) %*% bread * G / (G - 1) * (n - 1) / (n - k)
  }
  list(b = b, V = V)
}

ci <- function(est, var) c(est, est - Z * sqrt(var), est + Z * sqrt(var))

did <- function(d, y, waves = c(2021, 2023), cluster = NULL) {
  d <- d[!is.na(d[[y]]) & d$wave %in% waves, ]
  A <- as.numeric(d$A); T <- as.numeric(d$wave == waves[2])
  f <- wls(d[[y]], cbind(1, A, T, A * T), d$PROJWT, if (is.null(cluster)) NULL else d[[cluster]])
  ci(f$b[4], f$V[4, 4])
}

# (change in the affected regions, change in the rest of the country, gap)
changes <- function(d, y, waves = c(2021, 2023)) {
  m <- wmean(d, y, by = c("A", "wave"))
  aff <- m[[paste0("1_", waves[2])]] - m[[paste0("1_", waves[1])]]
  rest <- m[[paste0("0_", waves[2])]] - m[[paste0("0_", waves[1])]]
  c(affected = aff, rest = rest, gap = aff - rest)
}

# Gap (affected minus rest) at each wave and the change from 2023 to 2025.
gap_model <- function(d, y, cluster = NULL) {
  d <- d[!is.na(d[[y]]), ]
  waves <- sort(unique(d$wave))
  A <- as.numeric(d$A)
  Ts <- lapply(waves[-1], function(w) as.numeric(d$wave == w))
  X <- cbind(1, A, do.call(cbind, Ts), do.call(cbind, lapply(Ts, function(t) A * t)))
  f <- wls(d[[y]], X, d$PROJWT, if (is.null(cluster)) NULL else d[[cluster]])
  k <- length(Ts)
  out <- setNames(f$b[2], paste0("gap_", waves[1]))
  for (i in seq_len(k)) out[[paste0("gap_", waves[i + 1])]] <- f$b[2] + f$b[2 + k + i]
  if (identical(as.numeric(waves), c(2021, 2023, 2025))) {
    cc <- numeric(length(f$b)); cc[2 + k + 2] <- 1; cc[2 + k + 1] <- -1
    out[c("change", "lo", "hi")] <- ci(sum(cc * f$b), as.numeric(t(cc) %*% f$V %*% cc))
  }
  out
}

dummies <- function(x) { lv <- sort(unique(x)); m <- outer(x, lv, "==") * 1; colnames(m) <- lv; m }

# Pooled model: country-by-wave and country-by-affected effects plus `terms`; the weight is
# rescaled to sum to one within each country and wave. Returns b and V for the terms.
pooled <- function(frames, y, terms, cluster = NULL) {
  d <- as.data.frame(bind_rows(frames))
  d <- d[!is.na(d[[y]]), ]
  cw <- paste(d$iso, d$wave, sep = "_")
  d$w <- d$PROJWT / ave(d$PROJWT, cw, FUN = sum)
  extra <- do.call(cbind, lapply(terms, function(f) f(d)))
  X <- cbind(dummies(cw), dummies(d$iso) * d$A, extra)
  f <- wls(d[[y]], X, d$w, if (is.null(cluster)) NULL else cluster(d))
  idx <- (ncol(X) - ncol(extra) + 1):ncol(X)
  list(b = f$b[idx], V = f$V[idx, idx, drop = FALSE])
}

stacked <- function(cases, years, gallup = NULL, drop_also_reached = FALSE) {
  lapply(cases, function(iso) {
    d <- case_data(iso, years)
    if (drop_also_reached && !is.null(ALSO_REACHED[[iso]])) d <- d[!(d$region %in% ALSO_REACHED[[iso]]), ]
    d$iso <- iso
    if (length(gallup)) d <- merge_gallup(d, gallup)
    if (CONFIDENCE %in% gallup) d$confidence <- yes100(d[[CONFIDENCE]])
    d
  })
}

a_t <- function(year) function(d) as.numeric(d$A * (d$wave == year))

pooled_did <- function(cases, y, cluster = NULL, gallup = NULL) {
  p <- pooled(stacked(cases, c(2021, 2023), gallup), y, list(a2023 = a_t(2023)), cluster)
  ci(p$b[1], p$V[1, 1])
}

pooled_three <- function(cases, y, drop_also_reached = FALSE, gallup = NULL) {
  p <- pooled(stacked(cases, c(2021, 2023, 2025), gallup, drop_also_reached), y, list(a2023 = a_t(2023), a2025 = a_t(2025)))
  e <- ci(p$b[2] - p$b[1], p$V[1, 1] + p$V[2, 2] - 2 * p$V[1, 2])
  c(c2123 = p$b[1], c2125 = p$b[2], change = e[1], lo = e[2], hi = e[3])
}

region_cluster <- function(d) paste(d$iso, ifelse(is.na(d$region), -1, d$region), sep = "_")
psu_cluster <- function(d) paste(d$iso, d$wave, d[[PSU]], sep = "_")

region_mean <- function(d, region, wave, y = "index") {
  s <- d[d$region %in% region & d$wave == wave & !is.na(d[[y]]), ]
  if (nrow(s)) sum(s[[y]] * s$PROJWT) / sum(s$PROJWT) else NA_real_
}
region_change <- function(d, y1, y2, y = "index") {
  regs <- sort(unique(d$region))
  ch <- setNames(sapply(regs, function(r) region_mean(d, r, y2, y) - region_mean(d, r, y1, y)), regs)
  ch[!is.na(ch)]
}
n_region <- function(d, region, year, y = "index") sum(d$region %in% region & d$wave == year & !is.na(d[[y]]))
n_table <- function(d, regions, y = "index") {
  sapply(sort(unique(d$wave)), function(w) sapply(regions, function(r) n_region(d, r, w, y)))
}
n_affected <- function(d, year) sum(d$A == 1 & d$wave == year)

# --- Global and national figures --------------------------------------------------

GLOBAL <- list()
for (y in c(2021, 2023, 2025)) {
  GLOBAL[[as.character(y)]] <- prepare(load_wave(y, c("COUNTRY_ISO3", "PROJWT", unname(DIMS),
                                                     if (y == 2025) c("CountryIncomeLevel", EXPOSURE[["2025"]]))))
}

finding(report, "X01", function() nrow(GLOBAL[["2025"]]))
finding(report, "X02", function() length(unique(GLOBAL[["2025"]]$COUNTRY_ISO3)))
finding(report, "X03", function() c(national_2021 = mean_w(country(2021, "TUR"), "index"),
                                     national_2023 = mean_w(country(2023, "TUR"), "index")))
finding(report, "X04", function() {
  d <- GLOBAL[["2025"]]
  idx <- wmean(d, "index", by = "COUNTRY_ISO3")
  keep <- names(idx)
  hh <- wmean(d, "household", by = "COUNTRY_ISO3")[keep]
  so <- wmean(d, "societal", by = "COUNTRY_ISO3")[keep]
  c(household = rank(-hh)[["USA"]], societal = rank(-so)[["USA"]], countries = length(keep))
})
finding(report, "X05", function() pct(GLOBAL[["2025"]], EXPOSURE[["2025"]], 1))
finding(report, "X06", function() {
  # Countries with Index data in both editions (any dimension); changes are unrounded.
  m <- lapply(c("2021", "2023"), function(y) lapply(names(DIMS), function(k) wmean(GLOBAL[[y]], k, by = "COUNTRY_ISO3")) |>
                setNames(names(DIMS)))
  any_data <- lapply(m, function(x) unique(unlist(lapply(x, names))))
  both <- intersect(any_data[[1]], any_data[[2]])
  ch <- function(k) m[[2]][[k]][both] - m[[1]][[k]][both]
  c(countries = length(both), fell = sum(ch("index") < 0, na.rm = TRUE), rose = sum(ch("index") > 0, na.rm = TRUE),
    individual_fell = sum(ch("individual") < 0, na.rm = TRUE))
})
finding(report, "C1_1", function() {
  out <- numeric(0)
  for (k in names(DIMS)) for (y in names(GLOBAL)) out[[paste(k, y, sep = "_")]] <- wmean(GLOBAL[[y]], k)
  out
})
finding(report, "C1_2", function() {
  d <- GLOBAL[["2025"]]
  d <- d[d[[EXPOSURE[["2025"]]]] %in% c(1, 2), ]
  m <- wmean(d, "individual", by = c("CountryIncomeLevel", EXPOSURE[["2025"]]))
  out <- numeric(0)
  for (i in names(INCOME)) {
    out[[paste0(INCOME[[i]], "_impacted")]] <- m[[paste0(i, "_1")]]
    out[[paste0(INCOME[[i]], "_not_impacted")]] <- m[[paste0(i, "_2")]]
  }
  out
})

# --- Chapter 2: the seven case studies, 2021 to 2023 --------------------------------

map_trio <- function(d) changes(d, "index")

finding(report, "C2_1", function() {
  d <- case_data("MAR", c(2021, 2023))
  ch <- region_change(d, 2021, 2023)
  c(map_trio(d), rabat = ch[["4"]], souss_massa = ch[["9"]], not_fallen = sum(r0(ch) >= 0),
    n_draa_2021 = n_region(d, 8, 2021), n_draa_2023 = n_region(d, 8, 2023), n_guelmim_2021 = n_region(d, 10, 2021),
    n_guelmim_2023 = n_region(d, 10, 2023), n_laayoune_2023 = n_region(d, 11, 2023), n_dakhla_2023 = n_region(d, 12, 2023))
})
finding(report, "C2_2", function() {
  d <- case_data("MOZ", c(2021, 2023))
  ch <- region_change(d, 2021, 2023)
  c(map_trio(d), sofala = ch[["8"]], zambezia = ch[["10"]], manica = ch[["4"]], n_cabo_delgado = sum(d$region == 1))
})
finding(report, "C2_3", function() {
  d <- case_data("NZL", c(2021, 2023))
  ch <- region_change(d, 2021, 2023)
  n <- n_table(d, as.numeric(names(NZL_REGIONS)))
  c(map_trio(d)[c("rest", "gap")], northland = ch[["1"]], auckland = ch[["2"]], hatched = sum(apply(n, 1, min) < 50),
    n_hawkes_bay_2021 = n_region(d, 6, 2021), n_hawkes_bay_2023 = n_region(d, 6, 2023),
    n_east_cape_2021 = n_region(d, 5, 2021), n_east_cape_2023 = n_region(d, 5, 2023))
})
finding(report, "C2_4", function() {
  d <- case_data("TUR", c(2021, 2023))
  ch <- region_change(d, 2021, 2023)
  n <- n_table(d, sort(unique(d$region)))
  c(map_trio(d), cea = ch[["11"]], mediterranean = ch[["6"]], hatched = sum(apply(n, 1, min) < 50),
    n_min = min(n), n_max = max(n))
})
finding(report, "C2_5", function() {
  d <- case_data("PAK", c(2021, 2023))
  out <- map_trio(d)
  d$region[d$region == 6] <- 3  # the former FATA is shown with Khyber Pakhtunkhwa
  ch <- region_change(d, 2021, 2023)
  c(out, punjab = ch[["2"]], balochistan = ch[["4"]], kp = ch[["3"]], islamabad = ch[["8"]],
    n_islamabad_2021 = n_region(d, 8, 2021), n_islamabad_2023 = n_region(d, 8, 2023))
})
finding(report, "C2_6", function() {
  d <- case_data("ZAF", c(2021, 2023))
  c(map_trio(d), western_cape = region_change(d, 2021, 2023)[["9"]])
})
finding(report, "C2_7", function() {
  d <- case_data("ECU", c(2021, 2023))
  ch <- region_change(d, 2021, 2023)
  regs <- sort(unique(d$region))
  n <- n_table(d, regs)
  shaded <- n[apply(n, 1, min) > 0 & regs != 24, , drop = FALSE]  # 24 = Galapagos, omitted from the map
  c(map_trio(d), guayas = ch[["8"]], el_oro = ch[["6"]], pichincha = ch[["16"]], manabi = ch[["12"]], shaded = nrow(shaded),
    hatched = sum(apply(shaded, 1, min) < 50))
})

table_2_1 <- function(iso) {
  d <- case_data(iso, c(2021, 2023))
  e <- did(d, "exposure")
  c(n_2021 = n_affected(d, 2021), n_2023 = n_affected(d, 2023), exposure = e[1], exposure_lo = e[2], exposure_hi = e[3])
}
est_lo_hi <- function(d, keys) {
  out <- numeric(0)
  for (k in keys) out[paste0(k, c("_est", "_lo", "_hi"))] <- did(d, k)
  out
}
table_a1 <- function(iso) est_lo_hi(case_data(iso, c(2021, 2023)), names(DIMS))
table_a2 <- function(iso) est_lo_hi(case_data(iso, c(2021, 2023)), c("cares", "neighbours", "protect", "exposure"))
table_a2_confidence <- function(iso) {
  setNames(did(with_confidence(case_data(iso, c(2021, 2023))), "confidence"), c("est", "lo", "hi"))
}
chart_3_1 <- function(iso) {
  d <- case_data(iso, c(2021, 2023))
  out <- numeric(0)
  for (k in c("societal", "community", "household", "individual")) {
    out[paste0(k, c("_affected", "_rest", "_gap"))] <- changes(d, k)
  }
  out
}
question_trio <- function(iso, y) {
  d <- case_data(iso, c(2021, 2023))
  if (y == "confidence") d <- with_confidence(d)
  changes(d, y)
}
chart_3_4 <- function(iso) {
  d <- case_data(iso, c(2021, 2023))
  c(community = changes(d, "community")[["gap"]], neighbours = changes(d, "neighbours")[["gap"]])
}

for (iso in CASES) local({
  iso <- iso
  finding(report, paste0("T2_1_", iso), function() table_2_1(iso))
  finding(report, paste0("TA1_", iso), function() table_a1(iso))
  finding(report, paste0("TA2_", iso), function() table_a2(iso))
  finding(report, paste0("C3_1_", iso), function() chart_3_1(iso))
  finding(report, paste0("C3_3_", iso), function() question_trio(iso, "neighbours"))
  finding(report, paste0("C3_4_", iso), function() chart_3_4(iso))
  finding(report, paste0("C3_5_", iso), function() question_trio(iso, "protect"))
})
for (iso in CONF_CASES) local({
  iso <- iso
  finding(report, paste0("TA2conf_", iso), function() table_a2_confidence(iso))
})

finding(report, "C3_2", function() {
  out <- numeric(0)
  for (iso in CONF_CASES) {
    t <- question_trio(iso, "confidence")
    out[paste(iso, names(t), sep = "_")] <- t
  }
  c(out, pooled = pooled_did(CONF_CASES, "confidence", gallup = CONFIDENCE)[1])
})
finding(report, "T2_2", function() {
  out <- numeric(0)
  for (m in MEASURES) {
    cases <- if (m == "confidence") CONF_CASES else CASES
    out[paste0(m, c("_est", "_lo", "_hi"))] <- pooled_did(cases, m, gallup = if (m == "confidence") CONFIDENCE)
  }
  out
})
finding(report, "C3_1_pooled", function() sapply(c(societal = "societal", community = "community", household = "household",
                                                    individual = "individual"), function(k) pooled_did(CASES, k)[1]))
finding(report, "C3_3_pooled", function() pooled_did(CASES, "neighbours")[1])
finding(report, "C3_4_pooled", function() {
  c(community = pooled_did(CASES, "community")[1], neighbours = pooled_did(CASES, "neighbours")[1])
})
finding(report, "C3_5_pooled", function() pooled_did(CASES, "protect")[1])

national <- function(iso, y, years = c(2021, 2023)) sapply(years, function(t) mean_w(country(t, iso), y))

finding(report, "C3_6", function() {
  out <- numeric(0)
  for (iso in OTHERS) {
    v <- sapply(c(2021, 2023), function(t) mean_w(with_confidence(country(t, iso)), "confidence"))
    out[[iso]] <- v[2] - v[1]
  }
  for (iso in CONF_CASES) out[[iso]] <- question_trio(iso, "confidence")[["gap"]]
  out
})

# --- Chapter 2 and 3 text ------------------------------------------------------------

affected_levels <- function(d, y) {
  m <- wmean(d[d$A == 1, ], y, by = "wave")
  c(affected_2021 = m[["2021"]], affected_2023 = m[["2023"]])
}
finding(report, "X07", function() affected_levels(case_data("TUR", c(2021, 2023)), "societal"))
finding(report, "X08", function() affected_levels(with_confidence(case_data("TUR", c(2021, 2023))), "confidence"))
finding(report, "X09", function() {
  d <- case_data("ZAF", c(2021, 2023))
  e <- changes(d, "exposure")
  m <- wmean(d[d$A == 1, ], "neighbours", by = "wave")
  c(exposure_affected = e[["affected"]], exposure_rest = e[["rest"]],
    neighbours_2021 = m[["2021"]], neighbours_2023 = m[["2023"]])
})
finding(report, "X10", function() changes(case_data("MAR", c(2021, 2023)), "exposure")[c("affected", "rest")])
finding(report, "X11", function() {
  d <- case_data("TUR", c(2021, 2023))
  med <- wmean(d[d$region == 6, ], "exposure", by = "wave")
  unit <- wmean(d[d$REGION_TUR %in% TR62, ], "exposure", by = "wave")
  nine <- d[!(d$region %in% c(6, 11, 12)), ]
  rest <- wmean(nine, "exposure", by = "wave")
  nat <- national("TUR", "exposure")
  sea23 <- d[d$region == SE_ANATOLIA & d$wave == 2023, ]
  c(national_2021 = nat[1], national_2023 = nat[2], mediterranean_2021 = med[["2021"]], mediterranean_2023 = med[["2023"]],
    mediterranean_change = med[["2023"]] - med[["2021"]], adana_mersin_2021 = unit[["2021"]], adana_mersin_2023 = unit[["2023"]],
    nine_regions_2021 = rest[["2021"]], nine_regions_2023 = rest[["2023"]],
    adana_mersin_n_2021 = sum(d$REGION_TUR %in% TR62 & d$wave == 2021),
    adana_mersin_n_2023 = sum(d$REGION_TUR %in% TR62 & d$wave == 2023),
    nine_regions = length(unique(nine$region)),
    eight_provinces_n_2021 = sum(d$REGION_TUR %in% TUR_NO_2023 & d$wave == 2021),
    eight_provinces_n_2023 = sum(d$REGION_TUR %in% TUR_NO_2023 & d$wave == 2023),
    southeast_anatolia_n_2023 = nrow(sea23), southeast_anatolia_mardin_2023 = sum(sea23$REGION_TUR %in% TRC3))
})
finding(report, "X12", function() {
  d <- case_data("NZL", c(2021, 2023))
  m <- wmean(d[d$region == NZ_HAWKES_BAY, ], "exposure", by = "wave")
  c("2021" = m[["2021"]], "2023" = m[["2023"]])
})
finding(report, "X13", function() {
  m <- wmean(case_data("PAK", c(2021, 2023)), "neighbours", by = c("region", "wave"))
  c(sindh_2021 = m[["1_2021"]], sindh_2023 = m[["1_2023"]], punjab_2021 = m[["2_2021"]], punjab_2023 = m[["2_2023"]])
})
finding(report, "X14", function() {
  v <- national("MAR", "protect")
  c(national_2021 = v[1], national_2023 = v[2], national_change = v[2] - v[1])
})
finding(report, "X15", function() {
  tha <- national("THA", "index"); phl <- national("PHL", "index")
  c(thailand_exposure_2023 = mean_w(country(2023, "THA"), "exposure"), thailand_index_change = tha[2] - tha[1],
    philippines_index_change = phl[2] - phl[1])
})
finding(report, "X16", function() {
  out <- numeric(0)
  for (k in c("index", "cares", "protect", "exposure")) out[paste0(k, c("_2021", "_2023"))] <- national("LBN", k)
  for (k in c("community", "household", "individual", "societal")) {
    v <- national("LBN", k)
    out[[paste0(k, "_change")]] <- v[2] - v[1]
  }
  d <- country(2023, "LBN")
  out[["earthquake_2023"]] <- pct(d[d[[EXPOSURE[["2023"]]]] %in% 1, ], TYPE[["2023"]], 7)
  out
})
finding(report, "X17", function() {
  out <- numeric(0)
  for (p in list(c("THA", "thailand"), c("LBN", "lebanon"))) for (t in c(2021, 2023)) {
    out[[paste(p[2], t, sep = "_")]] <- mean_w(with_confidence(country(t, p[1])), "confidence")
  }
  out
})
finding(report, "X18", function() sapply(c(NZL = "NZL", PAK = "PAK", ECU = "ECU"),
                                         function(iso) did(case_data(iso, c(2021, 2023)), "neighbours")[1]))
finding(report, "X19", function() pooled_did(setdiff(CASES, "ZAF"), "neighbours")[1])
finding(report, "X20", function() {
  idx <- sapply(CASES, function(iso) did(case_data(iso, c(2021, 2023)), "index")[1])
  nbr <- sapply(CASES, function(iso) did(case_data(iso, c(2021, 2023)), "neighbours")[1])
  c(index_fell = sum(idx < 0), neighbours_rose = sum(nbr > 0))
})
finding(report, "X21", function() {
  tur <- case_data("TUR", c(2021, 2023)); nzl <- case_data("NZL", c(2021, 2023))
  c(turkiye_mediterranean = 100 * sum(tur$region == 6) / sum(tur$A == 1),
    nz_auckland = 100 * sum(nzl$region == 2) / sum(nzl$A == 1))
})
finding(report, "X22", function() {
  # Regions with respondents in 2021 or 2023 (South Africa: 2023, as its 2021 regions are not public).
  n <- sapply(CASES, function(iso) length(unique(na.omit(case_data(iso, if (iso == "ZAF") 2023 else c(2021, 2023))$region))))
  c(total = sum(n), min = min(n), max = max(n))
})
finding(report, "X23", function() {
  n <- sapply(CASES, function(iso) sum(sapply(c(2021, 2023), function(y) sum(!is.na(country(y, iso)$index)))))
  n[["ECU"]] <- sum(!is.na(case_data("ECU", c(2021, 2023))$index))  # region don't know / refused left out
  c(seven = sum(n), five = sum(n[CONF_CASES]))
})
finding(report, "X24", function() {
  d <- case_data("TUR", c(2021, 2023))
  aff <- d[d$A == 1, ]
  share <- tapply(aff$REGION_TUR %in% TUR_AFFECTED_UNITS, aff$wave, mean) * 100
  d25 <- case_data("TUR", 2025)
  c(share_2021 = share[["2021"]], share_2023 = share[["2023"]], tr63_n_2021 = sum(d$REGION_TUR %in% TR63 & d$wave == 2021),
    tr63_n_2023 = sum(d$REGION_TUR %in% TR63 & d$wave == 2023),
    southeast_anatolia_n_2021 = n_region(d, SE_ANATOLIA, 2021, "wave"),
    southeast_anatolia_n_2025 = n_region(d25, SE_ANATOLIA, 2025, "wave"))
})
finding(report, "X25", function() {
  d <- merge_gallup(case_data("TUR", 2025), "REGION_TUR")
  c(share_2025 = 100 * mean(d$REGION_TUR[d$A == 1] %in% TUR_AFFECTED_UNITS), tr63_n_2025 = sum(d$REGION_TUR %in% TR63))
})

# --- Pooled models and standard errors (appendix) ---------------------------------------

finding(report, "X36", function() {
  out <- numeric(0)
  for (k in c("index", "community", "neighbours")) out[paste0(k, c("", "_lo", "_hi"))] <- pooled_did(setdiff(CASES, "ECU"), k)
  out
})
finding(report, "X37", function() {
  out <- numeric(0)
  for (k in c("index", "community", "neighbours")) {
    out[paste0(k, c("_hc1_lo", "_hc1_hi"))] <- pooled_did(CASES, k)[2:3]
    out[paste0(k, c("_region_lo", "_region_hi"))] <- pooled_did(CASES, k, region_cluster)[2:3]
    out[paste0(k, c("_psu_lo", "_psu_hi"))] <- pooled_did(CASES, k, psu_cluster, gallup = c(PSU, STRATA))[2:3]
  }
  out
})
finding(report, "X38", function() {
  p <- pooled(stacked(RECOVERY, c(2021, 2023, 2025)), "index", list(a2023 = a_t(2023), a2025 = a_t(2025)))
  w <- ci(p$b[1], p$V[1, 1])
  n <- ci(p$b[2] - p$b[1], p$V[1, 1] + p$V[2, 2] - 2 * p$V[1, 2])
  c(widening_lo = w[2], widening_hi = w[3], narrowing_lo = n[2], narrowing_hi = n[3])
})
finding(report, "X39", function() {
  frames <- stacked(CASES, c(2021, 2023))
  check <- setNames(sapply(frames, function(f) did(f, "exposure")[1]), CASES)
  out <- numeric(0)
  for (key in c("months", "exposure")) {
    attr <- if (key == "months") MONTHS else check
    p <- pooled(frames, "index", list(a2023 = a_t(2023), slope = function(d) d$A * (d$wave == 2023) * unname(attr[d$iso])))
    out[paste0(key, c("", "_lo", "_hi"))] <- ci(p$b[2], p$V[2, 2])
  }
  out
})
finding(report, "X40", function() {
  count <- 0
  for (iso in CASES) {
    d <- case_data(iso, c(2021, 2023))
    ms <- setdiff(MEASURES, "confidence")
    if (iso %in% CONF_CASES) { d <- with_confidence(d); ms <- MEASURES }
    for (m in ms) {
      h <- did(d, m); cl <- did(d, m, cluster = "region")
      count <- count + ((h[2] <= 0 && 0 <= h[3]) && !(cl[2] <= 0 && 0 <= cl[3]))
    }
  }
  count
})
finding(report, "X41", function() {
  idx <- pooled_three(c(RECOVERY, "ZAF"), "index")
  nbr <- pooled_three(c(RECOVERY, "ZAF"), "neighbours")
  c(index_change = idx[["change"]], neighbours_2023 = nbr[["c2123"]], neighbours_2025 = nbr[["c2125"]])
})

# --- Chapter 4: three waves --------------------------------------------------------------

three_wave <- function(iso) case_data(iso, c(2021, 2023, 2025))

for (iso in c(RECOVERY, "ZAF")) local({
  iso <- iso
  finding(report, paste0("T4_1_", iso), function() {
    d <- three_wave(iso)
    c(n_2021 = n_affected(d, 2021), n_2023 = n_affected(d, 2023), n_2025 = n_affected(d, 2025))
  })
  for (m in setdiff(MEASURES, if (iso == "MAR") "confidence")) local({
    m <- m
    finding(report, paste("TA3", iso, m, sep = "_"), function() {
      d <- three_wave(iso)
      if (m == "confidence") d <- with_confidence(d)
      out <- gap_model(d, m)
      if (!is.null(ALSO_REACHED[[iso]]) && "change" %in% names(out)) {
        adj <- gap_model(d[!(d$region %in% ALSO_REACHED[[iso]]), ], m)
        out[c("adj", "adj_lo", "adj_hi")] <- adj[c("change", "lo", "hi")]
      }
      out
    })
  })
})

finding(report, "TA4", function() {
  out <- numeric(0)
  for (m in MEASURES) {
    # Morocco did not ask confidence, nor government care in 2025: those rows pool Türkiye and New Zealand.
    cases <- if (m %in% c("confidence", "cares")) c("TUR", "NZL") else RECOVERY
    g <- if (m == "confidence") CONFIDENCE
    main <- pooled_three(cases, m, gallup = g)
    adj <- pooled_three(cases, m, drop_also_reached = TRUE, gallup = g)
    out[paste(m, names(main), sep = "_")] <- main
    out[paste0(m, c("_adj", "_adj_lo", "_adj_hi"))] <- adj[c("change", "lo", "hi")]
  }
  out
})

finding(report, "X26", function() {
  E <- EXPOSURE[["2025"]]; Ty <- TYPE[["2025"]]
  out <- numeric(0)
  for (p in list(c("MAR", "mar"), c("ZAF", "zaf"), c("TUR", "tur"))) {
    d <- case_data(p[1], 2025)
    out[paste0(p[2], c("_affected", "_rest"))] <- c(mean_w(d[d$A == 1, ], "exposure"), mean_w(d[d$A == 0, ], "exposure"))
  }
  mar <- case_data("MAR", 2025); hit <- mar[mar$A == 1 & mar[[E]] %in% 1, ]
  out[c("mar_n_impacted", "mar_earthquake")] <- c(nrow(hit), pct(hit, Ty, 7))
  zaf <- case_data("ZAF", 2025); hit <- zaf[zaf$A == 1 & zaf[[E]] %in% 1, ]
  out[c("zaf_flood", "zaf_storm")] <- c(pct(hit, Ty, 1), pct(hit, Ty, 2))
  sea <- case_data("TUR", 2025); sea <- sea[sea$region == SE_ANATOLIA, ]
  hit <- sea[sea[[E]] %in% 1, ]
  sea$quake <- yes100(ifelse(sea[[E]] %in% 1, sea[[Ty]], 0), 7)
  out[c("sea_impacted", "sea_n_impacted", "sea_earthquake", "sea_earthquake_all")] <-
    c(mean_w(sea, "exposure"), nrow(hit), pct(hit, Ty, 7), mean_w(sea, "quake"))
  out
})
finding(report, "X27", function() {
  E <- EXPOSURE[["2025"]]; Ty <- TYPE[["2025"]]
  d <- case_data("NZL", 2025)
  hb <- d[d$region == NZ_HAWKES_BAY, ]
  hit <- hb[hb[[E]] %in% 1, ]
  hb$storm <- yes100(ifelse(hb[[E]] %in% 1, hb[[Ty]], 0), 2)
  c(affected = mean_w(d[d$A == 1, ], "exposure"), rest = mean_w(d[d$A == 0, ], "exposure"), hawkes_bay = mean_w(hb, "exposure"),
    hawkes_bay_n_impacted = nrow(hit), hawkes_bay_storm = pct(hit, Ty, 2), hawkes_bay_storm_all = mean_w(hb, "storm"),
    hawkes_bay_n = nrow(hb))
})
finding(report, "X28", function() {
  out <- numeric(0)
  for (p in list(c("MOZ", "REGION_MOZ"), c("PAK", "REGION_PAK"), c("ECU", "REGION_ECU"))) {
    var <- p[2]
    d <- merge_gallup(country(2025, p[1]), var)
    d <- d[!is.na(d[[var]]) & !(d[[var]] %in% c(98, 99)), ]
    aff <- d[[var]] %in% AFFECTED[[p[1]]]
    if (p[1] == "MOZ") {
      out[c("moz_nampula", "moz_affected")] <- c(mean_w(d[d[[var]] == 6, ], "exposure"), mean_w(d[aff, ], "exposure"))
    }
    if (p[1] == "PAK") out[c("pak_kp", "pak_sindh")] <- c(mean_w(d[d[[var]] == 3, ], "exposure"), mean_w(d[aff, ], "exposure"))
    if (p[1] == "ECU") out[c("ecu_affected", "ecu_rest")] <- c(mean_w(d[aff, ], "exposure"), mean_w(d[!aff, ], "exposure"))
  }
  out
})

vs_baseline <- function(iso, m) {
  d <- three_wave(iso)
  if (m == "confidence") d <- with_confidence(d)
  g <- gap_model(d, m)
  g[["gap_2025"]] - g[["gap_2021"]]
}
finding(report, "X29", function() c(mar_index = vs_baseline("MAR", "index"), tur_societal = vs_baseline("TUR", "societal")))
finding(report, "X30", function() {
  d <- with_confidence(three_wave("ZAF"))
  returned <- 0
  for (m in MEASURES) {
    g <- gap_model(d, m)
    returned <- returned + (sign(g[["gap_2025"]] - g[["gap_2023"]]) == sign(g[["gap_2021"]] - g[["gap_2023"]]))
  }
  c(nzl_index = vs_baseline("NZL", "index"), nzl_individual = vs_baseline("NZL", "individual"),
    tur_confidence = vs_baseline("TUR", "confidence"), zaf_community = vs_baseline("ZAF", "community"),
    zaf_household = vs_baseline("ZAF", "household"), zaf_protect = vs_baseline("ZAF", "protect"), zaf_returned = returned)
})
finding(report, "X31", function() {
  d <- case_data("ZAF", c(2023, 2025))
  gi <- gap_model(d, "index"); gn <- gap_model(d, "neighbours"); gc <- gap_model(d, "community")
  c(index_gap_2023 = gi[["gap_2023"]], index_gap_2025 = gi[["gap_2025"]], neighbours_gap_2023 = gn[["gap_2023"]],
    neighbours_change = gn[["gap_2025"]] - gn[["gap_2023"]], community_change = gc[["gap_2025"]] - gc[["gap_2023"]])
})
finding(report, "X32", function() {
  d <- case_data("TUR", c(2021, 2025))
  m <- wmean(d, "prepared", by = c("A", "wave"))
  d25 <- d[d$wave == 2025, ]
  c(affected_2021 = m[["1_2021"]], affected_2025 = m[["1_2025"]], rest_2021 = m[["0_2021"]], rest_2025 = m[["0_2025"]],
    local_affected = mean_w(d25[d25$A == 1, ], "local_prepared"), local_rest = mean_w(d25[d25$A == 0, ], "local_prepared"))
})
finding(report, "X33", function() {
  z <- case_data("ZAF", c(2021, 2025))
  m <- wmean(z, "prepared", by = c("A", "wave"))
  n <- case_data("NZL", 2025)
  p <- pooled(stacked(c("TUR", "NZL"), c(2021, 2025)), "prepared", list(a2025 = a_t(2025)))
  c(kzn_2021 = m[["1_2021"]], kzn_2025 = m[["1_2025"]], zaf_rest_2021 = m[["0_2021"]], zaf_rest_2025 = m[["0_2025"]],
    nzl_local_gap = mean_w(n[n$A == 1, ], "local_prepared") - mean_w(n[n$A == 0, ], "local_prepared"), pooled_tur_nzl = p$b[1])
})
finding(report, "X35", function() {
  out <- character(0)
  for (iso in c("MAR", "TUR")) {
    d <- three_wave(iso)
    h <- gap_model(d, "protect"); cl <- gap_model(d, "protect", cluster = "region")
    out[[paste0(iso, "_hc1")]] <- if (h[["lo"]] <= 0 && 0 <= h[["hi"]]) "no" else "yes"
    out[[paste0(iso, "_region")]] <- if (cl[["lo"]] <= 0 && 0 <= cl[["hi"]]) "no" else "yes"
  }
  out
})

changes_2023_2025 <- function(iso) {
  d <- case_data(iso, c(2023, 2025))
  list(d = d, ch = region_change(d, 2023, 2025))
}
finding(report, "C4_4", function() {
  x <- changes_2023_2025("MAR"); d <- x$d; ch <- x$ch
  keep <- intersect(names(ch), names(MAR_REGIONS)[!(MAR_REGIONS %in% c("tanger", "guelmim"))])
  c(setNames(ch[keep], MAR_REGIONS[keep]), fell = sum(ch < 0), n_guelmim_2023 = n_region(d, 10, 2023),
    n_guelmim_2025 = n_region(d, 10, 2025), n_draa_2023 = n_region(d, 8, 2023), n_draa_2025 = n_region(d, 8, 2025),
    n_souss_2023 = n_region(d, 9, 2023), n_souss_2025 = n_region(d, 9, 2025), n_saharan = sum(d$region %in% c(11, 12)))
})
finding(report, "C4_5", function() {
  x <- changes_2023_2025("TUR"); d <- x$d; ch <- x$ch
  rest <- ch[!(names(ch) %in% c("6", "11", as.character(SE_ANATOLIA)))]  # Southeast Anatolia is greyed
  c(setNames(ch, TUR_REGIONS[names(ch)]), not_fallen = sum(r0(rest) >= 0), n_nea_2023 = n_region(d, 10, 2023),
    n_nea_2025 = n_region(d, 10, 2025), n_ca_2023 = n_region(d, 7, 2023), n_ca_2025 = n_region(d, 7, 2025),
    n_ebs_2023 = n_region(d, 9, 2023), n_ebs_2025 = n_region(d, 9, 2025))
})
finding(report, "C4_6", function() {
  x <- changes_2023_2025("NZL"); d <- x$d; ch <- x$ch
  n <- n_table(d, as.numeric(names(NZL_REGIONS)))
  c(setNames(ch, NZL_REGIONS[names(ch)]), n_hawkes_bay_2023 = n_region(d, 6, 2023), n_hawkes_bay_2025 = n_region(d, 6, 2025),
    n_east_cape_2023 = n_region(d, 5, 2023), n_east_cape_2025 = n_region(d, 5, 2025), hatched = sum(apply(n, 1, min) < 50))
})
finding(report, "C4_7", function() {
  x <- changes_2023_2025("ZAF"); d <- x$d; ch <- x$ch
  g <- changes(d, "index", c(2023, 2025))
  vals <- c(kzn = g[["affected"]], rest = g[["rest"]], northern_cape = ch[["8"]], mpumalanga = ch[["6"]], north_west = ch[["7"]],
            western_cape = ch[["9"]], fell = sum(ch < 0), n_nc_2023 = n_region(d, 8, 2023), n_nc_2025 = n_region(d, 8, 2025),
            n_mp_2023 = n_region(d, 6, 2023), n_mp_2025 = n_region(d, 6, 2025))
  c(setNames(num(vals), names(vals)), smallest_rise = ZAF_REGIONS[[names(ch)[which.min(ch)]]])
})

for (iso in c(RECOVERY, "ZAF")) local({
  iso <- iso
  finding(report, paste0("C4_8_", iso), function() {
    d <- case_data(iso, 2025)
    a <- mean_w(d[d$A == 1, ], "worry"); r <- mean_w(d[d$A == 0, ], "worry")
    c(affected = a, rest = r, gap = a - r, n = sum(d$A == 1 & !is.na(d$worry)))
  })
})
for (iso in c("TUR", "NZL", "ZAF")) local({
  iso <- iso
  finding(report, paste0("C4_9_", iso), function() {
    g <- gap_model(case_data(iso, c(2021, 2025)), "prepared")
    c(gap_2021 = g[["gap_2021"]], gap_2025 = g[["gap_2025"]], change = g[["gap_2025"]] - g[["gap_2021"]])
  })
})
finding(report, "C4_9_pooled", function() {
  pooled(stacked(c("TUR", "NZL", "ZAF"), c(2021, 2025)), "prepared", list(a2025 = a_t(2025)))$b[1]
})

status <- run_report(report)
if (!interactive()) quit(status = status)
