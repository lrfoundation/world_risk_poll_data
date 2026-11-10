"""What goes in the book: the four polls and the 22 reports.

Every number shown in the book is a published figure. Text refers to a figure as
{FINDING_ID}, where the ID is a row of that report's published_figures.csv, and
build.py puts the printed value in its place. Nothing here is typed in by hand,
so a figure cannot drift from its report. The only values that are not published
figures are the country values on the maps, which maps.py computes from the
public data.

Format of a reference: {ID} prints the value as the report printed it,
{ID:words} prints a large count in words (600 million), {ID:abs} drops the sign.
"""

# Colours are the World Risk Poll 2026 report palette (wrp_style.py). Editions keep
# one colour each: 2021 fuchsia, 2023 green, 2025 teal. 2019 has no edition colour
# in the house style, so it takes navy.
FUCHSIA, GREEN, TEAL = "#E3076E", "#00785C", "#00A7B3"
ORANGE, PURPLE, LIME, RED = "#F07800", "#7B50DE", "#8CAB00", "#BF153D"
GREY, NAVY, INK = "#BDBDBD", "#0D2240", "#231F20"

WAVES = {
    2019: dict(
        colour=NAVY, text=NAVY, on="#FFFFFF", respondents="154,195", countries=142,
        brand="World Risk Poll 2019",
        blurb="The first poll. One full report covered every theme, from feeling safe to food, work, "
              "climate and technology. It appears here as four parts, so that it sits alongside the "
              "four core reports of each later poll.",
    ),
    2021: dict(
        colour=FUCHSIA, text=FUCHSIA, on="#FFFFFF", respondents="125,911", countries=121,
        brand="World Risk Poll 2021",
        blurb="Fieldwork ran during the Covid-19 pandemic. Four core reports followed, on risk in the "
              "Covid age, resilience, the digital world and violence and harassment at work, and then "
              "the first Focus On reports.",
    ),
    2023: dict(
        colour=GREEN, text=GREEN, on="#FFFFFF", respondents="146,910", countries=142,
        brand="World Risk Poll 2024",
        blurb="Resilience was measured for a second "
              "time, and new questions covered household waste and safety training at work.",
    ),
    2025: dict(
        colour=TEAL, text=NAVY, on=NAVY, respondents="143,459", countries=140,
        brand="World Risk Poll 2026",
        blurb="New questions asked what people think "
              "others believe about climate change, about heat, drought, wildfire and air, and about "
              "early warnings before disasters.",
    ),
}

# The 2019 full report as four parts. Chapters are those of the published report.
SPLIT_2019 = [
    ("2019_feeling_safe", "Feeling safe and the sources of risk", [1, 2, 3, 4, 10]),
    ("2019_risk_at_work", "Risk at work", [5]),
    ("2019_climate_food_water", "Climate change, food and water", [6, 9]),
    ("2019_technology", "Technology and the internet", [7, 8]),
]

F2019 = "WRP_2019/core_world_risk_poll_2019"
SAFETY = [("More safe", GREEN), ("About as safe", TEAL), ("Less safe", FUCHSIA), ("Don't know or refused", GREY)]

REPORTS = [
    # ------------------------------------------------------------------ 2019
    dict(
        key="2019_feeling_safe", wave=2019, type="core", folder=F2019, published="2020",
        title="Feeling safe and the sources of risk",
        subtitle="Part 1 of 4 of the 2019 full report: chapters 1 to 4 and 10",
        lede="The first World Risk Poll asked about {E01} people in {E02} countries and territories how safe they "
             "felt and what threatened them most. More people felt safer than five years earlier "
             "({C1_1_more}%) than felt less safe ({C1_1_less}%), but in low-income countries "
             "{C1_2_low_less}% felt less safe, the highest of any income group. Asked for the two greatest "
             "risks in their daily lives, people named road accidents most often, ahead of crime and "
             "personal health.",
        hero=("C1_1_less", "of people felt less safe than they had five years earlier"),
        stats=[
            ("C1_1_more", "felt more safe than five years earlier"),
            ("C1_2_low_less", "felt less safe in low-income countries, the highest of the four income groups"),
            ("C2_1_road", "named road-related accidents among their two greatest risks, the most common answer"),
            ("E07", "said they faced no risk when first asked for the greatest risk to their safety"),
            ("X4_01", "wear a seat belt in a motor vehicle when one is available"),
            ("X4_08_authority", "trust their government food safety agency most for information about food safety"),
        ],
        charts=[
            dict(kind="stacked", title="In low-income and high-income countries, more people felt less safe than felt safer",
                 question="Compared to five years ago, do you feel more safe, less safe or about as safe?",
                 note="Chart 1.2 of the report. The grey segment is the remainder: don't know or refused.",
                 segments=SAFETY, remainder=True,
                 rows=[("Low income", ["C1_2_low_more", "C1_2_low_same", "C1_2_low_less"]),
                       ("Lower-middle income", ["C1_2_lower_middle_more", "C1_2_lower_middle_same", "C1_2_lower_middle_less"]),
                       ("Upper-middle income", ["C1_2_upper_middle_more", "C1_2_upper_middle_same", "C1_2_upper_middle_less"]),
                       ("High income", ["C1_2_high_more", "C1_2_high_same", "C1_2_high_less"])]),
            dict(kind="hbar", title="Road accidents, crime and personal health were the risks people named most often",
                 question="In your own words, what is the greatest source of risk to your safety in your daily life? "
                          "Other than what you just mentioned, what is another major source of risk?",
                 note="Chart 2.1 of the report: first and second answers combined. {C2_1_none}% named no risk in at least one of their two answers.",
                 rows=[("Road-related accidents", "C2_1_road"), ("Crime, violence or terrorism", "C2_1_crime"),
                       ("Personal health", "C2_1_health"), ("The economy", "C2_1_economy"),
                       ("Not having enough money", "C2_1_financial"), ("Climate, disasters or weather", "C2_1_climate"),
                       ("Cooking or household accidents", "C2_1_cooking"), ("Work-related accidents", "C2_1_work")]),
        ],
        map=dict(fn="less_safe_2019", unit="%", title="Where people felt less safe than five years earlier",
                 sub="Share of adults who said they felt less safe than five years ago, 2019"),
    ),
    dict(
        key="2019_risk_at_work", wave=2019, type="core", folder=F2019, published="2020",
        title="Risk at work",
        subtitle="Part 2 of 4 of the 2019 full report: chapter 5",
        lede="{X5_02}% of workers worldwide said they had been seriously injured at work at some point, "
             "roughly {X5_03:words} people. The risk falls unevenly. {X5_04}% of farmers, farm workers and "
             "fishers had been seriously injured, against {C5_3_clerical}% of clerical workers, and workers "
             "in low-income countries ({X5_12_low}%) were about twice as likely to have been hurt as those "
             "in high-income countries ({X5_12_high}%).",
        hero=("X5_02", "of workers have been seriously injured while working"),
        stats=[
            ("X5_14", "of workers in Sierra Leone have been seriously injured at work, the highest of any country"),
            ("X5_15_men", "of working men have been seriously injured, against {X5_15_women}% of working women"),
            ("X5_06", "of workers in France named physical violence and harassment as a risk at work"),
            ("E15", "of working women in Zambia had experienced harm from violence or harassment at work"),
            ("X5_10_difficult", "of workers who say safety rules make the job harder have been seriously injured, against {X5_10_good}% of those who call the rules a good thing"),
            ("X5_11_edu_16plus", "of workers with 16 or more years of education say safety rules are a good thing, against {X5_11_edu_0_8}% of those with eight years or fewer"),
        ],
        charts=[
            dict(kind="hbar", title="Agricultural workers were the most likely to have been seriously injured at work",
                 question="Have you ever been seriously injured while working?",
                 note="Chart 5.3 of the report. Asked of people in work.",
                 rows=[("Agricultural labourer", "C5_3_farmer"), ("Construction or manufacturing", "C5_3_construction"),
                       ("Business owner", "C5_3_business_owner"), ("Vendor or trader", "C5_3_vendor"),
                       ("Hired worker", "C5_3_service"), ("Professional", "C5_3_professional"),
                       ("Hired manager or official", "C5_3_manager"), ("Clerical worker", "C5_3_clerical")]),
        ],
        map=dict(fn="injured_at_work_2019", unit="%", title="Where workers had been seriously injured",
                 sub="Share of workers who have ever been seriously injured while working, 2019"),
    ),
    dict(
        key="2019_climate_food_water", wave=2019, type="core", folder=F2019, published="2020",
        title="Climate change, food and water",
        subtitle="Part 3 of 4 of the 2019 full report: chapters 6 and 9",
        lede="{X6_01}% of people saw climate change as a very serious threat to their country over the next "
             "20 years, and a further {X6_02}% as a somewhat serious one. Yet {X6_06}% had no view at all and "
             "{X6_03}% saw no threat. Closer to home, {X9_01}% said they or someone they knew had been "
             "seriously harmed by the food they ate in the past two years, and {X9_02}% by the water they drank.",
        hero=("X6_01", "of people saw climate change as a very serious threat to their country in the next 20 years"),
        stats=[
            ("X6_09", "saw a very serious threat in Southern Europe, the highest of any region"),
            ("X6_05", "of people in the United States said climate change was not a threat at all"),
            ("X6_11", "of people with 16 or more years of education saw a very serious threat, against {X6_12}% of those with eight years or fewer"),
            ("X9_01", "had experienced serious harm from food, themselves or through someone they knew"),
            ("X9_24", "said their government does a good job of ensuring the food they buy is safe"),
            ("X9_23", "said their government does a good job of ensuring the water they drink is safe"),
        ],
        charts=[
            dict(kind="hbar", title="Concern about climate change was highest in Southern Europe and Latin America",
                 question="Do you think that climate change is a very serious threat, a somewhat serious threat, or not a "
                          "threat at all to the people in this country in the next 20 years?",
                 note="Chart 6.2 of the report: share answering 'very serious threat', by region.",
                 rows=[("Southern Europe", "C6_2_southern_europe_very"), ("Latin America and Caribbean", "C6_2_latin_america_very"),
                       ("Southern Africa", "C6_2_southern_africa_very"), ("Northern and Western Europe", "C6_2_northern_western_europe_very"),
                       ("Australia and New Zealand", "C6_2_australia_nz_very"), ("Northern America", "C6_2_northern_america_very"),
                       ("Eastern Europe", "C6_2_eastern_europe_very"), ("Central and Western Africa", "C6_2_central_western_africa_very"),
                       ("Eastern Africa", "C6_2_east_africa_very"), ("Southeastern Asia", "C6_2_southeastern_asia_very"),
                       ("Middle East", "C6_2_middle_east_very"), ("Southern Asia", "C6_2_southern_asia_very"),
                       ("Central Asia", "C6_2_central_asia_very"), ("Eastern Asia", "C6_2_eastern_asia_very"),
                       ("Northern Africa", "C6_2_northern_africa_very")]),
        ],
        map=dict(fn="climate_very_serious_2019", unit="%", title="Where climate change was seen as a very serious threat",
                 sub="Share of adults who said climate change is a very serious threat to people in their country in the next 20 years, 2019"),
    ),
    dict(
        key="2019_technology", wave=2019, type="core", folder=F2019, published="2020",
        title="Technology and the internet",
        subtitle="Part 4 of 4 of the 2019 full report: chapters 7 and 8",
        lede="The 2019 poll asked whether three technologies would mostly help or mostly harm people over "
             "the next 20 years. Opinion on artificial intelligence and nuclear power leaned towards help. "
             "Genetically modified food was the exception: {X7_01}% expected harm and {X7_02}% expected help. "
             "Online, {X8_08}% of people had used the internet in the past month, and {X8_01}% of those users "
             "worried about receiving false information.",
        hero=("X8_01", "of internet users worried about receiving false information online"),
        stats=[
            ("X8_02", "of internet users worried about online fraud"),
            ("X8_03", "of internet users worried about online bullying"),
            ("X8_09", "of people in Northern America had used the internet in the past month, against {X8_10}% in Eastern Africa"),
            ("X7_03", "of people in low-income countries expected genetically modified food to help, against {X7_04}% in high-income countries"),
            ("X7_15", "of people in Southern Europe expected nuclear power to mostly harm"),
            ("X8_19_PRT", "of internet users in Portugal worried about online fraud, the highest of any country"),
        ],
        charts=[
            dict(kind="stacked", title="Genetically modified food was the only one of three technologies that more people expected to harm than to help",
                 question="Do you think each of the following will mostly help or mostly harm people in this country in the next 20 years?",
                 note="Chart 7.1 of the report. The grey segment is no opinion, neither, don't know or refused.",
                 segments=[("Mostly help", GREEN), ("Mostly harm", FUCHSIA), ("No opinion, neither or don't know", GREY)],
                 rows=[("Artificial intelligence", ["C7_1_ai_help", "C7_1_ai_harm", "C7_1_ai_none"]),
                       ("Nuclear power", ["C7_1_nuclear_help", "C7_1_nuclear_harm", "C7_1_nuclear_none"]),
                       ("Genetically modified food", ["C7_1_gm_help", "C7_1_gm_harm", "C7_1_gm_none"])]),
        ],
        map=dict(fn="internet_use_2019", unit="%", title="Where people were online",
                 sub="Share of adults who had used the internet, including social media, in the past 30 days, 2019"),
    ),
    # ------------------------------------------------------------------ 2021
    dict(
        key="a_changed_world", wave=2021, type="core", folder="WRP_2021/core_a_changed_world", published="July 2022",
        title="A Changed World?", subtitle="Perceptions and experiences of risk in the Covid age",
        lede="The second poll went into the field during the pandemic. Among the countries surveyed in both "
             "years, {X06_less_2021}% of people felt less safe than five years earlier, up from "
             "{X06_less_2019}% in 2019. Covid-19 itself was only the fourth most commonly named risk "
             "({X07_covid}%), behind road accidents, crime and violence, and personal health. Concern about "
             "climate change did not move: {X11_very_2021}% saw a very serious threat, the same as in 2019.",
        hero=("X06_less_2021", "of people felt less safe than five years earlier, up from {X06_less_2019}% in 2019"),
        stats=[
            ("X07_road", "named road-related accidents as the greatest risk to their safety"),
            ("X07_crime", "named crime and violence"),
            ("X07_covid", "named Covid-19, the fourth most common answer"),
            ("X09_none_2021", "said they faced no risk, down from {X09_none_2019}% in 2019"),
            ("X10_health", "of people aged 65 and older named personal health as their greatest risk; {X10_covid}% named Covid-19"),
            ("X12_dk_primary", "of people with primary education or less did not know whether climate change was a threat"),
        ],
        charts=[
            dict(kind="grouped", title="The share of people who felt less safe rose between the first two polls",
                 question="Compared to five years ago, do you feel more safe, less safe or about as safe?",
                 note="Chart 1.1 of the report. Countries surveyed in both years.",
                 series=[("2019", NAVY), ("2021", FUCHSIA)],
                 rows=[("More safe", ["C1_1_2019_more", "C1_1_2021_more"]),
                       ("About as safe", ["C1_1_2019_same", "C1_1_2021_same"]),
                       ("Less safe", ["C1_1_2019_less", "C1_1_2021_less"])]),
            dict(kind="hbar", title="In the middle of a pandemic, Covid-19 ranked fourth among the risks people named",
                 question="In your own words, what is the greatest source of risk to your safety in your daily life?",
                 note="Chart 1.3 of the report: 2021, first answer only.",
                 highlight="Covid-19",
                 rows=[("Road-related accidents", "C1_3_road_2021"), ("Crime and violence", "C1_3_crime_2021"),
                       ("Personal health", "C1_3_health_2021"), ("Covid-19", "C1_3_covid_2021"),
                       ("Nothing, no risks", "C1_3_none_2021"), ("Not having enough money", "C1_3_financial_2021"),
                       ("Unemployment, high prices", "C1_3_economic_2021"), ("Climate change or severe weather", "C1_3_climate_2021")]),
        ],
        map=dict(fn="less_safe_2021", unit="%", title="Where people felt less safe in 2021",
                 sub="Share of adults who said they felt less safe than five years ago, 2021. The question was not asked in China."),
    ),
    dict(
        key="a_resilient_world", wave=2021, type="core", folder="WRP_2021/core_a_resilient_world", published="September 2022",
        title="A Resilient World?", subtitle="Understanding vulnerability in a changing climate",
        lede="Could you protect yourself or your family if a disaster struck? Just over half of people "
             "({X03_yes}%) said yes, and the answer tracked national wealth: {X04_high_income}% in "
             "high-income countries and {X04_low_income}% in low-income ones. Household finances were thin. "
             "{X07}% could cover their basic needs for less than a month if they lost all income, and "
             "{X08}% for less than a week.",
        hero=("X07", "of people could cover their basic needs for less than a month if they lost all income"),
        stats=[
            ("X03_yes", "said there was something they could do to protect themselves or their family from a disaster"),
            ("X16_low_income", "of people in low-income countries had experienced a disaster in the past five years, against {X16_high_income}% in high-income countries"),
            ("X20", "had experienced discrimination because of their skin colour, religion, nationality or ethnic group, sex or a disability"),
            ("X10_low_income", "of people in low-income countries had access to the internet, against {X10_high_income}% in high-income countries"),
            ("X17_latin_america", "of people in Latin America and the Caribbean had helped a stranger in the past month"),
            ("X09_southern_asia", "of people in Southern Asia could cover basic needs for less than a month"),
        ],
        charts=[
            dict(kind="stacked", title="People were more likely to say their neighbours care about them than to say their government does",
                 question="How much do you think each of the following cares about you and your wellbeing: "
                          "a lot, somewhat or not at all?",
                 note="Global figures from the report's text. The grey segment is the remainder: don't know or refused.",
                 segments=[("A lot", GREEN), ("Somewhat", TEAL), ("Not at all", FUCHSIA), ("Don't know or refused", GREY)], remainder=True,
                 rows=[("Your neighbours", ["X14_a_lot", "X14_somewhat", "X14_not_at_all"]),
                       ("The government of your country", ["X27_a_lot", "X27_somewhat", "X27_not_at_all"])]),
        ],
        map=dict(fn="could_protect_2021", unit="%", title="Where people felt able to protect themselves from a disaster",
                 sub="Share of adults who said there was something they could do to protect themselves or their family in a future disaster, 2021"),
    ),
    dict(
        key="a_digital_world", wave=2021, type="core", folder="WRP_2021/core_a_digital_world", published="November 2022",
        title="A Digital World", subtitle="Perceptions of risk from AI and misuse of personal data",
        lede="Asked whether artificial intelligence would mostly help or mostly harm people in their country "
             "over the next 20 years, {X03}% said help and {X04}% said harm; {X05}% had no opinion or did not "
             "know. Confidence thinned once the technology took the wheel: {C1_7_no}% would not feel safe in "
             "a car driven by a computer. Internet use rose from {X37_2019}% to {X37_2021}% between the "
             "polls, though only {X41_central_west_africa}% of people in Central and Western Africa were online.",
        hero=("C1_7_no", "of people would not feel safe in a car without a human driver"),
        stats=[
            ("X03", "thought artificial intelligence would mostly help people in their country in the next 20 years"),
            ("X04", "thought it would mostly harm"),
            ("X37_2021", "had used the internet in the past 30 days, up from {X37_2019}% in 2019"),
            ("X62", "of internet users were worried that companies could use their personal information for marketing without permission"),
            ("C3_1_stolen_very", "of internet users were very worried that their personal information could be stolen"),
            ("X66_central_west_africa", "of internet users in Central and Western Africa were very worried about theft of their personal information"),
        ],
        charts=[
            dict(kind="stacked", title="Theft worried internet users more than use of their data by companies or governments",
                 question="When using the internet or social media, how worried are you that your personal information "
                          "could be stolen, used by companies for marketing without your permission, or used by the "
                          "government without your permission?",
                 note="Chart 3.1 of the report: internet users. The grey segment is the remainder: don't know or refused.",
                 segments=[("Very worried", FUCHSIA), ("Somewhat worried", TEAL), ("Not worried", GREEN), ("Don't know or refused", GREY)], remainder=True,
                 rows=[("Stolen", ["C3_1_stolen_very", "C3_1_stolen_somewhat", "C3_1_stolen_not"]),
                       ("Used by companies", ["C3_1_companies_very", "C3_1_companies_somewhat", "C3_1_companies_not"]),
                       ("Used by the government", ["C3_1_government_very", "C3_1_government_somewhat", "C3_1_government_not"])]),
        ],
        map=dict(fn="ai_mostly_harm_2021", unit="%", title="Where people expected artificial intelligence to do harm",
                 sub="Share of adults who said artificial intelligence will mostly harm people in their country in the next 20 years, 2021"),
    ),
    dict(
        key="safe_at_work", wave=2021, type="core", folder="WRP_2021/core_safe_at_work", published="January 2023",
        title="Safe at Work?", subtitle="Global experiences of violence and harassment",
        lede="{X03}% of people who had ever worked said they had experienced violence or harassment at work, "
             "whether physical, psychological or sexual. For most it was not a single incident: {X04}% of "
             "those affected had experienced it more than once. Psychological violence and harassment was "
             "the most common form ({X06_psychological}%), and the experience was most widespread in "
             "Australia and New Zealand ({X09}%).",
        hero=("X03", "of people who have ever worked have experienced violence or harassment at work"),
        stats=[
            ("X04", "of those affected had experienced it more than once"),
            ("X05_men", "of men who have ever worked had experienced it, against {X05_women}% of women"),
            ("X08_women", "of women who experienced it said it had a sexual element, against {X08_men}% of men"),
            ("X11_foreign", "of foreign-born women had experienced it, against {X11_native}% of native-born women"),
            ("X07", "of those affected had experienced more than one form"),
            ("X10_told", "of women with tertiary education who experienced it told someone"),
        ],
        charts=[
            dict(kind="hbar", title="Psychological violence and harassment was more than twice as common as physical",
                 question="Have you ever experienced physical, psychological or sexual violence or harassment at work?",
                 note="Figures from the report's executive summary: people who have ever worked.",
                 decimals=1,
                 rows=[("Any form", "X03"), ("Psychological", "X06_psychological"),
                       ("Physical", "X06_physical"), ("Sexual", "X06_sexual")]),
        ],
        map=dict(fn="violence_harassment_2021", unit="%", title="Where people had experienced violence or harassment at work",
                 sub="Share of people who have ever worked who have experienced physical, psychological or sexual violence or harassment at work, 2021"),
    ),
    dict(
        key="fo_violence_income_migration", wave=2021, type="focus_on",
        folder="WRP_2021/focus_on_violence_and_harassment_income_migration", published="April 2023",
        title="The impact of income and migration on violence and harassment at work", subtitle="Focus On",
        lede="{X11}% of workers living outside their country of birth had experienced violence or harassment "
             "at work, against {X10}% of native-born workers. Money compounds the gap. Amongst foreign-born "
             "workers who were struggling financially the figure was {X27}%, and in Northern America it "
             "reached {X28}%. Foreign-born workers were also slightly less likely to tell anyone "
             "({X13}% against {X12}%).",
        hero=("X11", "of foreign-born workers had experienced violence or harassment at work, against {X10}% of native-born workers"),
        stats=[
            ("X28", "of foreign-born workers struggling financially in Northern America had experienced it"),
            ("X20", "of foreign-born workers in Northern America who told no one said procedures were unclear"),
            ("X03", "of workers in Australia and New Zealand had experienced it, the highest of any region"),
        ],
        charts=[
            dict(kind="hbar", title="Being foreign-born and struggling financially each raised the likelihood of violence and harassment at work",
                 question="Have you ever experienced physical, psychological or sexual violence or harassment at work?",
                 note="Global figures from the report's text. Country of birth and feelings about household income come from the Gallup World Poll.",
                 rows=[("Native-born workers", "X10"), ("Foreign-born workers", "X11"),
                       ("Financially comfortable", "X23"), ("Struggling financially", "X24"),
                       ("Foreign-born and comfortable", "X26"), ("Foreign-born and struggling", "X27")]),
        ],
    ),
    dict(
        key="fo_fossil_fuels", wave=2021, type="focus_on",
        folder="WRP_2021/focus_on_fossil_fuels_and_climate_change", published="June 2023",
        title="Fossil fuel dependency and perceptions of climate change", subtitle="Focus On",
        lede="Worldwide, {X03}% of people saw climate change as a very serious threat to their country. In "
             "Chile the figure was {X05}%; in Saudi Arabia, {X07}%. The pattern holds inside countries too. "
             "{X18}% of Canadians saw a very serious threat, against {X19}% in oil-producing Alberta, and in "
             "no country where energy made up more than half of exports did a majority see a very serious threat.",
        hero=("X07", "of people in Saudi Arabia saw climate change as a very serious threat, against {X03}% worldwide"),
        stats=[
            ("X05", "of people in Chile saw a very serious threat"),
            ("X19", "saw a very serious threat in Alberta, against {X18}% across Canada"),
            ("X17", "saw a very serious threat in Northern Norway, against {X15}% across Norway"),
        ],
        charts=[
            dict(kind="hbar", title="Concern about climate change was lower in countries and regions that depend on fossil fuels",
                 question="Do you think that climate change is a very serious threat, a somewhat serious threat, or not a "
                          "threat at all to the people in this country in the next 20 years?",
                 note="Share answering 'very serious threat'. Figures from the report's text.",
                 highlight="World",
                 rows=[("Chile", "X05"), ("Canada", "X18"), ("Norway", "X15"), ("World", "X03"),
                       ("Western Norway", "X16"), ("Alberta, Canada", "X19"), ("Northern Norway", "X17"),
                       ("China", "X12"), ("Saudi Arabia", "X07")]),
        ],
    ),
    dict(
        key="fo_critical_infrastructure", wave=2021, type="focus_on",
        folder="WRP_2021/focus_on_critical_infrastructure", published="October 2023",
        title="Critical infrastructure resilience and perceptions of disaster preparedness", subtitle="Focus On",
        lede="{X01}% of people had lost access to at least one of five critical services (electricity, clean "
             "water, food, medical help or a telephone) for more than a day in the past year, and those "
             "who had been through a disaster in the past five years were the more likely to have gone "
             "without. Around half "
             "thought their national government ({X03}%) and their local government ({X04}%) were well "
             "prepared to deal with a disaster.",
        hero=("X01", "of people lost access to at least one critical service for more than a day in the past year"),
        stats=[
            ("C1_electricity_disaster", "of people who had experienced a disaster went without electricity for more than a day"),
            ("X03", "said their national government was well prepared to deal with a disaster"),
            ("X04", "said the same of their local government"),
        ],
        charts=[
            dict(kind="grouped", title="People who had been through a disaster were more likely to have gone without each service",
                 question="In the past 12 months, has each of the following happened to you for more than a day?",
                 note="Chart 1 of the report. Medicine and medical care is left out: the published bar for people who had not experienced a disaster does not match the data.",
                 series=[("Experienced a disaster in the past five years", FUCHSIA), ("Did not", GREEN)],
                 rows=[("Electricity", ["C1_electricity_disaster", "C1_electricity_no_disaster"]),
                       ("Clean water", ["C1_water_disaster", "C1_water_no_disaster"]),
                       ("Telephone", ["C1_telephone_disaster", "C1_telephone_no_disaster"]),
                       ("Food", ["C1_food_disaster", "C1_food_no_disaster"])]),
        ],
    ),
    # ------------------------------------------------------------------ 2023
    dict(
        key="resilience_in_a_changing_world", wave=2023, type="core",
        folder="WRP_2023/core_resilience_in_a_changing_world", published="June 2024",
        title="Resilience in a Changing World", subtitle="World Risk Poll 2024 Report",
        lede="The global Resilience Index stood at {X04} out of 100 in 2023, against {X05} in 2021, and in "
             "{X06} of the {X03} countries surveyed in both years it did not change significantly. Beneath "
             "the steady headline, confidence slipped: {X11}% of people said there was nothing they could do "
             "to protect themselves or their families from a future disaster, up from {X10}%. And {X12}% of "
             "those who had lived through a disaster received no warning.",
        hero=("X11", "of people said they could do nothing to protect themselves or their family from a future disaster, up from {X10}% in 2021"),
        stats=[
            ("X04", "the global Resilience Index in 2023, on a scale of 0 to 100", "{v}"),
            ("X15", "had personally experienced a disaster in the past five years, up from {X16}% in 2021"),
            ("X12", "of those who experienced a disaster received no warning"),
            ("X14", "of those who were not warned own a mobile phone"),
            ("X07", "countries saw a significant fall in the Index of four points or more", "{v}"),
            ("X08", "countries saw a significant rise", "{v}"),
        ],
        charts=[
            dict(kind="grouped", title="More people had experienced a disaster in 2023, and more felt unable to protect themselves from one",
                 question="Is there anything you could do to protect yourself or your family from the impact of a future "
                          "disaster? Have you personally experienced a disaster in the past five years? Did you receive any warning?",
                 note="Figures from the report's executive summary. Warnings: people who experienced a disaster in the past five years.",
                 series=[("2021", FUCHSIA), ("2023", GREEN)],
                 rows=[("Could do nothing to protect themselves", ["X10", "X11"]),
                       ("Experienced a disaster in the past five years", ["X16", "X15"]),
                       ("Received no warning of the disaster", ["X13", "X12"])]),
        ],
        map=dict(fn="resilience_index_2023", unit="", title="The Resilience Index around the world, 2023",
                 sub="Average Resilience Index score, 0 to 100, 2023"),
    ),
    dict(
        key="a_world_of_waste", wave=2023, type="core", folder="WRP_2023/core_a_world_of_waste", published="September 2024",
        title="A World of Waste", subtitle="Risks and opportunities in household waste management",
        lede="Four in five households say plastic ({X04}%) or food ({X05}%) is the most common material in "
             "their waste. Just over half ({X06}%) separate it before disposal, but the gap between rich and "
             "poor countries is wide: {X07}% of households in high-income countries separate their waste, "
             "against {X08}% in low-income ones. {X12}% dispose of their waste in an uncontrolled way, by "
             "burning it, dumping it or taking it to landfill themselves.",
        hero=("X12", "of households dispose of their waste in an uncontrolled way: burning, dumping or taking it to landfill"),
        stats=[
            ("X13", "of households burn their waste"),
            ("X16", "of households in Indonesia burn their waste"),
            ("X06", "of households separate their waste before disposal"),
            ("X11", "of households in rural areas of low-income countries have their waste collected"),
            ("X20", "of households in high-income countries both separate their waste and have it collected"),
            ("X21", "of households in low-income countries do both"),
        ],
        charts=[
            dict(kind="hbar", title="Fewer than half of households have their waste collected by the municipal government",
                 question="What typically happens to your household's waste once it is taken outside of your home?",
                 note="Chart 4.1 of the report.",
                 rows=[("Municipal government collects it", "C4_1_government"), ("Household takes it to landfill", "C4_1_landfill"),
                       ("Household burns it", "C4_1_burns"), ("Household disposes of it in the street", "C4_1_street"),
                       ("Community group collects it", "C4_1_community"), ("Private company collects it", "C4_1_private"),
                       ("Other", "C4_1_other")]),
        ],
        map=dict(fn="burns_waste_2023", unit="%", title="Where households burn their waste",
                 sub="Share of adults who said someone from the household burns its waste, 2023"),
    ),
    dict(
        key="engineering_safer_workplaces", wave=2023, type="core",
        folder="WRP_2023/core_engineering_safer_workplaces", published="October 2024",
        title="Engineering Safer Workplaces", subtitle="Global trends in occupational safety and health",
        lede="{X03}% of the world's workforce, around {X04} million people, had been seriously harmed at "
             "work in the past two years. Only {X06}% of them told someone responsible for safety or health. "
             "Most workers have had no training at all: {X07}% had never received any occupational safety "
             "and health training, rising to {X10_never}% in agriculture.",
        hero=("X03", "of the current workforce had been seriously harmed at work in the past two years"),
        stats=[
            ("X07", "of workers have never received occupational safety and health training"),
            ("X10_never", "of agricultural workers have never been trained"),
            ("X11", "of workers in fishing have never been trained"),
            ("X06", "of workers who were harmed told someone responsible for safety or health"),
            ("X09_ft_employer", "of full-time employees were trained in the past two years, against {X09_part_time}% of part-time workers"),
            ("X08_lower_middle", "of workers in lower-middle-income countries have never been trained"),
        ],
        charts=[
            dict(kind="hbar", title="Worry about harm at work nearly doubled among workers who had seen or suffered it",
                 question="In general, how worried are you that the work you do could cause you serious harm? "
                          "Share very or somewhat worried, by experience of harm at work in the past two years.",
                 note="Figures from the report's executive summary: people in employment.",
                 rows=[("Not harmed", "X12_not_harmed"), ("Know someone who was harmed", "X12_know_someone"),
                       ("Personally harmed", "X12_personally"), ("Both", "X12_both")]),
        ],
        map=dict(fn="harmed_at_work_2023", unit="%", title="Where workers had been harmed in the past two years",
                 sub="Share of the current workforce who personally experienced serious harm from their work in the past two years, 2023"),
    ),
    dict(
        key="what_the_world_worries_about", wave=2023, type="core",
        folder="WRP_2023/core_what_the_world_worries_about", published="November 2024",
        title="What the World Worries About", subtitle="Global perceptions and experiences of risk and harm",
        lede="{X03}% of people saw climate change as a very or somewhat serious threat to their country, yet "
             "the risk named most often in daily life was the road: {X05}% named road-related accidents as "
             "their greatest risk, as in 2019. People felt safer than they had during the pandemic, with "
             "{X08}% feeling more safe than five years earlier and {X10}% less safe. Worry about mental "
             "health kept climbing, from {X11}% in 2019 to {X13}% in 2023.",
        hero=("X13", "of people were worried that mental health issues could cause them serious harm"),
        stats=[
            ("X03", "saw climate change as a very or somewhat serious threat to their country"),
            ("X05", "named road-related accidents as the greatest risk to their safety"),
            ("X08", "felt more safe than five years earlier"),
            ("X10", "felt less safe"),
        ],
        charts=[
            dict(kind="line", title="Worry about mental health rose at each poll, whilst road accidents stayed the most commonly named risk",
                 question="In general, how worried are you that mental health issues could cause you serious harm? "
                          "In your own words, what is the greatest source of risk to your safety in your daily life?",
                 note="Figures from the report's executive summary.",
                 years=[2019, 2021, 2023],
                 series=[("Very or somewhat worried about harm from mental health issues", FUCHSIA, ["X11", "X12", "X13"]),
                         ("Named road-related accidents as their greatest risk", GREEN, ["X07", "X06", "X05"])]),
        ],
        map=dict(fn="road_top_risk_2023", unit="%", title="Where road accidents were named as the greatest risk",
                 sub="Share of adults who named road-related accidents or injuries as the greatest source of risk to their safety, 2023"),
    ),
    dict(
        key="fo_ocean_workers", wave=2023, type="focus_on", folder="WRP_2023/focus_on_ocean_workers", published="June 2025",
        title="Risk perceptions and experiences of ocean workers", subtitle="Focus On",
        lede="People who make their living from the sea are more exposed to the weather than most. {X14}% of "
             "ocean workers had been seriously harmed by severe weather in the past two years, against "
             "{X15}% of other workers, and they were almost three times as likely to name climate change or "
             "severe weather as their greatest risk ({X03}% against {X05}%). The work itself is hazardous "
             "too: {X25}% had been seriously harmed by it, the highest of the eight sectors compared, yet "
             "only {X30}% had received safety training in the past two years.",
        hero=("X14", "of ocean workers had been seriously harmed by severe weather in the past two years, against {X15}% of other workers"),
        stats=[
            ("X03", "of ocean workers named climate change or severe weather as their greatest risk"),
            ("X25", "had been seriously harmed by their work in the past two years"),
            ("X30", "had received safety training in the past two years"),
        ],
        charts=[
            dict(kind="grouped", title="Ocean workers were more exposed to harm from weather and from work, and less likely to report it",
                 question="Experience of harm in the past two years, worry about severe weather, and whether people who "
                          "were harmed at work told someone.",
                 note="Figures from the report's text.",
                 series=[("Ocean workers", FUCHSIA), ("Other workers", GREEN)],
                 rows=[("Harmed by severe weather", ["X14", "X15"]),
                       ("Very worried about severe weather", ["X11", "X12"]),
                       ("Harmed by the work they do", ["X25", "X26"]),
                       ("Told someone about harm at work", ["X31", "X32"])]),
        ],
    ),
    dict(
        key="fo_migration", wave=2023, type="focus_on",
        folder="WRP_2023/focus_on_migration_in_a_warming_world", published="May 2026",
        title="Migration in a warming world", subtitle="Focus On",
        lede="Do people who fear climate change want to leave? Combining the 2021 and 2023 polls, {X29}% of "
             "those who saw climate change as a very serious threat said they would like to move "
             "permanently to another country, against {X30}% of those who saw a lesser threat or none. "
             "Money matters alongside the weather: {X33}% of people whose household could not cover a month "
             "without income wanted to leave, against {X32}% of those who could. Even so, at least {X31}% "
             "of every group preferred to stay.",
        hero=("X29", "of people who see climate change as a very serious threat would like to move permanently to another country, against {X30}% of others"),
        stats=[
            ("X02", "of households could not cover their basic needs for a month without income"),
            ("X17", "named not having enough money or the general economy as their greatest risk in 2023"),
            ("X03", "named climate change or severe weather as their greatest risk in 2023, the highest of the three polls"),
        ],
        charts=[
            dict(kind="grouped", title="A thin financial cushion raised the wish to migrate most among people who saw no climate threat",
                 question="Ideally, if you had the opportunity, would you like to move permanently to another country, "
                          "or would you prefer to continue living in this country?",
                 note="2021 and 2023 polls combined. The migration question comes from the Gallup World Poll and is not in the public data.",
                 series=[("Could cover a month or more without income", GREEN), ("Less than a month", FUCHSIA)],
                 rows=[("Climate change a very serious threat", ["X34", "X35"]),
                       ("Climate change not a threat", ["X36", "X37"])]),
        ],
    ),
    # ------------------------------------------------------------------ 2025
    dict(
        key="alone_together", wave=2025, type="core", folder="WRP_2025/core_alone_together", published="June 2026",
        title="Alone Together", subtitle="The hidden consensus on climate change",
        doi="10.60743/d5zy-ec79",
        lede="Three in four people ({X03}%) see climate change as a threat to their country, the highest "
             "share in any World Risk Poll. They are less sure that anyone else agrees. {X05}% call it a "
             "very serious threat themselves, but only {X13}% think most other people in their country do. "
             "The gap is widest in high-income countries, where {X14}% hold the view and {X15}% think most "
             "others share it.",
        hero=("X03", "of people see climate change as a very or somewhat serious threat to their country"),
        stats=[
            ("X05", "see a very serious threat themselves"),
            ("X13", "think most other people in their country see a very serious threat"),
            ("X16", "countries where the gap between the two is at least 40 points: Portugal and the United States", "{v}"),
            ("X09", "see a threat in lower-middle-income countries, up from {X08}% in 2019"),
            ("X11", "see a threat in upper-middle-income countries, up from {X10}% in 2019"),
            ("X15", "of people in high-income countries think most others see a very serious threat; {X14}% see one themselves"),
        ],
        charts=[
            dict(kind="grouped", title="People underestimate how many of their fellow citizens share their concern about climate change",
                 question="Do you think that climate change is a very serious threat, a somewhat serious threat, or not a "
                          "threat at all to the people in this country in the next 20 years? And how do you think most "
                          "other people in this country would answer?",
                 note="Share answering 'very serious threat'. Figures from the report's executive summary.",
                 series=[("See a very serious threat themselves", FUCHSIA), ("Think most others do", GREEN)],
                 rows=[("World", ["X05", "X13"]), ("High-income countries", ["X14", "X15"])]),
        ],
        map=dict(fn="climate_concern_gap_2025", unit=" pts", title="Where people most underestimate others' concern about climate change",
                 sub="Share who see a very serious threat, minus the share who think most others in their country do, in percentage points, 2025"),
    ),
    dict(
        key="the_quiet_hazards", wave=2025, type="core", folder="WRP_2025/core_the_quiet_hazards", published="June 2026",
        title="The Quiet Hazards", subtitle="How everyday risk shapes daily life",
        doi="10.60743/9djc-t718",
        lede="The 2025 poll widened its list of everyday hazards to take in heat, drought, wildfire and the "
             "air people breathe. {X13}% of adults had been personally harmed by prolonged severe weather "
             "such as droughts and heatwaves in the past two years, and {X14}% by floods or storms. Harm "
             "from food ({X06}%) and drinking water ({X07}%) reached the highest levels the Poll has "
             "recorded. At work, the share of the workforce harmed fell to {X03}%, from {X05}% in 2021.",
        hero=("X13", "of adults had been personally harmed by prolonged severe weather, such as droughts and heatwaves, in the past two years"),
        stats=[
            ("X14", "had been personally harmed by severe weather events such as floods and storms"),
            ("X15", "had been personally harmed by the air they breathe"),
            ("X17", "were not worried at all about being harmed by the air they breathe"),
            ("X08", "named road-related accidents as the greatest risk to their safety, still the most common answer"),
            ("X03", "of the current workforce had been seriously harmed at work in the past two years, down from {X04}% in 2023"),
            ("X16", "had been personally harmed by wildfires"),
        ],
        charts=[
            dict(kind="hbar", title="Droughts and heatwaves had harmed more people than floods and storms, food, water, air or wildfires",
                 question="Have you or someone you personally know experienced serious harm from any of the following "
                          "in the past two years?",
                 note="Share of adults who personally experienced harm. Figures from the report's executive summary.",
                 rows=[("Droughts, heatwaves and other prolonged weather", "X13"), ("Floods, storms and other severe weather", "X14"),
                       ("The food they eat", "X06"), ("The water they drink", "X07"),
                       ("The air they breathe", "X15"), ("Wildfires", "X16")]),
        ],
        map=dict(fn="harmed_prolonged_weather_2025", unit="%", title="Where prolonged severe weather had harmed people",
                 sub="Share of adults who personally experienced serious harm from severe prolonged weather events in the past two years, 2025"),
    ),
    dict(
        key="a_resilient_life", wave=2025, type="core", folder="WRP_2025/core_a_resilient_life", published="October 2026",
        title="A resilient life", subtitle="How wellbeing shapes the capacity to cope",
        doi="10.60743/sbwn-m411",
        lede="The global Resilience Index held at {X04} in 2025, level with 2023. The steady headline masks "
             "a decline at the personal level: individual resilience fell two points for the second edition "
             "running, to {X08}, whilst household ({X13}), community ({X15}) and societal ({X20}) resilience "
             "held or edged up. Wellbeing and resilience move together. Adults who are thriving score "
             "{X28_thriving} on the Index; those who are suffering score {X28_suffering}.",
        hero=("X04", "the global Resilience Index in 2025, on a scale of 0 to 100, unchanged since 2023", "{v}"),
        stats=[
            ("X08", "global individual resilience, down two points since 2023", "{v}"),
            ("X20", "global societal resilience, up from {X22} in 2021", "{v}"),
            ("X17", "countries where perceived agency rose by at least 10 points; it fell by as much in {X18}", "{v}"),
            ("X24_north_africa", "points gained by Northern Africa since 2023, the largest regional rise", "+{v}"),
            ("X29_thriving", "individual resilience among adults who are thriving, against {X29_suffering} among those who are suffering", "{v}"),
            ("X27_north_africa", "percentage point rise in internet access in Northern Africa since 2019", "+{v}"),
        ],
        charts=[
            dict(kind="hbar", title="Individual resilience is the weakest of the four dimensions, and the only one that fell",
                 question="The Resilience Index combines four dimensions, each scored from 0 to 100.",
                 note="Global scores, 2025. Figures from the report's executive summary.", unit="",
                 rows=[("Individual", "X08"), ("Household", "X13"), ("Community", "X15"), ("Societal", "X20")]),
            dict(kind="hbar", title="Resilience rises with wellbeing: thriving adults score 16 points higher than those who are suffering",
                 question="Global Resilience Index, by life evaluation: thriving, struggling or suffering.",
                 note="Life evaluation comes from the Gallup World Poll and is not in the public data.", unit="",
                 rows=[("Thriving", "X28_thriving"), ("Struggling", "X28_struggling"), ("Suffering", "X28_suffering")]),
        ],
        map=dict(fn="resilience_index_2025", unit="", title="The Resilience Index around the world, 2025",
                 sub="Average Resilience Index score, 0 to 100, 2025"),
    ),
    dict(
        key="from_alert_to_agency", wave=2025, type="core", folder="WRP_2025/core_from_alert_to_agency", published="October 2026",
        title="From alert to agency", subtitle="What turns warnings into action?",
        doi="10.60743/yx1k-t541",
        lede="One in five adults ({X013}%) had been impacted by a disaster in the past five years, and four "
             "in five of them ({X027}%) received at least one early warning. Reach is uneven: {X030_low}% "
             "were warned in low-income countries against {X030_high}% in high-income ones, and Central and "
             "Western Africa ({X031}%) was the only region where fewer than half were reached. Receiving a "
             "warning did not always mean being able to act on it. In low- and lower-middle-income "
             "countries, about half of those warned ({X007}%) could not.",
        hero=("X027", "of adults impacted by a disaster received at least one early warning"),
        stats=[
            ("X013", "of adults had been impacted by a disaster in the past five years"),
            ("X015", "had been impacted in low-income countries, against {X016}% in high-income countries"),
            ("X023", "of adults in the Philippines had been impacted, the highest of any country"),
            ("X031", "were warned in Central and Western Africa, the only region under half"),
            ("X008", "of those who received no warning own a mobile phone"),
            ("X009", "adults who were impacted, not warned and own a mobile phone", "{v} million"),
        ],
        charts=[
            dict(kind="hbar", title="Early warnings reached fewer people in low-income countries",
                 question="Before the disaster, did you receive a warning from any of the following sources? "
                          "Share of adults impacted by a disaster who received at least one early warning.",
                 note="Figures from the report's executive summary.",
                 rows=[("Low income", "X030_low"), ("Lower-middle income", "X030_lower_middle"),
                       ("Upper-middle income", "X030_upper_middle"), ("High income", "X030_high")]),
        ],
        map=dict(fn="impacted_by_disaster_2025", unit="%", title="Where disasters had impacted people",
                 sub="Share of adults who said they had been impacted by a disaster in their country in the past five years, 2025"),
    ),
    dict(
        key="after_the_storm", wave=2025, type="core", folder="WRP_2025/core_after_the_storm", published="October 2026",
        title="After the storm", subtitle="How disasters reshape resilience and trust",
        doi="10.60743/16n7-bn41",
        lede="What happens to resilience and trust in the places a disaster hits? This report follows seven "
             "disasters, comparing the affected regions with the rest of each country before and after. "
             "Communities drew together: across the seven cases, the share saying their neighbours care "
             "about them a lot rose {X015} percentage points relative to elsewhere. Confidence in government "
             "fared worse. In Türkiye's earthquake regions, the share calling the national government well "
             "prepared fell from {X024}% in 2021 to {X025}% in 2025.",
        hero=("X025", "of people in Türkiye's earthquake regions said the national government was well prepared for a disaster in 2025, down from {X024}% in 2021"),
        stats=[
            ("X015", "percentage point rise in the share saying neighbours care a lot, across the seven cases, relative to the rest of each country", "+{v}"),
            ("X008", "percentage point change in confidence in national government in Türkiye's earthquake regions, 2021 to 2023, relative to the rest of the country", "{v}"),
            ("X010", "percentage point rise in the share saying the government cares a lot in Mozambique's affected provinces, relative to the rest of the country", "+{v}"),
            ("X009", "percentage point change in confidence in national government in New Zealand's affected regions", "{v}"),
            ("X030", "of the seven cases where the Resilience Index fell relative to the rest of the country", "{v}"),
            ("X022", "percentage points by which Türkiye's confidence gap narrowed between 2023 and 2025", "{v}"),
        ],
        charts=[
            dict(kind="grouped", title="Belief that the government is well prepared collapsed in Türkiye's earthquake regions, and fell elsewhere too",
                 question="Do you think the national government is well prepared to deal with a disaster?",
                 note="Share answering 'yes, well prepared'. Figures from the report's executive summary.",
                 series=[("2021", FUCHSIA), ("2025", TEAL)],
                 rows=[("Earthquake regions", ["X024", "X025"]), ("Rest of Türkiye", ["X026", "X027"])]),
        ],
        map=dict(kind="locator", title="The seven case studies",
                 sub="Each case compares the regions hit by a disaster with the rest of the country, across the 2021, 2023 and 2025 polls.",
                 places=[("MAR", "Morocco", "Marrakech-Safi", FUCHSIA), ("TUR", "Türkiye", "Mediterranean and Central East Anatolia", GREEN),
                         ("NZL", "New Zealand", "Northland and Auckland", TEAL), ("ZAF", "South Africa", "KwaZulu-Natal", ORANGE),
                         ("MOZ", "Mozambique", "Zambezia, Sofala and Manica", PURPLE), ("PAK", "Pakistan", "Sindh", LIME),
                         ("ECU", "Ecuador", "Guayas and El Oro", RED)]),
    ),
]
