# Reproduce World Risk Poll 2021 Focus On: Risk and Gender.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/focus_on_risk_and_gender/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

SEX <- c("2" = "women", "1" = "men") # Gender: 1 = Male, 2 = Female
DK <- c(98, 99)
VH <- c("WP22400_ALL", "WP22403_ALL", "WP22406_ALL") # physical, psychological, sexual V&H at work

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "EMP_2010", "resilience_index",
  "WP20711", "WP20719", "WP22331",
  "WP20720", "WP20721", "WP20722", "WP20723", "WP22213", "WP20726", "WP22214",
  "WP22442", "WP22443", "WP22444", "WP22445", "WP22446", "WP22447", "WP22448",
  "WP22228", "WP22229", "WP22230", "WP22245", "WP22241", "WP22244", "WP22242", "WP22243",
  "WP22240", "WP22252", "WP22253", "WP22254", "WP22255", "WP22256", "WP22257", "WP22258",
  "WP22259", "WP22260", "WP22261", "WP22262", "WP22263",
  "WP22222", "WP22223", "WP22225", "WP22224", "WP22226", "WP22227",
  VH, "WP22401", "WP22404_ALL", "WP22407_ALL", "WP22409",
  "WP22410", "WP22411", "WP22412", "WP22413", "WP22421", "WP22414",
  "WP22415", "WP22416", "WP22417", "WP22418", "WP22419", "WP22420", "WP22422"
))

# --- Derived variables ---------------------------------------------------------

# Basic needs (Chart 2.2): the first question splits less / more than a month,
# follow-ups give weeks or months. 4 and 9 = follow-up missing or DK.
d$basic_needs <- with(d, case_when(
  WP22228 %in% 1 & WP22229 %in% 1:3 ~ as.numeric(WP22229),
  WP22228 %in% 1 ~ 4,
  WP22228 %in% 2 & WP22230 %in% 1:4 ~ as.numeric(WP22230) + 4,
  WP22228 %in% 2 ~ 9,
  TRUE ~ 98
))

# Any discrimination (Chart 2.8): yes to any of the five types. Respondents
# in countries that were not asked count as "no" (see README).
DISCRIMINATION <- c("WP22259", "WP22260", "WP22261", "WP22262", "WP22263")
d$any_discrimination <- ifelse(rowSums(d[DISCRIMINATION] == 1, na.rm = TRUE) > 0, 1, 2)

# Never worked (Chart 4.1): code 7 at any of the three V&H questions.
# Chapter 4 charts use everyone else, including China, where the physical
# V&H question was not asked.
d$never_worked <- ifelse(rowSums(d[VH] == 7, na.rm = TRUE) > 0, 1, 2)
ever <- d[d$never_worked == 2, ]

# Employment (Chart 4.2), among those who have ever worked.
ever$employment <- unname(c("1" = 1, "2" = 1, "3" = 1, "5" = 1, "4" = 2, "6" = 3)[as.character(ever$EMP_2010)])
ever$employment_type <- unname(c("1" = 1, "3" = 2, "5" = 2, "2" = 3, "4" = 4)[as.character(ever$EMP_2010)])

# Forms of V&H experienced (Charts 4.3, 4.4).
ever$n_forms <- rowSums(ever[VH] == 1, na.rm = TRUE)
# Chart 4.4 splits the combinations among those who answered yes or no to all
# three questions (so China, not asked about physical V&H, is left out).
answered_all <- rowSums(sapply(ever[VH], function(x) x %in% c(1, 2))) == length(VH)
anyvh <- ever[ever$n_forms > 0 & answered_all, ]
p <- anyvh$WP22400_ALL %in% 1
y <- anyvh$WP22403_ALL %in% 1
s <- anyvh$WP22406_ALL %in% 1
anyvh$combination <- case_when(
  p & !y & !s ~ 1, y & !p & !s ~ 2, s & !p & !y ~ 3, p & y & !s ~ 4,
  s & y & !p ~ 5, s & p & !y ~ 6, p & y & s ~ 7
)
anyvh$sexual_element <- ifelse(s, 1, 2)

# --- Helpers -------------------------------------------------------------------

# % in each named category of `var` for women and men: c(women_<name> = %, ...).
by_sex <- function(df, var, categories) {
  tab <- distribution(df, var, by = "Gender")
  out <- numeric(0)
  for (code in names(SEX)) {
    for (name in names(categories)) {
      cols <- intersect(as.character(categories[[name]]), colnames(tab))
      out[paste(SEX[[code]], name, sep = "_")] <- sum(tab[code, cols])
    }
  }
  out
}

# Percentage-point gap between the sexes: `higher` minus the other.
gap <- function(df, var, codes, higher = "women") {
  r <- pct(df, var, codes, by = "Gender")
  if (higher == "women") r[["2"]] - r[["1"]] else r[["1"]] - r[["2"]]
}

# by_sex() for several questions at once: names become <sex>_<item>_<answer>.
by_sex_items <- function(df, items, categories) {
  out <- numeric(0)
  for (item in names(items)) {
    v <- by_sex(df, items[[item]], categories)
    names(v) <- paste(sub("_.*$", "", names(v)), item, sub("^[^_]+_", "", names(v)), sep = "_")
    out <- c(out, v)
  }
  out
}

YES_NO <- list(yes = 1, no = 2)
WORRY <- list(very = 1, somewhat = 2, not = 3)

# --- Introduction ----------------------------------------------------------------

finding(report, "X01", function() nrow(d))
finding(report, "X02", function() sum(d$Gender == 2))
finding(report, "X03", function() length(unique(d$COUNTRY_ISO3)))

# Needs the Gallup World Poll "born in this country" item (WP4657:
# 1 = born in this country, 2 = born in another country).
born_abroad_women_not_told <- function(var) {
  g <- merge_gallup(d[d$Gender == 2 & d$WP22409 %in% 2, ], "WP4657")
  r <- pct(g, var, 1, by = "WP4657")
  c(r[["2"]], r[["1"]])
}
finding(report, "X04", function() born_abroad_women_not_told("WP22416")[1])
finding(report, "X05", function() born_abroad_women_not_told("WP22416")[2])
finding(report, "X06", function() born_abroad_women_not_told("WP22417")[1])
finding(report, "X07", function() born_abroad_women_not_told("WP22417")[2])

finding(report, "X08", function() gap(d, "WP20711", 1, higher = "men"))
finding(report, "X09", function() gap(d, "WP20711", 2))
finding(report, "X10", function() gap(d, "WP20722", 1))
finding(report, "X11", function() gap(d, "WP22444", 1))
finding(report, "X12", function() gap(d, "WP20726", 1))
finding(report, "X13", function() pct(d, "WP22447", 1, by = "Gender")[["2"]])
finding(report, "X14", function() gap(d, "WP22447", 1))
finding(report, "X15", function() gap(d, "basic_needs", 1))
finding(report, "X16", function() gap(d, "basic_needs", 1:5))
finding(report, "X17", function() gap(d, "never_worked", 1))
finding(report, "X18", function() pct(ever, "employment", c(2, 3), by = "Gender")[["2"]])
finding(report, "X19", function() pct(ever, "employment", c(2, 3), by = "Gender")[["1"]])
finding(report, "X20", function() gap(ever, "employment", c(2, 3)))

# --- Chapter 1: A Changed World? -------------------------------------------------

finding(report, "C1_1", function() by_sex(d, "WP20719", list(very = 1, somewhat = 2, not = 3, dk = DK)))
finding(report, "X21", function() gap(d, "WP20719", 3, higher = "men"))
finding(report, "C1_2", function() by_sex(d, "WP20711", list(more = 1, less = 2, same = 3)))
finding(report, "X22", function() gap(d, "WP20711", 1, higher = "men"))
finding(report, "X23", function() gap(d, "WP20711", 2))
finding(report, "X24", function() gap(d, "WP22331", 3))
finding(report, "X25", function() gap(d, "WP22331", 1, higher = "men"))

TOP_OF_MIND <- list( # WP22331 codes shown in Table 1.1
  road = 1, other_transport = 2, crime = 3, war = 4, health = 5, covid = 7,
  mental_stress = 8, financial = 9, economy = 10, politics = 11, technology = 12,
  water = 13, hunger = 15, household = 16, work = 17, pollution = 18,
  climate = 19, disasters = 20
)
finding(report, "T1_1", function() by_sex(d, "WP22331", TOP_OF_MIND))

# Chart 1.3: worry item and experience item for each of the seven risks.
WORRY_ITEMS <- c(food = "WP20720", water = "WP20721", crime = "WP20722", weather = "WP20723",
                 traffic = "WP22213", mental = "WP20726", work = "WP22214")
EXPERIENCE_ITEMS <- c(food = "WP22442", water = "WP22443", crime = "WP22444", weather = "WP22445",
                      traffic = "WP22446", mental = "WP22447", work = "WP22448")
finding(report, "C1_3", function() {
  c(by_sex_items(d, as.list(WORRY_ITEMS), WORRY),
    by_sex_items(d, as.list(EXPERIENCE_ITEMS), list(exp_personal = 1, exp_know = 2, exp_no = 4)))
})
finding(report, "X26", function() {
  sapply(names(WORRY_ITEMS), function(r) gap(d, WORRY_ITEMS[[r]], 1, higher = if (r == "work") "men" else "women"))
})
finding(report, "X27", function() {
  c(traffic = gap(d, "WP22446", 1, higher = "men"), work = gap(d, "WP22448", 1, higher = "men"))
})

# --- Chapter 2: A Resilient World? ---------------------------------------------

finding(report, "C2_1", function() {
  r <- wmean(d, "resilience_index", by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})
finding(report, "C2_2", function() {
  by_sex(d, "basic_needs", list(
    lt_week = 1, weeks_1_2 = 2, weeks_2_4 = 3, around_month = 5, months_2 = 6,
    months_3 = 7, months_4plus = 8, dk = 98, month_or_less = 1:5
  ))
})
finding(report, "C2_3", function() by_sex(d, "WP22245", YES_NO))
finding(report, "X28", function() gap(d, "WP22245", 1, higher = "men"))

PREPARED <- c(national = "WP22241", local = "WP22244", hospitals = "WP22242", family = "WP22243")
finding(report, "C2_4", function() by_sex_items(d, as.list(PREPARED), YES_NO))
finding(report, "X29", function() sapply(PREPARED, function(v) gap(d, v, 1, higher = "men")))

TRUST_MOST <- list(
  weather_service = 1, disaster_agency = 2, local_news = 3, religious = 4, famous = 5,
  emergency = 6, internet = 7, none = 8, other = 9, dk = DK
)
finding(report, "T2_1", function() by_sex(d, "WP22240", TRUST_MOST))
finding(report, "X30", function() {
  c(local_news = gap(d, "WP22240", 3),
    weather_service = gap(d, "WP22240", 1, higher = "men"),
    disaster_agency = gap(d, "WP22240", 2, higher = "men"),
    internet = gap(d, "WP22240", 7, higher = "men"))
})
finding(report, "C2_5", function() by_sex(d, "WP22252", list(yes = 1, no = 2, depends = 3, dk = DK)))
finding(report, "X31", function() gap(d, "WP22252", 1, higher = "men"))
finding(report, "C2_6", function() by_sex(d, "WP22253", YES_NO))
finding(report, "X32", function() gap(d, "WP22253", 1, higher = "men"))

VITAL_SERVICES <- c(electricity = "WP22254", water = "WP22255", food = "WP22256",
                    medical = "WP22257", telephone = "WP22258")
finding(report, "C2_7", function() by_sex_items(d, as.list(VITAL_SERVICES), YES_NO))
finding(report, "X33", function() sapply(VITAL_SERVICES[c("food", "water", "medical")], function(v) gap(d, v, 1)))

finding(report, "C2_8", function() by_sex(d, "any_discrimination", YES_NO))
finding(report, "X34", function() gap(d, "any_discrimination", 1, higher = "men"))

DISCRIMINATION_TYPES <- setNames(DISCRIMINATION, c("skin", "religion", "nationality", "gender", "disability"))
finding(report, "C2_9", function() {
  c(by_sex_items(d, as.list(DISCRIMINATION_TYPES[1:4]), YES_NO),
    by_sex_items(d, list(disability = "WP22263"), list(yes = 1, no = 2, na = 97)))
})
finding(report, "X35", function() {
  sapply(names(DISCRIMINATION_TYPES), function(k) {
    gap(d, DISCRIMINATION_TYPES[[k]], 1, higher = if (k %in% c("gender", "disability")) "women" else "men")
  })
})

# --- Chapter 3: A Digital World --------------------------------------------------

finding(report, "C3_1", function() by_sex(d, "WP22222", YES_NO))
finding(report, "X36", function() gap(d, "WP22222", 1, higher = "men"))
finding(report, "C3_2", function() by_sex(d, "WP22223", WORRY))
finding(report, "X37", function() c(very = gap(d, "WP22223", 1), somewhat = gap(d, "WP22223", 2)))
finding(report, "C3_3", function() by_sex(d, "WP22225", WORRY))
finding(report, "X38", function() c(very = gap(d, "WP22225", 1), somewhat = gap(d, "WP22225", 2)))
finding(report, "C3_4", function() by_sex(d, "WP22224", WORRY))
finding(report, "X39", function() c(somewhat = gap(d, "WP22224", 2), very = gap(d, "WP22224", 1)))
finding(report, "C3_5", function() by_sex(d, "WP22226", list(yes = 1, no = 2, dk = DK)))
finding(report, "X40", function() gap(d, "WP22226", 1, higher = "men"))
finding(report, "C3_6", function() by_sex(d, "WP22227", list(help = 1, harm = 2, no_opinion = 3, dk = DK)))
finding(report, "X41", function() {
  c(help = gap(d, "WP22227", 1, higher = "men"), harm = gap(d, "WP22227", 2), no_opinion = gap(d, "WP22227", 3))
})

# --- Chapter 4: Safe at Work? ------------------------------------------------------

finding(report, "C4_1", function() by_sex(d, "never_worked", list(worked = 2, never = 1)))
finding(report, "X42", function() gap(d, "never_worked", 1))
finding(report, "C4_2", function() {
  c(by_sex(ever, "employment", list(employed = 1, unemployed = 2, out = 3)),
    by_sex(ever, "employment_type", list(ex_full_time = 1, ex_part_time = 2, ex_self = 3, ex_unemployed = 4)))
})
finding(report, "X43", function() {
  c(out = gap(ever, "employment", 3),
    part_time = gap(ever, "employment_type", 2),
    full_time = gap(ever, "employment_type", 1, higher = "men"),
    self = gap(ever, "employment_type", 3, higher = "men"))
})
finding(report, "C4_3", function() by_sex(ever, "n_forms", list(none = 0, one = 1, two = 2)))
finding(report, "X44", function() gap(ever, "n_forms", 1:3, higher = "men"))
finding(report, "C4_4", function() {
  by_sex(anyvh, "combination", list(
    physical = 1, psych = 2, sexual = 3, psych_physical = 4,
    sexual_psych = 5, sexual_physical = 6, all_three = 7
  ))
})
finding(report, "X45", function() {
  r <- pct(anyvh, "sexual_element", 1, by = "Gender")
  c(women = r[["2"]], men = r[["1"]])
})

FREQUENCY <- list(once_twice = 1, three_five = 2, more_five = 3)
ever_and_frequency <- function(ever_var, times_var) {
  c(by_sex(ever, ever_var, YES_NO), by_sex(d, times_var, FREQUENCY))
}
finding(report, "C4_5", function() ever_and_frequency("WP22400_ALL", "WP22401"))
finding(report, "C4_6", function() ever_and_frequency("WP22403_ALL", "WP22404_ALL"))
finding(report, "C4_7", function() ever_and_frequency("WP22406_ALL", "WP22407_ALL"))
finding(report, "X46", function() gap(ever, "WP22400_ALL", 1, higher = "men"))
finding(report, "X47", function() gap(d, "WP22401", c(2, 3)))
finding(report, "X48", function() gap(ever, "WP22403_ALL", 1, higher = "men"))
finding(report, "X49", function() gap(d, "WP22404_ALL", c(2, 3), higher = "men"))
finding(report, "X50", function() gap(ever, "WP22406_ALL", 1))
finding(report, "X51", function() gap(d, "WP22407_ALL", c(2, 3)))

finding(report, "C4_8", function() by_sex(d, "WP22409", YES_NO))
finding(report, "X52", function() gap(d, "WP22409", 1))

WHOM_TOLD <- c(employer = "WP22410", union = "WP22413", coworker = "WP22411",
               police = "WP22421", family = "WP22412", social = "WP22414")
finding(report, "C4_9", function() by_sex_items(d, as.list(WHOM_TOLD), YES_NO))
finding(report, "X53", function() {
  who <- c("family", "employer", "coworker", "union", "police")
  sapply(setNames(who, who), function(w) gap(d, WHOM_TOLD[[w]], 1, higher = if (w == "family") "women" else "men"))
})

REASONS <- c(waste = "WP22415", not_know = "WP22416", procedures = "WP22417", find_out = "WP22418",
             punishment = "WP22419", reputation = "WP22420", trust = "WP22422")
finding(report, "C4_10", function() by_sex_items(d, as.list(REASONS), YES_NO))
finding(report, "X54", function() {
  reasons <- c("not_know", "find_out", "punishment", "waste", "trust")
  sapply(setNames(reasons, reasons), function(r) {
    gap(d, REASONS[[r]], 1, higher = if (r %in% c("waste", "trust")) "men" else "women")
  })
})

status <- run_report(report)
if (!interactive()) quit(status = status)
