# Reproduce World Risk Poll 2021 Focus On: Fossil fuel dependency and perceptions of climate change.
#
# Run from the repository root:
#   Rscript reports/WRP_2021/focus_on_fossil_fuels_and_climate_change/reproduce.R
#
# Same findings, same finding_ids and same method as reproduce.py; see
# README.md for the method notes.

here <- local({
  f <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(f)) dirname(normalizePath(sub("^--file=", "", f))) else getwd()
})
source(file.path(here, "..", "..", "R", "wrp.R"))

report <- wrp_report(here)

FUEL_EXPORTS <- file.path(here, "..", "..", "external",
                          "focus_on_fossil_fuels_and_climate_change__worldbank_TX.VAL.FUEL.ZS.UN.csv")
FUEL_YEAR <- 2021 # WDI year used for energy exports (see README)

d <- load_wave(2021, c(
  "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
  "WP20719", "WP22331", "REGION4_NOR", "REGION_CAN"
))

# --- Derived variables ---------------------------------------------------------

VERY <- 1            # WP20719: 1 = very serious threat, 2 = somewhat serious, 3 = not a threat, 98/99 = DK/refused
SERIOUS <- c(1, 2)
CLIMATE_RISK <- 19   # WP22331: 19 = ENVIRONMENT: climate change or severe weather-related events

# Chart regions: Europe = GlobalRegion 12-14, Latin America & the Caribbean = 5.
d$latam_europe <- d$GlobalRegion %in% c(5, 12, 13, 14)

# Norway (Chart 7): the report's five regions, built from the 2020 counties in
# REGION4_NOR. "Trøndelag" includes Møre og Romsdal (Mid-Norway), "Western"
# is Rogaland and Vestland, "Southern" is Agder and Vestfold og Telemark.
NORWAY_REGIONS <- list(
  northern = c(4, 12),    # Nordland, Troms og Finnmark
  trondelag = c(3, 11),   # Møre og Romsdal, Trøndelag
  western = c(2, 10),     # Rogaland, Vestland
  eastern = c(1, 5, 6),   # Oslo, Viken, Innlandet
  southern = c(7, 8)      # Vestfold og Telemark, Agder
)
nor <- d[d$COUNTRY_ISO3 == "NOR", ]

# Canada (Chart 8): REGION_CAN has eight regions, so only Quebec, Ontario and
# British Columbia can be built (CMA plus rest of province). The other
# provinces need a province variable that is not in the public release.
CANADA_REGIONS <- list(quebec = c(2, 3), ontario = c(4, 5), british_columbia = c(7, 8))
GALLUP_PROVINCES <- c( # finding key -> province name in the (placeholder) Gallup item
  alberta = "Alberta", saskatchewan = "Saskatchewan", manitoba = "Manitoba",
  newfoundland_labrador = "Newfoundland and Labrador", nova_scotia = "Nova Scotia",
  new_brunswick = "New Brunswick", prince_edward_island = "Prince Edward Island"
)
can <- d[d$COUNTRY_ISO3 == "CAN", ]

# Energy exports (Chart 6): World Bank fuel exports, % of merchandise exports.
fuel_raw <- read.csv(FUEL_EXPORTS, stringsAsFactors = FALSE)
fuel_raw <- fuel_raw[fuel_raw$year == FUEL_YEAR, ]
fuel <- setNames(fuel_raw$value, fuel_raw$country_iso3)

# --- Helpers -------------------------------------------------------------------

# % of respondents in each country (COUNTRY_ISO3) whose `var` is in `codes`.
by_country <- function(var, codes) pct(d, var, codes, by = "COUNTRY_ISO3")

country <- function(iso3, var = "WP20719", codes = VERY) pct(d[d$COUNTRY_ISO3 == iso3, ], var, codes)

name_of <- function(iso3) d$Country[match(iso3, d$COUNTRY_ISO3)]

norway_region <- function(key) pct(nor[nor$REGION4_NOR %in% NORWAY_REGIONS[[key]], ], "WP20719", VERY)

# Needs a Canadian province variable from the Gallup World Poll
# (placeholder name GWP_CANADA_PROVINCE, holding the province name).
canada_province_gallup <- function(key) {
  g <- merge_gallup(can, "GWP_CANADA_PROVINCE")
  pct(g[g$GWP_CANADA_PROVINCE %in% GALLUP_PROVINCES[[key]], ], "WP20719", VERY)
}

LABELLED <- list( # countries labelled in Charts 2-6
  C2 = c("ARE", "SAU", "MNG", "AUS", "CAN", "KAZ", "RUS", "USA", "CHN", "NOR", "GBR", "CHL"),
  C3 = c("ARE", "SAU", "AUS", "CAN", "USA", "KOR", "NOR", "GBR", "KAZ", "RUS", "CHN", "JOR",
         "MNG", "IRN", "DZA", "UKR", "MOZ", "TGO"),
  C4 = c("NOR", "ARE", "SAU", "AUS", "CAN", "USA", "GBR", "RUS", "KAZ", "CHN", "BRA", "MNG",
         "EGY", "BOL", "MOZ", "AFG", "SLE"),
  C5 = c("CHN", "USA", "RUS", "SAU", "CAN", "NOR", "GBR")
)

labelled <- function(chart) by_country("WP20719", VERY)[LABELLED[[chart]]]

# % 'very serious threat' in countries where fuel is more than 50% of merchandise exports.
energy_exporters <- function() {
  very <- by_country("WP20719", VERY)
  exporters <- sort(intersect(names(fuel)[fuel > 50], names(very)))
  very[exporters]
}

# --- Introduction ----------------------------------------------------------------

finding(report, "X01", function() length(unique(d$COUNTRY_ISO3)))
finding(report, "X02", function() nrow(d))
finding(report, "X03", function() pct(d, "WP20719", VERY))
finding(report, "X04", function() pct(d, "WP20719", SERIOUS))
finding(report, "X05", function() country("CHL"))
finding(report, "X06", function() country("CHL", codes = SERIOUS))
finding(report, "X07", function() country("SAU"))
finding(report, "X08", function() country("SAU", codes = SERIOUS))

# --- Public perceptions of climate change vary globally (Chart 1) -----------------

finding(report, "X09", function() pct(d, "WP22331", CLIMATE_RISK))
finding(report, "X10", function() country("CHL", "WP22331", CLIMATE_RISK))

# No values are printed on the chart: every country's % 'very serious threat'
# (top circles) and % naming climate change as the greatest risk (bottom).
# WP22331 was not asked in China.
finding(report, "C1", function() {
  very <- by_country("WP20719", VERY)
  risk <- by_country("WP22331", CLIMATE_RISK)
  c(setNames(very, paste0("very_", names(very))), setNames(risk, paste0("risk_", names(risk))))
})
finding(report, "C1_least_concerned", function() {
  very <- by_country("WP20719", VERY)
  name_of(names(very)[which.min(very)])
})
finding(report, "C1_most_climate_risk", function() {
  risk <- by_country("WP22331", CLIMATE_RISK)
  name_of(names(risk)[which.max(risk)])
})
finding(report, "C1_top12_latam_europe", function() {
  very <- by_country("WP20719", VERY)
  top12 <- names(sort(very, decreasing = TRUE))[1:12]
  sum(d$latam_europe[match(top12, d$COUNTRY_ISO3)])
})

# --- Charts 2-5: CO2 emissions and energy production (Our World in Data) ---------
# The charts print no values; the functions give the poll side for the
# labelled countries.

finding(report, "C2", function() labelled("C2"))
finding(report, "C3", function() labelled("C3"))
finding(report, "X11", function() sum(by_country("WP20719", VERY)[c("AUS", "USA", "CAN")] > 50))
finding(report, "C4", function() labelled("C4"))
finding(report, "C5", function() labelled("C5"))
finding(report, "X12", function() country("CHN"))

# --- Chart 6: energy exports (World Bank) ---------------------------------------

# No values are printed on the chart: % 'very serious threat' in each country
# where energy is more than 50% of exports (World Bank, 2021).
finding(report, "C6", function() energy_exporters())
finding(report, "X13", function() sum(energy_exporters() >= 50))

# --- Chart 7: Norway --------------------------------------------------------------

finding(report, "X14", function() min(table(d$COUNTRY_ISO3)))
finding(report, "X15", function() country("NOR"))
finding(report, "X16", function() norway_region("western"))
finding(report, "X17", function() norway_region("northern"))
finding(report, "C7", function() sapply(setNames(names(NORWAY_REGIONS), names(NORWAY_REGIONS)), norway_region))

# --- Chart 8: Canada --------------------------------------------------------------

finding(report, "X18", function() country("CAN"))
finding(report, "X19", function() canada_province_gallup("alberta"))
finding(report, "C8", function() {
  sapply(CANADA_REGIONS, function(codes) pct(can[can$REGION_CAN %in% codes, ], "WP20719", VERY))
})
for (key in names(GALLUP_PROVINCES)) {
  local({
    k <- key
    finding(report, paste0("C8_", k), function() canada_province_gallup(k))
  })
}

status <- run_report(report)
if (!interactive()) quit(status = status)
