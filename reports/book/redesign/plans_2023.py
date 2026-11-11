"""The plans for the reports of the 2023 poll: pages, opening figures and one specification per chart.

assemble_2023.py reads these. A chart that has no specification here is placed as a picture of the original.
"""

import appendix_2023
from assemble_2023 import plan

COPYRIGHT = "Copyright © 2024 Lloyd's Register Foundation. All rights reserved."
APPENDICES = (
    "The appendices of the original are set in full after the last chapter: the Resilience Index methodology, the scoring of each item and the table of "
    "index values for 142 countries. Appendix Tables 1, 2 and 3 and the scoring table for Cover Basic Needs are pictures of the original: the "
    "first two set their headings on their side, the third holds lists inside its cells and the fourth sets two tables side by side, none of "
    "which the tables of this edition can hold. In the table of index values the original marks China with an asterisk and gives no note for it.")


REGIONS = {
    "east_asia": "Eastern Asia", "southeast_asia": "Southeastern Asia", "anz": "Australia & New Zealand", "northern_western_europe": "Northern/Western Europe",
    "north_america": "Northern America", "central_asia": "Central Asia", "eastern_europe": "Eastern Europe", "southern_europe": "Southern Europe",
    "south_asia": "Southern Asia", "middle_east": "Middle East", "north_africa": "Northern Africa", "latin_america": "Latin America & the Caribbean",
    "southern_africa": "Southern Africa", "east_africa": "Eastern Africa", "central_western_africa": "Central/Western Africa",
    # the same regions as other files of findings name them
    "eastern_asia": "Eastern Asia", "southeastern_asia": "Southeastern Asia", "australia_nz": "Australia & New Zealand", "northern_america": "Northern America",
    "southern_asia": "Southern Asia", "northern_africa": "Northern Africa", "eastern_africa": "Eastern Africa",
    "se_asia": "Southeastern Asia", "south_europe": "Southern Europe", "nw_europe": "Northern/Western Europe", "cw_africa": "Central/Western Africa",
    "latam": "Latin America & the Caribbean", "east_europe": "Eastern Europe", "south_africa": "Southern Africa",
}
INCOME = (("low", "Low income"), ("lower_middle", "Lower-middle income"), ("upper_middle", "Upper-middle income"), ("high", "High income"))
AREAS = (("cities", "Cities"), ("towns", "Towns and semi-dense areas"), ("rural", "Rural areas"))
AGES = (("15_29", "15-29"), ("30_49", "30-49"), ("50_64", "50-64"), ("65plus", "65+"))
NOT_PRINTED = "Values the original does not print"
COUNTRIES = {
    "AFG": "Afghanistan", "ALB": "Albania", "ARE": "United Arab Emirates", "ARG": "Argentina", "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria", "AZE": "Azerbaijan",
    "BEL": "Belgium", "BEN": "Benin", "BFA": "Burkina Faso", "BGD": "Bangladesh", "BGR": "Bulgaria", "BHR": "Bahrain", "BIH": "Bosnia & Herzegovina", "BOL": "Bolivia",
    "BRA": "Brazil", "BWA": "Botswana", "CAN": "Canada", "CHE": "Switzerland", "CHL": "Chile", "CHN": "China", "CIV": "Côte d’Ivoire", "CMR": "Cameroon",
    "COD": "Congo (DRC)", "COG": "Congo", "COL": "Colombia", "COM": "Comoros", "CRI": "Costa Rica", "CYP": "Cyprus", "CZE": "Czech Republic", "DEU": "Germany",
    "DNK": "Denmark", "DOM": "Dominican Republic", "DZA": "Algeria", "ECU": "Ecuador", "EGY": "Egypt", "ESP": "Spain", "EST": "Estonia", "ETH": "Ethiopia",
    "FIN": "Finland", "FRA": "France", "GAB": "Gabon", "GBR": "United Kingdom", "GEO": "Georgia", "GHA": "Ghana", "GIN": "Guinea", "GMB": "Gambia", "GRC": "Greece",
    "GTM": "Guatemala", "HKG": "Hong Kong", "HND": "Honduras", "HRV": "Croatia", "HUN": "Hungary", "IDN": "Indonesia", "IND": "India", "IRL": "Ireland", "IRN": "Iran",
    "IRQ": "Iraq", "ISL": "Iceland", "ISR": "Israel", "ITA": "Italy", "JOR": "Jordan", "JPN": "Japan", "KAZ": "Kazakhstan", "KEN": "Kenya", "KGZ": "Kyrgyzstan",
    "KHM": "Cambodia", "KOR": "South Korea", "KWT": "Kuwait", "LAO": "Laos", "LBN": "Lebanon", "LBR": "Liberia", "LBY": "Libya", "LKA": "Sri Lanka", "LTU": "Lithuania",
    "LUX": "Luxembourg", "LVA": "Latvia", "MAR": "Morocco", "MDA": "Moldova", "MDG": "Madagascar", "MEX": "Mexico", "MKD": "North Macedonia", "MLI": "Mali", "MLT": "Malta",
    "MMR": "Myanmar", "MNE": "Montenegro", "MNG": "Mongolia", "MOZ": "Mozambique", "MRT": "Mauritania", "MUS": "Mauritius", "MWI": "Malawi", "MYS": "Malaysia",
    "NAM": "Namibia", "NER": "Niger", "NGA": "Nigeria", "NIC": "Nicaragua", "NLD": "Netherlands", "NOR": "Norway", "NPL": "Nepal", "NZL": "New Zealand", "PAK": "Pakistan",
    "PAN": "Panama", "PER": "Peru", "PHL": "Philippines", "POL": "Poland", "PRT": "Portugal", "PRY": "Paraguay", "PSE": "Palestine", "ROU": "Romania", "RUS": "Russia",
    "SAU": "Saudi Arabia", "SEN": "Senegal", "SGP": "Singapore", "SLE": "Sierra Leone", "SLV": "El Salvador", "SOM": "Somalia", "SRB": "Serbia", "SVK": "Slovakia",
    "SVN": "Slovenia", "SWE": "Sweden", "SWZ": "Eswatini", "TCD": "Chad", "TGO": "Togo", "THA": "Thailand", "TJK": "Tajikistan", "TUN": "Tunisia", "TUR": "Türkiye",
    "TWN": "Taiwan", "TZA": "Tanzania", "UGA": "Uganda", "UKR": "Ukraine", "URY": "Uruguay", "USA": "United States", "UZB": "Uzbekistan", "VEN": "Venezuela",
    "VNM": "Vietnam", "XKX": "Kosovo", "YEM": "Yemen", "ZAF": "South Africa", "ZMB": "Zambia", "ZWE": "Zimbabwe",
}
YEARS = dict(series=["2021", "2023"], colours=["navy", "fuchsia"])
DIMENSIONS = (("index", "Resilience Index"), ("individual", "Individual"), ("household", "Household"), ("community", "Community"), ("societal", "Societal"))
SCATTER = "the original plots every country without printing its value"
MEDIANS = ("Charts 2.3, 2.4 and 2.7 to 2.10 of the original also draw the global medians of 2021 and 2023 as dotted lines, without printing their values; "
           "the lines are not redrawn.")


def rows_of(ids, prefix, names, suffixes=None, also=None):
    """Rows in the printed order: [label, [finding per suffix]], or [label, finding] with no suffixes."""
    names = dict(names, **(also or {}))
    keys = ids.keys(prefix, "_" + suffixes[0] if suffixes else "", names)
    assert keys, prefix
    return [[names[k], [f"{prefix}{k}_{s}" for s in suffixes] if suffixes else f"{prefix}{k}"] for k in keys]


def changes(ids, prefix, heading, also=None):
    """The countries with the biggest changes: the two years as a pair of dots, the change in points beside them."""
    return dict(kind="dumbbell", unit="", total_unit="", signed=True, series=[heading, "2021", "2023"], colours=["navy", "fuchsia"],
                rows=[[name, [f"{prefix}{k}_change", f"{prefix}{k}_2021", f"{prefix}{k}_2023"]]
                      for name, k in ((dict(COUNTRIES, **(also or {}))[k], k) for k in ids.keys(prefix, "_2021", COUNTRIES))])


def by_dimension(prefix, groups, order="group_first", dims=DIMENSIONS):
    """Upright bars for each dimension of the index: one bar per group."""
    ident = (lambda g, d: f"{prefix}{g}_{d}") if order == "group_first" else (lambda g, d: f"{prefix}{d}_{g}")
    return [["", [[name, [ident(g, d) for g, _ in groups]] for d, name in dims]]]


def resilience(ids):
    warned = dict(series=["At least one warning", "No warning"], colours=["fuchsia", "navy"])
    work = (("ft_employer", "Employed full time by an employer"), ("other_workforce", "In workforce, but not employed full-time by an employer"), ("out_workforce", "Out of workforce"))
    money = (("less_week", "Less than a week"), ("week_month", "Between a week and a month"), ("month_plus", "A month or more"))
    four = DIMENSIONS[1:]
    shift = "Point change in Resilience Index*"

    def stacked(prefix, names):
        return dict(kind="stacked", rows=[[name, [f"{prefix}{k}_warned", f"{prefix}{k}_none"]] for k, name in names], **warned)

    def points(prefix, places):
        rows = []
        for k, name in places:
            rows += [[name, None]] + [[d_name, f"{prefix}{k}_{d}"] for d, d_name in DIMENSIONS]
        return dict(kind="diverging", unit="", row=46, series=["", ""], colours=["navy", "fuchsia"], rows=rows)

    return {
        "2.1": dict(kind="grouped", unit="", rows=rows_of(ids, "C2_1_", REGIONS, ("2021", "2023")), **YEARS),
        "2.2": dict(kind="hbar", unit="", key=["Decreased Resilience Index", "No significant change", "Increased Resilience Index"], colours=["fuchsia", "grey", "navy"],
                    rows=[["Significant decrease of four or more points", "C2_2_decrease", "Decreased Resilience Index"], ["No significant change", "C2_2_no_change", "No significant change"],
                          ["Significant increase of four or more points", "C2_2_increase", "Increased Resilience Index"]]),
        "T2.1": dict(kind="heading", text_from=[495, 180, 815, 532], note_from=[440, 532, 815, 562],
                     groups_of=[("Individual", 2), ("Household", 3), ("Community", 2), ("Societal", 3)]),
        "2.3": changes(ids, "C2_3_", shift),
        "2.4": changes(ids, "C2_4_", shift),
        "2.5": dict(kind="original", why=SCATTER),
        "2.6": dict(kind="grouped", unit="", series=["Increased resilience", "Decreased resilience"], colours=["fuchsia", "teal"],
                    rows=[[name if d != "index" else "Resilience Index", [f"C2_6_{d}_increase", f"C2_6_{d}_decrease"]] for d, name in DIMENSIONS]),
        "2.7": changes(ids, "C2_7_", "Point change in Individual Resilience*"),
        "2.8": changes(ids, "C2_8_", "Point change in Household Resilience*"),
        "2.9": changes(ids, "C2_9_", "Point change in Community Resilience*"),
        "2.10": changes(ids, "C2_10_", "Point change in Societal Resilience*"),
        "2.11": dict(kind="vgrouped", panels=[["", rows_of(ids, "C2_11_", {"total": "Total", "high": "High income", "upper_middle": "Upper-middle income",
                                                                               "lower_middle": "Lower-middle income", "low": "Low income"}, ("2021", "2023"))]], **YEARS),
        "T2.2": dict(kind="table", unit="", columns=["Rank", "Individual", "Household", "Community", "Societal"],
                     rows=[["Top 10", None]] + [["", [f"T2_2_{d}_top_{n}" for d, _ in four]] for n in range(1, 11)]
                     + [["Bottom 10", None]] + [["", [f"T2_2_{d}_bottom_{n}" for d, _ in four]] for n in range(1, 11)]),
        "3.1": dict(kind="hbar", rows=rows_of(ids, "C3_1_", COUNTRIES)),
        "3.2": dict(kind="vgrouped", panels=[["", rows_of(ids, "C3_2_", {"radio": "Radio, TV, or newspapers", "government": "Local government or police", "internet": "Internet/Social media",
                                                                           "community": "Local community organization"}, ("2021", "2023"))]], **YEARS),
        "3.3": dict(kind="vgrouped", panels=[["", rows_of(ids, "C3_3_", {"15_29": "15-29", "30_49": "30-49", "50_64": "50-64", "65plus": "65+"}, ("2021", "2023"))]], **YEARS),
        "3.4": stacked("C3_4_", [(k, REGIONS[k]) for k in ids.keys("C3_4_", "_warned", REGIONS)]),
        "3.5": stacked("C3_5_", (("primary", "Primary"), ("secondary", "Secondary"), ("tertiary", "Tertiary"))),
        "3.6": stacked("C3_6_", (("less_week", "Less than a week"), ("week_month", "Between a week and a month"), ("month_plus", "A month or more"))),
        "3.7": stacked("C3_7_", (("rural", "Rural areas"), ("towns", "Towns and semi-dense areas"), ("cities", "Cities"))),
        "3.8": dict(kind="grouped", rows=[[name, [f"C3_8_warned_{k}", f"C3_8_none_{k}"]] for k, name in (("internet", "Yes, phone can access internet"),
                    ("no_internet", "No, phone cannot access internet"), ("none", "Does not have phone"))], **warned),
        "3.9": dict(kind="vgrouped", unit="", panels=by_dimension("C3_9_", (("warned", ""), ("none", "")), "dimension_first"), **warned),
        "4.1": dict(kind="vgrouped", unit="", panels=by_dimension("C4_1_", work, dims=four), series=[name for _, name in work], colours=["fuchsia", "teal", "navy"]),
        "T4.1": dict(kind="matrix", unit="", columns=["Poorest 20%", "Richest 20%", shift], plain=[2],
                     rows=[[REGIONS[k], [f"T4_1_{k}_poorest", f"T4_1_{k}_richest", f"T4_1_{k}_gap"]] for k in ids.keys("T4_1_", "_poorest", REGIONS)]),
        "T4.2": dict(kind="matrix", unit="", columns=["2023", "2021"] * 5,
                     groups=[["Total Resilience Index score", 2], ["Individual resilience", 2], ["Household resilience", 2], ["Community resilience", 2], ["Societal resilience", 2]],
                     rows=[[COUNTRIES[k], [f"T4_2_{k}_{d}_{y}" for d, _ in DIMENSIONS for y in ("2023", "2021")]] for k in ids.keys("T4_2_", "_index_2023", COUNTRIES)]),
        "4.2": dict(kind="vgrouped", unit="", panels=by_dimension("C4_2_", money), series=[name for _, name in money], colours=["navy", "teal", "fuchsia"]),
        "5.1": dict(kind="grouped", rows=rows_of(ids, "C5_1_", REGIONS, ("2021", "2023")), **YEARS),
        "5.2": dict(kind="original", why=SCATTER),
        "5.3": dict(kind="original", why="the original plots every region without printing its values"),
        "5.4": dict(kind="original", why=SCATTER),
        "5.5": dict(kind="vgrouped", unit="", panels=[["", [[name, [f"C5_5_{d}_2021", f"C5_5_{d}_2023"]] for d, name in DIMENSIONS]]], **YEARS),
        "5.6": points("C5_6_", (("sindh", "Sindh"), ("punjab", "Punjab"), ("kp", "Khyber Pakhtunkhwa"))),
        "5.7": points("C5_7_", (("auckland", "Auckland"), ("wellington", "Wellington"), ("canterbury", "Canterbury"))),
    }


plan(
    "2023_resilience_in_a_changing_world",
    folder="WRP_2023/core_resilience_in_a_changing_world", pdf="core_resilience_in_a_changing_world.pdf",
    title="Resilience in a Changing World", published="June 2024",
    source="World Risk Poll 2024 Report: Resilience in a Changing World (Lloyd's Register Foundation, June 2024)",
    copyright=COPYRIGHT, cover_image=[0, 0], pages=[(1, 43), (44, 44)], small_text=(38, 39), appendix=appendix_2023.place,
    chapters=[
        dict(big="142", caption="countries and territories were surveyed for the 2023 World Risk Poll, **120** of them also measured in 2021"),
        dict(big="57", caption="is the world's score on the Resilience Index in 2023, largely similar to **55** in 2021"),
        dict(big="70%", caption="of people who experienced a disaster in the past five years received at least one warning; **30%** received none"),
        dict(big="43%", caption="of people say they can do nothing to protect themselves and their families from a future disaster, up from **36%** in 2021"),
        dict(big="30%", caption="of people worldwide experienced a disaster related to a natural hazard in the past five years, compared with **27%** in 2021"),
        dict(big="20", caption="countries saw significant declines of four points or more in resilience; **eight** saw significant increases"),
    ],
    charts=resilience, chart_note=MEDIANS, drop=("Powered by",),
    appendix_note=APPENDICES,
)


# -- A World of Waste

WASTE_NAMES = dict(COUNTRIES, COD="D.R. Congo", CIV="Cote d’Ivoire", USA="U.S.", GBR="U.K.", TWN="Taiwan (PoC)", COG="Republic of the Congo",
                   BIH="Bosnia Herzegovina", PSE="State of Palestine", DOM="D. Republic")
INDIA = {
    "delhi": "Delhi", "himachal_pradesh": "Himachal Pradesh", "punjab": "Punjab", "uttarakhand": "Uttarakhand", "haryana": "Haryana", "rajasthan": "Rajasthan",
    "uttar_pradesh": "Uttar Pradesh", "assam": "Assam", "bihar": "Bihar", "jharkhand": "Jharkhand", "gujarat": "Gujarat", "madhya_pradesh": "Madhya Pradesh",
    "chhattisgarh": "Chhattisgarh", "odisha": "Odisha", "west_bengal": "West Bengal", "maharashtra": "Maharashtra", "telangana": "Telangana", "karnataka": "Karnataka",
    "andhra_pradesh": "Andhra Pradesh", "tamil_nadu": "Tamil Nadu", "kerala": "Kerala",
}
BRAZIL = {
    "maranhao": "Maranhão", "amapa": "Amapá", "ceara": "Ceará", "rio_grande_do_norte": "Rio Grande do Norte", "amazonas": "Amazonas", "para": "Pará", "paraiba": "Paraíba",
    "pernambuco": "Pernambuco", "alagoas": "Alagoas", "rondonia": "Rondônia", "tocantins": "Tocantins", "bahia": "Bahia", "sergipe": "Sergipe",
    "federal_district": "Federal District", "goias": "Goiás", "minas_gerais": "Minas Gerais", "mato_grosso_do_sul": "Mato Grosso do Sul", "espirito_santo": "Espírito Santo",
    "sao_paulo": "São Paulo", "rio_de_janeiro": "Rio de Janeiro", "parana": "Paraná", "santa_catarina": "Santa Catarina", "rio_grande_do_sul": "Rio Grande do Sul",
}
WASTE_MEANS = ("Charts 2.3 and 2.4 of the original also draw global means as dotted lines, without printing their values; the lines are not redrawn. "
               "Where the original prints the value of a mean beside its line (Charts 3.4, 4.2, 4.3 and 5.1 to 5.4), the mean is drawn here as a row or a group of its own.")
ON_A_MAP = "The original prints these figures on a map of {}; here they are drawn as bars, from the highest to the lowest."


def gap_rows(ids, prefix, names, low, high, mean=None):
    """Two groups as a pair of dots, the gap between them in points at the right; the means, where printed, as the first row."""
    rows = [[names[k], [f"{prefix}{k}_gap", f"{prefix}{k}_{low}", f"{prefix}{k}_{high}"]] for k in ids.keys(prefix, "_gap", names)]
    return ([[mean, [None, f"{prefix}mean_{low}", f"{prefix}mean_{high}"]]] if mean else []) + rows


def waste(ids):
    separate = dict(series=["Separate waste", "Sometimes separate waste", "Don’t separate waste"], colours=["fuchsia", "teal", "navy"], gaps=NOT_PRINTED)
    burning = dict(series=["Someone from the household burns it", "Waste is collected"], colours=["fuchsia", "teal"])
    kinds = dict(series=["Food and green waste", "Dry recyclables (plastic, paper, metal, glass, etc...)"], colours=["teal", "fuchsia"])
    quintiles = (("q1", "Poorest 20%"), ("q2", "Second 20%"), ("q3", "Middle 20%"), ("q4", "Fourth 20%"), ("q5", "Richest 20%"))
    quadrants = (("both", "Collected and separated"), ("collected_only", "Collected NOT separated"), ("separated_only", "NOT collected but separated"),
                 ("neither", "NOT collected or separated"))
    difference = "Percentage-point difference"

    def have(*fids):
        return [f if f in ids.ids else None for f in fids]

    def separated(prefix, names):
        return dict(kind="stacked", rows=[[name, have(f"{prefix}{k}_yes", f"{prefix}{k}_sometimes", f"{prefix}{k}_no")] for k, name in names], **separate)

    def top(prefix, names=WASTE_NAMES):
        return [[names[k], f"{prefix}{k}"] for k in ids.keys(prefix, "", names)]

    def by_area(prefix, series, **more):
        return dict(kind="vgrouped", panels=[["", [[name, [f"{prefix}{a}_{k}" for k, _ in series]] for a, name in AREAS]]], series=[name for _, name in series], **more)

    def states(prefix, names, country):
        return dict(kind="hbar", rows=sorted(([name, f"{prefix}{k}"] for k, name in names.items()), key=lambda r: -float(ids.values[r[1]])), note_add=ON_A_MAP.format(country))

    return {
        "2.1": dict(kind="hbar", rows=[[name, f"C2_1_{k}"] for k, name in (("plastic", "Plastic"), ("food", "Food"), ("dust", "Household dust"), ("cardboard", "Cardboard/Paper"),
                                                                           ("cans", "Cans & metal"), ("other", "Other"), ("ash", "Ash"), ("glass", "Glass"))]),
        "2.2": dict(kind="stacked", gaps=NOT_PRINTED, series=["Plastic", "Food", "Cardboard/Paper", "Household dust*", "Other†"], colours=["fuchsia", "teal", "orange", "navy", "grey"],
                    rows=[[name, have(*(f"C2_2_{k}_{m}" for m in ("plastic", "food", "cardboard", "dust", "other")))] for k, name in INCOME]),
        "2.3": dict(kind="grouped", rows=[[name, [f"C2_3_food_green_{k}", f"C2_3_dry_{k}"]] for k, name in INCOME], **kinds),
        "2.4": dict(kind="grouped", rows=[[REGIONS[k], [f"C2_4_food_green_{k}", f"C2_4_dry_{k}"]] for k in ids.keys("C2_4_food_green_", "", REGIONS)],
                    series=["Food and green waste", "Dry recyclables"], colours=kinds["colours"]),
        "T2.1": dict(kind="lists", lists=[[name, top(f"T2_1_{k}_")] for k, name in (("plastic", "Plastic"), ("food", "Food-related"), ("dust", "Household dust*"),
                                                                                    ("cardboard", "Cardboard/paper"))]),
        "2.5": dict(kind="grouped", rows=[[name, [f"C2_5_{k}_food_green", f"C2_5_{k}_dry"]] for k, name in (("women", "Women"), ("men", "Men"))],
                    series=["Food and green waste", "Dry recyclables"], colours=kinds["colours"]),
        "2.6": dict(kind="vgrouped", panels=[["", [[name, [f"C2_6_{k}_{a}" for a, _ in AGES]] for k, name in INCOME]]], series=[name for _, name in AGES],
                    colours=["fuchsia", "navy", "teal", "orange"]),
        "T2.2": dict(kind="matrix", unit=["%", "%", ""], columns=["15-29", "65+", difference], plain=[2],
                     rows=[[WASTE_NAMES[k], [f"T2_2_{k}_15_29", f"T2_2_{k}_65plus", f"T2_2_{k}_gap"]] for k in ids.keys("T2_2_", "_gap", WASTE_NAMES)]),
        "2.7": dict(kind="vgrouped", panels=[["", [[name, [f"C2_7_{k}_{e}" for e in ("primary", "secondary", "tertiary")]] for k, name in INCOME]]],
                    series=["Primary", "Secondary", "Tertiary"], colours=["fuchsia", "navy", "teal"]),
        "3.1": separated("C3_1_", [(k, dict(REGIONS, **{"global": "Global"})[k]) for k in ids.keys("C3_1_", "_yes", dict(REGIONS, **{"global": "Global"}))]),
        "3.2": separated("C3_2_", INCOME),
        "T3.1": dict(kind="lists", lists=[["% Yes", top("T3_1_yes_")], ["% No", top("T3_1_no_")]]),
        "3.3": separated("C3_3_", AGES),
        "3.4": dict(kind="dumbbell", total_unit="", signed=True, series=[difference, "15-29", "65+"], colours=["navy", "fuchsia"],
                    rows=gap_rows(ids, "C3_4_", WASTE_NAMES, "15_29", "65plus", "Global mean")),
        "3.5": separated("C3_5_", (("women", "Women"), ("men", "Men"))),
        "3.6": dict(kind="vgrouped", panels=[["", [[name, [f"C3_6_{k}_{t}" for t in ("very", "somewhat", "not")]] for k, name in INCOME]]],
                    series=["Very serious threat", "Somewhat serious threat", "Not a threat at all"], colours=["fuchsia", "navy", "teal"]),
        "4.1": dict(kind="hbar", key=["Controlled disposal", "Uncontrolled disposal", "Other"], colours=["fuchsia", "navy", "grey"], label_width=0.42,
                    rows=[["Municipal government collects it", "C4_1_government", "Controlled disposal"],
                          ["Someone from the household takes it to landfill", "C4_1_landfill", "Uncontrolled disposal"],
                          ["Someone from the household burns it", "C4_1_burns", "Uncontrolled disposal"],
                          ["Someone from the household disposes of it in the street", "C4_1_street", "Uncontrolled disposal"],
                          ["Someone from a community group collects it", "C4_1_community", "Controlled disposal"],
                          ["Someone from a private company collects it", "C4_1_private", "Controlled disposal"],
                          ["Other", "C4_1_other", "Other"]]),
        "4.2": dict(kind="hbar", zero="<0.5", grey=["Global mean"], rows=rows_of(ids, "C4_2_", REGIONS, also={"global": "Global mean"})),
        "4.3": dict(kind="hbar", grey=["Global mean"], rows=rows_of(ids, "C4_3_", WASTE_NAMES, also={"global": "Global mean"})),
        "4.4": dict(kind="original", why=SCATTER),
        "5.1": dict(kind="hbar", grey=["Global mean"], rows=rows_of(ids, "C5_1_", REGIONS, also={"global": "Global mean"})),
        "5.2": dict(kind="vgrouped", panels=[["", [[name, [f"C5_2_{k}_{a}" for a, _ in AREAS]] for k, name in INCOME + (("mean", "Mean"),)]]],
                    series=[name for _, name in AREAS], colours=["fuchsia", "navy", "teal"]),
        "5.3": dict(kind="dumbbell", total_unit="", signed=True, series=[difference, "Rural", "Cities"], colours=["teal", "fuchsia"],
                    rows=gap_rows(ids, "C5_3_", REGIONS, "rural", "cities", "Mean")),
        "5.4": dict(kind="dumbbell", total_unit="", signed=True, series=[difference, "Rural", "Cities"], colours=["teal", "fuchsia"],
                    rows=gap_rows(ids, "C5_4_", WASTE_NAMES, "rural", "cities", "Mean")),
        "5.5": by_area("C5_5_", (("burns", burning["series"][0]), ("collected", burning["series"][1])), colours=burning["colours"]),
        "5.6": by_area("C5_6_", (("burns", burning["series"][0]), ("collected", burning["series"][1])), colours=burning["colours"]),
        "5.7": by_area("C5_7_", quintiles, colours=["fuchsia", "navy", "teal", "orange", "purple"]),
        "5.8": states("C5_8_", INDIA, "India"),
        "5.9": by_area("C5_9_", (("burns", burning["series"][0]), ("collected", burning["series"][1])), colours=burning["colours"]),
        "5.10": by_area("C5_10_", quintiles, colours=["fuchsia", "navy", "teal", "orange", "purple"]),
        "5.11": states("C5_11_", BRAZIL, "Brazil"),
        "6.1": dict(kind="stacked", series=[name for _, name in quadrants], colours=["fuchsia", "teal", "navy", "orange"],
                    rows=[[name, [f"C6_1_{k}_{q}" for q, _ in quadrants]] for k, name in (("global", "Global"),) + INCOME],
                    note_add="In the original, two of the segments carry a line of advice. Collected NOT separated: Education programmes to demonstrate value of separating waste, "
                             "coupled with adjustments to waste collection to support separated waste. NOT collected but separated: Focus on developing waste collection to support "
                             "existing sustainable household activities."),
        "T6.1": dict(kind="table", columns=["Country", "Percentage of households where waste is collected but not separated"], rows=top("T6_1_")),
        "T6.2": dict(kind="table", columns=["Country", "Percentage of households where waste is separated but not collected"], rows=top("T6_2_")),
        "6.2": dict(kind="original", why=SCATTER),
    }


plan(
    "2023_a_world_of_waste",
    folder="WRP_2023/core_a_world_of_waste", pdf="core_a_world_of_waste.pdf",
    title="A World of Waste", subtitle="Risks and opportunities in household waste management", published="September 2024",
    source="World Risk Poll 2024 Report: A World of Waste: Risks and opportunities in household waste management (Lloyd's Register Foundation, September 2024)",
    copyright=COPYRIGHT, cover_image=[0, 0], pages=[(1, 40), (41, 41)],
    chapters=[
        dict(big="3.8bn", caption="tonnes of municipal waste could be produced worldwide each year by 2050, up from more than **two billion** tonnes today"),
        dict(big="42%", caption="of people say plastic is the most common material in their household waste; **38%** say food"),
        dict(big="53%", caption="of people worldwide live in households that separate their waste before disposing of it; **40%** live in households that do not"),
        dict(big="14%", caption="of households worldwide burn their waste, and open burning is the most common form of disposal in **22** countries"),
        dict(big="56%", caption="of households worldwide have their waste collected: **71%** in cities and **38%** in rural areas"),
        dict(big="33%", caption="of households separate their waste and have it collected; **24%** do neither"),
        dict(big="1 in 7", caption="households globally burn their waste, and **two in five** do not separate it before disposing of it"),
    ],
    charts=waste, chart_note=WASTE_MEANS, drop=("Powered by",),
)


# -- Engineering Safer Workplaces

SEVENTH = "The original numbers its conclusion as chapter 7, though it is the fifth chapter of the report. The chapters are numbered in sequence here, so the conclusion is chapter 5."
WORK_NAMES = dict(COUNTRIES, COD="D.R. Congo", CIV="Cote d’Ivoire", GMB="The Gambia", PHL="Philippines*", VNM="Vietnam*", BRA="Brazil*", MAR="Morocco*")
INDUSTRY = {"fishing": "Fishing", "construction": "Construction", "mining": "Mining and quarrying", "agriculture": "Agriculture", "market_services": "Market services",
            "non_market_services": "Non-market services", "manufacturing": "Manufacturing", "electricity": "Electricity, gas or water supply"}
UNNUMBERED = "Occupational safety and health training rates among the current construction workforce, by region (% Yes)"


def workplaces(ids):
    trained = dict(series=["Past two years", "Not within the past two years or not sure when", "Never"], colours=["fuchsia", "teal", "navy"], gaps=NOT_PRINTED)
    harm = "Personally experienced harm at work in past two years"

    def training(prefix, names):
        return dict(kind="stacked", rows=[[name, [f if f in ids.ids else None for f in (f"{prefix}{k}_past2", f"{prefix}{k}_older", f"{prefix}{k}_never")]] for k, name in names], **trained)

    def named(prefix, suffix, names):
        return [(k, names[k]) for k in ids.keys(prefix, suffix, names)]

    africa = dict(COUNTRIES, COD="D.R. Congo")
    return {
        "2.1": dict(kind="hbar", rows=[["2019*", "C2_1_2019"], ["2021", "C2_1_2021"], ["2023", "C2_1_2023"]]),
        "2.2": dict(kind="grouped", rows=rows_of(ids, "C2_2_", REGIONS, ("2021", "2023")), **YEARS),
        "2.3": dict(kind="grouped", rows=[[name, [f"C2_3_{k}_2021", f"C2_3_{k}_2023"]] for k, name in INCOME], **YEARS),
        "T2.1": dict(kind="matrix", unit=["%", "%", ""], columns=["2021", "2023", "Percentage-point difference"], plain=[2],
                     rows=[[WORK_NAMES[k], [f"T2_1_{k}_2021", f"T2_1_{k}_2023", f"T2_1_{k}_diff"]] for k in ids.keys("T2_1_", "_diff", WORK_NAMES)]),
        "2.4": dict(kind="hbar", rows=sorted(([africa[k], f"C2_4_{k}"] for k in ids.keys("C2_4_", "", africa)), key=lambda r: -float(ids.values[r[1]])),
                    note_add=ON_A_MAP.format("Africa")),
        "2.5": dict(kind="grouped", rows=rows_of(ids, "C2_5_", REGIONS, ("harm", "worry")), series=[harm, "Worried about harm at work"], colours=["fuchsia", "navy"]),
        "2.6": dict(kind="hbar", rows=[["Not harmed", "C2_6_not_harmed"], ["Yes, know someone who has experienced", "C2_6_know_someone"],
                                       ["Yes, personally experienced", "C2_6_personally"], ["Both", "C2_6_both"]]),
        "2.7": dict(kind="original", why="the original plots each risk without printing its values"),
        "2.8": dict(kind="hbar", grey=["Global mean"], row=58, rows=[
            ["Global mean", "C2_8_global"],
            ["Gender", None], ["Men", "C2_8_men"], ["Women", "C2_8_women"],
            ["Age", None], ["15-29", "C2_8_age_15_29"], ["30-49", "C2_8_age_30_49"], ["50-64", "C2_8_age_50_64"], ["65+", "C2_8_age_65plus"],
            ["Education", None], ["Primary", "C2_8_primary"], ["Secondary", "C2_8_secondary"], ["Tertiary", "C2_8_tertiary"],
            ["Financial resilience", None], ["Less than a week", "C2_8_less_week"], ["Between a week and a month", "C2_8_week_month"], ["A month or more", "C2_8_month_plus"]]),
        "2.9": dict(kind="hbar", rows=[["Full time for an employer", "C2_9_ft_employer"], ["Full time for self", "C2_9_ft_self"], ["Part time", "C2_9_part_time"],
                                       ["Unemployed (in workforce)", "C2_9_unemployed"]]),
        "2.10": dict(kind="hbar", grey=["Global mean"],
                     rows=rows_of(ids, "C2_10_", dict(INDUSTRY, agriculture="Agriculture (excluding fishing)", market_services="Market services*",
                                                      non_market_services="Non-market services**"), also={"global": "Global mean"})),
        "2.11": dict(kind="original", why="the original plots each industry without printing its values"),
        "2.12": dict(kind="grouped", rows=rows_of(ids, "C2_12_", INDUSTRY, ("women", "men")), series=["Women", "Men"], colours=["fuchsia", "navy"]),
        "2.13": dict(kind="vgrouped", panels=[["", [[name, [f"C2_13_{k}_{i}" for i in ("construction", "agriculture", "market_services", "non_market_services", "manufacturing")]]
                                                    for k, name in INCOME]]],
                     series=["Construction", "Agriculture", "Market services", "Non-market services", "Manufacturing"], colours=["fuchsia", "navy", "teal", "orange", "purple"]),
        "3.1": dict(kind="original", why="the original plots each region without printing its values"),
        "3.2": dict(kind="hbar", rows=[["Full-time for an employer", "C3_2_ft_employer"], ["Part-time", "C3_2_part_time"], ["Self-employed", "C3_2_self_employed"]]),
        "3.3": dict(kind="original", why="the original plots each industry without printing its values", note=None),
        "4.1": training("C4_1", [("", "Global")]),
        "4.2": training("C4_2_", INCOME),
        "4.3": training("C4_3_", named("C4_3_", "_past2", REGIONS)),
        "T4.1": dict(kind="lists", lists=[["Top 10 countries: Proportion trained in last two years (%)", [[WORK_NAMES[k].rstrip("*"), f"T4_1_{k}"] for k in ids.keys("T4_1_", "", WORK_NAMES)[:10]]],
                                          ["Bottom 10 countries: Proportion NOT trained in last two years (%)", [[WORK_NAMES[k].rstrip("*"), f"T4_1_{k}"] for k in ids.keys("T4_1_", "", WORK_NAMES)[10:]]]]),
        "4.4": training("C4_4_", (("poorest", "Poorest 20%"), ("second", "Second 20%"), ("middle", "Middle 20%"), ("fourth", "Fourth 20%"), ("richest", "Richest 20%"),
                                  ("primary", "Primary"), ("secondary", "Secondary"), ("tertiary", "Tertiary"))),
        "4.5": training("C4_5_", named("C4_5_", "_past2", dict(INDUSTRY, electricity="Electricity, gas, or water supply"))),
        "4.6": training("C4_6_", named("C4_6_", "_past2", REGIONS)),
        "4.7": dict(kind="hbar", unit="x", decimals=1, rows=[["Training in last two years", "C4_7_past2"], ["Training not within the last two years or not sure when", "C4_7_older"]]),
    }


plan(
    "2023_engineering_safer_workplaces",
    folder="WRP_2023/core_engineering_safer_workplaces", pdf="core_engineering_safer_workplaces.pdf",
    title="Engineering Safer Workplaces", subtitle="Global trends in occupational safety and health", published="October 2024",
    source="World Risk Poll 2024 Report: Engineering Safer Workplaces: Global trends in occupational safety and health (Lloyd's Register Foundation, October 2024)",
    copyright=COPYRIGHT, cover_image=[0, 0], pages=[(1, 29), (30, 30)],
    chapters=[
        dict(big="142", caption="countries and territories were covered by the 2023 World Risk Poll, in nearly **147,000** interviews"),
        dict(big="18%", caption="of the current global workforce, around **667 million** adults, have personally experienced serious harm at work in the past two years"),
        dict(big="51%", caption="of the current workforce who experienced harm at work in the past two years say they reported the incident"),
        dict(big="62%", caption="of those currently in the workforce report having never received occupational safety and health training about the risks of their work"),
        dict(big="3.3x", caption="higher odds of reporting harm among workers trained in the past two years than among those never trained; **1.8** times for those trained longer ago"),
    ],
    charts=workplaces, drop=("Powered by",), numbers={UNNUMBERED: "Chart 4.6"}, numbering_note=SEVENTH,
    edits=["Chart 4.6 is printed without its number in the original. It is numbered here as the charts before and after it require.",
           "Under Chart 3.3 the original prints a broken line, ‘(3?’, where a second question text should be. It is left out."],
)


# -- What the World Worries About

WORRY_NAMES = dict(COUNTRIES, COD="D.R. Congo", TUR="Turkey")
RISKS = {"traffic": "Traffic/roadside accidents", "weather": "Severe weather events", "crime": "Violent crime", "food": "The food you eat", "mental": "Mental health issues",
         "work": "Work", "water": "The water you drink"}
EXPERIENCE = (("none", "No experience"), ("know", "Yes, know someone who has experienced"), ("personal", "Yes, personally experienced"), ("both", "Both"))
PLOT = "the original plots every {} without printing its values"


def worries(ids):
    worried = dict(series=["Very worried", "Somewhat worried"], colours=["fuchsia", "teal"], extra="Total")
    threat = ["Very serious threat", "Somewhat serious threat", "Don’t know/Refused", "Not a threat at all"]
    polls = ["2019", "2021", "2023"]
    short = dict(RISKS, traffic="Traffic accidents", mental="Mental health")

    def have(*fids):
        return [f if f in ids.ids else None for f in fids]

    def changed(prefix, names, **more):
        keys = [k for k in ids.keys(prefix, "_chg", names)]
        return dict(kind="hbar", rows=[[names[k], f"{prefix}{k}"] for k in keys], texts=[f"{prefix}{k}_chg" for k in keys], extra="Change since 2021", **more)

    def movers(kind_, word):
        keys = ids.keys(f"C2_6_{kind_}_", "_chg", WORRY_NAMES)
        about = "who worry about" if kind_ == "worry" else "with personal experience of"
        return dict(kind="dumbbell", heading=f"Proportion respondents {about}, experiencing serious harm from traffic accidents (%)", total_unit="", signed=True, series=["Change, 2021-2023", f"2021, {word}", f"2023, {word}"], colours=["teal", "fuchsia"],
                    rows=[[WORRY_NAMES[k], [f"C2_6_{kind_}_{k}_chg", f"C2_6_{kind_}_{k}_2021", f"C2_6_{kind_}_{k}_2023"]] for k in keys])

    def by_experience(prefix):
        return dict(kind="hbar", rows=[[name, f"{prefix}{k}"] for k, name in EXPERIENCE])

    def index(prefix):
        return dict(kind="grouped", unit="", rows=rows_of(ids, prefix, REGIONS, ("2021", "2023")), **YEARS)

    return {
        "2.1": changed("C2_1_", {"road": "Road-related accidents/injuries", "crime": "Crime/violence", "health": "Personal health", "dk": "Don’t know", "nothing": "Nothing/no risk",
                                 "economy": "Economy", "climate": "Climate change or severe weather", "financial": "Financial", "other": "Other", "war": "War/terrorism"}),
        "2.2": changed("C2_2_", REGIONS),
        "2.3": dict(kind="stacked", rows=[[RISKS[k], [f"C2_3_{k}_very", f"C2_3_{k}_somewhat"], f"C2_3_{k}_total"] for k in ids.keys("C2_3_", "_very", RISKS)], extra_unit="%", **worried),
        "2.4": dict(kind="original", why=PLOT.format("region")),
        "2.5": dict(kind="grouped", unit="", rows=[["Personal experience", ["C2_5_experience_decrease", "C2_5_experience_increase"]], ["Worry", ["C2_5_worry_decrease", "C2_5_worry_increase"]]],
                    series=["Decrease", "Increase"], colours=["navy", "fuchsia"]),
        "2.6": dict(kind="parts", parts=[movers("worry", "worry"), movers("experience", "personal experience")]),
        "2.7": dict(kind="stacked", rows=[[name, [f"C2_7_{k}_very", f"C2_7_{k}_somewhat"], f"C2_7_{k}_total"] for k, name in EXPERIENCE], extra_unit="%", **worried),
        "2.8": by_experience("C2_8_"),
        "2.9": by_experience("C2_9_"),
        "2.10": by_experience("C2_10_"),
        "2.11": dict(kind="original", why=PLOT.format("country")),
        "3.1": dict(kind="original", why="it plots temperature records that are not part of the poll"),
        "3.2": dict(kind="line", years=polls, colours=["fuchsia", "teal", "navy", "grey"],
                    rows=[[name, [f"C3_2_{k}_{y}" for y in polls]] for k, name in (("very", "Very serious threat"), ("somewhat", "Somewhat serious threat"), ("not", "Not a threat at all"),
                                                                                    ("dk", "Don’t know/Refused"))]),
        "3.3": dict(kind="stacked", gaps=NOT_PRINTED, series=threat, colours=["fuchsia", "teal", "grey", "navy"], extra="Combined threat*", extra_unit="%",
                    rows=[[REGIONS[k], have(*(f"C3_3_{k}_{t}" for t in ("very", "somewhat", "dk", "not"))), f"C3_3_{k}_combined"] for k in ids.keys("C3_3_", "_very", REGIONS)]),
        "T3.1": dict(kind="matrix", unit="", columns=["Change in ‘very serious threat’", "Change in ‘somewhat serious threat’", "Change in ‘not a threat at all’", "Change in ‘DK’"],
                     plain=[0, 1, 2, 3], rows=[[REGIONS[k], [f"T3_1_{k}_{t}" for t in ("very", "somewhat", "not", "dk")]] for k in ids.keys("T3_1_", "_very", REGIONS)]),
        "3.4": dict(kind="line", years=polls, colours=["fuchsia", "teal"], rows=[["China", [f"C3_4_china_{y}" for y in polls]], ["Rest of world", [f"C3_4_rest_{y}" for y in polls]]]),
        "3.5": dict(kind="stacked", series=threat[:2], colours=["fuchsia", "teal"], extra="Total", extra_unit="%",
                    rows=[[WORRY_NAMES[k], [f"C3_5_{k}_very", f"C3_5_{k}_somewhat"], f"C3_5_{k}_total"] for k in ids.keys("C3_5_", "_very", WORRY_NAMES)]),
        "3.6": dict(kind="hbar", colour="navy", rows=[[WORRY_NAMES[k], f"C3_6_{k}"] for k in ids.keys("C3_6_", "", WORRY_NAMES)]),
        "3.7": dict(kind="hbar", colour="orange", rows=[[WORRY_NAMES[k], f"C3_7_{k}"] for k in ids.keys("C3_7_", "", WORRY_NAMES)]),
        "3.8": dict(kind="hbar", unit="x", decimals=1, rows=[["Very worried", "C3_8_very"], ["Somewhat worried", "C3_8_somewhat"]]),
        "3.9": dict(kind="hbar", unit="x", decimals=1, rows=[["Tertiary education", "C3_9_tertiary"], ["Secondary education", "C3_9_secondary"]]),
        "4.1": dict(kind="line", years=polls, colours=["fuchsia", "teal", "navy"],
                    rows=[[name, [f"C4_1_{k}_{y}" for y in polls]] for k, name in (("less", "Less safe"), ("about", "About as safe"), ("more", "More safe"))]),
        "4.2": dict(kind="stacked", gaps=NOT_PRINTED, series=["Less safe", "Don’t know", "About as safe", "More safe"], colours=["fuchsia", "grey", "teal", "navy"],
                    rows=[[REGIONS[k], [f"C4_2_{k}_less", None, f"C4_2_{k}_about", f"C4_2_{k}_more"]] for k in ids.keys("C4_2_", "_less", REGIONS)]),
        "4.3": dict(kind="original", why=PLOT.format("region")),
        "4.4": dict(kind="vgrouped", panels=[["", [[short[k], have(*(f"C4_4_{k}_{y}" for y in polls))] for k in ids.keys("C4_4_", "_2023", RISKS)]]], series=polls,
                    colours=["teal", "navy", "fuchsia"]),
        "4.5": dict(kind="grouped", rows=rows_of(ids, "C4_5_", dict(short, weather="Severe weather events"), ("2021", "2023")), **YEARS),
        "4.6": index("C4_6_"),
        "4.7": index("C4_7_"),
        "4.8": dict(kind="dumbbell", unit="", series=["", "Experience index", "Worry index"], colours=["teal", "fuchsia"],
                    rows=[[REGIONS[k], [None, f"C4_8_{k}_experience", f"C4_8_{k}_worry"]] for k in ids.keys("C4_8_", "_worry", REGIONS)]),
    }


plan(
    "2023_what_the_world_worries_about",
    folder="WRP_2023/core_what_the_world_worries_about", pdf="core_what_the_world_worries_about.pdf",
    title="What the World Worries About", subtitle="Global perceptions and experiences of risk and harm", published="November 2024",
    source="World Risk Poll 2024 Report: What the World Worries About: Global perceptions and experiences of risk and harm (Lloyd's Register Foundation, November 2024)",
    copyright=COPYRIGHT, cover_image=[0, 0], pages=[(1, 34), (35, 35)],
    chapters=[
        dict(big="142", caption="countries and territories were covered by the 2023 World Risk Poll, in nearly **147,000** interviews"),
        dict(big="16%", caption="of the world's adult population say road-related accidents are the single greatest risk to safety in their daily lives, compared with **13%** in 2021"),
        dict(big="72%", caption="of the world's adult population say they feel very or somewhat threatened by climate change in the next 20 years"),
        dict(big="26%", caption="of people feel less safe than they did five years ago; **37%** feel more safe and **37%** about as safe"),
        dict(big="55%", caption="of people worry about being harmed by mental health issues, up from **48%** in 2019 and **52%** in 2021"),
    ],
    charts=worries, drop=("Powered by",), numbering_note=SEVENTH,
    edits=["Chart 2.6 of the original spells Thailand ‘Thaliand’ in its lower half. The name is spelt correctly here."],
)


# -- Focus On: Risk perceptions and experiences of ocean workers

UNNUMBERED_CHARTS = ("The original does not number its charts. They are numbered here by chapter, in the order of the original, as the repository's file of published figures "
                     "numbers them. Each chart's title is the heading the original sets over it, and the sentence under the title is the original's own.")
OCEAN_CHARTS = {
    "Rising ocean heat content fuels more intense storms": "Figure 1.1",
    "Ocean workers more likely to view climate change as a risk to their personal safety": "Chart 1.1",
    "Ocean workers more likely to view climate change as a very serious threat…": "Chart 1.2",
    "Ocean workers more worried about experiencing harm from severe weather events": "Chart 1.3",
    "Ocean workers more likely to have experienced harm from severe weather events": "Chart 1.4",
    "Ocean workers more likely to view work related accidents as their greatest source of daily risk": "Chart 2.1",
    "Ocean workers have very high levels of concern about experiencing workplace harm": "Chart 2.2",
    "Ocean workers have the highest personal experience of workplace harm compared with other sectors": "Chart 2.3",
    "Ocean workers less likely to have received OSH training in their role": "Chart 2.4",
    "Ocean workers are less likely to tell someone about their experience of workplace harm": "Chart 2.5",
}


def ocean(ids):
    two = (("ocean", "Ocean workers"), ("other", "All other workers"))
    sectors = dict(INDUSTRY, ocean="Ocean workers", agriculture="Agriculture (excluding fishing)", market_services="Market services*", non_market_services="Non-market services**",
                   utilities="Electricity, gas or water supply")

    def pair(prefix):
        return dict(kind="hbar", rows=[[name, f"{prefix}{k}"] for k, name in two])

    return {
        "F1.1": dict(kind="original", clip=[18, 262, 600, 506], blank=[], why="it plots records of cyclones and sea temperature that are not part of the poll"),
        "1.1": pair("C1_1_"),
        "1.2": dict(kind="stacked", series=["Very serious threat", "Somewhat serious threat", "Don’t know/Refused", "Not a threat at all"], colours=["fuchsia", "teal", "grey", "navy"],
                    rows=[[name, [f"C1_2_{k}_{t}" for t in ("very", "somewhat", "dk", "not")]] for k, name in two]),
        "1.3": dict(kind="stacked", series=["Very worried", "Somewhat worried"], colours=["fuchsia", "navy"], rows=[[name, [f"C1_3_{k}_very", f"C1_3_{k}_somewhat"]] for k, name in two]),
        "1.4": pair("C1_4_"),
        "2.1": pair("C2_1_"),
        "2.2": dict(kind="stacked", series=["Very worried", "Somewhat worried"], colours=["fuchsia", "navy"],
                    rows=[[sectors[k], [f"C2_2_{k}_very", f"C2_2_{k}_somewhat"]] for k in ids.keys("C2_2_", "_very", sectors)]),
        "2.3": dict(kind="hbar", grey=["Global mean"], rows=rows_of(ids, "C2_3_", sectors, also={"global": "Global mean"})),
        "2.4": dict(kind="stacked", series=["Received OSH training in last 2 years", "Received OSH training, more than 2 years ago"], colours=["fuchsia", "navy"],
                    rows=[[name, [f"C2_4_{k}_recent", f"C2_4_{k}_older"]] for k, name in two]),
        "2.5": pair("C2_5_"),
    }


plan(
    "2023_focus_ocean_workers",
    folder="WRP_2023/focus_on_ocean_workers", pdf="focus_on_ocean_workers.pdf", focus=True,
    title="Focus On", subtitle="Risk perceptions and experiences of ocean workers", running_title="Focus On: Risk perceptions and experiences of ocean workers",
    published="June 2025",
    source="World Risk Poll 2024 Focus On: Risk perceptions and experiences of ocean workers (Lloyd's Register Foundation, June 2025), doi:10.60743/xjn7-9x64",
    copyright="Copyright © 2025 Lloyd's Register Foundation. All rights reserved.", cover_image=[0, 0], pages=[(1, 10)],
    as_chapters=("Climate change and ocean workers: escalating environmental risks", "The cost of work at sea: exposure to harm without adequate support", "Conclusion"),
    inside=("Calls to action",), numbers=OCEAN_CHARTS, numbering_note=UNNUMBERED_CHARTS, small_text=(10,),
    chapters=[
        dict(big="17%", caption="of ocean workers name climate change as the greatest risk to their personal safety, almost three times the share of other workers"),
        dict(big="25%", caption="of ocean workers have been harmed by their work in the past two years, the highest rate of any sector"),
        dict(big="41%", caption="of ocean workers who experienced harm at work reported it, compared with **51%** of other workers"),
    ],
    charts=ocean, drop=("Powered by",),
    # the callout beside the chart of cyclone activity: a box
    replace={"# North Atlantic Tropical Cyclone Activity": "::box North Atlantic Tropical Cyclone Activity",
             "storm frequency and intensity.*\n\n": "storm frequency and intensity.*\n\n::endbox\n\n"},
)


# -- Focus On: Migration in a warming world

CHORD = "it is a chord diagram, with the report's commentary set around it"


def migration(ids):
    coping = ["Less than a month", "A month or more"]
    concern = (("very", "Very serious threat"), ("somewhat", "Somewhat serious threat"), ("not", "Not a threat"))
    polls = ("2019", "2021", "2023")
    gains = (("readiness", "ND-GAIN Readiness score difference (Destination - Origin)"), ("vulnerability", "ND-GAIN Vulnerability score difference (Destination - Origin)"))

    def pair(rows):
        """The two sub-scores, one under the other: gains in readiness to the right of nought, falls in vulnerability to the left."""
        out = []
        for g, name in gains:
            out += [[name, None]] + rows(g)
        return dict(kind="diverging", unit="", decimals=2, row=58, series=["", ""], colours=["navy", "fuchsia"], rows=out)

    return {
        "1": dict(kind="stacked", series=["Less than a week", "Less than a month", "Don’t know/Refused", "A month or more"], colours=["fuchsia", "teal", "grey", "navy"],
                  rows=[[y, [f"C2_1_{k}_{y}" for k in ("week", "month", "dk", "more")]] for y in ("2021", "2023")]),
        "2": dict(kind="grouped", decimals=1, rows=[["Personal finances", ["C2_2_personal_finances_2021", "C2_2_personal_finances_2023"]],
                                                    ["Economic risk", ["C2_2_economy_2021", "C2_2_economy_2023"]]], **YEARS),
        "3": dict(kind="stacked", series=["Very serious threat", "Somewhat serious threat", "Don’t know/Refused", "Not a threat"], colours=["fuchsia", "teal", "grey", "navy"],
                  rows=[[y, [f"C2_3_{k}_{y}" for k in ("very", "somewhat", "dk", "not")]] for y in polls]),
        "4": dict(kind="hbar", decimals=1, rows=[["2021", "C2_4_2021"], ["2023", "C2_4_2023"]]),
        "5": dict(kind="hbar", rows=[[name, f"C3_5_{k}"] for k, name in concern]),
        "6": dict(kind="hbar", rows=[[coping[0], "C3_6_less"], [coping[1], "C3_6_more"]]),
        "7": dict(kind="grouped", rows=[[name, [f"C3_7_{k}_less", f"C3_7_{k}_more"]] for k, name in concern], series=coping, colours=["fuchsia", "teal"]),
        "8": dict(kind="original", why=CHORD),
        "9": dict(kind="original", why=CHORD),
        "10": dict(kind="original", why=CHORD),
        "11a": dict(kind="hbar", unit="", decimals=1, rows=[["Very serious threat", "C5_11a_very"], ["Not a threat", "C5_11a_not"]]),
        "11b": pair(lambda g: [["Very serious threat", f"C5_11b_{g}_very"], ["Not a threat", f"C5_11b_{g}_not"]]),
        "12a": dict(kind="hbar", unit="", decimals=1, rows=[[coping[0], "C5_12a_less"], [coping[1], "C5_12a_more"]]),
        "12b": pair(lambda g: [[coping[0], f"C5_12b_{g}_less"], [coping[1], f"C5_12b_{g}_more"]]),
        "13a": dict(kind="grouped", unit="", decimals=1, rows=[[name, [f"C5_13a_{k}_less", f"C5_13a_{k}_more"]] for k, name in (concern[0], concern[2])],
                    series=coping, colours=["fuchsia", "teal"]),
        "13b": pair(lambda g: [[f"{name}, {cope.lower()}", f"C5_13b_{g}_{k}_{c}"] for k, name in (concern[0], concern[2]) for c, cope in zip(("less", "more"), coping)]),
        "14": dict(kind="original", why="it plots the coefficients of a regression, whose values the original does not print"),
    }


plan(
    "2023_focus_migration",
    folder="WRP_2023/focus_on_migration_in_a_warming_world", pdf="focus_on_migration_in_a_warming_world.pdf", focus=True,
    title="Focus On", subtitle="Migration in a warming world", running_title="Focus On: Migration in a warming world", published="May 2026",
    source="World Risk Poll 2024 Focus On: Migration in a warming world (Lloyd's Register Foundation Global Safety Evidence Centre, May 2026), https://doi.org/10.60743/5ppn-nc25",
    copyright="Copyright © 2026 Lloyd's Register Foundation. All rights reserved.", cover_image=[0, 0], pages=[(1, 18)], small_text=(18,), box_gap=14.5,
    chapters=[
        dict(big="6%", caption="of people saw climate change and severe weather as the biggest threat to their personal safety in 2023, the highest level since the Poll began"),
        dict(big="13%", caption="of people in 2023 said their household could cover its basic needs for less than a week without income, and a further **24%** for less than a month"),
        dict(big="15%", caption="of people who see climate change as a very serious threat would like to move permanently to another country, against **8%** of those who see no threat"),
        dict(big="27%", caption="of would-be migrants who see climate change as a threat name Northern America as their preferred destination, against **15%** of those who do not"),
        dict(big="19.0", caption="points is the average gain in ND-GAIN score sought by would-be migrants who could not cope for a month without income, against **16.2** for those who could"),
        dict(big="12%", caption="of people who could not cope for a month without income would like to migrate, against **8%** of those who could"),
    ],
    charts=migration, drop=("Powered by",),
)
