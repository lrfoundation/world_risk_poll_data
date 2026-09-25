# Reproduce World Risk Poll 2026: After the storm: How disasters reshape resilience and trust.
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_after_the_storm/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes. The report splits each case-study country
# into the regions a disaster struck ("affected") and the rest of the country,
# and compares their change between the 2021 and 2023 polls
# (difference-in-differences), then follows four case studies into 2025.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)
Z <- qnorm(0.975)

.memo <- new.env()
memo <- function(key, expr) {
  if (!exists(key, envir = .memo, inherits = FALSE)) assign(key, expr, envir = .memo)
  get(key, envir = .memo)
}

# --- Case studies ------------------------------------------------------------------

CASES <- c("MAR", "MOZ", "NZL", "TUR", "PAK", "ZAF", "ECU")
DIMS <- c("index", "societal", "community", "household", "individual")
QUESTIONS <- c("confidence", "gov", "neighbours", "protect")
NOT_ASKED <- list(confidence = c("MAR", "PAK")) # confidence in national government, 2021 and 2023

# Region variable per case study and wave (see reproduce.py). South Africa 2021
# and New Zealand 2025 are Gallup data, assumed to use the 2023 release's codes.
REGION_VAR <- list(
  MAR = c("2021" = "REGION_MAR", "2023" = "REGION3_MAR", "2025" = "REGION3_MAR"),
  MOZ = c("2021" = "REGION_MOZ", "2023" = "REGION_MOZ"),
  NZL = c("2021" = "REGION_NZL", "2023" = "REGION_NZL", "2025" = "REGION_NZL"),
  TUR = c("2021" = "REGION3_TUR", "2023" = "REGION3_TUR", "2025" = "REGION3_TUR"),
  PAK = c("2021" = "REGION_PAK", "2023" = "REGION_PAK"),
  ZAF = c("2021" = "REGION_ZAF", "2023" = "REGION_ZAF", "2025" = "REGION_ZAF"),
  ECU = c("2021" = "REGION_ECU", "2023" = "REGION_ECU")
)
GALLUP_REGION <- c("ZAF_2021", "NZL_2025")
AFFECTED <- list(MAR = 7, MOZ = c(4, 8, 10), NZL = c(1, 2), TUR = c(6, 11), PAK = 1, ZAF = 4, ECU = c(6, 8))
ALSO_REACHED <- list(TUR = 12, NZL = c(3, 4, 5, 6))
MONTHS <- c(MAR = 1, MOZ = 6, NZL = 7, TUR = 10, PAK = 14, ZAF = 22, ECU = 5) # Table 2.1

MAR_REGION_PROVINCES <- list(
  "1" = c("TANGER ASSILAH", "M DIQ-FNIDEQ", "TETOUAN", "FAHS ANJRA", "LARACHE", "AL HOCEIMA", "CHEFCHAOUEN", "OUEZZANE"),
  "2" = c("OUJDA ANGAD", "NADOR", "DRIOUCH", "JERADA", "BERKANE", "TAOURIRT", "GUERCIF", "FIGUIG"),
  "3" = c("FES", "MEKNES", "EL HAJEB", "IFRANE", "MOULAY YACOUB", "SEFROU", "BOULEMANE", "TAOUNATE", "TAZA"),
  "4" = c("RABAT", "SALE", "SKHIRATE-TEMARA", "KENITRA", "KHEMISSET", "SIDI KACEM", "SIDI SLIMANE"),
  "5" = c("BENI MELLAL", "AZILAL", "FQUIH BEN SALAH", "KHENIFRA", "KHOURIBGA"),
  "6" = c("CASABLANCA", "MOHAMMEDIA", "EL JADIDA", "NOUACEUR", "MEDIOUNA", "BENSLIMANE", "BERRECHID", "SETTAT", "SIDI BENNOUR"),
  "7" = c("MARRAKECH", "CHICHAOUA", "AL HAOUZ", "EL KELAA DES SRAGHNA", "ESSAOUIRA", "REHAMNA", "SAFI", "YOUSSOUFIA"),
  "8" = c("ERRACHIDIA", "OUARZAZATE", "MIDELT", "TINGHIR", "ZAGORA"),
  "9" = c("AGADIR IDA OU TANAN", "INEZGANE AIT MELLOUL", "CHTOUKA AIT BAHA", "TAROUDANNT", "TIZNIT", "TATA"),
  "10" = c("GUELMIM", "ASSA ZAG", "TAN TAN", "SIDI IFNI"),
  "11" = c("LAAYOUNE", "BOUJDOUR", "TARFAYA", "ES SEMARA"),
  "12" = c("OUED ED-DAHAB", "AOUSSERD")
)
MAR_PROVINCE <- local({
  name_region <- unlist(lapply(names(MAR_REGION_PROVINCES), function(r) setNames(rep(as.numeric(r), length(MAR_REGION_PROVINCES[[r]])), MAR_REGION_PROVINCES[[r]])))
  labels <- value_labels(2021, "REGION_MAR")
  labels <- labels[as.numeric(names(labels)) < 98]
  setNames(unname(name_region[labels]), names(labels))
})

TUR_AFFECTED_PROVINCES <- c("12" = 1, "13" = 3, "22" = 2, "24" = 3, "25" = 2) # NUTS-2 unit -> affected provinces
TUR_AFFECTED_UNITS <- c(12, 13, 22)

EXPOSURE <- c("2021" = "WP22245", "2023" = "WP23344", "2025" = "WP24213")
PREPARED <- c("2021" = "WP22241", "2025" = "WP24198")
HAZARD <- c("2023" = "WP22247", "2025" = "WP24180")

# --- Data ----------------------------------------------------------------------------

yes <- function(x, code = 1) ifelse(is.na(x), NA_real_, 100 * (x == code))

wave <- function(year) memo(paste("wave", year), {
  y <- as.character(year)
  regions <- unique(unlist(lapply(names(REGION_VAR), function(iso) {
    v <- REGION_VAR[[iso]][y]
    if (!is.na(v) && !(paste(iso, year, sep = "_") %in% GALLUP_REGION)) unname(v)
  })))
  extra <- switch(y, "2021" = c("REGION_TUR", "WP22241"), "2023" = c("REGION_TUR", "WP22247"),
                  "2025" = c("WP24198", "WP24199", "WP24180", "worry_index_published"))
  cols <- c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "CountryIncomeLevel", "resilience_index", "resilience_soc",
            "resilience_com", "resilience_hhl", "resilience_idv", "WP22231", "WP22232", "WP22252", EXPOSURE[[y]])
  d <- load_wave(year, unique(c(cols, regions, extra)))
  out <- data.frame(wpid = d$WPID_RANDOM, iso = d$COUNTRY_ISO3, wave = year, w = d$PROJWT,
                    income = d$CountryIncomeLevel, stringsAsFactors = FALSE)
  src <- c(index = "resilience_index", societal = "resilience_soc", community = "resilience_com",
           household = "resilience_hhl", individual = "resilience_idv")
  for (m in DIMS) out[[m]] <- 100 * d[[src[[m]]]]
  out$gov <- yes(d$WP22231)          # government cares 'a lot'
  out$neighbours <- yes(d$WP22232)   # neighbours care 'a lot'
  out$protect <- yes(d$WP22252)      # could protect yourself/family
  out$depends <- yes(d$WP22252, 3)
  out$expo <- yes(d[[EXPOSURE[[y]]]])
  out$expo_code <- d[[EXPOSURE[[y]]]]
  out$prep <- if (y %in% names(PREPARED)) yes(d[[PREPARED[[y]]]]) else NA_real_
  out$local_prep <- if (y == "2025") yes(d$WP24199) else NA_real_
  out$worry <- if (y == "2025") 100 * d$worry_index_published else NA_real_
  out$hazard <- if (y %in% names(HAZARD)) d[[HAZARD[[y]]]] else NA_real_
  out$nuts2 <- if (y %in% c("2021", "2023")) d$REGION_TUR else NA_real_
  for (v in regions) out[[v]] <- d[[v]]
  out
})

gallup_merge <- function(d, items) {
  names(d)[names(d) == "wpid"] <- "WPID_RANDOM"
  g <- merge_gallup(d, items)
  names(g)[names(g) == "WPID_RANDOM"] <- "wpid"
  g
}

with_confidence <- function(d) {
  g <- gallup_merge(d, "WP139") # Gallup: confidence in national government, 1 = yes
  g$confidence <- ifelse(is.na(g$WP139), NA_real_, 100 * (g$WP139 == 1))
  g
}

case_wave <- function(iso, year, confidence = FALSE) memo(paste("case", iso, year, confidence), {
  d <- wave(year)
  d <- d[d$iso == iso, , drop = FALSE]
  var <- unname(REGION_VAR[[iso]][as.character(year)])
  if (paste(iso, year, sep = "_") %in% GALLUP_REGION) d <- gallup_merge(d, var)
  d$region_raw <- d[[var]]
  if (iso == "MAR" && year == 2021) {
    # Province -> region; the 7 "don't know" provinces stay in the rest of the country.
    d$region <- unname(MAR_PROVINCE[as.character(d[[var]])])
  } else {
    d <- d[!is.na(d[[var]]) & d[[var]] < 98, , drop = FALSE]
    d$region <- d[[var]]
    if (iso == "PAK") d$region[d$region == 6] <- 3 # former FATA -> Khyber Pakhtunkhwa
  }
  d$aff <- as.numeric(d$region %in% AFFECTED[[iso]])
  if (confidence) d <- with_confidence(d)
  d
})

frame <- function(iso, years, m = "index") {
  as.data.frame(bind_rows(lapply(years, function(y) case_wave(iso, y, m == "confidence"))))
}

# --- Estimation --------------------------------------------------------------------------

wm <- function(d, m) {
  d <- d[!is.na(d[[m]]), , drop = FALSE]
  if (nrow(d) == 0) return(NA_real_)
  sum(d[[m]] * d$w) / sum(d$w)
}

# Weighted least squares with HC1 (or cluster-robust CR1) variance.
fit <- function(y, X, w, cluster = NULL) {
  X <- as.matrix(X)
  xtwx <- crossprod(X, X * w)
  beta <- as.vector(solve(xtwx, crossprod(X, w * y)))
  e <- as.vector(y - X %*% beta)
  n <- nrow(X); k <- ncol(X)
  inv <- solve(xtwx)
  s <- X * (w * e)
  if (is.null(cluster)) {
    meat <- crossprod(s); cc <- n / (n - k)
  } else {
    S <- rowsum(s, as.character(cluster))
    G <- nrow(S)
    meat <- crossprod(S); cc <- G / (G - 1) * (n - 1) / (n - k)
  }
  list(beta = beta, V = cc * inv %*% meat %*% inv)
}

estimate <- function(f, L) {
  est <- sum(L * f$beta)
  se <- sqrt(as.numeric(t(L) %*% f$V %*% L))
  list(est = est, lo = est - Z * se, hi = est + Z * se)
}

case_design <- function(d, waves) {
  X <- cbind(const = 1, aff = d$aff)
  for (y in waves[-1]) {
    wy <- as.numeric(d$wave == y)
    X <- cbind(X, wy, wy * d$aff)
    colnames(X)[ncol(X) - 1:0] <- c(paste0("w", y), paste0("aff", y))
  }
  X
}

cluster_ids <- function(d) paste(d$iso, ifelse(is.na(d$region), -1, d$region), sep = "_")

did_all <- function(iso, m, clustered = FALSE) memo(paste("did", iso, m, clustered), {
  d <- frame(iso, c(2021, 2023), m)
  d <- d[!is.na(d[[m]]), , drop = FALSE]
  X <- case_design(d, c(2021, 2023))
  f <- fit(d[[m]], X, d$w, if (clustered) cluster_ids(d) else NULL)
  estimate(f, as.numeric(colnames(X) == "aff2023"))
})

# Difference-in-differences 2021 to 2023 (affected change minus rest change), HC1 interval.
did <- function(iso, m, field = "est") did_all(iso, m)[[field]]

mean_in <- function(iso, m, year, grp) {
  d <- frame(iso, year, m)
  wm(d[d$aff == (if (grp == "aff") 1 else 0), , drop = FALSE], m)
}

gap <- function(iso, m, year) mean_in(iso, m, year, "aff") - mean_in(iso, m, year, "rest")

group_change <- function(iso, grp, y0, y1, m = "index") mean_in(iso, m, y1, grp) - mean_in(iso, m, y0, grp)

chg_all <- function(iso, m, adjusted = FALSE) memo(paste("chg", iso, m, adjusted), {
  waves <- if (iso == "ZAF") c(2023, 2025) else c(2021, 2023, 2025)
  d <- frame(iso, waves, m)
  d <- d[!is.na(d[[m]]), , drop = FALSE]
  if (adjusted) d <- d[!(d$region %in% ALSO_REACHED[[iso]]), , drop = FALSE]
  X <- case_design(d, waves)
  f <- fit(d[[m]], X, d$w)
  estimate(f, as.numeric(colnames(X) == "aff2025") - as.numeric(colnames(X) == "aff2023"))
})

chg <- function(iso, m, field = "est") {
  if (startsWith(field, "adj")) return(chg_all(iso, m, TRUE)[[c(adj = "est", adj_lo = "lo", adj_hi = "hi")[[field]]]])
  chg_all(iso, m)[[field]]
}

POOLED <- list(
  seven = list(CASES, c(2021, 2023)), six_noZAF = list(setdiff(CASES, "ZAF"), c(2021, 2023)),
  six_noECU = list(setdiff(CASES, "ECU"), c(2021, 2023)), prep3 = list(c("TUR", "NZL", "ZAF"), c(2021, 2025)),
  prep2 = list(c("TUR", "NZL"), c(2021, 2025)), three = list(c("MAR", "TUR", "NZL"), c(2021, 2023, 2025)),
  four = list(c("MAR", "TUR", "NZL", "ZAF"), c(2021, 2023, 2025))
)

# Stacked case studies, projection weight rescaled to sum to 1 in each country-wave;
# case studies where `m` was not asked in one of the waves are left out.
pooled_data <- function(name, m, adjusted = FALSE) {
  isos <- POOLED[[name]][[1]]; waves <- POOLED[[name]][[2]]
  parts <- list()
  for (iso in isos) {
    if (!is.null(NOT_ASKED[[m]]) && iso %in% NOT_ASKED[[m]]) next
    d <- frame(iso, waves, m)
    d <- d[!is.na(d[[m]]), , drop = FALSE]
    if (adjusted && !is.null(ALSO_REACHED[[iso]])) d <- d[!(d$region %in% ALSO_REACHED[[iso]]), , drop = FALSE]
    if (setequal(unique(d$wave), waves)) parts[[length(parts) + 1]] <- d
  }
  d <- as.data.frame(bind_rows(parts))
  d$pw <- d$w / ave(d$w, d$iso, d$wave, FUN = sum)
  d
}

pooled_design <- function(d, waves, slope = NULL) {
  X <- NULL; nm <- character(0)
  for (iso in sort(unique(d$iso))) {
    for (y in waves) { X <- cbind(X, as.numeric(d$iso == iso & d$wave == y)); nm <- c(nm, paste(iso, y, sep = "_")) }
    X <- cbind(X, as.numeric(d$iso == iso & d$aff == 1)); nm <- c(nm, paste0(iso, "_aff"))
  }
  for (y in waves[-1]) { X <- cbind(X, as.numeric(d$aff == 1 & d$wave == y)); nm <- c(nm, paste0("aff", y)) }
  if (!is.null(slope)) { X <- cbind(X, X[, ncol(X)] * unname(slope[d$iso])); nm <- c(nm, "slope") }
  colnames(X) <- nm
  X
}

pooled_all <- function(name, m) memo(paste("pooled", name, m), {
  waves <- POOLED[[name]][[2]]
  d <- pooled_data(name, m)
  X <- pooled_design(d, waves)
  f <- fit(d[[m]], X, d$pw)
  L <- as.numeric(colnames(X) == paste0("aff", waves[length(waves)]))
  list(out = estimate(f, L), d = d, X = X, f = f, L = L)
})

# Pooled difference-in-differences (Table 2.2): est/lo/hi (HC1), clo/chi (clustered by
# region within country) and plo/phi (clustered by Gallup's PSU, WP12259).
pooled <- function(name, m, field = "est") {
  p <- pooled_all(name, m)
  if (field %in% c("est", "lo", "hi")) return(p$out[[field]])
  d <- p$d
  if (field %in% c("clo", "chi")) {
    cl <- cluster_ids(d)
  } else {
    psu <- gallup_merge(d["wpid"], "WP12259")
    cl <- paste(d$iso, psu$WP12259, sep = "_")
  }
  f <- fit(d[[m]], p$X, d$pw, cl)
  estimate(f, p$L)[[c(clo = "lo", chi = "hi", plo = "lo", phi = "hi")[[field]]]]
}

pooled3_all <- function(name, m, adjusted = FALSE) memo(paste("pooled3", name, m, adjusted), {
  waves <- POOLED[[name]][[2]]
  d <- pooled_data(name, m, adjusted)
  X <- pooled_design(d, waves)
  f <- fit(d[[m]], X, d$pw)
  a23 <- as.numeric(colnames(X) == "aff2023"); a25 <- as.numeric(colnames(X) == "aff2025")
  c23 <- estimate(f, a23); c25 <- estimate(f, a25); ch <- estimate(f, a25 - a23)
  list(c2023 = c23$est, c2023_lo = c23$lo, c2023_hi = c23$hi, c2025 = c25$est,
       change = ch$est, lo = ch$lo, hi = ch$hi)
})

# Pooled three-wave model (Table A.4): affected x 2023 and affected x 2025 terms.
pooled3 <- function(name, m, field) {
  if (startsWith(field, "adj")) return(pooled3_all(name, m, TRUE)[[c(adj = "change", adj_lo = "lo", adj_hi = "hi")[[field]]]])
  pooled3_all(name, m)[[field]]
}

# Seven-case Index model with affected x 2023 interacted with months since the event
# (Table 2.1) or with the exposure check (Table A.2).
slope_all <- function(kind) memo(paste("slope", kind), {
  values <- if (kind == "months") MONTHS else setNames(sapply(CASES, function(iso) did(iso, "expo")), CASES)
  d <- pooled_data("seven", "index")
  X <- pooled_design(d, c(2021, 2023), values)
  estimate(fit(d$index, X, d$pw), as.numeric(colnames(X) == "slope"))
})

slope <- function(kind, field) slope_all(kind)[[field]]

significant <- function(e) e$lo > 0 || e$hi < 0

n_negative_did <- function(m) sum(sapply(CASES, function(iso) did(iso, m) < 0))
n_positive_did <- function(m) sum(sapply(CASES, function(iso) did(iso, m) > 0))
n_sig_cases <- function(m) sum(sapply(CASES, function(iso) significant(did_all(iso, m))))
case_measures <- function(iso) Filter(function(m) !(iso %in% NOT_ASKED[[m]]), c(DIMS, QUESTIONS))

# Measures (Index, dimensions and the four questions) whose HC1 interval excludes zero.
n_significant <- function(iso) sum(sapply(case_measures(iso), function(m) significant(did_all(iso, m))))

# Per-case estimates whose region-clustered interval excludes zero while HC1's does not.
n_cluster_only_sig <- function() {
  sum(unlist(lapply(CASES, function(iso) sapply(case_measures(iso), function(m)
    significant(did_all(iso, m, TRUE)) && !significant(did_all(iso, m))))))
}

# Pooled measures larger than the margin of error on more than one of the three errors.
n_multi_sig <- function() {
  sum(sapply(c(DIMS, QUESTIONS), function(m) {
    hits <- sum(sapply(list(c("lo", "hi"), c("clo", "chi"), c("plo", "phi")),
                       function(b) pooled("seven", m, b[1]) > 0 || pooled("seven", m, b[2]) < 0))
    hits > 1
  }))
}

# Measures whose 2023-2025 change moved the gap back towards (or past) its 2021 level.
n_returned <- function(iso) {
  sum(sapply(c(DIMS, QUESTIONS), function(m) chg(iso, m) * (gap(iso, m, 2021) - gap(iso, m, 2023)) > 0))
}

# --- Regions -------------------------------------------------------------------------

region_mean <- function(iso, reg, year, m) {
  d <- frame(iso, year, m)
  wm(d[!is.na(d$region) & d$region == reg, , drop = FALSE], m)
}

region_change <- function(iso, reg, y0, y1, m = "index") region_mean(iso, reg, y1, m) - region_mean(iso, reg, y0, m)

# Respondents with an Index score (the map notes' base).
region_n <- function(iso, reg, year) {
  d <- frame(iso, year)
  sum(!is.na(d$region) & d$region == reg & !is.na(d$index))
}

# Index respondents per region in both waves, for regions with respondents in both (shaded).
region_counts <- function(iso, y0, y1) {
  d <- frame(iso, c(y0, y1))
  d <- d[!is.na(d$index) & !is.na(d$region), , drop = FALSE]
  regs <- sort(unique(d$region))
  n0 <- sapply(regs, function(r) sum(d$region == r & d$wave == y0))
  n1 <- sapply(regs, function(r) sum(d$region == r & d$wave == y1))
  keep <- n0 > 0 & n1 > 0
  data.frame(region = regs[keep], n0 = n0[keep], n1 = n1[keep])
}

n_regions <- function(iso, y0, y1) nrow(region_counts(iso, y0, y1))
n_hatched <- function(iso, y0, y1) { n <- region_counts(iso, y0, y1); sum(n$n0 < 50 | n$n1 < 50) }
n_regions_50plus <- function(iso, y0, y1) { n <- region_counts(iso, y0, y1); sum(n$n0 >= 50 & n$n1 >= 50) }
region_changes <- function(iso, y0, y1, m = "index") {
  regs <- region_counts(iso, y0, y1)$region
  setNames(sapply(regs, function(r) region_change(iso, r, y0, y1, m)), regs)
}
n_regions_fell <- function(iso, y0, y1) sum(region_changes(iso, y0, y1) < 0)
n_regions_rose <- function(iso, y0, y1) sum(region_changes(iso, y0, y1) > 0)
min_region_n <- function(iso, y0, y1) { n <- region_counts(iso, y0, y1); min(c(n$n0, n$n1)) }
max_region_n <- function(iso, y0, y1) { n <- region_counts(iso, y0, y1); max(c(n$n0, n$n1)) }
expo_rise_rank <- function(iso, reg) {
  rise <- region_changes(iso, 2021, 2023, "expo")
  unname(rank(-rise)[as.character(reg)])
}

aff_n <- function(iso, year) sum(frame(iso, year)$aff == 1)

PUBLIC_CASE_WAVES <- c(as.vector(outer(setdiff(CASES, "ZAF"), c(2021, 2023), paste, sep = "_")),
                       "ZAF_2023", "ZAF_2025", "MAR_2025", "TUR_2025")
aff_n_range <- function(kind) {
  n <- sapply(strsplit(PUBLIC_CASE_WAVES, "_"), function(p) aff_n(p[1], as.numeric(p[2])))
  if (kind == "min") min(n) else max(n)
}

n_valid <- function(iso, m, year, grp) {
  d <- frame(iso, year, m)
  sum(d$aff == (if (grp == "aff") 1 else 0) & !is.na(d[[m]]))
}

# Unweighted share of the affected-region respondents (2021 and 2023) living in `reg`.
share_in_region <- function(iso, reg) {
  d <- frame(iso, c(2021, 2023))
  d <- d[d$aff == 1, , drop = FALSE]
  100 * mean(!is.na(d$region) & d$region == reg)
}

.where <- function(d, where) {
  if (is.character(where)) d[d$aff == 1, , drop = FALSE] else d[!is.na(d$region) & d$region == where, , drop = FALSE]
}

# Of those impacted by a disaster in 2025, % naming hazard `code`.
hazard_share <- function(iso, where, code) {
  d <- .where(frame(iso, 2025), where)
  d <- d[!is.na(d$expo_code) & d$expo_code == 1, , drop = FALSE]
  d$named <- 100 * (!is.na(d$hazard) & d$hazard == code)
  wm(d, "named")
}

# % of all adults impacted in 2025 and naming hazard `code`.
hazard_all <- function(iso, where, code) {
  d <- .where(frame(iso, 2025), where)
  d$named <- 100 * (!is.na(d$expo_code) & d$expo_code == 1 & !is.na(d$hazard) & d$hazard == code)
  wm(d, "named")
}

n_impacted <- function(iso, where) {
  d <- .where(frame(iso, 2025), where)
  sum(!is.na(d$expo_code) & d$expo_code == 1)
}

moe_pct <- function(n) 100 * Z * sqrt(0.25 / n)

# Half-width of the HC1 interval of the Index gap in one wave.
moe_index_gap <- function(iso, year) {
  d <- frame(iso, year)
  d <- d[!is.na(d$index), , drop = FALSE]
  f <- fit(d$index, cbind(1, d$aff), d$w)
  Z * sqrt(f$V[2, 2])
}

# Türkiye's NUTS-2 units (REGION_TUR); 2025 needs Gallup's variable.
tur_units <- function(year) {
  d <- case_wave("TUR", year)
  if (year == 2025) {
    g <- gallup_merge(d, "REGION_TUR")
    d$nuts2 <- g$REGION_TUR
  }
  d
}
tur_unit_n <- function(code, year) { d <- tur_units(year); sum(!is.na(d$nuts2) & d$nuts2 == code) }
tur_unit_mean <- function(code, year, m) { d <- tur_units(year); wm(d[!is.na(d$nuts2) & d$nuts2 == code, , drop = FALSE], m) }
tur_outside_expo <- function(year) { d <- case_wave("TUR", year); wm(d[!(d$region %in% c(6, 11, 12)), , drop = FALSE], "expo") }
n_unsurveyed_units <- function(year) sum(tur_units(year)$nuts2 %in% c(13, 24, 25))

# Officially affected provinces in NUTS-2 units with no 2023 respondents.
n_affected_provinces_unsurveyed <- function() {
  d <- tur_units(2023)
  sum(TUR_AFFECTED_PROVINCES[sapply(names(TUR_AFFECTED_PROVINCES), function(u) sum(d$nuts2 %in% as.numeric(u)) == 0)])
}

# Unweighted % of the affected-region respondents living in officially affected NUTS-2 units.
tur_affected_share <- function(year) {
  d <- tur_units(year)
  d <- d[d$aff == 1, , drop = FALSE]
  100 * mean(d$nuts2 %in% TUR_AFFECTED_UNITS)
}

PROVINCE_GROUPS <- list(MOZ_nampula = 6, MOZ_affected = c(4, 8, 10), PAK_kp = c(3, 6), PAK_sindh = 1,
                        ECU_affected = c(6, 8))

# 2025 impacted share in provinces; needs Gallup's 2025 province variable REGION_<iso>.
prov_expo_2025 <- function(iso, group) {
  d <- wave(2025)
  d <- d[d$iso == iso, , drop = FALSE]
  var <- paste0("REGION_", iso)
  g <- gallup_merge(d, var)
  g <- g[!is.na(g[[var]]) & g[[var]] < 98, , drop = FALSE]
  key <- paste(iso, group, sep = "_")
  if (!is.null(PROVINCE_GROUPS[[key]])) {
    g <- g[g[[var]] %in% PROVINCE_GROUPS[[key]], , drop = FALSE]
  } else {
    g <- g[!(g[[var]] %in% PROVINCE_GROUPS[[paste(iso, "affected", sep = "_")]]), , drop = FALSE]
  }
  wm(g, "expo")
}

# Month of each event (Table 2.1); Pakistan's months run from the late-August peak (onset June 2022).
EVENT_MONTH <- list(MAR = c(2023, 9), MOZ = c(2023, 3), NZL = c(2023, 2), TUR = c(2023, 2), PAK = c(2022, 8),
                    ZAF = c(2022, 4), ECU = c(2023, 3), PAK_onset = c(2022, 6))

# Calendar months from the event to the country's main fieldwork month. Needs Gallup's
# interview date (FIELD_DATE, as in the 2019 release), which is not in the 2021-2025 files.
months_to_fieldwork <- function(iso, year, event = iso) {
  d <- wave(year)
  d <- gallup_merge(d[d$iso == iso, "wpid", drop = FALSE], "FIELD_DATE")
  dates <- as.Date(substr(as.character(d$FIELD_DATE), 1, 10))
  ym <- table(as.numeric(format(dates, "%Y")) * 12 + as.numeric(format(dates, "%m")) - 1)
  main <- min(as.numeric(names(ym)[ym == max(ym)])) # modal month (earliest if tied)
  ev <- EVENT_MONTH[[event]]
  main - (ev[1] * 12 + ev[2] - 1)
}

# --- National and global ------------------------------------------------------------------

national <- function(iso, m, year) {
  d <- wave(year)
  d <- d[d$iso == iso, , drop = FALSE]
  if (m == "confidence") d <- with_confidence(d)
  wm(d, m)
}

it_depends <- function(iso, year) national(iso, "depends", year)

earthquake_share <- function(iso, year) {
  d <- wave(year)
  d <- d[d$iso == iso & !is.na(d$expo_code) & d$expo_code == 1, , drop = FALSE]
  d$named <- 100 * (!is.na(d$hazard) & d$hazard == 7)
  wm(d, "named")
}

global_mean <- function(dim, year) wm(wave(year), dim)

INCOME <- c(low = 1, lower_middle = 2, upper_middle = 3, high = 4)
income_idv <- function(inc, grp) {
  d <- wave(2025)
  d <- d[!is.na(d$income) & d$income == INCOME[[inc]] & !is.na(d$expo_code) &
         d$expo_code == (if (grp == "impacted") 1 else 2), , drop = FALSE]
  wm(d, "individual")
}

impacted_share <- function() wm(wave(2025), "expo")

country_means <- function(year, dim) {
  d <- wave(year)
  d <- d[!is.na(d[[dim]]), , drop = FALSE]
  tapply(d[[dim]] * d$w, d$iso, sum) / tapply(d$w, d$iso, sum)
}

us_rank <- function(dim) unname(rank(-country_means(2025, dim))["USA"])
n_ranked <- function(dim) length(country_means(2025, dim))

# Country Index = mean of its four dimension scores (Chapter 2's country counts).
country_score <- function(year, dim) {
  if (dim != "index") return(country_means(year, dim))
  parts <- lapply(DIMS[-1], function(m) country_means(year, m))
  isos <- Reduce(intersect, lapply(parts, names))
  setNames(rowMeans(sapply(parts, function(p) p[isos])), isos)
}

n_countries_both <- function() length(intersect(unique(wave(2021)$iso), unique(wave(2023)$iso)))

n_countries_change <- function(dim, direction) {
  a <- country_score(2021, dim); b <- country_score(2023, dim)
  isos <- intersect(names(a), names(b))
  change <- b[isos] - a[isos]
  if (direction == "fell") sum(change < 0) else sum(change > 0)
}

n_resp <- function() nrow(wave(2025))
n_countries <- function() length(unique(wave(2025)$iso))

# Difference of two scores rounded half up, as printed.
rdiff <- function(a, b) floor(a + 0.5) - floor(b + 0.5)

# Case studies whose country was asked `m` in both 2021 and 2023.
n_cases_asked <- function(m) {
  sum(sapply(CASES, function(iso) all(sapply(c(2021, 2023), function(y) {
    d <- wave(y)
    d <- d[d$iso == iso, , drop = FALSE]
    if (m == "confidence") d <- with_confidence(d)
    any(!is.na(d[[m]]))
  }))))
}

# Respondents in the pooled countries in 2021 and 2023 (no region needed to count them).
n_pooled_resp <- function(kind) {
  isos <- if (kind == "seven") CASES else c("MOZ", "NZL", "TUR", "ZAF", "ECU")
  sum(sapply(c(2021, 2023), function(y) {
    d <- wave(y)
    d <- d[d$iso %in% isos, , drop = FALSE]
    if (kind == "seven") sum(!is.na(d$index)) else nrow(d)
  }))
}

# Distinct regions per case study across 2021 and 2023 (South Africa: 2023, all nine provinces).
n_clusters <- function(kind) {
  counts <- sapply(CASES, function(iso) {
    years <- if (iso == "ZAF") 2023 else c(2021, 2023)
    regs <- unique(unlist(lapply(years, function(y) {
      d <- case_wave(iso, y)
      r <- if (iso == "MAR" && y == 2021) d$region else d$region_raw
      r[!is.na(r)]
    })))
    length(regs)
  })
  switch(kind, total = sum(counts), min = min(counts), max = max(counts))
}

# --- Maps (no printed values; written to output/ only) -------------------------------------

region_key <- function(label) {
  label <- sub(" region$", "", tolower(label))
  gsub("^_+|_+$", "", gsub("[^a-z0-9]+", "_", label))
}
LABEL_VAR <- list(MAR = "REGION3_MAR", MOZ = "REGION_MOZ", NZL = "REGION_NZL", TUR = "REGION3_TUR",
                  PAK = "REGION_PAK", ZAF = "REGION_ZAF", ECU = "REGION_ECU")
map_changes <- function(iso, y0, y1) {
  labels <- value_labels(2023, LABEL_VAR[[iso]])
  ch <- region_changes(iso, y0, y1)
  setNames(unname(ch), region_key(labels[names(ch)]))
}

for (i in seq_along(CASES)) {
  local({
    iso <- c("MAR", "MOZ", "NZL", "TUR", "PAK", "ZAF", "ECU")[i]
    finding(report, paste0("C2_", i), function() map_changes(iso, 2021, 2023))
  })
}
for (i in 1:4) {
  local({
    iso <- c("MAR", "TUR", "NZL", "ZAF")[i]
    finding(report, paste0("C4_", i + 3), function() map_changes(iso, 2023, 2025))
  })
}
finding(report, "C2_8_pooled6", function() setNames(sapply(DIMS, function(m) pooled("six_noECU", m)), DIMS))

# --- Charts and tables ------------------------------------------------------------------------

F <- list() # finding id -> function
put <- function(id, fn) F[[id]] <<- fn

for (dim in DIMS) for (y in c(2021, 2023, 2025)) local({
  dim <- dim; y <- y
  put(paste("C1_1", dim, y, sep = "_"), function() global_mean(dim, y))
})
for (inc in names(INCOME)) for (grp in c("impacted", "not")) local({
  inc <- inc; grp <- grp
  put(paste("C1_2", inc, grp, sep = "_"), function() income_idv(inc, grp))
})
for (iso in CASES) local({ # Table 2.1
  iso <- iso
  put(paste0("T2_1_", iso, "_n2021"), function() aff_n(iso, 2021))
  put(paste0("T2_1_", iso, "_n2023"), function() aff_n(iso, 2023))
  for (f in c("est", "lo", "hi")) local({ f <- f; put(paste0("T2_1_", iso, "_expo_", f), function() did(iso, "expo", f)) })
})
for (m in c(DIMS, QUESTIONS)) for (f in c("est", "lo", "hi")) local({ # Table 2.2
  m <- m; f <- f
  put(paste("T2_2", m, f, sep = "_"), function() pooled("seven", m, f))
})

# Paired bars (affected change, rest change) and the gap between them, 2021 to 2023.
bars <- function(prefix, m, isos) {
  force(m)
  for (iso in isos) local({
    iso <- iso
    put(paste(prefix, iso, "aff", sep = "_"), function() group_change(iso, "aff", 2021, 2023, m))
    put(paste(prefix, iso, "rest", sep = "_"), function() group_change(iso, "rest", 2021, 2023, m))
    put(paste(prefix, iso, "gap", sep = "_"), function() did(iso, m))
  })
  put(paste(prefix, "pooled", sep = "_"), function() pooled("seven", m))
}
for (iso in CASES) local({ iso <- iso; put(paste0("T2_1_", iso, "_months"), function() months_to_fieldwork(iso, 2023)) })
for (iso in c("MAR", "TUR", "NZL", "ZAF")) local({ iso <- iso; put(paste0("T4_1_", iso, "_months"), function() months_to_fieldwork(iso, 2025)) })
put("T2_1_PAK_onset_months", function() months_to_fieldwork("PAK", 2023, "PAK_onset"))
for (dim in DIMS[-1]) bars(paste0("C3_1_", dim), dim, CASES)
bars("C3_2", "confidence", c("ECU", "MOZ", "NZL", "TUR", "ZAF"))
bars("C3_3", "neighbours", CASES)
bars("C3_5", "protect", CASES)
for (iso in c(CASES, "pooled")) for (m in c("community", "neighbours")) local({
  iso <- iso; m <- m
  put(paste("C3_4", iso, m, sep = "_"), if (iso == "pooled") function() pooled("seven", m) else function() did(iso, m))
})
for (iso in c("THA", "PHL", "LBN")) local({
  iso <- iso
  put(paste0("C3_6_", iso), function() national(iso, "confidence", 2023) - national(iso, "confidence", 2021))
})
for (iso in c("ECU", "MOZ", "NZL", "TUR", "ZAF")) local({ iso <- iso; put(paste0("C3_6_", iso), function() did(iso, "confidence")) })
for (iso in c("MAR", "TUR", "NZL", "ZAF")) local({ # Table 4.1, Chart 4.8
  iso <- iso
  for (y in c(2021, 2023, 2025)) local({ y <- y; put(paste("T4_1", iso, y, sep = "_"), function() aff_n(iso, y)) })
  put(paste0("C4_8_", iso, "_aff"), function() mean_in(iso, "worry", 2025, "aff"))
  put(paste0("C4_8_", iso, "_rest"), function() mean_in(iso, "worry", 2025, "rest"))
  put(paste0("C4_8_", iso, "_gap"), function() gap(iso, "worry", 2025))
})
for (iso in c("TUR", "NZL", "ZAF")) local({ # Chart 4.9
  iso <- iso
  put(paste0("C4_9_", iso, "_gap2021"), function() gap(iso, "prep", 2021))
  put(paste0("C4_9_", iso, "_gap2025"), function() gap(iso, "prep", 2025))
  put(paste0("C4_9_", iso, "_change"), function() gap(iso, "prep", 2025) - gap(iso, "prep", 2021))
})
put("C4_9_pooled", function() pooled("prep3", "prep"))
for (iso in CASES) for (m in c(DIMS, QUESTIONS, "expo")) for (f in c("est", "lo", "hi")) local({ # Tables A.1, A.2
  iso <- iso; m <- m; f <- f
  put(paste(if (m %in% DIMS) "TA_1" else "TA_2", iso, m, f, sep = "_"), function() did(iso, m, f))
})
for (iso in c("MAR", "TUR", "NZL", "ZAF")) for (m in c(DIMS, QUESTIONS)) local({ # Table A.3
  iso <- iso; m <- m
  for (y in c(2021, 2023, 2025)) local({ y <- y; put(paste0("TA_3_", iso, "_", m, "_gap", y), function() gap(iso, m, y)) })
  for (f in c("est", "lo", "hi", "adj", "adj_lo", "adj_hi")) local({
    f <- f
    key <- if (f == "est") "change" else if (f == "adj") "adj_est" else f
    put(paste("TA_3", iso, m, key, sep = "_"), function() chg(iso, m, f))
  })
})
for (m in c(DIMS, QUESTIONS)) for (f in c("c2023", "c2025", "change", "lo", "hi", "adj", "adj_lo", "adj_hi")) local({ # Table A.4
  m <- m; f <- f
  put(paste("TA_4", m, if (f == "adj") "adj_est" else f, sep = "_"), function() pooled3("three", m, f))
})

# --- Text statements (one line each; the comment is the statement) ----------------------------

TEXT <- list(
X001 = function() n_resp(),  # Interviews in the 2025 Poll ('more than 143,000')
  X002 = function() n_countries(),  # Countries and territories in 2025
  X003 = function() mean_in("ZAF", "neighbours", 2023, "aff") / mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: share saying neighbours care 'a lot' 'nearly tripled' after the 2022 floods (2023 / 2021)
  X004 = function() mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions: national government well prepared, 2021 ('roughly two in five')
  X005 = function() mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions: national government well prepared, 2025 ('fewer than one in ten')
  X006 = function() n_resp(),  # Interviews ('more than 143,000')
  X007 = function() n_countries(),  # Countries and territories
  X008 = function() did("TUR", "confidence", "est"),  # Türkiye: confidence in national government, difference-in-differences 2021-2023
  X009 = function() did("NZL", "confidence", "est"),  # New Zealand: confidence in national government, difference-in-differences
  X010 = function() did("MOZ", "gov", "est"),  # Mozambique: government cares 'a lot', difference-in-differences
  X011 = function() national("TUR", "index", 2021),  # Türkiye national Resilience Index, 2021
  X012 = function() national("TUR", "index", 2023),  # Türkiye national Resilience Index, 2023
  X013 = function() group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions: Index change 2021-2023
  X014 = function() group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye: Index change 2021-2023
  X015 = function() pooled("seven", "neighbours", "est"),  # Pooled seven cases: neighbours care 'a lot', difference-in-differences
  X016 = function() 100 * (1 - pooled("six_noZAF", "neighbours", "est") / pooled("seven", "neighbours", "est")),  # Share of the pooled neighbours rise that comes from KwaZulu-Natal ('half')
  X017 = function() mean_in("ZAF", "neighbours", 2023, "aff") / mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 'nearly tripled' (2023 / 2021)
  X018 = function() chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal: neighbours care 'a lot', change in the gap 2023-2025
  X019 = function() gap("ZAF", "neighbours", 2023),  # KwaZulu-Natal: neighbours care 'a lot', gap above the rest of South Africa in 2023
  X020 = function() gap("TUR", "confidence", 2023),  # Türkiye: confidence gap, 2023
  X021 = function() gap("TUR", "confidence", 2025),  # Türkiye: confidence gap, 2025
  X022 = function() chg("TUR", "confidence", "est"),  # Türkiye: confidence gap narrowing 2023-2025
  X023 = function() chg("NZL", "confidence", "est"),  # New Zealand: confidence gap narrowing 2023-2025
  X024 = function() mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions: well prepared, 2021
  X025 = function() mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions: well prepared, 2025
  X026 = function() mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye: well prepared, 2021
  X027 = function() mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye: well prepared, 2025
  X028 = function() pooled("prep3", "prep", "est"),  # Pooled three countries: well prepared, change in the gap 2021-2025
  X029 = function() pooled("seven", "index", "est"),  # Pooled seven cases: Resilience Index difference-in-differences ('about two points')
  X030 = function() n_negative_did("index"),  # Case studies where the Index fell relative to the rest of the country ('six of the seven')
  X031 = function() pooled("seven", "community", "est"),  # Pooled seven cases: community dimension ('about three points')
  X032 = function() did("TUR", "societal", "est"),  # Türkiye: societal dimension difference-in-differences
  X033 = function() did("MOZ", "societal", "est"),  # Mozambique: societal dimension difference-in-differences
  X034 = function() did("TUR", "confidence", "est"),  # Policy implications: Türkiye confidence difference-in-differences
  X035 = function() did("MOZ", "gov", "est"),  # Policy implications: Mozambique government cares 'a lot'
  X036 = function() pooled("seven", "neighbours", "est"),  # Policy implications: pooled neighbours care 'a lot'
  X037 = function() chg("TUR", "confidence", "est"),  # Policy implications: Türkiye confidence recovered 2023-2025
  X038 = function() mean_in("TUR", "prep", 2021, "aff"),  # Policy implications: Türkiye earthquake regions well prepared 2021
  X039 = function() mean_in("TUR", "prep", 2025, "aff"),  # Policy implications: Türkiye earthquake regions well prepared 2025
  X040 = function() mean_in("TUR", "prep", 2021, "rest"),  # Policy implications: rest of Türkiye well prepared 2021
  X041 = function() mean_in("TUR", "prep", 2025, "rest"),  # Policy implications: rest of Türkiye well prepared 2025
  X042 = function() us_rank("household"),  # United States: rank on household resilience, 2025
  X043 = function() us_rank("societal"),  # United States: rank on societal resilience, 2025
  X044 = function() n_ranked("societal"),  # Countries ranked on societal resilience, 2025
  X045 = function() global_mean("individual", 2025),  # Chart 1.1 subtitle: individual resilience 2025
  X046 = function() global_mean("societal", 2025),  # Chart 1.1 subtitle: societal resilience 2025
  X047 = function() global_mean("index", 2025),  # Chart 1.1 subtitle: Resilience Index 2025
  X048 = function() rdiff(global_mean("index", 2025), global_mean("index", 2023)),  # Chart 1.1 subtitle: Index 2025 minus 2023 ('level with 2023')
  X049 = function() rdiff(global_mean("index", 2025), global_mean("index", 2021)),  # Chart 1.1 subtitle: Index 2025 minus 2021 ('two points above')
  X050 = function() global_mean("index", 2025),  # Global Index 2025
  X051 = function() rdiff(global_mean("index", 2025), global_mean("index", 2023)),  # Global Index 2025 minus 2023 ('level with 2023')
  X052 = function() rdiff(global_mean("index", 2025), global_mean("index", 2021)),  # Global Index 2025 minus 2021 ('two points above 2021')
  X053 = function() global_mean("individual", 2021),  # Global individual dimension 2021
  X054 = function() global_mean("individual", 2023),  # Global individual dimension 2023
  X055 = function() global_mean("individual", 2025),  # Global individual dimension 2025
  X056 = function() global_mean("societal", 2021),  # Global societal dimension 2021
  X057 = function() global_mean("societal", 2023),  # Global societal dimension 2023
  X058 = function() global_mean("societal", 2025),  # Global societal dimension 2025
  X059 = function() global_mean("household", 2023),  # Global household dimension 2023
  X060 = function() global_mean("household", 2025),  # Global household dimension 2025
  X061 = function() rdiff(global_mean("household", 2025), global_mean("household", 2021)),  # Household 2025 minus 2021 ('one point above 2021')
  X062 = function() global_mean("community", 2021),  # Global community dimension 2021
  X063 = function() global_mean("community", 2023),  # Global community dimension 2023
  X064 = function() global_mean("community", 2025),  # Global community dimension 2025
  X065 = function() impacted_share(),  # Adults impacted by a disaster in the past five years, 2025 ('one adult in five (20%)')
  X066 = function() income_idv("low", "impacted"),  # Chart 1.2 subtitle: low income, impacted
  X067 = function() income_idv("low", "not"),  # Chart 1.2 subtitle: low income, not impacted
  X068 = function() income_idv("lower_middle", "impacted"),  # Individual resilience, lower_middle income, impacted
  X069 = function() income_idv("lower_middle", "not"),  # Individual resilience, lower_middle income, not impacted
  X070 = function() income_idv("upper_middle", "impacted"),  # Individual resilience, upper_middle income, impacted
  X071 = function() income_idv("upper_middle", "not"),  # Individual resilience, upper_middle income, not impacted
  X072 = function() income_idv("high", "impacted"),  # Individual resilience, high income, impacted
  X073 = function() income_idv("high", "not"),  # Individual resilience, high income, not impacted
  X074 = function() income_idv("low", "impacted"),  # Individual resilience, low income, impacted
  X075 = function() income_idv("low", "not"),  # Individual resilience, low income, not impacted
  X076 = function() national("TUR", "index", 2021),  # Türkiye national Index 2021
  X077 = function() national("TUR", "index", 2023),  # Türkiye national Index 2023
  X078 = function() group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions: Index change
  X079 = function() group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye: Index change
  X080 = function() global_mean("index", 2021),  # Global Index 2021
  X081 = function() global_mean("index", 2023),  # Global Index 2023
  X082 = function() n_countries_change("index", "fell"),  # Countries where the Index fell 2021-2023
  X083 = function() n_countries_both(),  # Countries measured in both 2021 and 2023
  X084 = function() n_countries_change("index", "rose"),  # Countries where the Index rose 2021-2023
  X085 = function() n_countries_change("individual", "fell"),  # Countries where the individual dimension fell 2021-2023
  X086 = function() share_in_region("TUR", 6),  # Share of Türkiye's affected respondents in the Mediterranean region ('two thirds')
  X087 = function() share_in_region("NZL", 2),  # Share of New Zealand's affected respondents in Auckland ('nine in ten')
  X088 = function() group_change("MAR", "aff", 2021, 2023, "index"),  # Chart 2.1 subtitle: Marrakech-Safi Index change 2021-2023
  X089 = function() group_change("MAR", "rest", 2021, 2023, "index"),  # Chart 2.1 subtitle: rest of Morocco Index change
  X090 = function() group_change("MAR", "aff", 2021, 2023, "index"),  # Marrakech-Safi Index change
  X091 = function() group_change("MAR", "rest", 2021, 2023, "index"),  # Rest of Morocco Index change
  X092 = function() n_regions_fell("MAR", 2021, 2023),  # Shaded regions that fell ('every shaded region fell'; 10 shaded)
  X093 = function() region_change("MAR", 4, 2021, 2023, "index"),  # Rabat-Salé-Kénitra Index change
  X094 = function() region_change("MAR", 9, 2021, 2023, "index"),  # Souss-Massa Index change
  X095 = function() did("MAR", "index", "est"),  # Gap between the two groups ('one point')
  X096 = function() region_n("MAR", 8, 2021),  # Draa-Tafilalet respondents 2021
  X097 = function() region_n("MAR", 8, 2023),  # Draa-Tafilalet respondents 2023
  X098 = function() region_n("MAR", 10, 2021),  # Guelmim-Oued Noun respondents 2021
  X099 = function() region_n("MAR", 10, 2023),  # Guelmim-Oued Noun respondents 2023
  X100 = function() group_change("MOZ", "aff", 2021, 2023, "index"),  # Chart 2.2 subtitle: cyclone-hit provinces Index change
  X101 = function() group_change("MOZ", "rest", 2021, 2023, "index"),  # Chart 2.2 subtitle: rest of Mozambique Index change
  X102 = function() region_change("MOZ", 8, 2021, 2023, "index"),  # Sofala Index change
  X103 = function() region_change("MOZ", 10, 2021, 2023, "index"),  # Zambezia Index change
  X104 = function() region_change("MOZ", 4, 2021, 2023, "index"),  # Manica Index change
  X105 = function() group_change("MOZ", "aff", 2021, 2023, "index"),  # Three affected provinces together
  X106 = function() group_change("MOZ", "rest", 2021, 2023, "index"),  # Rest of the country
  X107 = function() did("MOZ", "index", "est"),  # Gap ('one point')
  X108 = function() region_change("MOZ", 2, 2021, 2023, "index"),  # Gaza Index change
  X109 = function() region_change("MOZ", 7, 2021, 2023, "index"),  # Niassa Index change
  X110 = function() did("NZL", "index", "est"),  # Chart 2.3 subtitle: Northland and Auckland fell further ('three points')
  X111 = function() region_change("NZL", 1, 2021, 2023, "index"),  # Northland Index change
  X112 = function() region_change("NZL", 2, 2021, 2023, "index"),  # Auckland Index change
  X113 = function() group_change("NZL", "rest", 2021, 2023, "index"),  # Rest of New Zealand Index change
  X114 = function() did("NZL", "index", "est"),  # Gap ('three points')
  X115 = function() n_hatched("NZL", 2021, 2023),  # Regions hatched (fewer than 50 respondents in an edition)
  X116 = function() n_regions("NZL", 2021, 2023),  # Regions shaded
  X117 = function() region_n("NZL", 1, 2021),  # Northland respondents 2021
  X118 = function() region_n("NZL", 1, 2023),  # Northland respondents 2023
  X119 = function() region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
  X120 = function() region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
  X121 = function() region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
  X122 = function() region_n("NZL", 5, 2023),  # Tairāwhiti/Gisborne respondents 2023
  X123 = function() region_change("TUR", 11, 2021, 2023, "index"),  # Chart 2.4 subtitle: Central East Anatolia Index change
  X124 = function() region_change("TUR", 6, 2021, 2023, "index"),  # Chart 2.4 subtitle: Mediterranean Index change
  X125 = function() n_affected_provinces_unsurveyed(),  # Chart 2.4 subtitle: affected provinces with no 2023 respondents
  X126 = function() region_change("TUR", 11, 2021, 2023, "index"),  # Central East Anatolia Index change
  X127 = function() region_n("TUR", 11, 2021),  # Central East Anatolia respondents 2021
  X128 = function() region_n("TUR", 11, 2023),  # Central East Anatolia respondents 2023
  X129 = function() region_change("TUR", 6, 2021, 2023, "index"),  # Mediterranean Index change
  X130 = function() group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye Index change
  X131 = function() group_change("TUR", "aff", 2021, 2023, "index"),  # Two affected regions together
  X132 = function() did("TUR", "index", "est"),  # Gap ('four points')
  X133 = function() min_region_n("TUR", 2021, 2023),  # Smallest regional sample
  X134 = function() max_region_n("TUR", 2021, 2023),  # Largest regional sample
  X135 = function() n_hatched("TUR", 2021, 2023),  # Regions hatched
  X136 = function() region_n("TUR", 11, 2021),  # Central East Anatolia respondents 2021 (note)
  X137 = function() region_n("TUR", 11, 2023),  # Central East Anatolia respondents 2023 (note)
  X138 = function() region_n("TUR", 10, 2021),  # Northeast Anatolia respondents 2021
  X139 = function() region_n("TUR", 10, 2023),  # Northeast Anatolia respondents 2023
  X140 = function() group_change("PAK", "aff", 2021, 2023, "index"),  # Chart 2.5 subtitle: Sindh Index change
  X141 = function() group_change("PAK", "rest", 2021, 2023, "index"),  # Chart 2.5 subtitle: rest of Pakistan
  X142 = function() group_change("PAK", "aff", 2021, 2023, "index"),  # Sindh Index change
  X143 = function() group_change("PAK", "rest", 2021, 2023, "index"),  # Rest of Pakistan Index change
  X144 = function() did("PAK", "index", "est"),  # Gap ('three points')
  X145 = function() region_change("PAK", 2, 2021, 2023, "index"),  # Punjab Index change
  X146 = function() region_change("PAK", 4, 2021, 2023, "index"),  # Balochistan Index change
  X147 = function() region_change("PAK", 3, 2021, 2023, "index"),  # Khyber Pakhtunkhwa Index change ('did not change')
  X148 = function() region_change("PAK", 8, 2021, 2023, "index"),  # Islamabad Index change
  X149 = function() region_n("PAK", 8, 2021),  # Islamabad respondents 2021 (text)
  X150 = function() region_n("PAK", 8, 2023),  # Islamabad respondents 2023 (text)
  X151 = function() region_n("PAK", 8, 2021),  # Islamabad respondents 2021 (note)
  X152 = function() region_n("PAK", 8, 2023),  # Islamabad respondents 2023 (note)
  X153 = function() group_change("ZAF", "aff", 2021, 2023, "index"),  # Chart 2.6 subtitle: KwaZulu-Natal Index change
  X154 = function() group_change("ZAF", "rest", 2021, 2023, "index"),  # Chart 2.6 subtitle: rest of South Africa
  X155 = function() group_change("ZAF", "aff", 2021, 2023, "index"),  # KwaZulu-Natal Index change
  X156 = function() group_change("ZAF", "rest", 2021, 2023, "index"),  # Rest of South Africa Index change
  X157 = function() did("ZAF", "index", "est"),  # Gap in the province's favour ('four points')
  X158 = function() region_change("ZAF", 9, 2021, 2023, "index"),  # Western Cape Index change
  X159 = function() region_n("ZAF", 8, 2021),  # Northern Cape respondents 2021 (text)
  X160 = function() region_n("ZAF", 8, 2023),  # Northern Cape respondents 2023 (text)
  X161 = function() region_n("ZAF", 8, 2021),  # Northern Cape respondents 2021 (note)
  X162 = function() region_n("ZAF", 8, 2023),  # Northern Cape respondents 2023 (note)
  X163 = function() group_change("ECU", "aff", 2021, 2023, "index"),  # Chart 2.7 subtitle: Guayas and El Oro Index change
  X164 = function() group_change("ECU", "rest", 2021, 2023, "index"),  # Chart 2.7 subtitle: rest of Ecuador
  X165 = function() did("ECU", "index", "est"),  # Chart 2.7 subtitle: gap
  X166 = function() region_change("ECU", 8, 2021, 2023, "index"),  # Guayas Index change
  X167 = function() region_change("ECU", 6, 2021, 2023, "index"),  # El Oro Index change
  X168 = function() group_change("ECU", "aff", 2021, 2023, "index"),  # Guayas and El Oro together
  X169 = function() group_change("ECU", "rest", 2021, 2023, "index"),  # Rest of Ecuador
  X170 = function() did("ECU", "index", "est"),  # Gap ('four points')
  X171 = function() region_change("ECU", 16, 2021, 2023, "index"),  # Pichincha Index change
  X172 = function() region_change("ECU", 12, 2021, 2023, "index"),  # Manabí Index change
  X173 = function() n_hatched("ECU", 2021, 2023),  # Provinces hatched
  X174 = function() n_regions("ECU", 2021, 2023),  # Provinces shaded
  X175 = function() region_n("ECU", 6, 2021),  # El Oro respondents 2021
  X176 = function() region_n("ECU", 6, 2023),  # El Oro respondents 2023
  X177 = function() n_regions_50plus("ECU", 2021, 2023),  # Provinces with 50 or more respondents in both editions
  X178 = function() did("TUR", "societal", "est"),  # Türkiye societal dimension difference-in-differences
  X179 = function() group_change("TUR", "aff", 2021, 2023, "societal"),  # Türkiye affected regions: societal change
  X180 = function() mean_in("TUR", "societal", 2021, "aff"),  # Türkiye affected regions: societal 2021
  X181 = function() mean_in("TUR", "societal", 2023, "aff"),  # Türkiye affected regions: societal 2023
  X182 = function() group_change("TUR", "rest", 2021, 2023, "societal"),  # Rest of Türkiye: societal change
  X183 = function() group_change("TUR", "aff", 2021, 2023, "confidence"),  # Türkiye affected regions: confidence change
  X184 = function() mean_in("TUR", "confidence", 2021, "aff"),  # Türkiye affected regions: confidence 2021
  X185 = function() mean_in("TUR", "confidence", 2023, "aff"),  # Türkiye affected regions: confidence 2023
  X186 = function() group_change("TUR", "rest", 2021, 2023, "confidence"),  # Rest of Türkiye: confidence change
  X187 = function() did("TUR", "confidence", "est"),  # Türkiye: confidence gap ('24 percentage points')
  X188 = function() did("TUR", "gov", "est"),  # Türkiye: government cares 'a lot' fell further
  X189 = function() aff_n("TUR", 2021),  # Türkiye affected respondents 2021
  X190 = function() aff_n("TUR", 2023),  # Türkiye affected respondents 2023
  X191 = function() n_affected_provinces_unsurveyed(),  # Officially affected provinces with no 2023 respondents
  X192 = function() group_change("ZAF", "aff", 2021, 2023, "expo"),  # KwaZulu-Natal: reported disaster experience change
  X193 = function() group_change("ZAF", "rest", 2021, 2023, "expo"),  # Rest of South Africa: reported disaster experience change
  X194 = function() mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 2021
  X195 = function() mean_in("ZAF", "neighbours", 2023, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 2023
  X196 = function() did("ZAF", "neighbours", "est"),  # South Africa: neighbours difference-in-differences
  X197 = function() did("ZAF", "household", "est"),  # South Africa: household dimension difference-in-differences
  X198 = function() did("ZAF", "confidence", "est"),  # South Africa: confidence difference-in-differences
  X199 = function() did("ZAF", "index", "est"),  # South Africa: Index gap in the province's favour
  X200 = function() aff_n("ZAF", 2021),  # KwaZulu-Natal respondents 2021
  X201 = function() aff_n("ZAF", 2023),  # KwaZulu-Natal respondents 2023
  X202 = function() group_change("MAR", "rest", 2021, 2023, "expo"),  # Morocco: reported disaster experience rose where the earthquake did not strike
  X203 = function() n_significant("MOZ"),  # Mozambique: estimates larger than the margin of error
  X204 = function() did("MOZ", "societal", "est"),  # Mozambique: societal dimension
  X205 = function() did("MOZ", "gov", "est"),  # Mozambique: government cares 'a lot'
  X206 = function() n_significant("PAK"),  # Pakistan: estimates larger than the margin of error
  X207 = function() did("PAK", "societal", "est"),  # Pakistan: societal dimension
  X208 = function() did("NZL", "index", "est"),  # New Zealand: Index
  X209 = function() did("NZL", "confidence", "est"),  # New Zealand: confidence
  X210 = function() did("ECU", "index", "est"),  # Ecuador: Index gap
  X211 = function() did("ECU", "household", "est"),  # Ecuador: household dimension gap
  X212 = function() group_change("ECU", "aff", 2021, 2023, "confidence"),  # Ecuador: confidence change inside the affected provinces
  X213 = function() group_change("ECU", "rest", 2021, 2023, "confidence"),  # Ecuador: confidence change outside
  X214 = function() pooled("seven", "index", "est"),  # Chart 2.8 subtitle: pooled Index ('about two points lower')
  X215 = function() pooled("seven", "index", "est"),  # Pooled Index ('about two points lower')
  X216 = function() n_negative_did("index"),  # Case studies going that way ('six of the seven')
  X217 = function() mean_in("ZAF", "neighbours", 2021, "aff"),  # Box: KwaZulu-Natal neighbours 2021
  X218 = function() mean_in("ZAF", "neighbours", 2023, "aff"),  # Box: KwaZulu-Natal neighbours 2023
  X219 = function() did("ZAF", "neighbours", "est"),  # Box: South Africa neighbours relative change
  X220 = function() group_change("MAR", "aff", 2021, 2023, "neighbours"),  # Box: Marrakech-Safi neighbours rise
  X221 = function() group_change("MAR", "rest", 2021, 2023, "neighbours"),  # Box: rest of Morocco neighbours rise
  X222 = function() did("MAR", "neighbours", "est"),  # Box: rise specific to the earthquake region
  X223 = function() pooled("seven", "community", "est"),  # Pooled community dimension ('about three points')
  X224 = function() pooled("seven", "neighbours", "est"),  # Pooled neighbours care 'a lot'
  X225 = function() pooled("six_noZAF", "neighbours", "est") / pooled("seven", "neighbours", "est"),  # Pooled neighbours rise 'halves without KwaZulu-Natal' (ratio)
  X226 = function() n_affected_provinces_unsurveyed(),  # Officially affected Turkish provinces with no 2023 respondents
  X227 = function() n_unsurveyed_units(2021),  # Respondents in those provinces, 2021
  X228 = function() n_unsurveyed_units(2023),  # Respondents in those provinces, 2023
  X229 = function() national("TUR", "expo", 2021),  # Türkiye: reported disaster experience 2021
  X230 = function() national("TUR", "expo", 2023),  # Türkiye: reported disaster experience 2023
  X231 = function() region_change("TUR", 6, 2021, 2023, "expo"),  # Mediterranean region: rise in reported experience
  X232 = function() region_mean("TUR", 6, 2021, "expo"),  # Mediterranean region: reported experience 2021
  X233 = function() region_mean("TUR", 6, 2023, "expo"),  # Mediterranean region: reported experience 2023
  X234 = function() expo_rise_rank("TUR", 6),  # Mediterranean: rank of the rise among Türkiye's 12 regions ('largest rise anywhere')
  X235 = function() tur_unit_n(12, 2021),  # Adana and Mersin unit (TR62) respondents 2021
  X236 = function() tur_unit_n(12, 2023),  # Adana and Mersin unit respondents 2023
  X237 = function() tur_unit_mean(12, 2021, "expo"),  # Adana and Mersin unit: reported experience 2021
  X238 = function() tur_unit_mean(12, 2023, "expo"),  # Adana and Mersin unit: reported experience 2023
  X239 = function() tur_outside_expo(2021),  # Nine regions outside the earthquake zone: reported experience 2021
  X240 = function() tur_outside_expo(2023),  # Nine regions outside the earthquake zone: reported experience 2023
  X241 = function() region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
  X242 = function() region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
  X243 = function() region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
  X244 = function() region_n("NZL", 5, 2023),  # Tairāwhiti/Gisborne respondents 2023
  X245 = function() region_mean("NZL", 6, 2021, "expo"),  # Hawke's Bay reported experience 2021
  X246 = function() region_mean("NZL", 6, 2023, "expo"),  # Hawke's Bay reported experience 2023
  X247 = function() group_change("MAR", "aff", 2021, 2023, "expo"),  # Marrakech-Safi: rise in reported experience
  X248 = function() group_change("MAR", "rest", 2021, 2023, "expo"),  # Rest of Morocco: rise in reported experience
  X249 = function() did("TUR", "societal", "est"),  # Türkiye societal dimension
  X250 = function() did("TUR", "confidence", "est"),  # Türkiye confidence
  X251 = function() did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot'
  X252 = function() national("TUR", "index", 2021),  # Türkiye national Index 2021
  X253 = function() national("TUR", "index", 2023),  # Türkiye national Index 2023
  X254 = function() group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions Index change
  X255 = function() group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye Index change
  X256 = function() region_n("NZL", 6, 2023) + region_n("NZL", 5, 2023),  # Hawke's Bay and Tairāwhiti/Gisborne respondents 2023
  X257 = function() did("TUR", "community", "est"),  # Türkiye community dimension fell further
  X258 = function() did("TUR", "neighbours", "est"),  # Türkiye neighbours rose further
  X259 = function() pooled("seven", "neighbours", "est"),  # Pooled neighbours
  X260 = function() did("TUR", "societal", "est"),  # Türkiye societal
  X261 = function() did("MOZ", "societal", "est"),  # Mozambique societal
  X262 = function() did("PAK", "societal", "est"),  # Pakistan societal
  X263 = function() did("MAR", "societal", "est"),  # Morocco societal ('flat')
  X264 = function() pooled("seven", "societal", "est"),  # Pooled societal
  X265 = function() did("TUR", "community", "est"),  # Türkiye community
  X266 = function() did("NZL", "community", "est"),  # New Zealand community
  X267 = function() did("PAK", "community", "est"),  # Pakistan community
  X268 = function() max(abs(did("MAR", "community", "est")), abs(did("MOZ", "community", "est")), abs(did("ECU", "community", "est")), abs(did("ZAF", "community", "est"))),  # Other four case studies within three points of zero (largest absolute value)
  X269 = function() pooled("seven", "community", "est"),  # Pooled community
  X270 = function() n_sig_cases("household"),  # Household: case studies larger than the margin of error
  X271 = function() did("ZAF", "household", "est"),  # South Africa household
  X272 = function() did("ECU", "household", "est"),  # Ecuador household
  X273 = function() group_change("MAR", "aff", 2021, 2023, "household"),  # Marrakech-Safi household change
  X274 = function() group_change("MAR", "rest", 2021, 2023, "household"),  # Rest of Morocco household change
  X275 = function() pooled("seven", "household", "est"),  # Pooled household
  X276 = function() did("MAR", "individual", "est"),  # Morocco individual
  X277 = function() did("MOZ", "individual", "est"),  # Mozambique individual
  X278 = function() did("TUR", "individual", "est"),  # Türkiye individual
  X279 = function() pooled("seven", "individual", "est"),  # Pooled individual
  X280 = function() did("TUR", "societal", "est"),  # Chart 3.1 subtitle: Türkiye societal
  X281 = function() did("MOZ", "societal", "est"),  # Chart 3.1 subtitle: Mozambique societal
  X282 = function() pooled("seven", "community", "est"),  # Chart 3.1 subtitle: pooled community
  X283 = function() did("ZAF", "confidence", "est"),  # KwaZulu-Natal confidence relative rise
  X284 = function() pooled("seven", "confidence", "est"),  # Pooled five cases: confidence
  X285 = function() did("TUR", "confidence", "est"),  # Chart 3.2 subtitle: Türkiye
  X286 = function() did("ZAF", "confidence", "est"),  # Chart 3.2 subtitle: KwaZulu-Natal
  X287 = function() did("NZL", "confidence", "est"),  # New Zealand confidence gap
  X288 = function() did("MOZ", "confidence", "est"),  # Mozambique confidence rose further
  X289 = function() did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot' rose further
  X290 = function() n_positive_did("neighbours"),  # Case studies where neighbours rose relative ('four of the seven')
  X291 = function() did("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours
  X292 = function() did("MOZ", "neighbours", "est"),  # Mozambique neighbours
  X293 = function() did("TUR", "neighbours", "est"),  # Türkiye neighbours
  X294 = function() did("MAR", "neighbours", "est"),  # Morocco neighbours
  X295 = function() did("NZL", "neighbours", "est"),  # New Zealand neighbours ('other way by five')
  X296 = function() did("PAK", "neighbours", "est"),  # Pakistan neighbours
  X297 = function() did("ECU", "neighbours", "est"),  # Ecuador neighbours
  X298 = function() pooled("seven", "neighbours", "est"),  # Pooled seven cases neighbours
  X299 = function() pooled("six_noZAF", "neighbours", "est"),  # Pooled without KwaZulu-Natal ('halves to four')
  X300 = function() pooled("seven", "neighbours", "est"),  # Chart 3.3 subtitle: pooled
  X301 = function() did("ZAF", "neighbours", "est"),  # Chart 3.3 subtitle: KwaZulu-Natal
  X302 = function() did("NZL", "neighbours", "est"),  # Northland and Auckland neighbours fell relative
  X303 = function() did("TUR", "community", "est"),  # Chart 3.4 subtitle: Türkiye community
  X304 = function() did("TUR", "neighbours", "est"),  # Chart 3.4 subtitle: Türkiye neighbours
  X305 = function() region_mean("PAK", 1, 2021, "neighbours"),  # Sindh neighbours 'a lot' 2021
  X306 = function() region_mean("PAK", 1, 2023, "neighbours"),  # Sindh neighbours 'a lot' 2023
  X307 = function() region_mean("PAK", 2, 2021, "neighbours"),  # Punjab neighbours 'a lot' 2021
  X308 = function() region_mean("PAK", 2, 2023, "neighbours"),  # Punjab neighbours 'a lot' 2023
  X309 = function() did("PAK", "neighbours", "est"),  # Pakistan neighbours gap change
  X310 = function() pooled("seven", "protect", "est"),  # Chart 3.5 subtitle: pooled could protect
  X311 = function() pooled("seven", "protect", "est"),  # Pooled could protect
  X312 = function() national("MAR", "protect", 2021),  # Morocco could protect, national 2021
  X313 = function() national("MAR", "protect", 2023),  # Morocco could protect, national 2023
  X314 = function() national("MAR", "protect", 2023) - national("MAR", "protect", 2021),  # Morocco national fall
  X315 = function() group_change("MAR", "aff", 2021, 2023, "protect"),  # Marrakech-Safi fall
  X316 = function() group_change("MAR", "rest", 2021, 2023, "protect"),  # Rest of Morocco fall
  X317 = function() did("MAR", "protect", "est"),  # Morocco gap
  X318 = function() group_change("TUR", "aff", 2021, 2023, "protect"),  # Türkiye earthquake regions change
  X319 = function() group_change("TUR", "rest", 2021, 2023, "protect"),  # Rest of Türkiye change
  X320 = function() did("ZAF", "protect", "est"),  # South Africa could protect relative
  X321 = function() did("ECU", "protect", "est"),  # Ecuador could protect relative
  X322 = function() national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Chart 3.6 subtitle: Thailand confidence rise
  X323 = function() national("THA", "expo", 2023),  # Thailand reported a disaster in past five years, 2023
  X324 = function() national("THA", "index", 2023) - national("THA", "index", 2021),  # Thailand Index change
  X325 = function() national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand confidence change
  X326 = function() national("THA", "confidence", 2021),  # Thailand confidence 2021
  X327 = function() national("THA", "confidence", 2023),  # Thailand confidence 2023
  X328 = function() national("PHL", "confidence", 2023) - national("PHL", "confidence", 2021),  # Philippines confidence change
  X329 = function() national("PHL", "index", 2023) - national("PHL", "index", 2021),  # Philippines Index change
  X330 = function() national("LBN", "index", 2021),  # Lebanon Index 2021
  X331 = function() national("LBN", "index", 2023),  # Lebanon Index 2023
  X332 = function() national("LBN", "community", 2023) - national("LBN", "community", 2021),  # Lebanon community dimension change
  X333 = function() national("LBN", "household", 2023) - national("LBN", "household", 2021),  # Lebanon household dimension change
  X334 = function() national("LBN", "individual", 2023) - national("LBN", "individual", 2021),  # Lebanon individual dimension change
  X335 = function() national("LBN", "societal", 2023) - national("LBN", "societal", 2021),  # Lebanon societal dimension change
  X336 = function() national("LBN", "confidence", 2021),  # Lebanon confidence 2021
  X337 = function() national("LBN", "confidence", 2023),  # Lebanon confidence 2023
  X338 = function() national("LBN", "gov", 2021),  # Lebanon government cares 'a lot' 2021
  X339 = function() national("LBN", "gov", 2023),  # Lebanon government cares 'a lot' 2023
  X340 = function() national("LBN", "protect", 2021),  # Lebanon could protect 2021
  X341 = function() national("LBN", "protect", 2023),  # Lebanon could protect 2023
  X342 = function() national("LBN", "expo", 2021),  # Lebanon reported a disaster 2021
  X343 = function() national("LBN", "expo", 2023),  # Lebanon reported a disaster 2023
  X344 = function() national("LBN", "expo", 2023) / national("LBN", "expo", 2021),  # Lebanon reported disaster 'doubled' (2023 / 2021)
  X345 = function() earthquake_share("LBN", 2023),  # Lebanon 2023 disaster reports naming an earthquake
  X346 = function() pooled("seven", "neighbours", "est"),  # Pooled neighbours
  X347 = function() pooled("seven", "community", "est"),  # Pooled community ('about three points')
  X348 = function() pooled("seven", "protect", "est"),  # Pooled could protect
  X349 = function() national("MAR", "protect", 2023) - national("MAR", "protect", 2021),  # Morocco national fall in could protect
  X350 = function() gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
  X351 = function() gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
  X352 = function() gap("ZAF", "index", 2021),  # South Africa baseline Index gap ('three points below')
  X353 = function() gap("NZL", "index", 2021),  # New Zealand baseline Index gap ('two points above')
  X354 = function() mean_in("MAR", "expo", 2025, "aff"),  # Marrakech-Safi impacted by a disaster, 2025
  X355 = function() mean_in("MAR", "expo", 2025, "rest"),  # Rest of Morocco impacted, 2025
  X356 = function() hazard_share("MAR", "aff", 7),  # Marrakech-Safi impacted respondents naming an earthquake
  X357 = function() n_impacted("MAR", "aff"),  # Marrakech-Safi impacted respondents
  X358 = function() mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
  X359 = function() mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
  X360 = function() mean_in("NZL", "expo", 2025, "aff"),  # Northland and Auckland impacted 2025
  X361 = function() mean_in("NZL", "expo", 2025, "rest"),  # Rest of New Zealand impacted 2025
  X362 = function() mean_in("TUR", "expo", 2025, "aff"),  # Türkiye earthquake regions impacted 2025
  X363 = function() mean_in("TUR", "expo", 2025, "rest"),  # Rest of Türkiye impacted 2025
  X364 = function() region_mean("TUR", 12, 2025, "expo"),  # Southeast Anatolia impacted 2025
  X365 = function() hazard_share("TUR", 12, 7),  # Southeast Anatolia impacted respondents naming an earthquake
  X366 = function() n_impacted("TUR", 12),  # Southeast Anatolia impacted respondents
  X367 = function() hazard_all("TUR", 12, 7),  # Southeast Anatolia: all adults impacted by an earthquake
  X368 = function() region_mean("NZL", 6, 2025, "expo"),  # Hawke's Bay impacted 2025
  X369 = function() hazard_share("NZL", 6, 2),  # Hawke's Bay impacted respondents naming a tropical storm
  X370 = function() n_impacted("NZL", 6),  # Hawke's Bay impacted respondents
  X371 = function() hazard_all("NZL", 6, 2),  # Hawke's Bay: all adults impacted by a tropical storm
  X372 = function() region_n("NZL", 6, 2025),  # Hawke's Bay sample 2025
  X373 = function() gap("TUR", "index", 2021),  # Türkiye Index gap 2021
  X374 = function() gap("TUR", "index", 2023),  # Türkiye Index gap 2023
  X375 = function() gap("TUR", "index", 2025),  # Türkiye Index gap 2025
  X376 = function() gap("MAR", "index", 2025) - gap("MAR", "index", 2021),  # Marrakech-Safi ends above its own baseline (gap 2025 minus 2021)
  X377 = function() gap("NZL", "index", 2021),  # New Zealand Index gap 2021
  X378 = function() gap("NZL", "index", 2023),  # New Zealand Index gap 2023
  X379 = function() gap("NZL", "index", 2025),  # New Zealand Index gap 2025
  X380 = function() chg("NZL", "index", "est"),  # New Zealand Index gap change 2023-2025 ('no change at all')
  X381 = function() aff_n("NZL", 2025),  # New Zealand affected respondents 2025
  X382 = function() gap("NZL", "index", 2025) - gap("NZL", "index", 2021),  # New Zealand 2025 gap below the 2021 baseline
  X383 = function() moe_index_gap("MAR", 2023),  # Chart 4.1 note: margin of error on the Index gap at 132 respondents
  X384 = function() gap("TUR", "societal", 2023) - gap("TUR", "societal", 2021),  # Türkiye societal gap widened 2021-2023
  X385 = function() chg("TUR", "societal", "est"),  # Türkiye societal gap narrowed 2023-2025
  X386 = function() gap("TUR", "societal", 2025) - gap("TUR", "societal", 2021),  # Türkiye societal: remaining compared with 2021
  X387 = function() gap("MAR", "individual", 2023),  # Marrakech-Safi individual gap 2023
  X388 = function() gap("MAR", "individual", 2025),  # Marrakech-Safi individual gap 2025
  X389 = function() gap("MAR", "individual", 2025) - gap("MAR", "individual", 2021),  # Marrakech-Safi individual 2025 minus baseline ('level with its baseline')
  X390 = function() gap("NZL", "individual", 2023),  # New Zealand individual gap 2023
  X391 = function() gap("NZL", "individual", 2025),  # New Zealand individual gap 2025
  X392 = function() gap("NZL", "individual", 2025) - gap("NZL", "individual", 2021),  # New Zealand individual 2025 minus baseline
  X393 = function() gap("MAR", "household", 2025),  # Morocco household gap 2025
  X394 = function() gap("MAR", "household", 2021),  # Morocco household gap 2021
  X395 = function() max(abs(gap("TUR", "household", 2021)), abs(gap("TUR", "household", 2023)), abs(gap("TUR", "household", 2025))),  # Türkiye household gaps within about two points of zero (largest absolute)
  X396 = function() max(abs(gap("NZL", "household", 2021)), abs(gap("NZL", "household", 2023)), abs(gap("NZL", "household", 2025))),  # New Zealand household gaps within about two points of zero (largest absolute)
  X397 = function() gap("TUR", "community", 2023),  # Türkiye community gap 2023
  X398 = function() gap("TUR", "community", 2023) - gap("TUR", "community", 2021),  # Türkiye community 2023 below its 2021 baseline
  X399 = function() chg("TUR", "community", "est"),  # Türkiye community recovered 2023-2025
  X400 = function() chg("TUR", "confidence", "est"),  # Chart 4.3 subtitle: Türkiye confidence narrows
  X401 = function() chg("ZAF", "neighbours", "est"),  # Chart 4.3 subtitle: KwaZulu-Natal neighbours fall
  X402 = function() tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
  X403 = function() gap("TUR", "confidence", 2021),  # Türkiye confidence gap 2021
  X404 = function() gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
  X405 = function() gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
  X406 = function() chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing
  X407 = function() gap("TUR", "confidence", 2025) - gap("TUR", "confidence", 2021),  # Türkiye confidence gap remaining against 2021
  X408 = function() chg("NZL", "confidence", "est"),  # New Zealand confidence change
  X409 = function() chg("TUR", "gov", "est"),  # Türkiye government cares 'a lot' narrowing
  X410 = function() national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand national confidence rise
  X411 = function() gap("TUR", "neighbours", 2023),  # Türkiye neighbours gap 2023
  X412 = function() gap("TUR", "neighbours", 2025),  # Türkiye neighbours gap 2025
  X413 = function() chg("TUR", "neighbours", "est"),  # Türkiye neighbours change
  X414 = function() pooled3("three", "neighbours", "change"),  # Pooled three: neighbours change 2023-2025
  X415 = function() chg("MAR", "protect", "est"),  # Morocco could protect change 2023-2025
  X416 = function() chg("TUR", "protect", "est"),  # Türkiye could protect change 2023-2025
  X417 = function() chg("NZL", "protect", "est"),  # New Zealand could protect change 2023-2025
  X418 = function() region_change("TUR", 11, 2023, 2025, "index"),  # Türkiye Central East Anatolia Index change 2023-2025
  X419 = function() region_change("TUR", 6, 2023, 2025, "index"),  # Türkiye Mediterranean Index change 2023-2025
  X420 = function() region_change("TUR", 3, 2023, 2025, "index"),  # Türkiye Aegean Index change 2023-2025
  X421 = function() region_change("TUR", 5, 2023, 2025, "index"),  # Türkiye West Anatolia Index change 2023-2025
  X422 = function() region_change("MAR", 7, 2023, 2025, "index"),  # Morocco Marrakech-Safi Index change 2023-2025
  X423 = function() region_change("MAR", 3, 2023, 2025, "index"),  # Morocco Fès-Meknès Index change 2023-2025
  X424 = function() region_change("MAR", 2, 2023, 2025, "index"),  # Morocco Oriental Index change 2023-2025
  X425 = function() region_change("MAR", 6, 2023, 2025, "index"),  # Morocco Casablanca-Settat Index change 2023-2025
  X426 = function() region_change("MAR", 9, 2023, 2025, "index"),  # Morocco Souss-Massa Index change 2023-2025
  X427 = function() region_change("MAR", 5, 2023, 2025, "index"),  # Morocco Béni Mellal-Khénifra Index change 2023-2025
  X428 = function() region_change("MAR", 4, 2023, 2025, "index"),  # Morocco Rabat-Salé-Kénitra Index change 2023-2025
  X429 = function() region_change("MAR", 8, 2023, 2025, "index"),  # Morocco Draa-Tafilalet Index change 2023-2025
  X430 = function() region_n("MAR", 8, 2025),  # Draa-Tafilalet sample ('about 50')
  X431 = function() gap("MAR", "index", 2023),  # Marrakech-Safi Index gap 2023
  X432 = function() abs(gap("MAR", "index", 2025)),  # Marrakech-Safi Index gap 2025 ('within two points')
  X433 = function() gap("MAR", "index", 2025) - gap("MAR", "index", 2021),  # Marrakech-Safi ends above its baseline
  X434 = function() gap("MAR", "individual", 2023),  # Marrakech-Safi individual gap 2023
  X435 = function() gap("MAR", "individual", 2025),  # Marrakech-Safi individual gap 2025
  X436 = function() chg("MAR", "individual", "est"),  # Marrakech-Safi individual recovery
  X437 = function() region_n("MAR", 10, 2025),  # Guelmim-Oued Noun sample ('about 20')
  X438 = function() region_change("MAR", 7, 2023, 2025, "index"),  # Chart 4.4 subtitle: Marrakech-Safi Index change
  X439 = function() gap("MAR", "index", 2023),  # Chart 4.4 subtitle: gap 2023
  X440 = function() abs(gap("MAR", "index", 2025)),  # Chart 4.4 subtitle: gap 2025 ('within two points')
  X441 = function() region_n("MAR", 10, 2023),  # Guelmim-Oued Noun respondents 2023
  X442 = function() region_n("MAR", 10, 2025),  # Guelmim-Oued Noun respondents 2025
  X443 = function() region_n("MAR", 8, 2023),  # Draa-Tafilalet respondents 2023
  X444 = function() region_n("MAR", 8, 2025),  # Draa-Tafilalet respondents 2025
  X445 = function() region_n("MAR", 9, 2023),  # Souss-Massa respondents 2023
  X446 = function() region_n("MAR", 9, 2025),  # Souss-Massa respondents 2025
  X447 = function() region_change("TUR", 11, 2023, 2025, "index"),  # Chart 4.5 subtitle: Central East Anatolia
  X448 = function() region_change("TUR", 6, 2023, 2025, "index"),  # Chart 4.5 subtitle: Mediterranean
  X449 = function() gap("TUR", "index", 2023),  # Chart 4.5 subtitle: gap 2023
  X450 = function() gap("TUR", "index", 2025),  # Chart 4.5 subtitle: gap 2025
  X451 = function() tur_unit_n(26, 2023),  # Southeast Anatolia 2023 respondents, all in the Mardin unit
  X452 = function() region_n("TUR", 12, 2025),  # Southeast Anatolia 2025 respondents
  X453 = function() tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023
  X454 = function() tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
  X455 = function() region_n("TUR", 10, 2023),  # Northeast Anatolia respondents 2023
  X456 = function() region_n("TUR", 10, 2025),  # Northeast Anatolia respondents 2025
  X457 = function() region_n("TUR", 7, 2023),  # Central Anatolia respondents 2023
  X458 = function() region_n("TUR", 7, 2025),  # Central Anatolia respondents 2025
  X459 = function() region_n("TUR", 9, 2023),  # East Black Sea respondents 2023
  X460 = function() region_n("TUR", 9, 2025),  # East Black Sea respondents 2025
  X461 = function() region_change("TUR", 11, 2023, 2025, "index"),  # Türkiye Central East Anatolia Index change 2023-2025 (text)
  X462 = function() region_change("TUR", 6, 2023, 2025, "index"),  # Türkiye Mediterranean Index change 2023-2025 (text)
  X463 = function() region_change("TUR", 3, 2023, 2025, "index"),  # Türkiye Aegean Index change 2023-2025 (text)
  X464 = function() region_change("TUR", 5, 2023, 2025, "index"),  # Türkiye West Anatolia Index change 2023-2025 (text)
  X465 = function() region_change("TUR", 7, 2023, 2025, "index"),  # Türkiye Central Anatolia Index change 2023-2025 (text)
  X466 = function() region_change("TUR", 10, 2023, 2025, "index"),  # Türkiye Northeast Anatolia Index change 2023-2025 (text)
  X467 = function() region_change("TUR", 4, 2023, 2025, "index"),  # Türkiye East Marmara Index change 2023-2025 (text)
  X468 = function() region_change("TUR", 1, 2023, 2025, "index"),  # Türkiye Istanbul ('level') Index change 2023-2025 (text)
  X469 = function() gap("TUR", "index", 2021),  # Türkiye earthquake regions Index gap 2021
  X470 = function() gap("TUR", "index", 2023),  # Türkiye Index gap 2023
  X471 = function() gap("TUR", "index", 2025),  # Türkiye Index gap 2025
  X472 = function() did("TUR", "societal", "est"),  # Türkiye societal fell further by 2023
  X473 = function() chg("TUR", "societal", "est"),  # Türkiye societal recovered by 2025
  X474 = function() gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
  X475 = function() gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
  X476 = function() tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023 (text)
  X477 = function() tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025 (text)
  X478 = function() region_change("NZL", 1, 2023, 2025, "index"),  # Chart 4.6 subtitle: Northland Index change 2023-2025
  X479 = function() region_change("NZL", 2, 2023, 2025, "index"),  # Chart 4.6 subtitle: Auckland
  X480 = function() region_change("NZL", 1, 2023, 2025, "index"),  # New Zealand Northland Index change 2023-2025
  X481 = function() region_change("NZL", 2, 2023, 2025, "index"),  # New Zealand Auckland Index change 2023-2025
  X482 = function() region_change("NZL", 3, 2023, 2025, "index"),  # New Zealand Waikato Index change 2023-2025
  X483 = function() region_change("NZL", 4, 2023, 2025, "index"),  # New Zealand Bay of Plenty Index change 2023-2025
  X484 = function() region_change("NZL", 9, 2023, 2025, "index"),  # New Zealand Wellington ('flat') Index change 2023-2025
  X485 = function() region_change("NZL", 14, 2023, 2025, "index"),  # New Zealand Canterbury ('flat') Index change 2023-2025
  X486 = function() region_change("NZL", 15, 2023, 2025, "index"),  # New Zealand Otago ('flat') Index change 2023-2025
  X487 = function() chg("NZL", "index", "est"),  # New Zealand gap change 2023-2025 ('did not change at all')
  X488 = function() did("NZL", "index", "est"),  # Gap opened by 2023 ('three points')
  X489 = function() gap("NZL", "index", 2025) - gap("NZL", "index", 2021),  # Gap remains below 2021 ('three points')
  X490 = function() region_change("NZL", 6, 2023, 2025, "index"),  # Hawke's Bay Index change 2023-2025
  X491 = function() region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
  X492 = function() region_n("NZL", 6, 2025),  # Hawke's Bay respondents 2025
  X493 = function() region_change("NZL", 5, 2023, 2025, "index"),  # East Cape (Tairāwhiti) Index change 2023-2025
  X494 = function() region_n("NZL", 5, 2023),  # East Cape respondents 2023
  X495 = function() region_n("NZL", 5, 2025),  # East Cape respondents 2025
  X496 = function() n_hatched("NZL", 2023, 2025),  # Regions hatched ('ten of the 16')
  X497 = function() chg("NZL", "confidence", "est"),  # Confidence returned towards the rest of the country
  X498 = function() gap("NZL", "individual", 2023),  # Individual gap 2023
  X499 = function() gap("NZL", "individual", 2025),  # Individual gap 2025
  X500 = function() region_n("NZL", 1, 2023),  # Note: Northland respondents 2023
  X501 = function() region_n("NZL", 1, 2025),  # Note: Northland respondents 2025
  X502 = function() region_n("NZL", 6, 2023),  # Note: Hawke's Bay respondents 2023
  X503 = function() region_n("NZL", 6, 2025),  # Note: Hawke's Bay respondents 2025
  X504 = function() region_n("NZL", 5, 2023),  # Note: East Cape respondents 2023
  X505 = function() region_n("NZL", 5, 2025),  # Note: East Cape respondents 2025
  X506 = function() n_hatched("NZL", 2023, 2025),  # Note: regions hatched
  X507 = function() n_regions("NZL", 2023, 2025),  # Note: regions
  X508 = function() group_change("ZAF", "aff", 2023, 2025, "index"),  # Chart 4.7 subtitle: KwaZulu-Natal Index change 2023-2025
  X509 = function() group_change("ZAF", "rest", 2023, 2025, "index"),  # Chart 4.7 subtitle: rest of South Africa
  X510 = function() gap("ZAF", "index", 2023),  # Chart 4.7 subtitle: gap 2023 ('level')
  X511 = function() gap("ZAF", "index", 2025),  # Chart 4.7 subtitle: gap 2025
  X512 = function() did("ZAF", "index", "est"),  # KwaZulu-Natal Index difference-in-differences 2021-2023
  X513 = function() gap("ZAF", "index", 2021),  # KwaZulu-Natal Index gap 2021
  X514 = function() gap("ZAF", "index", 2023),  # KwaZulu-Natal Index gap 2023 ('level')
  X515 = function() did("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours relative rise 2021-2023
  X516 = function() mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
  X517 = function() mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
  X518 = function() hazard_share("ZAF", "aff", 1),  # KwaZulu-Natal impacted naming a flood
  X519 = function() hazard_share("ZAF", "aff", 2),  # KwaZulu-Natal impacted naming a tropical storm
  X520 = function() n_regions_rose("ZAF", 2023, 2025),  # Provinces that rose 2023-2025 ('every province')
  X521 = function() region_change("ZAF", 4, 2023, 2025, "index"),  # KwaZulu-Natal Index change 2023-2025
  X522 = function() region_change("ZAF", 8, 2023, 2025, "index"),  # Northern Cape Index change 2023-2025
  X523 = function() region_n("ZAF", 8, 2025),  # Northern Cape sample ('about 40')
  X524 = function() region_change("ZAF", 6, 2023, 2025, "index"),  # Mpumalanga Index change
  X525 = function() region_change("ZAF", 7, 2023, 2025, "index"),  # North West Index change
  X526 = function() region_change("ZAF", 9, 2023, 2025, "index"),  # Western Cape Index change
  X527 = function() gap("ZAF", "index", 2025),  # KwaZulu-Natal Index gap 2025
  X528 = function() gap("ZAF", "neighbours", 2023),  # Neighbours gap 2023
  X529 = function() chg("ZAF", "neighbours", "est"),  # Neighbours change 2023-2025
  X530 = function() chg("ZAF", "community", "est"),  # Community dimension change 2023-2025
  X531 = function() gap("ZAF", "community", 2025) - gap("ZAF", "community", 2021),  # Community gap 2025 below 2021 baseline
  X532 = function() did("ZAF", "confidence", "est"),  # Confidence relative rise 2021-2023
  X533 = function() gap("ZAF", "confidence", 2025),  # Confidence gap 2025
  X534 = function() n_returned("ZAF"),  # Measures that returned towards or past their 2021 position ('seven of the nine')
  X535 = function() gap("ZAF", "household", 2025) - gap("ZAF", "household", 2021),  # Household gap above 2021 baseline
  X536 = function() gap("ZAF", "protect", 2025) - gap("ZAF", "protect", 2021),  # Could protect gap above 2021 baseline
  X537 = function() region_n("ZAF", 8, 2023),  # Note: Northern Cape respondents 2023
  X538 = function() region_n("ZAF", 8, 2025),  # Note: Northern Cape respondents 2025
  X539 = function() region_n("ZAF", 6, 2023),  # Note: Mpumalanga respondents 2023
  X540 = function() region_n("ZAF", 6, 2025),  # Note: Mpumalanga respondents 2025
  X541 = function() pooled3("three", "index", "change"),  # Pooled three: Index gap narrower than in 2023
  X542 = function() pooled3("three", "confidence", "c2023"),  # Türkiye and New Zealand: confidence change in the gap by 2023
  X543 = function() pooled3("three", "confidence", "c2025"),  # Türkiye and New Zealand: confidence change in the gap by 2025
  X544 = function() pooled3("three", "confidence", "change"),  # Confidence narrowing ('11 percentage points')
  X545 = function() max(abs(pooled3("three", "household", "c2023")), abs(pooled3("three", "household", "c2025")), abs(pooled3("three", "household", "change")), abs(pooled3("three", "individual", "c2023")), abs(pooled3("three", "individual", "c2025")), abs(pooled3("three", "individual", "change"))),  # Household and individual change by a point or less (largest absolute)
  X546 = function() pooled3("three", "neighbours", "c2023"),  # Neighbours change in the gap by 2023
  X547 = function() mean_in("ZAF", "worry", 2025, "aff"),  # Chart 4.8 subtitle: KwaZulu-Natal Worry Index
  X548 = function() mean_in("ZAF", "worry", 2025, "rest"),  # Chart 4.8 subtitle: rest of South Africa Worry Index
  X549 = function() n_valid("MAR", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, MAR
  X550 = function() n_valid("TUR", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, TUR
  X551 = function() n_valid("NZL", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, NZL
  X552 = function() n_valid("ZAF", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, ZAF
  X553 = function() gap("MAR", "worry", 2025),  # Morocco worry gap
  X554 = function() gap("TUR", "worry", 2025),  # Türkiye worry gap
  X555 = function() gap("NZL", "worry", 2025),  # New Zealand worry gap
  X556 = function() gap("ZAF", "worry", 2025),  # South Africa worry gap
  X557 = function() pooled("prep3", "prep", "est"),  # Chart 4.9 subtitle: pooled well prepared change
  X558 = function() mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions well prepared 2021
  X559 = function() mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions well prepared 2025
  X560 = function() mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye well prepared 2021
  X561 = function() mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye well prepared 2025
  X562 = function() gap("TUR", "prep", 2021),  # Türkiye well prepared gap 2021
  X563 = function() gap("TUR", "prep", 2025),  # Türkiye well prepared gap 2025
  X564 = function() gap("TUR", "prep", 2025) - gap("TUR", "prep", 2021),  # Türkiye well prepared change in the gap
  X565 = function() gap("NZL", "prep", 2025) - gap("NZL", "prep", 2021),  # New Zealand well prepared change in the gap
  X566 = function() mean_in("ZAF", "prep", 2021, "aff"),  # KwaZulu-Natal well prepared 2021
  X567 = function() mean_in("ZAF", "prep", 2025, "aff"),  # KwaZulu-Natal well prepared 2025
  X568 = function() mean_in("ZAF", "prep", 2021, "rest"),  # Rest of South Africa well prepared 2021
  X569 = function() mean_in("ZAF", "prep", 2025, "rest"),  # Rest of South Africa well prepared 2025
  X570 = function() pooled("prep3", "prep", "est"),  # Pooled three countries well prepared
  X571 = function() pooled("prep2", "prep", "est"),  # Pooled Türkiye and New Zealand well prepared
  X572 = function() mean_in("TUR", "local_prep", 2025, "aff"),  # Türkiye earthquake regions: local government well prepared 2025
  X573 = function() mean_in("TUR", "local_prep", 2025, "rest"),  # Rest of Türkiye: local government well prepared 2025
  X574 = function() gap("NZL", "local_prep", 2025),  # New Zealand local government well prepared gap 2025
  X575 = function() chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours fall
  X576 = function() n_returned("ZAF"),  # Measures returned towards 2021 ('seven of the nine')
  X577 = function() chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing
  X578 = function() gap("TUR", "prep", 2025) - gap("TUR", "prep", 2021),  # Türkiye well prepared fell further 2021-2025
  X579 = function() gap("NZL", "prep", 2025) - gap("NZL", "prep", 2021),  # Northland and Auckland well prepared fell further
  X580 = function() chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing (31 months)
  X581 = function() chg("NZL", "confidence", "est"),  # New Zealand confidence narrowing
  X582 = function() did("TUR", "confidence", "est"),  # Türkiye confidence fell further
  X583 = function() did("NZL", "confidence", "est"),  # New Zealand confidence fell further
  X584 = function() did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot'
  X585 = function() national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand confidence rise
  X586 = function() n_positive_did("neighbours"),  # Neighbours rose in four of the seven case studies
  X587 = function() pooled("seven", "protect", "est"),  # Pooled could protect
  X588 = function() pooled3("three", "confidence", "change"),  # Confidence narrowing across Türkiye and New Zealand
  X589 = function() pooled("prep3", "prep", "est"),  # Pooled well prepared fell further
  X590 = function() pooled3("three", "index", "change"),  # Pooled three: Index gap narrowed
  X591 = function() chg("NZL", "index", "est"),  # New Zealand Index gap did not change
  X592 = function() chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours fall
  X593 = function() national("TUR", "index", 2021),  # Türkiye national Index
  X594 = function() did("TUR", "societal", "est"),  # Türkiye societal fell further
  X595 = function() pooled("seven", "index", "est"),  # Pooled Index ('about two')
  X596 = function() n_negative_did("index"),  # Six of the seven
  X597 = function() chg("TUR", "confidence", "est"),  # Türkiye confidence narrowed
  X598 = function() mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions well prepared 2021
  X599 = function() mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions well prepared 2025
  X600 = function() mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye well prepared 2021
  X601 = function() mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye well prepared 2025
  X602 = function() pooled("seven", "neighbours", "est"),  # Pooled neighbours
  X603 = function() n_affected_provinces_unsurveyed(),  # Turkish affected provinces with no 2023 respondents
  X604 = function() n_cases_asked("confidence"),  # Case studies that asked confidence in national government in both waves
  X605 = function() min(n_cases_asked("gov"), n_cases_asked("neighbours"), n_cases_asked("protect")),  # Case studies that asked the other three questions
  X606 = function() it_depends("THA", 2023),  # 'It depends' on the protect question: Thailand, 2023
  X607 = function() it_depends("LBN", 2023),  # 'It depends' on the protect question: Lebanon, 2023
  X608 = function() did("ECU", "expo", "est"),  # Ecuador: reported experience fell faster inside Guayas and El Oro
  X609 = function() prov_expo_2025("MOZ", "nampula"),  # Mozambique 2025: Nampula impacted
  X610 = function() prov_expo_2025("MOZ", "affected"),  # Mozambique 2025: Zambezia, Sofala and Manica impacted
  X611 = function() prov_expo_2025("PAK", "kp"),  # Pakistan 2025: Khyber Pakhtunkhwa impacted
  X612 = function() prov_expo_2025("PAK", "sindh"),  # Pakistan 2025: Sindh impacted
  X613 = function() mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
  X614 = function() mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
  X615 = function() prov_expo_2025("ECU", "affected"),  # Ecuador 2025: Guayas and El Oro impacted
  X616 = function() prov_expo_2025("ECU", "rest"),  # Ecuador 2025: rest of Ecuador impacted
  X617 = function() pooled("six_noECU", "index", "est"),  # Without Ecuador: pooled Index ('about one')
  X618 = function() pooled("six_noECU", "index", "lo"),  # Without Ecuador: pooled Index, HC1 lower
  X619 = function() pooled("six_noECU", "index", "hi"),  # Without Ecuador: pooled Index, HC1 upper
  X620 = function() pooled("six_noECU", "community", "est"),  # Without Ecuador: community ('about three points')
  X621 = function() pooled("six_noECU", "community", "lo"),  # Without Ecuador: community, HC1 lower
  X622 = function() pooled("six_noECU", "community", "hi"),  # Without Ecuador: community, HC1 upper
  X623 = function() pooled("seven", "neighbours", "est"),  # Seven cases: neighbours ('seven')
  X624 = function() pooled("six_noECU", "neighbours", "est"),  # Without Ecuador: neighbours ('nine')
  X625 = function() pooled("six_noECU", "neighbours", "lo"),  # Without Ecuador: neighbours, HC1 lower
  X626 = function() pooled("six_noECU", "neighbours", "hi"),  # Without Ecuador: neighbours, HC1 upper
  X627 = function() slope("months", "est"),  # Slope of the Index change on months from event to fieldwork
  X628 = function() slope("months", "lo"),  # Months slope, 95% CI lower
  X629 = function() slope("months", "hi"),  # Months slope, 95% CI upper
  X630 = function() slope("expo", "est"),  # Slope on the strength of the exposure check
  X631 = function() slope("expo", "lo"),  # Exposure-check slope, 95% CI lower
  X632 = function() slope("expo", "hi"),  # Exposure-check slope, 95% CI upper
  X633 = function() n_pooled_resp("seven"),  # Respondents behind the seven-case estimates ('about 14,000')
  X634 = function() n_pooled_resp("five"),  # Respondents behind the confidence row ('about 10,000')
  X635 = function() n_clusters("total"),  # Region clusters across the seven countries
  X636 = function() n_clusters("min"),  # Fewest region clusters in a country
  X637 = function() n_clusters("max"),  # Most region clusters in a country
  X638 = function() n_cluster_only_sig(),  # Per-case estimates significant only with region clustering
  X639 = function() pooled("seven", "index", "lo"),  # Pooled seven cases, index: HC1 lower
  X640 = function() pooled("seven", "index", "hi"),  # Pooled seven cases, index: HC1 upper
  X641 = function() pooled("seven", "index", "clo"),  # Pooled seven cases, index: region-clustered lower
  X642 = function() pooled("seven", "index", "chi"),  # Pooled seven cases, index: region-clustered upper
  X643 = function() pooled("seven", "index", "plo"),  # Pooled seven cases, index: PSU-clustered lower
  X644 = function() pooled("seven", "index", "phi"),  # Pooled seven cases, index: PSU-clustered upper
  X645 = function() pooled("seven", "community", "lo"),  # Pooled seven cases, community: HC1 lower
  X646 = function() pooled("seven", "community", "hi"),  # Pooled seven cases, community: HC1 upper
  X647 = function() pooled("seven", "community", "clo"),  # Pooled seven cases, community: region-clustered lower
  X648 = function() pooled("seven", "community", "chi"),  # Pooled seven cases, community: region-clustered upper
  X649 = function() pooled("seven", "community", "plo"),  # Pooled seven cases, community: PSU-clustered lower
  X650 = function() pooled("seven", "community", "phi"),  # Pooled seven cases, community: PSU-clustered upper
  X651 = function() pooled("seven", "neighbours", "lo"),  # Pooled seven cases, neighbours: HC1 lower
  X652 = function() pooled("seven", "neighbours", "hi"),  # Pooled seven cases, neighbours: HC1 upper
  X653 = function() pooled("seven", "neighbours", "clo"),  # Pooled seven cases, neighbours: region-clustered lower
  X654 = function() pooled("seven", "neighbours", "chi"),  # Pooled seven cases, neighbours: region-clustered upper
  X655 = function() pooled("seven", "neighbours", "plo"),  # Pooled seven cases, neighbours: PSU-clustered lower
  X656 = function() pooled("seven", "neighbours", "phi"),  # Pooled seven cases, neighbours: PSU-clustered upper
  X657 = function() n_multi_sig(),  # Pooled measures significant on more than one of the three standard errors
  X658 = function() pooled3("three", "index", "c2023_lo"),  # Pooled three-wave: widening to 2023, HC1 lower
  X659 = function() pooled3("three", "index", "c2023_hi"),  # Pooled three-wave: widening to 2023, HC1 upper
  X660 = function() pooled3("three", "index", "lo"),  # Pooled three-wave: narrowing 2023-2025, HC1 lower
  X661 = function() pooled3("three", "index", "hi"),  # Pooled three-wave: narrowing 2023-2025, HC1 upper
  X662 = function() pooled3("four", "index", "change"),  # All four case studies: Index narrowing ('zero')
  X663 = function() pooled3("four", "neighbours", "c2023"),  # All four: neighbours above the 2021 baseline by 2023
  X664 = function() pooled3("four", "neighbours", "c2025"),  # All four: neighbours above the 2021 baseline by 2025
  X665 = function() aff_n("MAR", 2021),  # Smallest affected region: Morocco 2021
  X666 = function() aff_n("MAR", 2023),  # Morocco 2023
  X667 = function() aff_n("MAR", 2025),  # Morocco 2025
  X668 = function() tur_unit_n(12, 2021),  # Adana and Mersin unit respondents 2021
  X669 = function() tur_unit_n(12, 2023),  # Adana and Mersin unit respondents 2023
  X670 = function() region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
  X671 = function() region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
  X672 = function() n_impacted("MAR", "aff"),  # Marrakech-Safi impacted respondents 2025
  X673 = function() n_impacted("TUR", 12),  # Southeast Anatolia impacted respondents 2025
  X674 = function() n_impacted("NZL", 6),  # Hawke's Bay impacted respondents 2025
  X675 = function() region_n("NZL", 6, 2025),  # Hawke's Bay sample 2025
  X676 = function() aff_n_range("min"),  # Smallest affected-region sample
  X677 = function() aff_n_range("max"),  # Largest affected-region sample
  X678 = function() moe_pct(aff_n_range("min")),  # Margin of error on a percentage at 132 respondents ('about nine')
  X679 = function() moe_index_gap("MAR", 2023),  # Margin of error on an Index score at 132 respondents ('about three')
  X680 = function() moe_pct(aff_n_range("max")),  # Margin of error on a percentage at 418 respondents ('about five')
  X681 = function() moe_index_gap("NZL", 2023),  # Margin of error on an Index score at 418 respondents ('about two')
  X682 = function() aff_n("ZAF", 2025),  # KwaZulu-Natal respondents 2025
  X683 = function() moe_pct(aff_n("ZAF", 2025)),  # Margin of error at 181 respondents ('roughly seven')
  X684 = function() n_affected_provinces_unsurveyed(),  # Officially affected Turkish provinces with no 2023 respondents
  X685 = function() tur_affected_share(2021),  # Affected regions made up of officially affected NUTS-2 units, 2021
  X686 = function() tur_affected_share(2023),  # Same, 2023
  X687 = function() tur_affected_share(2025),  # Same, 2025
  X688 = function() tur_unit_n(13, 2021),  # Hatay, Kahramanmaraş and Osmaniye respondents 2021
  X689 = function() tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023
  X690 = function() tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
  X691 = function() region_n("TUR", 12, 2021),  # Southeast Anatolia respondents 2021
  X692 = function() region_n("TUR", 12, 2023),  # Southeast Anatolia respondents 2023
  X693 = function() region_n("TUR", 12, 2025),  # Southeast Anatolia respondents 2025
  X694 = function() tur_unit_n(26, 2023),  # Southeast Anatolia 2023 respondents from the Mardin unit
  X695 = function() region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
  X696 = function() region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
  X697 = function() region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
  X698 = function() region_n("NZL", 5, 2023)  # Tairāwhiti/Gisborne respondents 2023
)
F <- c(F, TEXT)

# Register every published finding.
for (fid in report$published$finding_id) finding(report, fid, F[[fid]])

status <- run_report(report)
if (!interactive()) quit(status = status)
