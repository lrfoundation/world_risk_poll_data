# Reproduce World Risk Poll 2026: From alert to agency: What turns warnings into action?
#
# Run from the repository root:
#   Rscript reports/WRP_2025/core_early_warnings/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

IMPACTED <- "WP24213"; TYPE <- "WP24180"; ACT <- "WP24215" # 1 = yes, 2 = no, 98/99 = DK/refused
AGENCY <- "WP22252"; PLAN <- "WP23345" # could protect self/family; household plan (1 = yes, 2 = no)
CHANNELS <- c(internet = "WP24181", radio = "WP24182", tv = "WP24183", newspapers = "WP24184",
              whatsapp = "WP24185", sms = "WP24186", billboard = "WP24187", loudspeaker = "WP24188")
PHONE <- "WP17626"; INTERNET <- "WP16056" # Gallup World Poll items (not in the public release): 1 = yes
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # CountryIncomeLevel
REGIONS <- c( # GlobalRegion codes -> keys
  "1" = "eastern_africa", "2" = "cw_africa", "3" = "northern_africa", "4" = "southern_africa", "5" = "latam",
  "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia", "9" = "southeastern_asia",
  "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe", "13" = "nw_europe",
  "14" = "southern_europe", "15" = "anz"
)
TYPES <- c( # WP24180 codes -> keys (98 don't know and 99 refused are combined as "dk")
  "1" = "flood", "2" = "hurricane", "3" = "tornado", "4" = "thunder", "5" = "tsunami", "6" = "landslide",
  "7" = "earthquake", "8" = "wildfire", "9" = "volcano", "10" = "blizzard", "50" = "drought", "51" = "heatwave",
  "52" = "sandstorm", "53" = "gale", "96" = "other_nature", "97" = "other_not_nature", "98" = "dk"
)
TYPE_CODE <- setNames(names(TYPES), TYPES)
CHART_2_5 <- c("hurricane", "heatwave", "sandstorm", "blizzard", "other_nature", "thunder", "wildfire", "gale",
               "tornado", "flood", "volcano", "drought", "earthquake", "landslide") # no tsunami or non-natural
CHART_3_3 <- setdiff(CHART_2_5, "tornado") # the bubbles in Chart 3.3
PHL_REGIONS <- c("1" = "ncr", "3" = "balance_luzon", "4" = "visayas", "5" = "mindanao") # REGION2_PHL
# The UN Early Warnings for All initiative's initial priority countries that were surveyed in 2025
# (the 2023 report lists 17; Tajikistan, Ethiopia, Liberia and Ecuador have too few respondents).
EW4A <- c("BGD", "KHM", "TCD", "COM", "ECU", "ETH", "GTM", "LAO", "LBR", "MDG", "MUS", "MOZ", "NPL", "NER",
          "SOM", "TJK", "UGA")
MIN_N <- 100 # "sufficient data": at least 100 respondents asked about warnings (in a country or region)
DIMS <- c(index = "resilience_index", individual = "resilience_idv", household = "resilience_hhl",
          community = "resilience_com", societal = "resilience_soc")

d <- load_wave(2025, c("WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", "Education",
                       "REGION2_PHL", IMPACTED, TYPE, unname(CHANNELS), ACT, AGENCY, PLAN, unname(DIMS)))

# --- Derived variables ---------------------------------------------------------

# Resilience scores on 0-100.
for (k in names(DIMS)) d[[k]] <- 100 * d[[DIMS[[k]]]]

# Disaster type with don't know and refused combined (Chart 1.2 shows them together).
d$type <- ifelse(d[[TYPE]] %in% 99, 98, d[[TYPE]])

# Warnings. The eight channel questions were asked of everyone impacted who named
# a disaster type. `nwarn` counts the channels answered yes; don't know, refused
# and "does not apply" count as no. warned: 1 = at least one warning, 2 = none;
# missing for those not asked.
asked <- !is.na(d[[CHANNELS[["internet"]]]])
yes_count <- rowSums(sapply(CHANNELS, function(v) d[[v]] %in% 1))
d$nwarn <- ifelse(asked, yes_count, NA)
d$nwarn6 <- pmin(d$nwarn, 6) # 6 = six or more
d$warned <- ifelse(asked, ifelse(d$nwarn > 0, 1, 2), NA)

# Household plan and agency (Chart 3.6): among the warned who answered yes or no
# to both questions. 1 = plan and agency, 2 = plan only, 3 = agency only, 4 = neither.
yes_no <- d[[PLAN]] %in% c(1, 2) & d[[AGENCY]] %in% c(1, 2)
d$plan_agency <- ifelse(yes_no, 1 + 2 * (d[[PLAN]] %in% 2) + (d[[AGENCY]] %in% 2), NA)

imp <- d[d[[IMPACTED]] %in% 1, ]       # impacted by a disaster (Charts 1.2, 1.6)
ew <- d[!is.na(d$warned), ]            # impacted and asked about warnings (Chapter 2)
w <- ew[ew$warned == 1, ]              # warned: asked whether they could act (Chapter 3)
unwarned <- ew[ew$warned == 2, ]

# Country table: % impacted, % warned and the number asked about warnings.
imp_c <- pct(d, IMPACTED, 1, by = "COUNTRY_ISO3")
cov_c <- pct(ew, "warned", 1, by = "COUNTRY_ISO3")
n_c <- table(ew$COUNTRY_ISO3)
country <- data.frame(iso = names(imp_c), impacted = unname(imp_c), coverage = unname(cov_c[names(imp_c)]),
                      n = as.numeric(n_c[names(imp_c)]))
rownames(country) <- country$iso
sufficient <- country[!is.na(country$n) & country$n >= MIN_N, ]
ew4a <- sufficient[sufficient$iso %in% EW4A, ]

# 2023 comparison: experienced a disaster (WP23344), its type (WP22247), and at
# least one warning from the four 2023 sources, defined as in the 2023 report.
d23 <- load_wave(2023, c("PROJWT", "WP23344", "WP22247", "WP22248", "WP22249", "WP22250", "WP22251"))
src23 <- d23[c("WP22248", "WP22249", "WP22250", "WP22251")]
any_yes <- rowSums(sapply(src23, function(x) x %in% 1)) > 0
any_no <- rowSums(sapply(src23, function(x) x %in% 2)) > 0
d23$warned <- ifelse(any_yes, 1, ifelse(any_no, 2, NA))
exp23 <- d23[d23$WP23344 %in% 1, ]

# --- Helpers -------------------------------------------------------------------

by_income <- function(df, var, codes, keys = NULL) {
  r <- pct(df, var, codes, by = "CountryIncomeLevel")
  r <- r[names(r) %in% names(INCOME)]
  out <- setNames(unname(r), INCOME[names(r)])
  if (is.null(keys)) out else out[keys]
}

by_region <- function(df, var, codes, keys = NULL) {
  r <- pct(df, var, codes, by = "GlobalRegion")
  out <- setNames(unname(r), REGIONS[names(r)])
  if (is.null(keys)) out else out[keys]
}

by_type <- function(df, var, codes, keys) {
  r <- pct(df, var, codes, by = "type")
  setNames(unname(r[TYPE_CODE[keys]]), keys)
}

impacted <- function() pct(d, IMPACTED, 1)

# % of the impacted naming each type as the most impactful.
type_share <- function(keys) {
  dist <- distribution(imp, "type")
  v <- dist[TYPE_CODE[keys]]
  v[is.na(v)] <- 0
  setNames(unname(v), keys)
}

coverage <- function(df = ew) pct(df, "warned", 1)
able <- function(df = w) pct(df, ACT, 1)
not_able <- function() pct(w, ACT, 2)
channel <- function(keys) setNames(vapply(keys, function(k) pct(ew, CHANNELS[[k]], 1), numeric(1)), keys)

# % by number of warnings (0-5, 6 = six or more) among those asked.
n_warnings <- function() distribution(ew, "nwarn6")
able_by_n <- function() pct(w, ACT, 1, by = "nwarn6")

# Gains from each channel after three, on rounded percentages as in Chart 3.5.
gains_after_three <- function() {
  r <- round(able_by_n())
  gains <- r[c("4", "5", "6")] - r[c("3", "4", "5")]
  c(min = min(gains), max = max(gains))
}

idv_by_n <- function(keys) {
  r <- wmean(ew, "individual", by = "nwarn6")
  setNames(unname(r[as.character(keys)]), as.character(keys))
}

by_action <- function(dim) {
  r <- wmean(w, dim, by = ACT)
  c(able = r[["1"]], not = r[["2"]])
}

# Gap able minus not able, on rounded scores as in Chart 3.4.
action_gap <- function(dim) {
  r <- by_action(dim)
  round(r[["able"]]) - round(r[["not"]])
}

plan_agency <- function(keys) {
  r <- pct(w, ACT, 1, by = "plan_agency")
  codes <- c(both = "1", plan = "2", agency = "3", neither = "4")
  setNames(unname(r[codes[keys]]), keys)
}

regions_below_half <- function() sum(by_region(ew, "warned", 1) < 50)

income_ratio <- function() {
  r <- by_income(d, IMPACTED, 1)
  r[["low"]] / r[["high"]]
}

low_income_education <- function() {
  r <- pct(d[d$CountryIncomeLevel %in% 1, ], IMPACTED, 1, by = "Education")
  c(primary = r[["1"]], secondary = r[["2"]], tertiary = r[["3"]])
}

countries <- function(var, isos) setNames(country[isos, var], isos)

phl <- function(region_key = NULL) {
  p <- imp[imp$COUNTRY_ISO3 == "PHL", ]
  if (is.null(region_key)) return(distribution(p, "type"))
  m <- distribution(p, "type", by = "REGION2_PHL")
  m[names(PHL_REGIONS)[PHL_REGIONS == region_key], ]
}

hazard_pair <- function(h) {
  c(warned = by_type(ew, "warned", 1, h)[[h]], act = by_type(w, ACT, 1, h)[[h]])
}

storms_floods <- function() {
  s <- hazard_pair("hurricane"); f <- hazard_pair("flood")
  c(storm_warned = s[["warned"]], flood_warned = f[["warned"]], storm_act = s[["act"]], flood_act = f[["act"]])
}

# Mobile phone ownership (Gallup WP17626) among the unwarned.
unwarned_phone <- function() merge_gallup(unwarned, PHONE)
phone_share <- function() pct(unwarned_phone(), PHONE, 1)
phone_millions <- function() {
  g <- unwarned_phone()
  sum(g$PROJWT[g[[PHONE]] %in% 1]) / 1e6
}

# Every region's % owning a phone, and whether it has 100+ unwarned respondents (shown in Chart 2.9).
phone_by_region <- function() {
  g <- unwarned_phone()
  r <- pct(g, PHONE, 1, by = "GlobalRegion")
  n <- table(unwarned$GlobalRegion)
  data.frame(phone = unname(r), shown = as.numeric(n[names(r)]) >= MIN_N, row.names = REGIONS[names(r)])
}
phone_regions <- function(keys) {
  r <- phone_by_region()
  setNames(r[keys, "phone"], keys)
}
phone_90_regions <- function() sum(round(phone_by_region()$phone) >= 90)

# --- Foreword ------------------------------------------------------------------------

interviews <- function() nrow(d)
n_countries <- function() length(unique(d$COUNTRY_ISO3))
finding(report, "X001", interviews)
finding(report, "X002", n_countries)
finding(report, "X003", coverage)
finding(report, "X004", regions_below_half)
finding(report, "X005", income_ratio)
finding(report, "X006", function() by_income(ew, "warned", 1)[["low"]])
finding(report, "X007", function() pct(w[w$CountryIncomeLevel %in% c(1, 2), ], ACT, 2))
finding(report, "X008", phone_share)
finding(report, "X009", phone_millions)

# --- Executive summary -----------------------------------------------------------------

experienced_2023 <- function() pct(d23, "WP23344", 1)
warned_2023 <- function() pct(exp23[!is.na(exp23$warned), ], "warned", 1)
channels_asked <- function() c("2025" = length(CHANNELS), "2023" = 4) # WP24181-WP24188; WP22248-WP22251

finding(report, "X010", interviews)
finding(report, "X011", n_countries)
finding(report, "X012", impacted)
finding(report, "X013", impacted)
finding(report, "X014", experienced_2023)
finding(report, "X015", function() by_income(d, IMPACTED, 1)[["low"]])
finding(report, "X016", function() by_income(d, IMPACTED, 1)[["high"]])
finding(report, "X017", income_ratio)
finding(report, "X018", function() by_income(d, IMPACTED, 1)[["lower_middle"]])
finding(report, "X019", function() by_income(d, IMPACTED, 1)[["upper_middle"]])
finding(report, "X020", low_income_education)
finding(report, "X021", function() by_region(d, IMPACTED, 1)[["anz"]])
finding(report, "X022", function() by_region(d, IMPACTED, 1, c("eastern_africa", "southeastern_asia")))
finding(report, "X023", function() country["PHL", "impacted"])
finding(report, "X024", function() country["ISR", "impacted"])
finding(report, "X025", function() type_share(c("flood", "hurricane", "earthquake")))
finding(report, "X026", coverage)
finding(report, "X027", coverage)
finding(report, "X028", warned_2023)
finding(report, "X029", channels_asked)
finding(report, "X030", function() by_income(ew, "warned", 1))
finding(report, "X031", function() by_region(ew, "warned", 1)[["cw_africa"]])
finding(report, "X032", function() nrow(ew4a))
finding(report, "X033", function() sum(ew4a$coverage >= 200 / 3))
finding(report, "X034", function() countries("coverage", c("MOZ", "SOM")))
finding(report, "X035", function() by_type(ew, "warned", 1, c("hurricane", "heatwave", "sandstorm", "earthquake",
                                                              "landslide")))
finding(report, "X036", able)
finding(report, "X037", not_able)
finding(report, "X038", function() by_income(w, ACT, 1))
finding(report, "X039", function() hazard_pair("sandstorm")[["warned"]])
finding(report, "X040", function() hazard_pair("sandstorm")[["act"]])
finding(report, "X041", storms_floods)
finding(report, "X042", function() by_action("index"))
finding(report, "X043", function() action_gap("index"))
finding(report, "X044", function() by_action("individual"))
finding(report, "X045", function() action_gap("societal"))
finding(report, "X046", coverage)
finding(report, "X047", function() c("1" = n_warnings()[["1"]], "6plus" = n_warnings()[["6"]]))
finding(report, "X048", function() channel(c("internet", "tv", "sms")))
finding(report, "X049", function() able_by_n()[c("1", "2", "3")])
finding(report, "X050", gains_after_three)
finding(report, "X051", function() idv_by_n(c(1, 0, 2, 3)))
finding(report, "X052", function() plan_agency(c("neither", "plan", "agency", "both")))

# Policy implications
finding(report, "X053", function() country["TCD", "coverage"])
finding(report, "X054", function() country["TCD", "impacted"])
finding(report, "X055", phone_share)
finding(report, "X056", phone_millions)
finding(report, "X057", phone_90_regions)
finding(report, "X058", function() plan_agency(c("neither", "both")))

# --- Chapter 1: which disasters impact people the most? ------------------------------

finding(report, "X059", impacted)
finding(report, "X060", function() type_share("flood")[["flood"]])
finding(report, "X061", impacted)
finding(report, "X062", experienced_2023)
finding(report, "X063", impacted)
finding(report, "C1_1", function() c(yes = pct(d, IMPACTED, 1), no = pct(d, IMPACTED, 2)))
finding(report, "X064", function() type_share(c("flood", "hurricane", "earthquake")))
finding(report, "X065", function() type_share(c("flood", "hurricane", "earthquake")))
finding(report, "X066", function() {
  dist <- distribution(exp23, "WP22247")
  c(flood = dist[["1"]], hurricane = dist[["2"]], earthquake = dist[["7"]])
})
finding(report, "X067", function() type_share(c("drought", "wildfire", "heatwave")))
finding(report, "X068", function() type_share(c("tornado", "blizzard", "landslide", "thunder", "volcano")))
finding(report, "X069", function() type_share(c("sandstorm", "tsunami")))
finding(report, "C1_2", function() type_share(unname(TYPES)))
finding(report, "X070", function() by_income(d, IMPACTED, 1, c("low", "high")))
finding(report, "X071", income_ratio)
finding(report, "C1_3", function() by_income(d, IMPACTED, 1))
finding(report, "X072", function() by_income(d, IMPACTED, 1)[["low"]])
finding(report, "X073", function() by_income(d, IMPACTED, 1)[["high"]])
finding(report, "X074", function() 1 / income_ratio())
finding(report, "X075", function() by_income(d, IMPACTED, 1, c("lower_middle", "upper_middle")))
finding(report, "X076", low_income_education)
finding(report, "X077", function() by_region(d, IMPACTED, 1, c("anz", "eastern_africa", "southeastern_asia",
                                                               "northern_africa", "central_asia")))
finding(report, "C1_4", function() by_region(d, IMPACTED, 1))
finding(report, "X078", function() by_region(d, IMPACTED, 1)[["anz"]])
finding(report, "X079", function() by_region(d, IMPACTED, 1, c("eastern_africa", "southeastern_asia")))
finding(report, "X080", function() by_region(d, IMPACTED, 1)[["eastern_asia"]])
finding(report, "X081", function() by_region(d, IMPACTED, 1)[["southern_europe"]])
finding(report, "X082", function() by_region(d, IMPACTED, 1, c("eastern_europe", "nw_europe")))
finding(report, "X083", function() by_region(d, IMPACTED, 1, c("northern_africa", "central_asia")))
finding(report, "X084", function() countries("impacted", c("PHL", "ISR")))
# Every country's % impacted; the map labels 13 of them.
finding(report, "C1_5", function() setNames(country$impacted, country$iso))

# The Philippines (page 7, Chart 1.6): shares of the impacted.
finding(report, "X085", function() {
  dist <- phl()
  c(hurricane = dist[["2"]], flood = dist[["1"]], earthquake = dist[["7"]])
})
finding(report, "X086", function() {
  k <- c("visayas", "balance_luzon", "ncr")
  setNames(vapply(k, function(r) phl(r)[["2"]], numeric(1)), k)
})
finding(report, "X087", function() phl("ncr")[["1"]])
finding(report, "X088", function() {
  k <- c("balance_luzon", "mindanao")
  setNames(vapply(k, function(r) phl("ncr")[["1"]] / phl(r)[["1"]], numeric(1)), k)
})
finding(report, "X089", function() phl("mindanao")[["7"]])
finding(report, "X090", function() c(visayas_hurricane = phl("visayas")[["2"]],
                                     balance_luzon_hurricane = phl("balance_luzon")[["2"]],
                                     ncr_flood = phl("ncr")[["1"]], mindanao_earthquake = phl("mindanao")[["7"]]))
finding(report, "C1_6", function() {
  out <- c()
  for (r in PHL_REGIONS) {
    p <- phl(r)
    out[paste0(r, c("_hurricane", "_flood", "_earthquake"))] <- c(p[["2"]], p[["1"]], p[["7"]])
  }
  out
})

# --- Chapter 2: how prevalent are early warnings before disasters? --------------------

finding(report, "X091", coverage)
finding(report, "X092", coverage)
finding(report, "X093", warned_2023)
finding(report, "X094", channels_asked)
finding(report, "X095", function() by_income(ew, "warned", 1))
finding(report, "X096", function() c(warned = coverage(), none = pct(ew, "warned", 2)))
finding(report, "C2_1", function() c(warned = coverage(), none = pct(ew, "warned", 2)))
finding(report, "X097", function() by_income(ew, "warned", 1, c("low", "upper_middle", "high")))
finding(report, "C2_2", function() by_income(ew, "warned", 1))
finding(report, "X098", function() by_region(ew, "warned", 1, c("eastern_asia", "anz", "northern_america", "nw_europe")))
finding(report, "X099", function() by_region(ew, "warned", 1)[["cw_africa"]])
finding(report, "X100", function() by_region(ew, "warned", 1, c("eastern_asia", "cw_africa")))
finding(report, "C2_3", function() by_region(ew, "warned", 1))

# Countries (page 11): only countries with at least 100 respondents asked about warnings.
finding(report, "X101", function() countries("coverage", c("VNM", "HKG", "CHN")))
finding(report, "X102", function() {
  paste(sort(head(sufficient$iso[order(-sufficient$coverage)], 3)), collapse = ", ")
})
finding(report, "X103", function() countries("coverage", c("COG", "GAB")))
finding(report, "X104", function() {
  paste(sort(head(sufficient$iso[order(sufficient$coverage)], 2)), collapse = ", ")
})
finding(report, "X105", function() nrow(ew4a))
finding(report, "X106", function() sum(ew4a$coverage < 200 / 3))
finding(report, "X107", function() countries("coverage", c("MOZ", "SOM", "MUS", "LAO", "KHM")))
finding(report, "X108", function() sum(ew4a$coverage < 50))
finding(report, "X109", function() countries("coverage", c("TCD", "NPL")))
finding(report, "X110", function() country["TCD", "impacted"])
finding(report, "X111", function() country["NPL", "impacted"])
finding(report, "X112", function() country["TCD", "coverage"])
finding(report, "X113", function() country["TCD", "impacted"])
# Scatter of the 13 priority countries: no values are printed.
finding(report, "C2_4", function() {
  out <- c()
  for (iso in ew4a$iso) out[paste0(iso, c("_coverage", "_impacted"))] <- c(ew4a[iso, "coverage"], ew4a[iso, "impacted"])
  out
})
finding(report, "X114", function() by_type(ew, "warned", 1, c("hurricane", "heatwave", "sandstorm")))
finding(report, "X115", function() by_type(ew, "warned", 1, c("earthquake", "landslide")))
finding(report, "X116", function() by_type(ew, "warned", 1, c("hurricane", "earthquake", "landslide")))
finding(report, "C2_5", function() by_type(ew, "warned", 1, CHART_2_5))
finding(report, "X117", function() c(channels = length(CHANNELS), ratio = length(CHANNELS) / 4))
finding(report, "X118", function() channel(c("internet", "tv", "sms")))
finding(report, "X119", function() channel("radio")[["radio"]])
finding(report, "X120", function() channel(c("newspapers", "loudspeaker")))
finding(report, "X121", function() channel("billboard")[["billboard"]])
finding(report, "X122", function() channel(c("internet", "tv", "sms", "billboard")))
finding(report, "C2_6", function() channel(names(CHANNELS)))
finding(report, "X123", coverage)
finding(report, "X124", function() n_warnings()[["1"]])
finding(report, "X125", function() n_warnings()[["6"]])
finding(report, "X126", function() c("1" = n_warnings()[["1"]], "6plus" = n_warnings()[["6"]]))
finding(report, "C2_7", function() {
  r <- n_warnings()
  names(r)[names(r) == "6"] <- "6plus"
  c(r, any = coverage())
})
finding(report, "X127", function() idv_by_n(c(1, 0)))
finding(report, "X128", function() idv_by_n(2)[["2"]])
finding(report, "X129", function() idv_by_n(3)[["3"]])
finding(report, "X130", function() idv_by_n(c(1, 2, 3)))
finding(report, "C2_8", function() {
  r <- idv_by_n(0:6)
  names(r)[names(r) == "6"] <- "6plus"
  r
})

# Mobile phones and the unwarned (page 16): needs Gallup's WP17626.
finding(report, "X131", function() pct(ew, "warned", 2))
finding(report, "X132", phone_share)
finding(report, "X133", phone_millions)
finding(report, "X134", function() phone_regions(c("northern_america", "anz")))
finding(report, "X135", function() {
  r <- phone_by_region()
  sum(round(r$phone[r$shown]) > 90)
})
finding(report, "X136", function() phone_regions(c("southern_asia", "eastern_africa")))
finding(report, "X137", function() c(global = phone_share(), phone_regions(c("northern_america", "anz"))))
# Regions with fewer than 100 unwarned respondents are not shown (Northern America,
# Eastern Asia, Australia and New Zealand); they are still written to output/.
finding(report, "C2_9", function() {
  r <- phone_by_region()
  c(global = phone_share(), setNames(r$phone, rownames(r)))
})
finding(report, "X138", phone_share)

# --- Chapter 3: how effective are early warnings before a disaster? --------------------

finding(report, "X139", function() plan_agency(c("both", "agency", "plan", "neither")))
finding(report, "X140", coverage)
finding(report, "X141", able)
finding(report, "X142", not_able)
finding(report, "X143", function() c(able = able(), not = not_able()))
finding(report, "C3_1", function() c(able = able(), not = not_able()))
finding(report, "X144", function() by_income(w, ACT, 1, c("low", "lower_middle")))
finding(report, "X145", function() by_income(w, ACT, 1, c("upper_middle", "high")))
finding(report, "X146", function() by_region(w, ACT, 1)[["northern_america"]])
finding(report, "X147", function() by_region(w, ACT, 1, c("eastern_asia", "southeastern_asia", "anz", "nw_europe")))
finding(report, "X148", function() by_region(w, ACT, 1, c("northern_africa", "eastern_africa", "cw_africa",
                                                          "southern_africa")))
finding(report, "X149", function() by_region(w, ACT, 1, c("southern_europe", "latam", "eastern_europe")))
finding(report, "X150", function() by_region(w, ACT, 1, c("central_asia", "southern_asia")))
finding(report, "X151", function() by_region(w, ACT, 1, c("northern_america", "northern_africa", "eastern_africa",
                                                          "southern_africa")))
finding(report, "C3_2", function() by_region(w, ACT, 1))
finding(report, "X152", function() hazard_pair("sandstorm")[["warned"]])
finding(report, "X153", function() hazard_pair("sandstorm")[["act"]])
finding(report, "X154", storms_floods)
finding(report, "X155", function() hazard_pair("earthquake")[["act"]])
finding(report, "X156", function() hazard_pair("earthquake")[["warned"]])
finding(report, "X157", function() hazard_pair("drought")[["warned"]])
finding(report, "X158", function() hazard_pair("drought")[["act"]])
finding(report, "X159", function() {
  s <- hazard_pair("sandstorm"); e <- hazard_pair("earthquake")
  c(sandstorm_warned = s[["warned"]], sandstorm_act = s[["act"]], earthquake_warned = e[["warned"]],
    earthquake_act = e[["act"]])
})
# Bubble chart: no values are printed.
finding(report, "C3_3", function() {
  out <- c()
  for (h in CHART_3_3) out[paste0(h, c("_warned", "_act"))] <- hazard_pair(h)
  out
})
finding(report, "X160", function() by_action("index")[["able"]])
finding(report, "X161", function() action_gap("index"))
finding(report, "X162", function() by_action("index")[["not"]])
finding(report, "X163", function() action_gap("individual"))
finding(report, "X164", function() by_action("individual"))
finding(report, "X165", function() action_gap("household"))
finding(report, "X166", function() action_gap("community"))
finding(report, "X167", function() action_gap("societal"))
finding(report, "X168", function() {
  i <- by_action("index"); v <- by_action("individual")
  c(index_able = i[["able"]], index_not = i[["not"]], individual_able = v[["able"]], individual_not = v[["not"]])
})
finding(report, "C3_4", function() {
  out <- c()
  for (dim in names(DIMS)) {
    r <- by_action(dim)
    out[paste0(dim, c("_not", "_able", "_gap"))] <- c(r[["not"]], r[["able"]], action_gap(dim))
  }
  out
})
finding(report, "X169", function() able_by_n()[["1"]])
finding(report, "X170", function() round(able_by_n()[["2"]]) - round(able_by_n()[["1"]]))
finding(report, "X171", function() able_by_n()[["2"]])
finding(report, "X172", function() round(able_by_n()[["3"]]) - round(able_by_n()[["2"]]))
finding(report, "X173", function() able_by_n()[["3"]])
finding(report, "X174", gains_after_three)
finding(report, "X175", function() able_by_n()[c("1", "2", "3")])
finding(report, "X176", gains_after_three)
# Values by number of warnings; the gains are differences of the rounded values.
finding(report, "C3_5", function() {
  r <- able_by_n()
  key <- c("1" = "1", "2" = "2", "3" = "3", "4" = "4", "5" = "5", "6" = "6plus")
  out <- setNames(unname(r), key[names(r)])
  for (k in 2:6) out[paste0("gain_", key[[as.character(k)]])] <- round(r[[as.character(k)]]) - round(r[[as.character(k - 1)]])
  out
})

mean_warnings_by <- function(item, keys) {
  g <- merge_gallup(ew, item)
  r <- wmean(g, "nwarn", by = item)
  setNames(c(r[["1"]], r[["2"]]), keys)
}
finding(report, "X177", function() mean_warnings_by(PHONE, c("phone", "no_phone")))
finding(report, "X178", function() mean_warnings_by(INTERNET, c("internet", "no_internet")))
finding(report, "X179", function() plan_agency("neither")[["neither"]])
finding(report, "X180", function() plan_agency("plan")[["plan"]])
finding(report, "X181", function() plan_agency("agency")[["agency"]])
finding(report, "X182", function() plan_agency("both")[["both"]])
finding(report, "X183", function() plan_agency(c("both", "neither")))
finding(report, "C3_6", function() plan_agency(c("both", "plan", "agency", "neither")))

# --- Turning the World Risk Poll into action, and conclusion ---------------------------

finding(report, "X184", function() sum(ew4a$coverage < 50))
finding(report, "X185", function() country["NPL", "coverage"])
finding(report, "X186", function() by_type(ew, "warned", 1, "landslide")[["landslide"]])
finding(report, "X187", function() phone_regions("eastern_africa")[["eastern_africa"]])
finding(report, "X188", function() plan_agency(c("both", "neither")))
finding(report, "X189", coverage)
finding(report, "X190", regions_below_half)
finding(report, "X191", function() by_income(d, IMPACTED, 1, c("low", "high")))
finding(report, "X192", income_ratio)
finding(report, "X193", function() low_income_education()[["primary"]])
finding(report, "X194", function() by_income(ew, "warned", 1, c("low", "upper_middle", "high")))
finding(report, "X195", function() by_income(w, ACT, 1)[["low"]])
# Individual resilience in low-income countries, impacted (WP24213 = 1) vs not (= 2).
finding(report, "X196", function() {
  r <- wmean(d[d$CountryIncomeLevel %in% 1, ], "individual", by = IMPACTED)
  c(impacted = r[["1"]], not_impacted = r[["2"]])
})
finding(report, "X197", not_able)
finding(report, "X198", function() plan_agency(c("both", "neither")))
finding(report, "X199", function() idv_by_n(c(1, 0)))
finding(report, "X200", function() able_by_n()[["1"]])
finding(report, "X201", function() able_by_n()[c("2", "3")])
finding(report, "X202", gains_after_three)
finding(report, "X203", phone_share)
finding(report, "X204", phone_millions)
finding(report, "X205", phone_90_regions)
finding(report, "X206", function() country["TCD", "coverage"])
finding(report, "X207", function() country["TCD", "impacted"])

status <- run_report(report)
if (!interactive()) quit(status = status)
