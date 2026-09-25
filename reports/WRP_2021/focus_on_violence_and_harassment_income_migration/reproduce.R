# Reproduce World Risk Poll 2021 Focus On: The impact of income and migration on
# violence and harassment at work.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/focus_on_violence_and_harassment_income_migration/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes. Country of birth is a Gallup World Poll item
# that is not in the public data, so most findings are GALLUP_ONLY unless
# GALLUP_WP_PATH points to a file with it.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

VH <- c("WP22400_ALL", "WP22403_ALL", "WP22406_ALL") # physical, psychological, sexual V&H at work
REGIONS <- c( # GlobalRegion code -> key
  "1" = "eastern_africa", "2" = "central_western_africa", "3" = "north_africa", "4" = "southern_africa",
  "5" = "latin_america_caribbean", "6" = "northern_america", "7" = "central_asia", "8" = "east_asia",
  "9" = "south_eastern_asia", "10" = "south_asia", "11" = "middle_east", "12" = "eastern_europe",
  "13" = "northern_western_europe", "14" = "southern_europe", "15" = "australia_nz"
)
# Feelings about household income (footnote 5): living comfortably or getting by =
# comfortable; finding it difficult or very difficult = difficult; DK/refused = neither.
FIN <- c("1" = "comfortable", "2" = "comfortable", "3" = "difficult", "4" = "difficult")
BIRTH <- c("1" = "native", "2" = "foreign") # GWP WP4657: 1 = born in this country, 2 = born in another country
SEX <- c("1" = "men", "2" = "women") # Gender: 1 = Male, 2 = Female
YES_NO <- list(yes = 1, no = 2)
THREE_REGIONS <- c("northern_america", "australia_nz", "northern_western_europe") # Charts 3-6

# Countries marked as having ratified ILO Convention 190 (in force or not yet in force)
# in the report's own table on page 13, as ISO3 codes.
C190_RATIFIED <- c(
  "ARG", "ECU", "FJI", "GRC", "ITA", "MUS", "NAM", "SOM", "ZAF", "GBR", "URY", # in force
  "ALB", "ATG", "BHS", "BRB", "CAN", "CAF", "SLV", "IRL", "LSO", "MEX", "NGA", # not yet in force
  "PAN", "PER", "SMR", "ESP"
)

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "GlobalRegion", "IncomeFeelings", VH,
  "WP22409", "WP22415", "WP22416", "WP22417", "WP22419", "WP22420"
))

# --- Derived variables ---------------------------------------------------------

# Ever worked: not "respondent has never worked" (code 7) at any of the three
# V&H questions. This includes China, which was asked only the psychological
# and sexual questions (reproduces East Asia in Chart 1).
d$never_worked <- ifelse(rowSums(d[VH] == 7, na.rm = TRUE) > 0, 1, 2)
workers <- d[d$never_worked == 2, ]
workers$region <- unname(REGIONS[as.character(workers$GlobalRegion)])
workers$fin <- unname(FIN[as.character(workers$IncomeFeelings)])
workers$sex <- unname(SEX[as.character(workers$Gender)])

# Any V&H: yes to at least one of the three forms (DK/refused count as no).
workers$n_forms <- rowSums(workers[VH] == 1, na.rm = TRUE)
workers$any_vh <- ifelse(workers$n_forms > 0, 1, 2)

.cache <- new.env()

# Workers with a valid country of birth (footnote 4), labelled native/foreign.
# Needs the Gallup World Poll item "born in this country" (WP4657).
workers_by_birth <- function() {
  if (is.null(.cache$born)) {
    g <- merge_gallup(workers, "WP4657")
    g <- g[g$WP4657 %in% c(1, 2), ]
    g$born <- unname(BIRTH[as.character(g$WP4657)])
    .cache$born <- g
  }
  .cache$born
}

# Workers with a valid country of birth who experienced V&H (asked WP22409).
told_base <- function() {
  w <- workers_by_birth()
  w[w$any_vh == 1, ]
}

# --- Helpers -------------------------------------------------------------------

# Weighted % with `var` in `codes` for each group of the label column(s) `by`:
# c(northern_america_foreign = %, ...). pct() drops rows with a missing group.
rate <- function(df, var, codes, by) as.list(pct(df, var, codes, by = by))

# % in each named category of `var` for each group of `by`: c(<group>_<category> = %).
shares <- function(df, var, categories, by) {
  df <- df[stats::complete.cases(df[by]), , drop = FALSE]
  tab <- distribution(df, var, by = by)
  out <- numeric(0)
  for (g in rownames(tab)) {
    for (name in names(categories)) {
      cols <- intersect(as.character(categories[[name]]), colnames(tab))
      out[paste(g, name, sep = "_")] <- sum(tab[g, cols])
    }
  }
  out
}

# Keep the elements whose names start with one of `prefixes`.
only <- function(values, prefixes) {
  keep <- Reduce(`|`, lapply(prefixes, function(p) startsWith(names(values), p)))
  values[keep]
}

# --- Page 2: Introduction ---------------------------------------------------------

finding(report, "X01", function() pct(workers, "any_vh", 1))
finding(report, "X02", function() rate(workers_by_birth(), "any_vh", 1, "born")$foreign)

# --- Page 3: Chart 1 --------------------------------------------------------------

by_region <- function() rate(workers, "any_vh", 1, "region")
finding(report, "C1", function() unlist(by_region()))
finding(report, "X03", function() by_region()$australia_nz)
finding(report, "X04", function() by_region()$northern_america)
finding(report, "X05", function() by_region()$central_asia)
finding(report, "X06", function() by_region()$south_eastern_asia)

# --- Page 4: Chart 2 --------------------------------------------------------------

experience_by_birth <- function() {
  w <- workers_by_birth()
  c(rate(w, "any_vh", 1, "born"), rate(w, "any_vh", 1, c("region", "born")))
}
get_or_na <- function(x, key) if (is.null(x[[key]])) NA_real_ else x[[key]]

# The chart prints the size of the gap without its sign.
finding(report, "C2", function() {
  r <- experience_by_birth()
  out <- c(global = abs(r$foreign - r$native))
  for (region in REGIONS) {
    out[region] <- abs(get_or_na(r, paste0(region, "_foreign")) - get_or_na(r, paste0(region, "_native")))
  }
  out
})
finding(report, "X07", function() with(experience_by_birth(), east_asia_native - east_asia_foreign))
finding(report, "X08", function() with(experience_by_birth(), eastern_europe_foreign - eastern_europe_native))
finding(report, "X09", function() with(experience_by_birth(), foreign - native))
finding(report, "X10", function() experience_by_birth()$native)
finding(report, "X11", function() experience_by_birth()$foreign)

# --- Page 5: Charts 3 and 4 ----------------------------------------------------------

told_by_birth <- function() {
  t <- told_base()
  c(rate(t, "WP22409", 1, "born"), rate(t, "WP22409", 1, c("region", "born")))
}
finding(report, "X12", function() told_by_birth()$native)
finding(report, "X13", function() told_by_birth()$foreign)
finding(report, "X14", function() with(told_by_birth(), australia_nz_native - australia_nz_foreign))
finding(report, "X15", function() with(told_by_birth(), northern_america_native - northern_america_foreign))
finding(report, "X16", function() with(told_by_birth(), northern_western_europe_native - northern_western_europe_foreign))
finding(report, "C3", function() {
  only(shares(told_base(), "WP22409", list(told = 1, didnt = 2), c("region", "born")), THREE_REGIONS)
})

REASONS <- c(not_know = "WP22416", procedures = "WP22417") # asked of those who did not tell anyone
reasons_by_birth <- function(reason) {
  w <- workers_by_birth()
  c(rate(w, REASONS[[reason]], 1, "born"), rate(w, REASONS[[reason]], 1, c("region", "born")))
}
finding(report, "C4", function() {
  out <- numeric(0)
  for (reason in names(REASONS)) {
    v <- unlist(only(reasons_by_birth(reason), THREE_REGIONS))
    names(v) <- paste(names(v), reason, sep = "_")
    out <- c(out, v)
  }
  out
})
finding(report, "X17", function() reasons_by_birth("not_know")$northern_america_foreign)
finding(report, "X18", function() with(reasons_by_birth("not_know"), northern_america_foreign - northern_america_native))
finding(report, "X19", function() with(reasons_by_birth("not_know"), northern_america_foreign - foreign))
finding(report, "X20", function() reasons_by_birth("procedures")$northern_america_foreign)
finding(report, "X21", function() reasons_by_birth("procedures")$northern_america_native)
finding(report, "X22", function() reasons_by_birth("procedures")$foreign)

# --- Pages 6-7: Charts 5 and 6 --------------------------------------------------------

by_fin <- function() rate(workers, "any_vh", 1, "fin")
finding(report, "X23", function() by_fin()$comfortable)
finding(report, "X24", function() by_fin()$difficult)
finding(report, "X25", function() with(by_fin(), difficult - comfortable))

experience_by_birth_fin <- function() {
  w <- workers_by_birth()
  c(rate(w, "any_vh", 1, c("born", "fin")), rate(w, "any_vh", 1, c("region", "born", "fin")))
}
finding(report, "X26", function() experience_by_birth_fin()$foreign_comfortable)
finding(report, "X27", function() experience_by_birth_fin()$foreign_difficult)
finding(report, "C5", function() unlist(only(experience_by_birth_fin(), THREE_REGIONS)))
finding(report, "X28", function() experience_by_birth_fin()$northern_america_foreign_difficult)
finding(report, "X29", function() {
  with(experience_by_birth_fin(), northern_america_foreign_difficult - northern_america_native_difficult)
})
finding(report, "X30", function() {
  with(experience_by_birth_fin(), northern_america_foreign_difficult - northern_america_foreign_comfortable)
})
finding(report, "X31", function() experience_by_birth_fin()$australia_nz_native_difficult)
finding(report, "X32", function() with(experience_by_birth_fin(), australia_nz_native_difficult - australia_nz_foreign_difficult))
finding(report, "X33", function() with(experience_by_birth_fin(), australia_nz_native_difficult - australia_nz_native_comfortable))
finding(report, "X34", function() min(unlist(only(experience_by_birth_fin(), "northern_western_europe"))))
finding(report, "X35", function() max(unlist(only(experience_by_birth_fin(), "northern_western_europe"))))

told_by_birth_fin <- function() rate(told_base(), "WP22409", 1, c("region", "born", "fin"))
finding(report, "C6", function() unlist(only(told_by_birth_fin(), THREE_REGIONS)))
finding(report, "X36", function() told_by_birth_fin()$northern_america_foreign_difficult)

# --- Pages 9-12: South-eastern Asia and Latin America ------------------------------------

region_by_birth <- function(region) {
  w <- workers_by_birth()
  w[w$region %in% region, ]
}

# Charts 7 and 9: experience (top) and told someone (bottom) by birth and income.
experience_and_told <- function(region) {
  w <- region_by_birth(region)
  exp <- shares(w, "any_vh", YES_NO, c("born", "fin"))
  told <- shares(w[w$any_vh == 1, ], "WP22409", YES_NO, c("born", "fin"))
  c(setNames(exp, paste0("exp_", names(exp))), setNames(told, paste0("told_", names(told))))
}

region_rates <- function(region, var, codes, by) {
  w <- region_by_birth(region)
  if (var == "WP22409") w <- w[w$any_vh == 1, ]
  rate(w, var, codes, by)
}

SEA <- "south_eastern_asia"
LAC <- "latin_america_caribbean"

finding(report, "X37", function() by_region()[[SEA]])
finding(report, "X38", function() region_rates(SEA, "any_vh", 1, "born")$foreign)
finding(report, "X39", function() region_rates(SEA, "any_vh", 1, "born")$native)
finding(report, "X40", function() region_rates(SEA, "WP22409", 1, "born")$foreign)
finding(report, "X41", function() region_rates(SEA, "WP22409", 1, "born")$native)
finding(report, "X42", function() with(region_rates(SEA, "WP22409", 1, "born"), foreign - native))
finding(report, "C7", function() experience_and_told(SEA))
finding(report, "X43", function() region_rates(SEA, "any_vh", 1, c("born", "fin"))$foreign_difficult)
finding(report, "X44", function() with(region_rates(SEA, "any_vh", 1, c("born", "fin")), foreign_difficult - foreign_comfortable))
finding(report, "X45", function() region_rates(SEA, "any_vh", 1, c("born", "fin"))$native_difficult)
finding(report, "X46", function() region_rates(SEA, "any_vh", 1, c("born", "fin"))$native_comfortable)
finding(report, "X47", function() with(region_rates(SEA, "any_vh", 1, c("born", "fin")), native_difficult - native_comfortable))
finding(report, "X48", function() region_rates(SEA, "WP22409", 1, c("born", "fin"))$foreign_difficult)
finding(report, "X49", function() region_rates(SEA, "WP22409", 1, c("born", "fin"))$foreign_comfortable)
finding(report, "X50", function() with(region_rates(SEA, "WP22409", 1, c("born", "fin")), foreign_difficult - foreign_comfortable))
finding(report, "X51", function() region_rates(SEA, "WP22409", 1, c("born", "fin"))$native_comfortable)

SEA_REASONS <- c(reputation = "WP22420", waste = "WP22415")
finding(report, "C8", function() {
  w <- region_by_birth(SEA)
  out <- numeric(0)
  for (reason in names(SEA_REASONS)) {
    v <- shares(w, SEA_REASONS[[reason]], YES_NO, "born")
    out <- c(out, setNames(v, paste(reason, names(v), sep = "_")))
  }
  out
})
finding(report, "X52", function() region_rates(SEA, "WP22420", 1, "born")$native)
finding(report, "X53", function() region_rates(SEA, "WP22420", 1, "born")$foreign)
finding(report, "X54", function() with(region_rates(SEA, "WP22420", 1, "born"), native - foreign))
finding(report, "X55", function() region_rates(SEA, "WP22415", 1, "born")$foreign)
finding(report, "X56", function() region_rates(SEA, "WP22415", 1, "born")$native)

finding(report, "X57", function() by_region()[[LAC]])
finding(report, "X58", function() with(region_rates(LAC, "any_vh", 1, "born"), foreign - native))
finding(report, "X59", function() with(region_rates(LAC, "any_vh", 1, c("born", "fin")), foreign_difficult - foreign_comfortable))
finding(report, "X60", function() with(region_rates(LAC, "any_vh", 1, c("born", "fin")), native_difficult - native_comfortable))
finding(report, "X61", function() region_rates(LAC, "WP22409", 1, "born")$foreign)
finding(report, "X62", function() region_rates(LAC, "WP22409", 1, "born")$native)
finding(report, "X63", function() with(region_rates(LAC, "WP22409", 1, "born"), foreign - native))
finding(report, "X64", function() region_rates(LAC, "WP22409", 1, c("born", "fin"))$foreign_comfortable)
finding(report, "X65", function() region_rates(LAC, "WP22409", 1, c("born", "fin"))$foreign_difficult)
finding(report, "C9", function() experience_and_told(LAC))

FORMS <- list(three = 3, two = 2, one = 1, none = 0)
finding(report, "C10", function() {
  w <- region_by_birth(LAC)
  c(shares(w, "n_forms", FORMS, "born"), only(shares(w, "n_forms", FORMS, c("born", "sex")), "foreign_"))
})
finding(report, "X66", function() region_rates(LAC, "n_forms", 3, "born")$foreign)
finding(report, "X67", function() region_rates(LAC, "n_forms", 3, "born")$native)
finding(report, "X68", function() region_rates(LAC, "n_forms", 3, c("born", "sex"))$foreign_men)
finding(report, "X69", function() region_rates(LAC, "n_forms", 3, c("born", "sex"))$foreign_women)
finding(report, "X70", function() region_rates(LAC, "WP22409", 1, c("born", "sex"))$foreign_men)
finding(report, "X71", function() region_rates(LAC, "WP22409", 1, c("born", "sex"))$native_men)
finding(report, "X72", function() region_rates(LAC, "WP22409", 1, c("born", "sex"))$foreign_women)
finding(report, "X73", function() region_rates(LAC, "WP22419", 1, c("born", "sex"))$foreign_men)
finding(report, "X74", function() with(region_rates(LAC, "WP22419", 1, c("born", "sex")), foreign_men - foreign_women))
finding(report, "X75", function() region_rates(LAC, "WP22420", 1, c("born", "sex"))$foreign_men)
finding(report, "X76", function() with(region_rates(LAC, "WP22420", 1, c("born", "sex")), foreign_men - foreign_women))

# --- Page 13: Concluding remarks ---------------------------------------------------------

finding(report, "X77", function() {
  countries <- unique(d$COUNTRY_ISO3[d$GlobalRegion %in% 5])
  100 * sum(countries %in% C190_RATIFIED) / length(countries)
})

status <- run_report(report)
if (!interactive()) quit(status = status)
