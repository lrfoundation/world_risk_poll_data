# Reproduce World Risk Poll 2021: Safe at Work? Global experiences of violence and harassment.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/core_safe_at_work/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

SEX <- c("1" = "men", "2" = "women") # Gender: 1 = Male, 2 = Female
REGION <- c( # GlobalRegion
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "northern_africa", "4" = "southern_africa",
  "5" = "latin_america", "6" = "northern_america", "7" = "central_asia", "8" = "eastern_asia",
  "9" = "southeastern_asia", "10" = "southern_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
)
INCOME <- c("1" = "low", "2" = "lower_middle", "3" = "upper_middle", "4" = "high") # CountryIncomeLevel
INCOME_LABEL <- c("1" = "Low", "2" = "Lower-middle", "3" = "Upper-middle", "4" = "High") # as printed in Table 1.1
EDUCATION <- c("3" = "tertiary", "2" = "secondary", "1" = "primary") # Education
QUINTILE <- c("1" = "poorest", "2" = "second", "3" = "middle", "4" = "fourth", "5" = "richest") # INCOME_5
BIRTH <- c("1" = "native", "2" = "foreign") # Gallup WP4657: 1 = born in this country, 2 = born in another country

VH <- c("WP22400_ALL", "WP22403_ALL", "WP22406_ALL") # physical, psychological, sexual V&H at work: ever
TIMES <- c("WP22401", "WP22404_ALL", "WP22407_ALL") # how many times (asked if yes)
WHEN <- c("WP22402", "WP22405_ALL", "WP22408_ALL") # when last (asked if yes)
FORMS <- setNames(VH, c("physical", "psychological", "sexual"))
FORM_TIMES <- setNames(TIMES, c("physical", "psychological", "sexual"))
DISCRIMINATION <- c(skin = "WP22259", religion = "WP22260", nationality = "WP22261",
                    gender = "WP22262", disability = "WP22263")
TOLD_WHOM <- c(employer = "WP22410", coworker = "WP22411", family = "WP22412", union = "WP22413",
               police = "WP22421", social = "WP22414")
NOT_TOLD <- c(waste = "WP22415", not_know = "WP22416", procedures = "WP22417", find_out = "WP22418",
              punishment = "WP22419", reputation = "WP22420")

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "Education",
  "INCOME_5", "EMP_2010", VH, TIMES, WHEN, "WP22406", "WP22409", TOLD_WHOM, NOT_TOLD, DISCRIMINATION
))

# --- Derived variables ---------------------------------------------------------

# Never worked: code 7 at any of the three V&H questions. Everyone else is
# the report's base ("ever worked", 113,873 respondents). China stays in the
# base (see reproduce.py and README).
d$never_worked <- ifelse(rowSums(d[VH] == 7, na.rm = TRUE) > 0, 1, 2)
ever <- d[d$never_worked == 2, ]

# Number of forms experienced and any V&H (1 = yes, 2 = no).
ever$n_forms <- rowSums(ever[VH] == 1, na.rm = TRUE)
ever$any_vh <- ifelse(ever$n_forms > 0, 1, 2)

# When last experienced (Chart 1.1): the most recent timing over the forms
# experienced. 0 = never experienced, 8 = experienced but no timing given.
latest <- do.call(pmin, c(lapply(WHEN, function(v) ifelse(ever[[v]] %in% 1:3, ever[[v]], NA)), na.rm = TRUE))
ever$when <- ifelse(ever$n_forms == 0, 0, ifelse(is.na(latest), 8, latest))

# Any discrimination: yes to any of the five types; countries not asked count as no.
ever$any_discrimination <- ifelse(rowSums(ever[DISCRIMINATION] == 1, na.rm = TRUE) > 0, 1, 2)

# Those who experienced any V&H.
anyvh <- ever[ever$n_forms > 0, ]

# Combination of forms (Chart 2.2): only respondents who answered yes or no
# to all three questions.
complete <- anyvh[Reduce(`&`, lapply(VH, function(v) anyvh[[v]] %in% c(1, 2))), ]
p <- complete$WP22400_ALL %in% 1
y <- complete$WP22403_ALL %in% 1
s <- complete$WP22406_ALL %in% 1
complete$combination <- case_when(
  p & !y & !s ~ 1, y & !p & !s ~ 2, s & !p & !y ~ 3, p & y & !s ~ 4,
  s & y & !p ~ 5, s & p & !y ~ 6, p & y & s ~ 7
)
complete$sexual_element <- ifelse(s, 1, 2)
COMBINATION <- c(physical = 1, psychological = 2, sexual = 3, psychological_physical = 4,
                 sexual_psychological = 5, sexual_physical = 6, all_three = 7)

# Question order (Appendix 3): physical, psychological, sexual; in China,
# psychological then sexual.
china <- d$COUNTRY_ISO3 == "CHN"
d$q1 <- ifelse(china, d$WP22403_ALL, d$WP22400_ALL)
d$q2 <- ifelse(china, d$WP22406_ALL, d$WP22403_ALL)
d$q3 <- ifelse(china, NA, d$WP22406_ALL)
d$never_at <- case_when(d$q1 %in% 7 ~ 1, d$q2 %in% 7 ~ 2, d$q3 %in% 7 ~ 3, TRUE ~ 0)

# --- Helpers -------------------------------------------------------------------

# % with `var` in `codes` for each `group` code, named by names_map[code].
by_codes <- function(df, var, codes, group, names_map) {
  r <- pct(df, var, codes, by = group)
  setNames(unname(r[names(names_map)]), unname(names_map))
}
by_sex <- function(df, var, codes) by_codes(df, var, codes, "Gender", SEX)

# % in one group, or in one cell of two groupings.
one <- function(df, var, codes, group, code) pct(df, var, codes, by = group)[[as.character(code)]]
two <- function(df, var, codes, group1, code1, group2, code2) {
  pct(df[df[[group1]] %in% code1, ], var, codes, by = group2)[[as.character(code2)]]
}
cell <- function(r, ...) r[[paste(..., sep = "_")]]

# % in each named category of `var`: c("<name>_<cat>" = %) (or c(<cat> = %) without `group`).
categories <- function(df, var, cats, group = NULL, names_map = NULL) {
  if (is.null(group)) {
    t <- distribution(df, var)
    return(sapply(cats, function(codes) sum(t[intersect(as.character(codes), names(t))])))
  }
  t <- distribution(df, var, by = group)
  out <- numeric(0)
  for (code in names(names_map)) {
    for (cat in names(cats)) {
      cols <- intersect(as.character(cats[[cat]]), colnames(t))
      out[paste(names_map[[code]], cat, sep = "_")] <- sum(t[code, cols])
    }
  }
  out
}

three_plus <- function(df, var) pct(df, var, c(2, 3))
women <- function(df) df[df$Gender == 2, ]
with_birth <- function(df) merge_gallup(df, "WP4657")

YES_NO <- list(yes = 1, no = 2)
N_FORMS <- list(one = 1, two = 2, three = 3)

# --- Executive summary -----------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X03", function() pct(ever, "any_vh", 1))
finding(report, "X04", function() {
  # Each form experienced counts once: share of experiences that happened three or more times.
  long <- data.frame(times = unlist(lapply(TIMES, function(t) ever[[t]])), PROJWT = rep(ever$PROJWT, length(TIMES)))
  pct(long, "times", c(2, 3))
})
finding(report, "X05", function() by_sex(ever, "any_vh", 1))
finding(report, "X06", function() sapply(FORMS, function(v) pct(ever, v, 1)))
finding(report, "X07", function() pct(anyvh, "n_forms", c(2, 3)))
finding(report, "X08", function() by_sex(complete, "sexual_element", 1))
finding(report, "X09", function() one(ever, "any_vh", 1, "GlobalRegion", 15))
finding(report, "X10", function() {
  c(experienced = one(women(ever), "any_vh", 1, "Education", 3),
    told = one(women(anyvh), "WP22409", 1, "Education", 3))
})
finding(report, "X11", function() by_codes(with_birth(women(ever)), "any_vh", 1, "WP4657", c("2" = "foreign", "1" = "native")))

# Foreign-born minus native-born, % with `var` = 1, by income quintile.
birth_gap_by_quintile <- function(df, var) {
  r <- pct(with_birth(df), var, 1, by = c("INCOME_5", "WP4657"))
  sapply(setNames(names(QUINTILE), QUINTILE), function(q) cell(r, q, 2) - cell(r, q, 1))
}
finding(report, "X12", function() birth_gap_by_quintile(women(ever), "any_vh")[c("poorest", "richest")])

# --- Chapter 1 -------------------------------------------------------------------

WHEN_CATS <- list(last_year = 1, two_five = 2, five_plus = 3)
finding(report, "X13", function() categories(ever, "when", WHEN_CATS))
finding(report, "X14", function() pct(ever, "when", 8))
finding(report, "C1_1", function() categories(ever, "when", c(list(no = 0), WHEN_CATS)))
finding(report, "C1_2", function() categories(ever, "any_vh", list(no = 2, yes = 1), "Gender", SEX))
finding(report, "X15", function() c(ever = sum(d$never_worked == 2), never = sum(d$never_worked == 1)))
finding(report, "X16", function() sum(d$EMP_2010 %in% c(1, 2, 3, 5)))
finding(report, "X17", function() {
  r <- pct(ever, "any_vh", 1, by = "GlobalRegion")
  rs <- pct(ever, "any_vh", 1, by = c("GlobalRegion", "Gender"))
  c(northern_america = r[["6"]], australia_nz_women = cell(rs, 15, 2),
    northern_america_gap = cell(rs, 6, 2) - cell(rs, 6, 1), southern_africa_gap = cell(rs, 4, 1) - cell(rs, 4, 2),
    central_asia = r[["7"]], central_asia_men = cell(rs, 7, 1), central_asia_women = cell(rs, 7, 2))
})
finding(report, "C1_3", function() {
  rs <- pct(ever, "any_vh", 1, by = c("GlobalRegion", "Gender"))
  out <- numeric(0)
  for (r in names(REGION)) for (sx in names(SEX)) out[paste(REGION[[r]], SEX[[sx]], sep = "_")] <- cell(rs, r, sx)
  out
})

# (all, men, women) % with `var` = 1 in a country.
country <- function(iso, var = "any_vh", df = ever) {
  g <- df[df$COUNTRY_ISO3 == iso, ]
  r <- pct(g, var, 1, by = "Gender")
  c(pct(g, var, 1), r[["1"]], r[["2"]])
}
finding(report, "X18", function() c(AUS = country("AUS")[1], AUS_men = country("AUS")[2], FIN_women = country("FIN")[3]))

TABLE_1_1 <- c("AUS", "FIN", "ISL", "NZL", "DNK", "USA", "NOR", "CAN", "GRC", "SWE",
               "KGZ", "LBN", "MYS", "UZB", "ARM", "IDN", "GEO", "KAZ", "PAK", "TJK")
finding(report, "T1_1", function() {
  out <- character(0)
  for (iso in TABLE_1_1) {
    v <- country(iso)
    out[paste0(iso, c("_all", "_men", "_women", "_diff"))] <- as.character(c(v, v[3] - v[2]))
    out[paste0(iso, "_income")] <- INCOME_LABEL[[as.character(ever$CountryIncomeLevel[ever$COUNTRY_ISO3 == iso][1])]]
  }
  out
})
finding(report, "X19", function() {
  # World Risk Poll 2019: L21D, experienced harm while working in the past two
  # years from physical harassment or violence (asked of those who work).
  w19 <- load_wave(2019, c("COUNTRY_ISO3", "PROJWT", "Gender", "L21D"))
  by_sex(w19[w19$COUNTRY_ISO3 == "AUS", ], "L21D", 1)
})
finding(report, "X20", function() country("FIN")[1])
finding(report, "X21", function() {
  v <- country("TJK")
  c(all = v[1], gap = v[3] - v[2])
})
income_by_sex <- function(df, var) {
  r <- pct(df, var, 1, by = c("CountryIncomeLevel", "Gender"))
  out <- numeric(0)
  for (i in names(INCOME)) for (sx in names(SEX)) out[paste(INCOME[[i]], SEX[[sx]], sep = "_")] <- cell(r, i, sx)
  out
}
finding(report, "C1_4", function() income_by_sex(ever, "any_vh"))
finding(report, "X22", function() {
  i <- by_codes(ever, "any_vh", 1, "CountryIncomeLevel", INCOME)
  r <- pct(ever, "any_vh", 1, by = c("CountryIncomeLevel", "Gender"))
  c(i[c("low", "high", "lower_middle", "upper_middle")], high_gap = cell(r, 4, 2) - cell(r, 4, 1))
})
finding(report, "C1_5", function() income_by_sex(d, "never_worked"))
finding(report, "X23", function() {
  r <- pct(d, "never_worked", 1, by = c("CountryIncomeLevel", "Gender"))
  c(by_sex(d, "never_worked", 1), low_women = cell(r, 1, 2), lower_middle_women = cell(r, 2, 2))
})
DISC_GROUPS <- c("1" = "discrimination", "2" = "none")
finding(report, "X24", function() by_codes(ever, "any_vh", 1, "any_discrimination", DISC_GROUPS))
finding(report, "C1_6", function() categories(ever, "any_vh", list(no = 2, yes = 1), "any_discrimination", DISC_GROUPS))
finding(report, "C1_7", function() {
  # Both bars are % who experienced V&H: among those who said no (2) and yes (1).
  out <- numeric(0)
  for (kind in c("gender", "skin", "nationality", "religion", "disability")) {
    out[paste0(kind, "_no")] <- one(ever, "any_vh", 1, DISCRIMINATION[[kind]], 2)
    out[paste0(kind, "_yes")] <- one(ever, "any_vh", 1, DISCRIMINATION[[kind]], 1)
  }
  out
})
finding(report, "X25", function() {
  sx <- function(kind, code) two(ever, "any_vh", 1, DISCRIMINATION[[kind]], 1, "Gender", code)
  c(gender = one(ever, "any_vh", 1, "WP22262", 1), gender_men = sx("gender", 1), gender_women = sx("gender", 2),
    religion_men = sx("religion", 1), religion_women = sx("religion", 2),
    disability_men = sx("disability", 1), disability_women = sx("disability", 2))
})
ORDERED_FORMS <- c(sexual = "WP22406_ALL", psychological = "WP22403_ALL", physical = "WP22400_ALL")
finding(report, "C1_8", function() {
  out <- numeric(0)
  for (f in names(ORDERED_FORMS)) for (a in names(YES_NO)) out[paste(f, a, sep = "_")] <- pct(ever, ORDERED_FORMS[[f]], YES_NO[[a]])
  out
})

# % yes to one form: by sex, and for named regions (overall, by sex, gap).
form_text <- function(var, regions, extra = NULL) {
  out <- by_sex(ever, var, 1)
  r <- pct(ever, var, 1, by = "GlobalRegion")
  rs <- pct(ever, var, 1, by = c("GlobalRegion", "Gender"))
  for (code in names(regions)) {
    name <- REGION[[code]]
    for (part in regions[[code]]) {
      if (part == "all") out[name] <- r[[code]]
      else if (part == "gap") out[paste0(name, "_gap")] <- cell(rs, code, 2) - cell(rs, code, 1)
      else out[paste(name, part, sep = "_")] <- cell(rs, code, if (part == "men") 1 else 2)
    }
  }
  c(out, extra)
}
finding(report, "X26", function() {
  form_text("WP22403_ALL", list("15" = c("all", "women", "men"), "6" = c("all", "women", "men"), "7" = c("all", "gap")))
})
finding(report, "X27", function() {
  inc <- pct(ever, "WP22400_ALL", 1, by = "CountryIncomeLevel")
  form_text("WP22400_ALL", list("15" = "all", "6" = c("all", "women", "men"), "1" = c("all", "men", "women"),
                                "2" = c("all", "men", "women"), "7" = "all"),
            c(low_income = inc[["1"]], lower_middle_income = inc[["2"]]))
})
finding(report, "X28", function() {
  form_text("WP22406_ALL", list("6" = c("all", "women", "men"), "15" = c("all", "women", "men")))
})
finding(report, "C1_9", function() {
  out <- numeric(0)
  for (f in names(ORDERED_FORMS)) {
    v <- categories(ever, ORDERED_FORMS[[f]], YES_NO, "Gender", SEX)
    out[paste(f, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "X29", function() {
  region <- function(var, code) one(ever, var, c(2, 3), "GlobalRegion", code)
  phys <- TIMES[1]; psych <- TIMES[2]; sex <- TIMES[3]
  anz <- ever[ever$GlobalRegion %in% 15, ]
  nam <- ever[ever$GlobalRegion %in% 6, ]
  nam_sex <- pct(nam, sex, c(2, 3), by = "Gender")
  c(psychological = three_plus(ever, psych), psychological_more_five = pct(ever, psych, 3),
    psychological_australia_nz = region(psych, 15), psychological_northern_america = region(psych, 6),
    physical_NLD = three_plus(ever[ever$COUNTRY_ISO3 == "NLD", ], phys),
    sexual_BRA = three_plus(ever[ever$COUNTRY_ISO3 == "BRA", ], sex),
    physical = three_plus(ever, phys), sexual = three_plus(ever, sex),
    physical_australia_nz = region(phys, 15), physical_central_western_africa = region(phys, 2),
    sexual_australia_nz = region(sex, 15), sexual_northern_america = region(sex, 6),
    sexual_australia_nz_women = one(anz, sex, c(2, 3), "Gender", 2),
    sexual_australia_nz_men = one(anz, sex, c(2, 3), "Gender", 1),
    sexual_northern_america_gap = nam_sex[["2"]] - nam_sex[["1"]])
})
FREQUENCY <- list(once_twice = 1, three_five = 2, more_five = 3)
finding(report, "C1_10", function() {
  out <- numeric(0)
  for (f in c("sexual", "psychological", "physical")) {
    v <- categories(ever, FORM_TIMES[[f]], FREQUENCY)
    out[paste(f, names(v), sep = "_")] <- v
  }
  out
})
finding(report, "T1_2", function() {
  out <- character(0)
  for (f in list(list("physical", c(15, 2, 8)), list("psychological", c(15, 6, 12)), list("sexual", c(6, 15, 7)))) {
    r <- pct(ever, FORM_TIMES[[f[[1]]]], c(2, 3), by = "GlobalRegion")
    for (code in f[[2]]) out[paste(f[[1]], REGION[[as.character(code)]], sep = "_")] <- as.character(r[[as.character(code)]])
    out[paste0(f[[1]], "_top3")] <- paste(REGION[names(sort(r, decreasing = TRUE))[1:3]], collapse = "; ")
  }
  out
})

# --- Chapter 2 -------------------------------------------------------------------

finding(report, "X30", function() categories(anyvh, "n_forms", N_FORMS))
finding(report, "X31", function() {
  three <- pct(anyvh, "n_forms", 3, by = "COUNTRY_ISO3")
  c(SEN_three = three[["SEN"]], ZMB_three = three[["ZMB"]], UGA_three = three[["UGA"]], ZAF_three = three[["ZAF"]],
    SEN_multiple = pct(anyvh, "n_forms", c(2, 3), by = "COUNTRY_ISO3")[["SEN"]])
})
finding(report, "C2_1", function() categories(anyvh, "n_forms", N_FORMS, "Gender", SEX))
finding(report, "X32", function() {
  t <- distribution(complete, "combination", by = "Gender")
  c(men_psychological = t["1", "2"], men_psychological_physical = t["1", "4"], men_physical = t["1", "1"],
    women_psychological = t["2", "2"], women_sexual = t["2", "3"], women_sexual_psychological = t["2", "5"])
})
finding(report, "C2_2", function() {
  out <- categories(complete, "combination", as.list(COMBINATION), "Gender", SEX)
  out[names(out) != "men_sexual_physical"] # not labelled in the chart
})
finding(report, "X33", function() {
  multiple <- pct(anyvh, "n_forms", c(2, 3), by = "any_discrimination")
  three <- pct(anyvh, "n_forms", 3, by = "any_discrimination")
  c(multiple_discrimination = multiple[["1"]], multiple_none = multiple[["2"]],
    three_none = three[["2"]], three_discrimination = three[["1"]])
})
finding(report, "C2_3", function() {
  out <- categories(anyvh, "n_forms", N_FORMS, "any_discrimination", DISC_GROUPS)
  out[names(out) != "none_three"] # not labelled in the chart
})
finding(report, "X34", function() {
  groups <- list(low_income = c("CountryIncomeLevel", 1), eastern_africa = c("GlobalRegion", 1),
                 southern_africa = c("GlobalRegion", 4))
  out <- numeric(0)
  for (name in names(groups)) {
    g <- groups[[name]][1]; code <- groups[[name]][2]
    out[paste0(name, "_multiple")] <- one(anyvh, "n_forms", c(2, 3), g, code)
    out[paste0(name, "_three")] <- one(anyvh, "n_forms", 3, g, code)
  }
  out
})

# --- Chapter 3 -------------------------------------------------------------------

finding(report, "X35", function() {
  e <- pct(ever, "any_vh", 1, by = "Education")
  r <- pct(ever, "any_vh", 1, by = c("Education", "Gender"))
  c(tertiary = e[["3"]], primary = e[["1"]], secondary = e[["2"]], men_tertiary = cell(r, 3, 1),
    men_primary = cell(r, 1, 1), women_primary = cell(r, 1, 2),
    women_gap = cell(r, 3, 2) - cell(r, 1, 2), men_gap = cell(r, 3, 1) - cell(r, 1, 1))
})
finding(report, "C3_1", function() categories(women(ever), "n_forms", list(none = 0, one = 1, two = 2), "Education", EDUCATION))
finding(report, "X36", function() {
  r <- pct(women(ever), "any_vh", 1, by = c("COUNTRY_ISO3", "Education"))
  sapply(c(DEU = "DEU", SWE = "SWE", ITA = "ITA", ISR = "ISR"), function(iso) cell(r, iso, 3) - cell(r, iso, 1))
})
finding(report, "X37", function() {
  r <- pct(anyvh, "WP22409", 1, by = c("Education", "Gender"))
  c(women_secondary = cell(r, 2, 2), women_primary = cell(r, 1, 2), all = pct(anyvh, "WP22409", 1),
    men_primary = cell(r, 1, 1), men_secondary = cell(r, 2, 1), men_tertiary = cell(r, 3, 1))
})
finding(report, "C3_2", function() categories(women(anyvh), "WP22409", list(no = 2, yes = 1), "Education", EDUCATION))
finding(report, "T3_1", function() {
  told <- women(anyvh)[women(anyvh)$WP22409 %in% 1, ]
  out <- numeric(0)
  for (e in names(EDUCATION)) for (who in names(TOLD_WHOM)) {
    out[paste(EDUCATION[[e]], who, sep = "_")] <- one(told, TOLD_WHOM[[who]], 1, "Education", e)
  }
  out
})
finding(report, "T3_2", function() {
  not_told <- women(anyvh)[women(anyvh)$WP22409 %in% 2, ]
  out <- numeric(0)
  for (e in names(EDUCATION)) for (reason in c("find_out", "reputation", "waste")) {
    out[paste(EDUCATION[[e]], reason, sep = "_")] <- one(not_told, NOT_TOLD[[reason]], 1, "Education", e)
  }
  out
})
finding(report, "C3_3", function() {
  r <- pct(with_birth(ever), "any_vh", 1, by = c("Gender", "WP4657"))
  c(women_native = cell(r, 2, 1), women_foreign = cell(r, 2, 2), men_native = cell(r, 1, 1), men_foreign = cell(r, 1, 2))
})
finding(report, "X38", function() {
  r <- pct(with_birth(ever), "any_vh", 1, by = c("Gender", "WP4657"))
  c(men_foreign = cell(r, 1, 2), men_native = cell(r, 1, 1), women_native = cell(r, 2, 1))
})
birth_by <- function(df, var, group, names_map) {
  r <- pct(with_birth(df), var, 1, by = c(group, "WP4657"))
  out <- numeric(0)
  for (g in names(names_map)) for (b in names(BIRTH)) out[paste(names_map[[g]], BIRTH[[b]], sep = "_")] <- cell(r, g, b)
  out
}
finding(report, "C3_4", function() birth_by(women(ever), "any_vh", "INCOME_5", QUINTILE))
finding(report, "C3_5", function() birth_by(women(ever), "any_vh", "CountryIncomeLevel", INCOME))
finding(report, "X39", function() {
  r <- pct(with_birth(women(anyvh)), "WP22259", 1, by = c("INCOME_5", "WP4657"))
  c(foreign = cell(r, 1, 2), native = cell(r, 1, 1))
})
finding(report, "C3_6", function() birth_by(women(anyvh), "WP22259", "INCOME_5", QUINTILE))
finding(report, "C3_7", function() birth_by(women(anyvh), "WP22261", "INCOME_5", QUINTILE))
finding(report, "X40", function() {
  g <- with_birth(women(anyvh))
  told <- g[g$WP22409 %in% 1, ]
  not_told <- g[g$WP22409 %in% 2, ]
  birth <- function(df, var) {
    r <- pct(df, var, 1, by = "WP4657")
    c(native = r[["1"]], foreign = r[["2"]])
  }
  q <- pct(g, "WP22409", 1, by = c("INCOME_5", "WP4657"))
  out <- c(told = birth(g, "WP22409"))
  names(out) <- c("told_native", "told_foreign")
  out["told_poorest_gap"] <- cell(q, 1, 1) - cell(q, 1, 2)
  items <- list(employer = list(told, "WP22410"), coworker = list(told, "WP22411"), family = list(told, "WP22412"),
                not_know = list(not_told, "WP22416"), procedures = list(not_told, "WP22417"),
                punishment = list(not_told, "WP22419"))
  for (key in names(items)) {
    v <- birth(items[[key]][[1]], items[[key]][[2]])
    out[paste0(key, "_native")] <- v[["native"]]
    out[paste0(key, "_foreign")] <- v[["foreign"]]
  }
  out
})
finding(report, "C3_8", function() birth_by(women(anyvh), "WP22409", "INCOME_5", QUINTILE))

# --- Appendix 3: data filtering --------------------------------------------------

finding(report, "X41", function() {
  later <- d[d$never_worked == 1 & d$never_at != 1, ]
  c(answered_first = nrow(later), first_yes = sum(later$q1 %in% 1), first_no = sum(later$q1 %in% 2))
})
finding(report, "X42", function() {
  # Not explained (see README): respondents outside China who reached the
  # sexual question in its modified wording.
  sum(is.na(d$WP22406) & !is.na(d$WP22406_ALL) & d$never_at %in% c(0, 3) & !china)
})
finding(report, "X43", function() 100 * mean(d$Gender[d$never_at == 3] == 2))
finding(report, "X44", function() sum(d[d$never_worked == 1, VH] == 1, na.rm = TRUE))
finding(report, "TA3_1", function() {
  c(first = sum(d$never_at == 1), second = sum(d$never_at == 2), third = sum(d$never_at == 3),
    total = sum(d$never_at > 0))
})

status <- run_report(report)
if (!interactive()) quit(status = status)
