"""Reproduce World Risk Poll 2021 Focus On: Fossil fuel dependency and perceptions of climate change.

Run from the repository root:
    python reports/WRP_2021/focus_on_fossil_fuels_and_climate_change/reproduce.py

The report compares the share of people who see climate change as a 'very
serious threat' (WP20719) across countries, and within Norway and Canada,
with country-level fossil fuel indicators from the World Bank and Our World
in Data. Each function below computes one chart or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

EXTERNAL = Path(__file__).resolve().parents[2] / "external"
FUEL_EXPORTS = EXTERNAL / "focus_on_fossil_fuels_and_climate_change__worldbank_TX.VAL.FUEL.ZS.UN.csv"
FUEL_YEAR = 2021  # WDI year used for energy exports (see README)

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
    "WP20719", "WP22331", "REGION4_NOR", "REGION_CAN",
])

# --- Derived variables ---------------------------------------------------------

VERY = [1]          # WP20719: 1 = very serious threat, 2 = somewhat serious, 3 = not a threat, 98/99 = DK/refused
SERIOUS = [1, 2]
CLIMATE_RISK = [19]  # WP22331: 19 = ENVIRONMENT: climate change or severe weather-related events

# Chart regions: Europe = GlobalRegion 12-14, Latin America & the Caribbean = 5.
d["latam_europe"] = d.GlobalRegion.isin([5, 12, 13, 14])

# Norway (Chart 7): the report's five regions, built from the 2020 counties in
# REGION4_NOR. "Trøndelag" includes Møre og Romsdal (Mid-Norway), "Western"
# is Rogaland and Vestland, "Southern" is Agder and Vestfold og Telemark.
# This is the grouping that reproduces all five published values (see README).
NORWAY_REGIONS = {
    "northern": [4, 12],     # Nordland, Troms og Finnmark
    "trondelag": [3, 11],    # Møre og Romsdal, Trøndelag
    "western": [2, 10],      # Rogaland, Vestland
    "eastern": [1, 5, 6],    # Oslo, Viken, Innlandet
    "southern": [7, 8],      # Vestfold og Telemark, Agder
}
nor = d[d.COUNTRY_ISO3 == "NOR"]

# Canada (Chart 8): REGION_CAN has eight regions, so only Quebec, Ontario and
# British Columbia can be built (CMA plus rest of province). The other
# provinces need a province variable that is not in the public release.
CANADA_REGIONS = {"quebec": [2, 3], "ontario": [4, 5], "british_columbia": [7, 8]}
GALLUP_PROVINCES = {  # finding key -> province name in the (placeholder) Gallup item
    "alberta": "Alberta", "saskatchewan": "Saskatchewan", "manitoba": "Manitoba",
    "newfoundland_labrador": "Newfoundland and Labrador", "nova_scotia": "Nova Scotia",
    "new_brunswick": "New Brunswick", "prince_edward_island": "Prince Edward Island",
}
can = d[d.COUNTRY_ISO3 == "CAN"]

# Energy exports (Chart 6): World Bank fuel exports, % of merchandise exports.
fuel = pd.read_csv(FUEL_EXPORTS)
fuel = fuel[fuel.year == FUEL_YEAR].set_index("country_iso3")["value"]

# --- Helpers -------------------------------------------------------------------


def by_country(var, codes):
    """% of respondents in each country (COUNTRY_ISO3) whose `var` is in `codes`."""
    return pct(d, var, codes, by="COUNTRY_ISO3")


def country(iso3, var="WP20719", codes=VERY):
    return pct(d[d.COUNTRY_ISO3 == iso3], var, codes)


def name_of(iso3):
    return d.loc[d.COUNTRY_ISO3 == iso3, "Country"].iloc[0]


def norway_region(key):
    return pct(nor[nor.REGION4_NOR.isin(NORWAY_REGIONS[key])], "WP20719", VERY)


def canada_province_gallup(key):
    # Needs a Canadian province variable from the Gallup World Poll
    # (placeholder name GWP_CANADA_PROVINCE, holding the province name).
    g = merge_gallup(can, ["GWP_CANADA_PROVINCE"])
    return pct(g[g.GWP_CANADA_PROVINCE == GALLUP_PROVINCES[key]], "WP20719", VERY)


LABELLED = {  # countries labelled in Charts 2-6
    "C2": ["ARE", "SAU", "MNG", "AUS", "CAN", "KAZ", "RUS", "USA", "CHN", "NOR", "GBR", "CHL"],
    "C3": ["ARE", "SAU", "AUS", "CAN", "USA", "KOR", "NOR", "GBR", "KAZ", "RUS", "CHN", "JOR",
           "MNG", "IRN", "DZA", "UKR", "MOZ", "TGO"],
    "C4": ["NOR", "ARE", "SAU", "AUS", "CAN", "USA", "GBR", "RUS", "KAZ", "CHN", "BRA", "MNG",
           "EGY", "BOL", "MOZ", "AFG", "SLE"],
    "C5": ["CHN", "USA", "RUS", "SAU", "CAN", "NOR", "GBR"],
}

# --- Introduction ----------------------------------------------------------------


@report.finding("X01")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X02")
def respondents():
    return len(d)


@report.finding("X03")
def very_serious_global():
    return pct(d, "WP20719", VERY)


@report.finding("X04")
def serious_global():
    return pct(d, "WP20719", SERIOUS)


@report.finding("X05")
def very_serious_chile():
    return country("CHL")


@report.finding("X06")
def serious_chile():
    return country("CHL", codes=SERIOUS)


@report.finding("X07")
def very_serious_saudi_arabia():
    return country("SAU")


@report.finding("X08")
def serious_saudi_arabia():
    return country("SAU", codes=SERIOUS)


# --- Public perceptions of climate change vary globally (Chart 1) -----------------


@report.finding("X09")
def climate_greatest_risk_global():
    return pct(d, "WP22331", CLIMATE_RISK)


@report.finding("X10")
def climate_greatest_risk_chile():
    return country("CHL", "WP22331", CLIMATE_RISK)


@report.finding("C1")
def chart1_by_country():
    # No values are printed on the chart: every country's % 'very serious threat'
    # (top circles) and % naming climate change as the greatest risk (bottom).
    # WP22331 was not asked in China.
    very = by_country("WP20719", VERY)
    risk = by_country("WP22331", CLIMATE_RISK).dropna()
    out = {f"very_{k}": v for k, v in very.items()}
    out.update({f"risk_{k}": v for k, v in risk.items()})
    return out


@report.finding("C1_least_concerned")
def least_concerned():
    return name_of(by_country("WP20719", VERY).idxmin())


@report.finding("C1_most_climate_risk")
def most_climate_risk():
    return name_of(by_country("WP22331", CLIMATE_RISK).idxmax())


@report.finding("C1_top12_latam_europe")
def top12_latam_europe():
    top12 = by_country("WP20719", VERY).nlargest(12).index
    region = d.drop_duplicates("COUNTRY_ISO3").set_index("COUNTRY_ISO3").latam_europe
    return int(region[top12].sum())


# --- Charts 2-5: CO2 emissions and energy production (Our World in Data) ---------
# The charts print no values. They plot each country's % 'very serious threat'
# against OWID indicators; the functions give the poll side for the labelled
# countries.


def labelled(chart):
    very = by_country("WP20719", VERY)
    return {iso3: very[iso3] for iso3 in LABELLED[chart]}


@report.finding("C2")
def chart2():
    return labelled("C2")


@report.finding("C3")
def chart3():
    return labelled("C3")


@report.finding("X11")
def over_half_anglosphere():
    very = by_country("WP20719", VERY)
    return int((very[["AUS", "USA", "CAN"]] > 50).sum())


@report.finding("C4")
def chart4():
    return labelled("C4")


@report.finding("C5")
def chart5():
    return labelled("C5")


@report.finding("X12")
def very_serious_china():
    return country("CHN")


# --- Chart 6: energy exports (World Bank) ---------------------------------------


def energy_exporters():
    """% 'very serious threat' in countries where fuel is more than 50% of merchandise exports."""
    very = by_country("WP20719", VERY)
    exporters = fuel[fuel > 50].index.intersection(very.index)
    return very[exporters].sort_index()


@report.finding("C6")
def chart6():
    # No values are printed on the chart: % 'very serious threat' in each
    # country where energy is more than 50% of exports (World Bank, 2021).
    return energy_exporters()


@report.finding("X13")
def exporters_with_majority_concerned():
    return int((energy_exporters() >= 50).sum())


# --- Chart 7: Norway --------------------------------------------------------------


@report.finding("X14")
def smallest_country_sample():
    return int(d.groupby("COUNTRY_ISO3").size().min())


@report.finding("X15")
def very_serious_norway():
    return country("NOR")


@report.finding("X16")
def western_norway():
    return norway_region("western")


@report.finding("X17")
def northern_norway():
    return norway_region("northern")


@report.finding("C7")
def chart7():
    return {key: norway_region(key) for key in NORWAY_REGIONS}


# --- Chart 8: Canada --------------------------------------------------------------


@report.finding("X18")
def very_serious_canada():
    return country("CAN")


@report.finding("X19")
def alberta():
    return canada_province_gallup("alberta")


@report.finding("C8")
def chart8():
    return {key: pct(can[can.REGION_CAN.isin(codes)], "WP20719", VERY) for key, codes in CANADA_REGIONS.items()}


for _key in GALLUP_PROVINCES:
    report.finding(f"C8_{_key}")(lambda key=_key: canada_province_gallup(key))


if __name__ == "__main__":
    sys.exit(report.run())
