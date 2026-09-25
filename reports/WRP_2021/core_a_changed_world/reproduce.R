# Reproduce World Risk Poll 2021: A Changed World? Perceptions and experiences
# of risk in the Covid age.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/core_a_changed_world/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

REGIONS <- c( # GlobalRegion code -> key
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia",
  "9" = "southeastern_asia", "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
)
QUINTILES <- c("1" = "bottom", "2" = "second", "3" = "middle", "4" = "fourth", "5" = "top") # INCOME_5
FEELINGS <- c("1" = "comfortable", "2" = "getting_by", "3" = "difficult", "4" = "very_difficult") # IncomeFeelings
EDUCATION <- c("1" = "primary", "2" = "secondary", "3" = "post_secondary")
PERSONAL <- c(1, 3) # experience items: 1 = yes, personally; 2 = know someone; 3 = both; 4 = no
DK <- c(98, 99)

WORRY_21 <- c(food = "WP20720", water = "WP20721", crime = "WP20722", weather = "WP20723",
              traffic = "WP22213", mental = "WP20726", work = "WP22214")
HARM_21 <- c(food = "WP22442", water = "WP22443", crime = "WP22444", weather = "WP22445",
             traffic = "WP22446", mental = "WP22447", work = "WP22448")
WORRY_19 <- c(food = "L6A", water = "L6B", crime = "L6C", weather = "L6D", mental = "L6G")
HARM_19 <- c(food = "L8A", water = "L8B", crime = "L8C", weather = "L8D", mental = "L8G")

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "AgeGroups4", "Gender",
  "Education", "INCOME_5", "IncomeFeelings", "WP20711", "WP22331", "WP20719",
  unname(WORRY_21), unname(HARM_21)
))
d19 <- load_wave(2019, c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "L2", "L3_A", "L5", "L14",
  unname(WORRY_19), unname(HARM_19)
))

# --- Derived variables ---------------------------------------------------------

# Trend frames. Comparisons use only the 119 countries surveyed in both years
# (report p. 10), with the questions under common names:
#   safe     feel more (1), less (2) or about as safe (3) as five years ago
#   risk     greatest source of risk, on the 2021 codes (WP22331)
#   climate  climate change a threat: very (1), somewhat (2), not (3)
#   worry_*  very (1), somewhat (2), not worried (3)
#   harm_*   experienced serious harm in the past two years: yes (1), no (2).
#            2019 has only yes/no; in 2021 "yes" is the respondent, someone
#            they know, or both, which is how the report trends it (p. 22).
COMMON <- countries_in_all(c(2019, 2021))
recode <- function(x, map) unname(map[as.character(x)])
RISK_2019_TO_2021 <- c( # L3_A code -> WP22331 code. 2019 has no hunger, Covid-19, war or disaster codes.
  "1" = 1, "2" = 2, "3" = 3, "4" = 16, "5" = 9, "6" = 10, "7" = 11, "8" = 12, "9" = 5, "10" = 6, "11" = 13,
  "12" = 14, "13" = 18, "14" = 17, "15" = 8, "16" = 19, "17" = 21, "18" = 22, "19" = 23, "98" = 98, "99" = 99
)
ANY_HARM <- c("1" = 1, "2" = 1, "3" = 1, "4" = 2, "98" = 98, "99" = 99)

t19 <- d19[d19$COUNTRY_ISO3 %in% COMMON, ]
t19$safe <- t19$L2
t19$risk <- recode(t19$L3_A, RISK_2019_TO_2021)
t19$climate <- t19$L5
t21 <- d[d$COUNTRY_ISO3 %in% COMMON, ]
t21$safe <- t21$WP20711
t21$risk <- t21$WP22331
t21$climate <- t21$WP20719
for (item in names(WORRY_19)) {
  t19[[paste0("worry_", item)]] <- t19[[WORRY_19[[item]]]]
  t19[[paste0("harm_", item)]] <- t19[[HARM_19[[item]]]]
}
for (item in names(WORRY_21)) {
  t21[[paste0("worry_", item)]] <- t21[[WORRY_21[[item]]]]
  t21[[paste0("harm_", item)]] <- recode(t21[[HARM_21[[item]]]], ANY_HARM)
}
TREND <- list("2019" = t19, "2021" = t21)

# The two waves for a trend on `var`, both restricted to the countries asked it
# in 2021. The safety and greatest-risk questions were not asked in China in
# 2021, so China is left out of the 2019 figures for those questions too.
trend <- function(var) {
  asked <- unique(t21$COUNTRY_ISO3[!is.na(t21[[var]])])
  lapply(TREND, function(df) df[df$COUNTRY_ISO3 %in% asked, ])
}

# Severe weather harm group (Chart 5.3): experienced (personally or both),
# know someone who has, neither. Don't know / refused are not shown.
d$weather_harm <- recode(d$WP22445, c("1" = 1, "3" = 1, "2" = 2, "4" = 3))

# --- Helpers -------------------------------------------------------------------

# % in each named category of `var` (a category may pool several codes): a
# named vector, or with `by` a groups x names matrix.
shares <- function(df, var, cats, by = NULL) {
  tab <- distribution(df, var, by = by)
  if (is.null(by)) {
    return(vapply(cats, function(codes) sum(tab[intersect(as.character(codes), names(tab))]), numeric(1)))
  }
  out <- sapply(cats, function(codes) rowSums(tab[, intersect(as.character(codes), colnames(tab)), drop = FALSE]))
  matrix(out, nrow = nrow(tab), dimnames = list(rownames(tab), names(cats)))
}

# c("<keys[group]>_<column>" = value) for a groups x names matrix, in the order of `keys`.
flat <- function(tab, keys) {
  out <- numeric(0)
  for (g in names(keys)) {
    if (!g %in% rownames(tab)) next
    for (cc in colnames(tab)) out[paste(keys[[g]], cc, sep = "_")] <- tab[g, cc]
  }
  out
}

by_country <- function(df, var, codes, countries) {
  pct(df[df$COUNTRY_ISO3 %in% countries, ], var, codes, by = "COUNTRY_ISO3")[countries]
}

# Difference and ratio of rounded percentages, as the report computes them.
rdiff <- function(a, b) round(a) - round(b)
rratio <- function(a, b) round(a) / round(b)

# Region code -> codes of its `n` most-named risks; 'other', DK and refused excluded.
top_named <- function(df, n = 3) {
  tab <- distribution(df, "WP22331", by = "GlobalRegion")
  tab <- tab[, setdiff(colnames(tab), c("22", "98", "99")), drop = FALSE]
  tops <- lapply(rownames(tab), function(g) as.numeric(names(sort(tab[g, ], decreasing = TRUE))[seq_len(n)]))
  setNames(tops, rownames(tab))
}

SAFE <- list(more = 1, same = 3, less = 2, dk = DK)
RISKS <- c( # Chart 1.3 / 1.4 category -> WP22331 code
  road = 1, crime = 3, health = 5, covid = 7, none = 23, financial = 9, economic = 10, other = 22,
  climate = 19, work = 17, war = 4, politics = 11, non_road = 2, cooking = 16, mental = 8,
  disasters = 20, drugs = 6, hunger = 15, pollution = 18, water = 13, internet = 12, food = 14, drowning = 21
)
CLIMATE <- list(very = 1, somewhat = 2, not = 3, dk = DK)
workers <- d[!is.na(d$WP22214), ] # worry about work was asked only of the employed

# --- Preface, Executive Summary, Introduction -----------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() length(unique(d19$COUNTRY_ISO3)))
finding(report, "X04", function() length(setdiff(unique(d$COUNTRY_ISO3), unique(d19$COUNTRY_ISO3))))
finding(report, "X05", function() length(COMMON))

finding(report, "X06", function() {
  w <- trend("safe")
  more19 <- pct(w[["2019"]], "safe", 1)
  more21 <- pct(w[["2021"]], "safe", 1)
  c(less_2019 = pct(w[["2019"]], "safe", 2), less_2021 = pct(w[["2021"]], "safe", 2),
    more_2021 = more21, more_change = rdiff(more21, more19))
})
finding(report, "X07", function() sapply(RISKS[c("covid", "road", "crime", "health")], function(code) pct(d, "WP22331", code)))
finding(report, "X08", function() {
  t <- distribution(d, "WP22331")
  t <- t[setdiff(names(t), c("22", "23", "98", "99"))]
  sum(t > t[["7"]]) + 1
})
finding(report, "X09", function() {
  w <- trend("risk")
  c(health_2019 = pct(w[["2019"]], "risk", 5), none_2019 = pct(w[["2019"]], "risk", 23),
    none_2021 = pct(w[["2021"]], "risk", 23))
})
finding(report, "X10", function() {
  old <- d[d$AgeGroups4 %in% 4, ]
  c(covid = pct(old, "WP22331", 7), health = pct(old, "WP22331", 5))
})
finding(report, "X11", function() {
  c(threat_2021 = pct(t21, "climate", 1:2), threat_2019 = pct(t19, "climate", 1:2),
    very_2021 = pct(t21, "climate", 1), very_2019 = pct(t19, "climate", 1))
})
finding(report, "X12", function() {
  very <- pct(d, "WP20719", 1, by = "Education")
  dk <- pct(d, "WP20719", DK, by = "Education")
  c(setNames(very[names(EDUCATION)], paste0("very_", EDUCATION)), setNames(dk[names(EDUCATION)], paste0("dk_", EDUCATION)))
})
finding(report, "X13", function() pct(d19, "L14", 5)) # 5 = the government food safety agency

# --- Chapter 1: Global perceptions of safety and greatest risks in 2021 ---------------

less_safe_by <- function(by) {
  w <- trend("safe")
  list(pct(w[["2019"]], "safe", 2, by = by), pct(w[["2021"]], "safe", 2, by = by))
}

finding(report, "X14", function() {
  r <- less_safe_by("GlobalRegion")
  sum(rdiff(r[[2]][names(REGIONS)], r[[1]][names(REGIONS)]) > 10)
})
finding(report, "X15", function() {
  r <- pct(d, "WP22331", 3, by = "GlobalRegion")
  c(latin_america = r[["5"]], southern_africa = r[["4"]])
})
finding(report, "X16", function() {
  r <- less_safe_by("GlobalRegion")
  out <- numeric(0)
  for (code in c("9", "2", "6", "13", "12", "5")) {
    k <- REGIONS[[code]]
    out[paste0(k, "_2019")] <- r[[1]][[code]]
    out[paste0(k, "_2021")] <- r[[2]][[code]]
    out[paste0(k, "_change")] <- rdiff(r[[2]][[code]], r[[1]][[code]])
  }
  out
})
finding(report, "X17", function() {
  # Gallup World Poll: satisfied with the availability of quality healthcare
  # in the city or area where you live (1 = satisfied). Placeholder item name.
  g <- merge_gallup(d, "GWP_HEALTHCARE_SATISFACTION")
  r <- pct(g, "GWP_HEALTHCARE_SATISFACTION", 1, by = "GlobalRegion")
  setNames(r[c("13", "14", "12")], REGIONS[c("13", "14", "12")])
})
finding(report, "X18", function() {
  r <- less_safe_by("COUNTRY_ISO3")
  c("2019" = r[[1]][["NGA"]], "2021" = r[[2]][["NGA"]])
})
finding(report, "X19", function() {
  na <- d[d$GlobalRegion %in% 6, ]
  100 * sum(na$PROJWT[na$COUNTRY_ISO3 == "USA"]) / sum(na$PROJWT)
})
finding(report, "X20", function() by_country(d, "WP22331", 7, "USA")[["USA"]])
finding(report, "X21", function() {
  t <- shares(d, "WP22331", list(road = 1, crime = 3, financial = 9), by = "Education")
  c(post_secondary_road = t["3", "road"], post_secondary_crime = t["3", "crime"],
    primary_financial = t["1", "financial"], primary_road = t["1", "road"],
    primary_crime = t["1", "crime"], post_secondary_financial = t["3", "financial"])
})
finding(report, "X22", function() pct(d[d$WP22331 %in% 7, ], "WP20711", 2))
finding(report, "X89", function() sum(round(pct(d, "WP20711", 2, by = "WP22331")[c("4", "11", "3")]) >= 50))
finding(report, "X90", function() {
  r <- pct(d, "WP20711", 2, by = "WP22331")
  c(road = r[["1"]], cooking = r[["16"]])
})
finding(report, "X23", function() sum(sapply(top_named(d), function(top) 7 %in% top)))
finding(report, "X24", function() {
  tops <- top_named(d)
  sapply(RISKS[c("road", "health", "crime")], function(code) sum(sapply(tops, function(top) code %in% top)))
})
finding(report, "X25", function() sum(sapply(top_named(d, 1), function(top) top[1] == 7)))
finding(report, "X26", function() by_country(d, "WP22331", 7, c("DZA", "EGY")))
finding(report, "X27", function() {
  r <- round(pct(d, "WP22331", 3, by = "GlobalRegion"))
  min(r[["5"]], r[["4"]]) / max(r[setdiff(names(r), c("5", "4"))])
})
finding(report, "X28", function() by_country(d, "WP22331", 3, c("VEN", "ECU", "ARG", "COL", "MEX")))
finding(report, "X29", function() {
  # Gallup World Poll WP1325: would like to move permanently to another
  # country (1) or continue living in this country (2).
  g <- merge_gallup(d, "WP1325")
  c(latin_america = pct(g[g$GlobalRegion %in% 5, ], "WP1325", 1), global = pct(g, "WP1325", 1))
})
finding(report, "X30", function() {
  la <- d[d$GlobalRegion %in% 5, ]
  age <- pct(la, "WP22331", 3, by = "AgeGroups4")
  sex <- pct(la, "WP22331", 3, by = "Gender")
  inc <- pct(la, "WP22331", 3, by = "INCOME_5")
  edu <- pct(la, "WP22331", 3, by = "Education")
  c(age_15_29 = age[["1"]], age_65plus = age[["4"]], men = sex[["1"]], women = sex[["2"]],
    income_bottom = inc[["1"]], income_top = inc[["5"]], post_secondary = edu[["3"]], primary = edu[["1"]])
})
finding(report, "X31", function() by_country(d, "WP22331", 1, c("FIN", "ISL", "NZL", "NOR", "NLD", "AUS")))
finding(report, "X32", function() {
  # Gallup World Poll: satisfied with the roads and highways (1 = satisfied). Placeholder item name.
  g <- merge_gallup(d, "GWP_ROADS_SATISFACTION")
  r <- pct(g, "GWP_ROADS_SATISFACTION", 1, by = "GlobalRegion")
  setNames(r[c("2", "1", "5", "13")], REGIONS[c("2", "1", "5", "13")])
})

road_trend <- function() {
  w <- trend("risk")
  list(pct(w[["2019"]], "risk", 1, by = "COUNTRY_ISO3"), pct(w[["2021"]], "risk", 1, by = "COUNTRY_ISO3"))
}
finding(report, "X33", function() {
  r <- road_trend()
  east <- unique(t21$COUNTRY_ISO3[t21$GlobalRegion %in% 8])
  east <- east[east %in% names(r[[1]]) & east %in% names(r[[2]])]
  sum(rdiff(r[[2]][east], r[[1]][east]) > 10)
})
finding(report, "X34", function() {
  r <- road_trend()
  c(KOR_2019 = r[[1]][["KOR"]], KOR_2021 = r[[2]][["KOR"]], HKG_2019 = r[[1]][["HKG"]], HKG_2021 = r[[2]][["HKG"]])
})

finding(report, "C1_1", function() {
  w <- trend("safe")
  c(setNames(shares(w[["2019"]], "safe", SAFE), paste0("2019_", names(SAFE))),
    setNames(shares(w[["2021"]], "safe", SAFE), paste0("2021_", names(SAFE))))
})
finding(report, "C1_2", function() {
  w <- trend("safe")
  cats <- SAFE[c("more", "same", "less")]
  t <- lapply(w, function(df) shares(df, "safe", cats, by = "GlobalRegion"))
  out <- numeric(0)
  for (code in names(REGIONS)) {
    k <- REGIONS[[code]]
    for (y in c("2019", "2021")) for (cc in names(cats)) out[paste(k, y, cc, sep = "_")] <- t[[y]][code, cc]
    out[paste0(k, "_diff")] <- rdiff(t[["2021"]][code, "less"], t[["2019"]][code, "less"])
  }
  out
})
finding(report, "T1_1", function() {
  w <- trend("safe")
  cats <- SAFE[c("less", "same", "more")]
  t <- lapply(w, function(df) shares(df, "safe", cats, by = "COUNTRY_ISO3"))
  out <- numeric(0)
  for (iso in c("MMR", "ARM", "VNM", "NGA", "TUR")) {
    for (y in c("2019", "2021")) for (cc in names(cats)) out[paste(iso, y, cc, sep = "_")] <- t[[y]][iso, cc]
    out[paste0(iso, "_diff")] <- rdiff(t[["2021"]][iso, "less"], t[["2019"]][iso, "less"])
  }
  out
})
finding(report, "C1_3", function() {
  w <- trend("risk")
  out <- numeric(0)
  for (k in names(RISKS)) {
    code <- RISKS[[k]]
    # Covid-19, war and non-weather disasters were not coded in 2019. 2019 has
    # no hunger code either, so hunger comes out as 0% (see README).
    if (!code %in% c(7, 4, 20)) out[paste0(k, "_2019")] <- pct(w[["2019"]], "risk", code)
    out[paste0(k, "_2021")] <- pct(w[["2021"]], "risk", code)
  }
  out
})
finding(report, "C1_4", function() {
  r <- pct(d, "WP20711", 2, by = "WP22331")
  keep <- RISKS[!names(RISKS) %in% c("none", "other")]
  setNames(r[as.character(keep)], names(keep))
})

T12_CATS <- list(covid = 7, health = 5, road = 1, crime = 3, financial = 9, economic = 10, cooking = 16, none = 23)
# Table 1.2 and Chart 1.5 use the 119 countries surveyed in both years (t21):
# with all 121, Eastern Europe's road figure is 13% (published 12%), because
# of the Czech Republic, surveyed only in 2021. Every other value is the
# same either way (see README).
finding(report, "T1_2", function() flat(shares(t21, "WP22331", T12_CATS, by = "GlobalRegion"), REGIONS))
finding(report, "C1_5", function() {
  r <- pct(t21, "WP22331", 3, by = "GlobalRegion")
  setNames(r[names(REGIONS)], REGIONS)
})

# --- Chapter 2: Risk perceptions and experiences of harm ---------------------------
# Worry about work was asked only of the employed. Personal experience of harm
# from work is taken over everyone asked the experience item: that is what
# reproduces Charts 2.1 and 2.3 and Table 2.2 (see README).

finding(report, "X35", function() {
  w <- pct(t21, "worry_work", 1)
  e <- pct(t21, "harm_work", 1)
  c(experienced = e, very_worried = w, ratio = rratio(w, e))
})
finding(report, "X36", function() {
  it <- d[d$COUNTRY_ISO3 == "ITA", ]
  c(experienced = pct(it, "WP22448", PERSONAL), very_worried = pct(it, "WP22214", 1))
})
finding(report, "X37", function() {
  listed <- c("SLE", "GHA", "ZMB", "IND", "PHL", "AFG")
  food <- by_country(d, "WP22442", PERSONAL, listed)
  water <- by_country(d, "WP22443", PERSONAL, listed)
  sum(pmax(food, water) > 20)
})
finding(report, "X38", function() {
  w <- pct(t21, "worry_crime", 1)
  e <- pct(t21, "harm_crime", 1)
  c(very_worried = w, experienced = e, ratio = rratio(w, e))
})
finding(report, "X39", function() {
  c(experienced_2019 = pct(t19, "harm_weather", 1), experienced_2021 = pct(t21, "harm_weather", 1),
    very_worried_2019 = pct(t19, "worry_weather", 1), very_worried_2021 = pct(t21, "worry_weather", 1))
})
finding(report, "X40", function() {
  r <- pct(workers, "WP22214", 1, by = "GlobalRegion")
  codes <- c("2", "4", "10", "1", "6", "13", "15")
  setNames(r[codes], REGIONS[codes])
})
finding(report, "X41", function() sum(round(pct(workers, "WP22214", 1, by = "GlobalRegion")) >= 30))
finding(report, "X42", function() {
  r <- pct(d, "WP22448", PERSONAL, by = "GlobalRegion")
  codes <- c("10", "14", "9")
  setNames(r[codes], REGIONS[codes])
})
finding(report, "X43", function() {
  e <- by_country(d, "WP22448", PERSONAL, c("BEL", "GIN"))
  w <- by_country(workers, "WP22214", 1, c("BEL", "GIN"))
  c(BEL_experienced = e[["BEL"]], BEL_very_worried = w[["BEL"]], GIN_experienced = e[["GIN"]], GIN_very_worried = w[["GIN"]])
})
finding(report, "X44", function() {
  rratio(by_country(workers, "WP22214", 1, "BEL")[["BEL"]], by_country(d, "WP22448", PERSONAL, "BEL")[["BEL"]])
})
finding(report, "X45", function() sum(by_country(d, "WP22448", PERSONAL, c("ITA", "CHE", "AFG", "VNM")) >= 18))
finding(report, "X46", function() by_country(d, "WP20722", 1, "AFG")[["AFG"]])
finding(report, "X47", function() sum(pct(d, "WP22448", PERSONAL, by = "COUNTRY_ISO3") > 30))
finding(report, "X48", function() {
  e <- pct(d, "WP22448", PERSONAL, by = "IncomeFeelings")
  w <- pct(workers, "WP22214", 1, by = "IncomeFeelings")
  c(experienced_very_difficult = e[["4"]], experienced_comfortable = e[["1"]], experienced_getting_by = e[["2"]],
    very_worried_very_difficult = w[["4"]], very_worried_comfortable = w[["1"]])
})
finding(report, "X49", function() {
  w <- pct(workers, "WP22214", 1, by = "IncomeFeelings")
  rratio(w[["4"]], w[["1"]])
})

struggling <- d[d$IncomeFeelings %in% c(3, 4), ] # finding it difficult or very difficult
finding(report, "X50", function() pct(struggling[struggling$GlobalRegion %in% 10, ], "WP22448", PERSONAL))
finding(report, "X51", function() pct(struggling[struggling$COUNTRY_ISO3 == "IND", ], "WP22448", PERSONAL))
finding(report, "X52", function() {
  # PROJWT sums to the adult population, so this is the number of people.
  ind <- struggling[struggling$COUNTRY_ISO3 == "IND", ]
  sum(ind$PROJWT[ind$WP22448 %in% PERSONAL])
})
finding(report, "X53", function() {
  vd <- d[d$IncomeFeelings %in% 4, ]
  c(northern_america = pct(vd[vd$GlobalRegion %in% 6, ], "WP22448", PERSONAL),
    by_country(vd, "WP22448", PERSONAL, c("USA", "CAN")))
})

finding(report, "T2_1", function() {
  out <- numeric(0)
  for (item in c("work", "mental", "food", "traffic", "water", "weather", "crime")) {
    for (y in names(TREND)) {
      df <- TREND[[y]]
      if (!paste0("worry_", item) %in% names(df)) next
      w <- pct(df, paste0("worry_", item), 1)
      e <- pct(df, paste0("harm_", item), 1)
      out[paste(item, y, c("very_worried", "experienced", "ratio"), sep = "_")] <- c(w, e, rratio(w, e))
    }
  }
  out
})
finding(report, "C2_1", function() {
  w <- pct(workers, "WP22214", 1, by = "GlobalRegion")
  e <- pct(d, "WP22448", PERSONAL, by = "GlobalRegion")
  out <- numeric(0)
  for (code in names(REGIONS)) {
    out[paste0(REGIONS[[code]], "_very_worried")] <- w[[code]]
    out[paste0(REGIONS[[code]], "_experienced")] <- e[[code]]
  }
  out
})
finding(report, "C2_2", function() {
  # Scatter plot with no printed values: computed for reference only.
  w <- pct(workers, "WP22214", 1, by = "COUNTRY_ISO3")
  e <- pct(d, "WP22448", PERSONAL, by = "COUNTRY_ISO3")
  iso <- sort(names(w))
  c(setNames(w[iso], paste0(iso, "_very_worried")), setNames(e[iso], paste0(iso, "_experienced")))
})
finding(report, "C2_3", function() {
  e <- pct(d, "WP22448", PERSONAL, by = "IncomeFeelings")
  w <- pct(workers, "WP22214", 1, by = "IncomeFeelings")
  c(setNames(e[names(FEELINGS)], paste0("experienced_", FEELINGS)),
    setNames(w[names(FEELINGS)], paste0("very_worried_", FEELINGS)))
})
finding(report, "T2_2", function() {
  r <- pct(d[d$IncomeFeelings %in% 1:4, ], "WP22448", PERSONAL, by = c("GlobalRegion", "IncomeFeelings"))
  keys <- expand.grid(f = names(FEELINGS), g = names(REGIONS), stringsAsFactors = FALSE)
  setNames(r[paste(keys$g, keys$f, sep = "_")], paste(REGIONS[keys$g], FEELINGS[keys$f], sep = "_"))
})
finding(report, "X54", function() by_country(d, "WP22442", PERSONAL, c("SLE", "GHA", "ZMB", "IND", "MOZ", "PHL", "AFG", "DZA")))
finding(report, "X55", function() sum(pct(d, "WP22442", PERSONAL, by = "COUNTRY_ISO3") >= 20))
finding(report, "X56", function() by_country(d, "WP20720", 1, c("MOZ", "SLE", "GHA", "PHL", "ZMB", "DZA")))
finding(report, "X57", function() sum(by_country(d, "WP22443", PERSONAL, c("CMR", "COG")) > 25))
finding(report, "X58", function() {
  listed <- c("SLE", "COG", "GHA", "PHL")
  w <- by_country(d, "WP20721", 1, listed)
  e <- by_country(d, "WP22443", PERSONAL, listed)
  out <- numeric(0)
  for (iso in listed) {
    out[paste0(iso, "_very_worried")] <- w[[iso]]
    out[paste0(iso, "_experienced")] <- e[[iso]]
  }
  out
})
finding(report, "X91", function() {
  listed <- c("SLE", "COG", "GHA")
  rratio(by_country(d, "WP20721", 1, listed), by_country(d, "WP22443", PERSONAL, listed))
})
finding(report, "C2_4", function() {
  # Scatter plots with no printed values: computed for reference only.
  out <- numeric(0)
  items <- list(food = c("WP20720", "WP22442"), water = c("WP20721", "WP22443"))
  for (item in names(items)) {
    w <- pct(d, items[[item]][1], 1, by = "COUNTRY_ISO3")
    e <- pct(d, items[[item]][2], PERSONAL, by = "COUNTRY_ISO3")
    iso <- sort(names(w))
    out <- c(out, setNames(w[iso], paste(item, iso, "very_worried", sep = "_")),
             setNames(e[iso], paste(item, iso, "experienced", sep = "_")))
  }
  out
})

# --- Chapter 3: Covid-19 and risk perceptions -----------------------------------------

covid_by_country <- function(df = d) pct(df, "WP22331", 7, by = "COUNTRY_ISO3")
SEA <- sort(unique(d$COUNTRY_ISO3[d$GlobalRegion %in% 9]))

finding(report, "X59", function() sum(covid_by_country()[SEA] > 10))
finding(report, "X60", function() covid_by_country()[c("MYS", "PHL")])
finding(report, "X61", function() length(SEA))
finding(report, "C3_1", function() {
  flat(shares(d, "WP22331", list(health = 5, covid = 7), by = "AgeGroups4"),
       c("1" = "15_29", "2" = "30_49", "3" = "50_64", "4" = "65plus"))
})
finding(report, "X62", function() {
  r <- pct(d, "WP22331", 7, by = "INCOME_5")
  c(bottom = r[["1"]], top = r[["5"]])
})
finding(report, "X63", function() {
  r <- pct(d[d$GlobalRegion %in% 3, ], "WP22331", 7, by = "INCOME_5")
  c(bottom = r[["1"]], top_three_min = min(r[c("3", "4", "5")]), top_three_max = max(r[c("3", "4", "5")]))
})
finding(report, "T3_1", function() {
  overall <- pct(d, "WP22331", 7, by = "GlobalRegion")
  q <- pct(d, "WP22331", 7, by = c("GlobalRegion", "INCOME_5"))
  out <- numeric(0)
  for (code in names(REGIONS)) {
    k <- REGIONS[[code]]
    out[paste0(k, "_overall")] <- overall[[code]]
    for (qc in names(QUINTILES)) out[paste(k, QUINTILES[[qc]], sep = "_")] <- q[[paste(code, qc, sep = "_")]]
  }
  out
})
finding(report, "C3_2", function() {
  # Scatter plot with no printed values; needs the Gallup healthcare item.
  g <- merge_gallup(d, "GWP_HEALTHCARE_SATISFACTION")
  h <- pct(g, "GWP_HEALTHCARE_SATISFACTION", 1, by = "COUNTRY_ISO3")
  s <- pct(g, "WP20711", 2, by = "COUNTRY_ISO3")
  iso <- sort(names(s))
  c(setNames(h[iso], paste0(iso, "_satisfied")), setNames(s[iso], paste0(iso, "_less_safe")))
})
finding(report, "X64", function() sum(pct(d, "WP20711", 2, by = "COUNTRY_ISO3") > 200 / 3))
finding(report, "X65", function() {
  r <- pct(d, "WP22331", 7, by = "GlobalRegion")
  c(southeastern_asia = r[["9"]], northern_africa = r[["3"]])
})
finding(report, "M3_1", function() covid_by_country()[c("MMR", "LAO", "VNM", "THA", "PHL", "MYS", "KHM", "SGP", "IDN")])
finding(report, "X66", function() {
  r <- covid_by_country()
  sum(r[setdiff(names(r), SEA)] >= 100 / 3)
})

# --- Chapter 4: Do policymakers focus on people's greatest sources of risk? ---------

FIVE <- c("weather", "mental", "crime", "food", "water")

finding(report, "X67", function() c("2019" = pct(t19, "harm_mental", 1), "2021" = pct(t21, "harm_mental", 1)))
finding(report, "X68", function() {
  sapply(c(weather = "weather", mental = "mental"), function(k) {
    rdiff(pct(t21, paste0("harm_", k), 1), pct(t19, paste0("harm_", k), 1))
  })
})
finding(report, "C4_1", function() {
  out <- numeric(0)
  for (k in FIVE) for (y in c("2019", "2021")) out[paste(k, y, sep = "_")] <- pct(TREND[[y]], paste0("harm_", k), 1)
  out
})
finding(report, "X69", function() {
  sum(sapply(FIVE, function(k) abs(rdiff(pct(t21, paste0("worry_", k), 1), pct(t19, paste0("worry_", k), 1))) <= 1))
})
finding(report, "X70", function() {
  out <- numeric(0)
  for (k in c("crime", "food", "water")) for (y in c("2019", "2021")) out[paste(k, y, sep = "_")] <- pct(TREND[[y]], paste0("worry_", k), 1)
  out
})
finding(report, "X71", function() c("2019" = pct(t19, "worry_mental", 1), "2021" = pct(t21, "worry_mental", 1)))
finding(report, "C4_2", function() {
  out <- numeric(0)
  for (k in c("weather", "crime", "mental", "food", "water")) {
    for (y in c("2019", "2021")) out[paste(k, y, sep = "_")] <- pct(TREND[[y]], paste0("worry_", k), 1)
  }
  out
})
finding(report, "X72", function() c(personally = pct(t21, "WP22447", PERSONAL), someone_known = pct(t21, "WP22447", 2)))
finding(report, "C4_3", function() {
  # Totals for each World Bank income group; the country points carry no values.
  r <- pct(d, "WP22447", PERSONAL, by = "CountryIncomeLevel")
  cc <- pct(d, "WP22447", PERSONAL, by = "COUNTRY_ISO3")
  c(low = r[["1"]], lower_middle = r[["2"]], upper_middle = r[["3"]], high = r[["4"]], cc[sort(names(cc))])
})
finding(report, "X73", function() {
  r <- pct(d, "WP20719", 1, by = "GlobalRegion")
  c(northern_america = r[["6"]], australia_nz = r[["15"]])
})
finding(report, "C4_4", function() {
  r <- pct(d[d$GlobalRegion %in% c(6, 15, 10, 9), ], "WP20719", 1, by = c("GlobalRegion", "WP20723"))
  keys <- expand.grid(w = c("1", "2", "3"), g = c("6", "15", "10", "9"), stringsAsFactors = FALSE)
  setNames(r[paste(keys$g, keys$w, sep = "_")], paste(REGIONS[keys$g], c("1" = "very", "2" = "somewhat", "3" = "not")[keys$w], sep = "_"))
})

QWORRY <- list(road = "WP22213", weather = "WP20723", mental = "WP20726", work = "WP22214",
               food = "WP20720", water = "WP20721", crime = "WP20722")
worry_by_quintile <- function(item) {
  df <- if (item == "work") workers else d
  pct(df, QWORRY[[item]], 1, by = "INCOME_5")
}
finding(report, "X74", function() {
  out <- numeric(0)
  for (item in c("road", "weather", "mental", "work")) {
    r <- worry_by_quintile(item)
    out[paste0(item, "_top")] <- r[["5"]]
    out[paste0(item, "_bottom")] <- r[["1"]]
  }
  out
})
finding(report, "X75", function() {
  sum(sapply(names(QWORRY), function(item) {
    r <- worry_by_quintile(item)
    rdiff(r[["1"]], r[["5"]]) >= 10
  }))
})

C45 <- c(weather = "WP22445", work = "WP22448", mental = "WP22447", road = "WP22446", food = "WP22442",
         water = "WP22443", crime = "WP22444")
finding(report, "C4_5", function() {
  out <- numeric(0)
  for (item in names(C45)) {
    r <- pct(d, C45[[item]], PERSONAL, by = "INCOME_5")
    out[paste(item, QUINTILES, sep = "_")] <- r[names(QUINTILES)]
  }
  out
})
regional_harm_by_quintile <- function() {
  list(sa = pct(d[d$GlobalRegion %in% 4, ], "WP22444", PERSONAL, by = "INCOME_5"),
       ea = pct(d[d$GlobalRegion %in% 8, ], "WP22445", PERSONAL, by = "INCOME_5"))
}
finding(report, "X76", function() {
  r <- regional_harm_by_quintile()
  c(southern_africa_crime_bottom = r$sa[["1"]], southern_africa_crime_top = r$sa[["5"]],
    eastern_asia_weather_bottom = r$ea[["1"]], eastern_asia_weather_top = r$ea[["5"]])
})
finding(report, "X77", function() {
  r <- regional_harm_by_quintile()
  rratio(r$sa[["1"]], r$sa[["5"]])
})

# --- Chapter 5: Risk perceptions related to climate change ---------------------------

finding(report, "X78", function() c("2019" = pct(t19, "climate", c(3, 98)), "2021" = pct(t21, "climate", c(3, 98))))
finding(report, "C5_1", function() {
  c(setNames(shares(t19, "climate", CLIMATE), paste0("2019_", names(CLIMATE))),
    setNames(shares(t21, "climate", CLIMATE), paste0("2021_", names(CLIMATE))))
})
finding(report, "C5_2", function() flat(shares(d, "WP20719", CLIMATE, by = "Education"), EDUCATION))

NOT_RECOGNISED <- list(not = 3, dk = 98, total = c(3, 98)) # Table 5.1: refused not in 'don't know' or total
finding(report, "X79", function() {
  r <- pct(t21, "climate", NOT_RECOGNISED$total, by = "GlobalRegion")
  codes <- c("5", "12", "6", "15")
  setNames(r[codes], REGIONS[codes])
})
finding(report, "X80", function() sum(pct(t21, "climate", NOT_RECOGNISED$total, by = "GlobalRegion") > 40))
finding(report, "X81", function() {
  r <- pct(d[d$GlobalRegion %in% 3, ], "WP20719", c(3, 98), by = "Education")
  setNames(r[names(EDUCATION)], EDUCATION)
})
finding(report, "X82", function() sum(pct(d, "WP20719", 98, by = "COUNTRY_ISO3") > 30))

china <- d[d$COUNTRY_ISO3 == "CHN", ]
finding(report, "X83", function() pct(china, "WP20719", 98))
finding(report, "X84", function() sum(china$PROJWT[china$WP20719 %in% 98]))
finding(report, "X85", function() {
  r <- pct(china, "WP20719", c(3, 98), by = "Education")
  c(primary = r[["1"]], post_secondary = r[["3"]])
})
finding(report, "T5_1", function() {
  t <- lapply(TREND, function(df) shares(df, "climate", NOT_RECOGNISED, by = "GlobalRegion"))
  out <- numeric(0)
  for (code in names(REGIONS)) {
    for (y in c("2019", "2021")) for (cc in names(NOT_RECOGNISED)) out[paste(REGIONS[[code]], y, cc, sep = "_")] <- t[[y]][code, cc]
  }
  out
})

WEATHER_HARM <- c("1" = "experienced", "2" = "know_someone", "3" = "neither")
finding(report, "X86", function() {
  r <- pct(d, "WP20719", 1, by = "weather_harm")
  setNames(r[names(WEATHER_HARM)], WEATHER_HARM)
})
finding(report, "X87", function() pct(d[d$Education %in% 1 & d$weather_harm %in% 1, ], "WP20719", 1))
finding(report, "X88", function() pct(d[d$Education %in% c(2, 3) & d$weather_harm %in% 1, ], "WP20719", 1))
finding(report, "C5_3", function() {
  total <- pct(d, "WP20719", 1, by = "weather_harm")
  r <- pct(d, "WP20719", 1, by = c("Education", "weather_harm"))
  out <- setNames(total[names(WEATHER_HARM)], paste0("total_", WEATHER_HARM))
  for (e in names(EDUCATION)) {
    for (h in names(WEATHER_HARM)) out[paste(EDUCATION[[e]], WEATHER_HARM[[h]], sep = "_")] <- r[[paste(e, h, sep = "_")]]
  }
  out
})

status <- run_report(report)
if (!interactive()) quit(status = status)
