# Quickstart: load one World Risk Poll wave, then stack all four waves
# into a trend file using the harmonised block described in
# docs/CODEBOOK.md.
#
# Requires: arrow, dplyr
#   install.packages(c("arrow", "dplyr"))
#
# Run from the repository root:
#   Rscript examples/quickstart.R

library(arrow)
library(dplyr)

# Weighted mean of `value`, over the rows where `value` is present.
weighted_mean <- function(value, weight) {
  ok <- !is.na(value)
  sum(value[ok] * weight[ok]) / sum(weight[ok])
}

# --- Load a single wave ----------------------------------------------

wave <- read_parquet("WRP_2025/WRP_2025.parquet")
cat(sprintf(
  "%s respondents, %d variables\n",
  format(nrow(wave), big.mark = ","), ncol(wave)
))

# Within-country weighted average worry score for this wave.
cat(sprintf(
  "2025 worry_score (WGT-weighted): %.3f\n",
  weighted_mean(wave$worry_score, wave$WGT)
))

# --- Stack all four waves for a trend ---------------------------------
# Only the first 37 columns (the harmonised block) carry matching names,
# codes and labels across waves -- that's what makes stacking valid.
# See docs/CODEBOOK.md for what each one means and which waves it covers.

harmonised_cols <- c(
  "WPID_RANDOM", "Wave", "Year", "WP5", "Country", "COUNTRY_ISO2",
  "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT",
  "Age", "AgeGroups3", "AgeGroups4", "AgeGroups5", "Gender", "Education",
  "Urbanicity", "Urbanicity2", "EMP_2010", "INCOME_5", "HouseholdSize",
  "ChildrenInHousehold", "worry_score", "worry_score_core7",
  "worry_index_published", "experience_score", "experience_score_self",
  "experience_score_core7", "experience_index_published", "worry_exp_gap",
  "resilience_index", "resilience_index_100", "resilience_idv",
  "resilience_hhl", "resilience_com", "resilience_soc"
)

waves <- c("WRP_2019", "WRP_2021", "WRP_2023", "WRP_2025")

trend <- bind_rows(lapply(waves, function(w) {
  read_parquet(file.path(w, paste0(w, ".parquet")), col_select = all_of(harmonised_cols))
}))
cat(sprintf(
  "\nPooled trend file: %s respondents across %d waves\n",
  format(nrow(trend), big.mark = ","), length(waves)
))

# Global worry_score by wave, weighted by PROJWT (a population weight,
# appropriate here because the trend is being pooled across countries --
# use WGT instead for a within-country-only comparison).
trend %>%
  group_by(Year) %>%
  summarise(worry_score = round(weighted_mean(worry_score, PROJWT), 3)) %>%
  print()

# --- A wave-specific question, trended by hand ------------------------
# "Climate change is a threat to [country] in the next 20 years" is asked
# in every wave, but it sits OUTSIDE the harmonised block and its variable
# name changes: L5 in 2019, WP20719 from 2021 on. Codes: 1 = very serious
# threat, 2 = somewhat serious, 3 = not a threat; 98/99 are DK/refused.
# This is the general recipe for any comparable question that isn't
# pre-harmonised: map the per-wave name, keep the substantive codes, then
# bind the rows.

climate_var <- c(
  WRP_2019 = "L5", WRP_2021 = "WP20719",
  WRP_2023 = "WP20719", WRP_2025 = "WP20719"
)

climate <- bind_rows(lapply(names(climate_var), function(w) {
  var <- climate_var[[w]]
  read_parquet(
    file.path(w, paste0(w, ".parquet")),
    col_select = all_of(c("Year", "PROJWT", var))
  ) %>%
    rename(climate_threat = all_of(var)) %>%
    filter(climate_threat %in% c(1, 2, 3))
}))

# % who see climate change as at least a somewhat serious threat (code
# 1 or 2), by year.
climate %>%
  mutate(serious = as.numeric(climate_threat %in% c(1, 2))) %>%
  group_by(Year) %>%
  summarise(pct_serious_threat = round(100 * weighted_mean(serious, PROJWT), 1)) %>%
  print()
