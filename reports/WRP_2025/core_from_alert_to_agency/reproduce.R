# Reproduce World Risk Poll 2026: From alert to agency: What turns warnings into action?
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_from_alert_to_agency/reproduce.R
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

IMPACTED <- "WP24213"  # impacted by a disaster in the past five years: 1 yes, 2 no
TYPE <- "WP24180"      # type of the most impactful disaster
ACTED <- "WP24215"     # able to take action ahead of the disaster because of the warning: 1 yes, 2 no
AGENCY <- "WP22252"    # could protect yourself or family in a future disaster: 1 yes, 2 no, 3 it depends
PLAN <- "WP23345"      # household disaster plan known to all over 10 years old: 1 yes, 2 no
CHANNELS <- c(internet = "WP24181", television = "WP24183", sms = "WP24186", radio = "WP24182",
              print = "WP24184", megaphone = "WP24188", whatsapp = "WP24185", billboard = "WP24187")
EXPERIENCED_2023 <- "WP23344"
TYPE_2023 <- "WP22247"
SOURCES_2023 <- c("WP22248", "WP22249", "WP22250", "WP22251")
MOBILE <- "WP17626"    # Gallup World Poll: has a mobile phone (1 = yes)
INTERNET <- "WP16056"  # Gallup World Poll: has access to the internet (1 = yes)
YES <- 1

TYPES <- c("1" = "flood", "2" = "hurricane", "3" = "tornado", "4" = "thunderstorm", "5" = "tsunami", "6" = "mudslide",
           "7" = "earthquake", "8" = "wildfire", "9" = "volcano", "10" = "blizzard", "50" = "drought", "51" = "heatwave",
           "52" = "sandstorm", "53" = "gale", "96" = "other_nature", "97" = "other_not_nature")
TYPES_2023 <- c("1" = "flood", "2" = "hurricane", "7" = "earthquake")
REGION <- c("1" = "east_africa", "2" = "cw_africa", "3" = "north_africa", "4" = "southern_africa", "5" = "latam",
            "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
            "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
            "14" = "southern_europe", "15" = "anz")
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # 9 = not classified
EDUCATION <- c("1" = "primary", "2" = "secondary", "3" = "tertiary")
PHL_REGION <- c("1" = "ncr", "3" = "balance_luzon", "4" = "visayas", "5" = "mindanao")
NWARN <- c("0" = "none", "1" = "one", "2" = "two", "3" = "three", "4" = "four", "5" = "five", "6" = "six_plus")
DIMS <- c(index = "resilience_index_100", individual = "resilience_idv", household = "resilience_hhl",
          community = "resilience_com", societal = "resilience_soc")

# Early Warnings for All: the 30 initial priority countries announced in 2023. Those with at
# least MIN_N respondents asked about warnings are the 13 in Chart 2.4.
EW4A <- c("ATG", "BGD", "BRB", "KHM", "TCD", "COM", "DJI", "ECU", "ETH", "FJI", "GTM", "GUY", "HTI", "KIR", "LAO",
          "LBR", "MDG", "MDV", "MUS", "MOZ", "NPL", "NER", "WSM", "SOM", "SSD", "SDN", "TON", "TUV", "UGA", "VUT")
MIN_N <- 100

d <- load_wave(2025, c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", "Education",
                       "REGION2_PHL", IMPACTED, TYPE, ACTED, AGENCY, PLAN, unname(CHANNELS), unname(DIMS)))
d23 <- load_wave(2023, c("COUNTRY_ISO3", "PROJWT", EXPERIENCED_2023, TYPE_2023, SOURCES_2023))

# --- Derived variables -----------------------------------------------------------

for (k in names(DIMS)) d[[k]] <- if (k == "index") d[[DIMS[[k]]]] else 100 * d[[DIMS[[k]]]]

# Asked about warnings: everyone impacted whose most impactful disaster has a type.
# "Warned" = yes to at least one channel; don't know counts as no.
asked_rows <- !is.na(d[[CHANNELS[["internet"]]]])
yes_count <- rowSums(sapply(CHANNELS, function(v) !is.na(d[[v]]) & d[[v]] == 1))
d$n_warnings <- ifelse(asked_rows, yes_count, NA)
d$warned <- ifelse(asked_rows, as.numeric(yes_count > 0), NA)
d$n_warnings_6 <- pmin(d$n_warnings, 6)

impacted <- d[!is.na(d[[IMPACTED]]) & d[[IMPACTED]] == 1, ]
asked <- d[asked_rows, ]
warned <- d[!is.na(d[[ACTED]]), ]

# --- Helpers ---------------------------------------------------------------------

r0 <- function(x) floor(x + 0.5 + 1e-9)
num <- function(x) sprintf("%.17g", x)  # numbers stored alongside text values
lt1 <- function(v) ifelse(r0(v) == 0, "<1", num(v))

keyed <- function(v, keys) {
  v <- v[names(v) %in% names(keys)]
  setNames(unname(v), unname(keys[names(v)]))
}

get0 <- function(v, k) if (k %in% names(v)) v[[k]] else 0

type_shares <- function(df, var = TYPE) {
  t <- distribution(df, var)
  out <- vapply(names(TYPES), function(code) get0(t, code), numeric(1))
  names(out) <- TYPES
  c(out, dk_refused = get0(t, "98") + get0(t, "99"))
}

n_asked <- table(asked$COUNTRY_ISO3)

country_warned <- function() {
  s <- pct(asked, "warned", YES, by = "COUNTRY_ISO3")
  s[as.vector(n_asked[names(s)]) >= MIN_N]
}

ew4a_countries <- function() EW4A[EW4A %in% names(n_asked) & as.vector(n_asked[EW4A]) >= MIN_N]

unwarned_mobile <- function() merge_gallup(asked[asked$warned == 0, ], MOBILE)

# --- Text figures ----------------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() pct(d23, EXPERIENCED_2023, YES))
finding(report, "X04", function() {
  t <- distribution(d23[!is.na(d23[[EXPERIENCED_2023]]) & d23[[EXPERIENCED_2023]] == 1, ], TYPE_2023)
  setNames(vapply(names(TYPES_2023), function(code) get0(t, code), numeric(1)), TYPES_2023)
})
finding(report, "X05", function() {
  a <- d23[!is.na(d23[[SOURCES_2023[1]]]), ]
  a$warned <- as.numeric(rowSums(sapply(SOURCES_2023, function(v) !is.na(a[[v]]) & a[[v]] == 1)) > 0)
  pct(a, "warned", YES)
})
finding(report, "X06", function() {
  s <- pct(d, IMPACTED, YES, by = "COUNTRY_ISO3")
  c(highest = names(which.max(s)), lowest = names(which.min(s)), ISR = lt1(s[["ISR"]]))
})
finding(report, "X07", function() keyed(pct(d[d$CountryIncomeLevel == 1, ], IMPACTED, YES, by = "Education"), EDUCATION))
finding(report, "X08", function() type_shares(impacted[impacted$COUNTRY_ISO3 == "PHL", ])[c("hurricane", "flood", "earthquake")])
finding(report, "X09", function() {
  s <- sort(country_warned())
  c(vapply(c("VNM", "HKG", "CHN", "COG", "GAB"), function(iso) num(s[[iso]]), character(1)),
    top3 = paste(sort(tail(names(s), 3)), collapse = ", "),
    bottom2 = paste(sort(head(names(s), 2)), collapse = ", "))
})
finding(report, "X10", function() {
  s <- pct(asked, "warned", YES, by = "COUNTRY_ISO3")[ew4a_countries()]
  c(countries = length(s), two_thirds = sum(s >= 200 / 3), under_half = sum(s < 50))
})
finding(report, "X11", function() keyed(pct(warned, ACTED, YES, by = "CountryIncomeLevel"), INCOME))
finding(report, "X12", function() {
  low <- d[d$CountryIncomeLevel == 1 & d[[IMPACTED]] %in% c(1, 2), ]
  keyed(wmean(low, "individual", by = IMPACTED), c("1" = "impacted", "2" = "not_impacted"))
})
finding(report, "X13", function() keyed(wmean(merge_gallup(asked, MOBILE), "n_warnings", by = MOBILE), c("1" = "yes", "2" = "no")))
finding(report, "X14", function() keyed(wmean(merge_gallup(asked, INTERNET), "n_warnings", by = INTERNET), c("1" = "yes", "2" = "no")))
finding(report, "X15", function() {
  g <- unwarned_mobile()
  sum(g$PROJWT[!is.na(g[[MOBILE]]) & g[[MOBILE]] == 1]) / 1e6
})
finding(report, "X16", function() sum(r0(keyed(pct(unwarned_mobile(), MOBILE, YES, by = "GlobalRegion"), REGION)) >= 90))
finding(report, "X17", function() keyed(pct(unwarned_mobile(), MOBILE, YES, by = "GlobalRegion"), REGION)[c("northern_america", "anz")])

# --- Chapter 1: who is impacted ------------------------------------------------------

finding(report, "C1_1", function() {
  t <- distribution(d, IMPACTED)
  c(yes = get0(t, "1"), no = get0(t, "2"))
})
finding(report, "C1_2", function() lt1(type_shares(impacted)))
finding(report, "C1_3", function() keyed(pct(d, IMPACTED, YES, by = "CountryIncomeLevel"), INCOME))
finding(report, "C1_4", function() keyed(pct(d, IMPACTED, YES, by = "GlobalRegion"), REGION))
finding(report, "C1_5", function() pct(d, IMPACTED, YES, by = "COUNTRY_ISO3"))
finding(report, "C1_6", function() {
  p <- impacted[impacted$COUNTRY_ISO3 == "PHL", ]
  out <- c()
  for (code in c("2", "1", "7")) {
    v <- keyed(pct(p, TYPE, as.numeric(code), by = "REGION2_PHL"), PHL_REGION)
    out[paste(names(v), TYPES[[code]], sep = "_")] <- unname(v)
  }
  out
})

# --- Chapter 2: who is warned ----------------------------------------------------------

finding(report, "C2_1", function() {
  v <- pct(asked, "warned", YES)
  c(yes = v, no = 100 - v)
})
finding(report, "C2_2", function() keyed(pct(asked, "warned", YES, by = "CountryIncomeLevel"), INCOME))
finding(report, "C2_3", function() keyed(pct(asked, "warned", YES, by = "GlobalRegion"), REGION))
finding(report, "C2_4", function() {
  isos <- ew4a_countries()
  w <- pct(asked, "warned", YES, by = "COUNTRY_ISO3")
  i <- pct(d, IMPACTED, YES, by = "COUNTRY_ISO3")
  c(setNames(unname(w[isos]), paste0("warned_", isos)), setNames(unname(i[isos]), paste0("impacted_", isos)))
})
finding(report, "C2_5", function() keyed(pct(asked, "warned", YES, by = TYPE), TYPES))
finding(report, "C2_6", function() vapply(CHANNELS, function(v) pct(asked, v, YES), numeric(1)))
finding(report, "C2_7", function() keyed(distribution(asked, "n_warnings_6"), NWARN))
finding(report, "C2_8", function() keyed(wmean(asked, "individual", by = "n_warnings_6"), NWARN))
finding(report, "C2_9", function() {
  g <- unwarned_mobile()
  c(global = pct(g, MOBILE, YES), keyed(pct(g, MOBILE, YES, by = "GlobalRegion"), REGION))
})

# --- Chapter 3: who acts ---------------------------------------------------------------

finding(report, "C3_1", function() {
  v <- pct(warned, ACTED, YES)
  c(yes = v, no = 100 - v)
})
finding(report, "C3_2", function() keyed(pct(warned, ACTED, YES, by = "GlobalRegion"), REGION))
finding(report, "C3_3", function() keyed(pct(warned, ACTED, YES, by = TYPE), TYPES))
finding(report, "C3_4", function() {
  out <- c()
  for (k in names(DIMS)) {
    m <- wmean(warned, k, by = ACTED)
    out[paste0(k, "_acted")] <- m[["1"]]
    out[paste0(k, "_not_acted")] <- m[["2"]]
    out[paste0(k, "_gap")] <- r0(m[["1"]]) - r0(m[["2"]])
  }
  out
})
finding(report, "C3_5", function() {
  s <- keyed(pct(warned, ACTED, YES, by = "n_warnings_6"), NWARN)
  order <- unname(NWARN)[-1]
  changes <- setNames(r0(s[order[-1]]) - r0(s[order[-length(order)]]), paste0("change_", order[-1]))
  c(s, changes)
})
finding(report, "C3_6", function() {
  # Agency yes/no and plan yes/no; "it depends", don't know and refused are left out.
  w <- warned
  w$agency <- unname(c("1" = 1, "2" = 0)[as.character(w[[AGENCY]])])
  w$plan <- unname(c("1" = 1, "2" = 0)[as.character(w[[PLAN]])])
  s <- pct(w[!is.na(w$agency) & !is.na(w$plan), ], ACTED, YES, by = c("plan", "agency"))
  keyed(s, c("1_1" = "both", "1_0" = "plan_only", "0_1" = "agency_only", "0_0" = "neither"))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
