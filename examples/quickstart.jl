# Quickstart: load one World Risk Poll wave, then stack all four waves
# into a trend file using the harmonised block described in
# docs/CODEBOOK.md.
#
# Requires: DataFrames, Parquet2
#   import Pkg; Pkg.add(["DataFrames", "Parquet2"])
#
# Run from the repository root:
#   julia examples/quickstart.jl

using DataFrames, Parquet2

const WAVES = ["WRP_2019", "WRP_2021", "WRP_2023", "WRP_2025"]

readwave(name) = DataFrame(Parquet2.Dataset(joinpath(name, name * ".parquet")); copycols = false)

# Weighted mean of `value`, over the rows where `value` is present.
function weighted_mean(value, weight)
    ok = .!ismissing.(value)
    sum(value[ok] .* weight[ok]) / sum(weight[ok])
end

# --- Load a single wave ----------------------------------------------

wave = readwave("WRP_2025")
println(nrow(wave), " respondents, ", ncol(wave), " variables")

# Within-country weighted average worry score for this wave.
println("2025 worry_score (WGT-weighted): ",
        round(weighted_mean(wave.worry_score, wave.WGT); digits = 3))

# --- Stack all four waves for a trend ---------------------------------
# Only the first 37 columns (the harmonised block) carry matching names,
# codes and labels across waves -- that's what makes stacking valid.
# See docs/CODEBOOK.md for what each one means and which waves it covers.

const HARMONISED_COLS = [
    "WPID_RANDOM", "Wave", "Year", "WP5", "Country", "COUNTRY_ISO2",
    "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT",
    "Age", "AgeGroups3", "AgeGroups4", "AgeGroups5", "Gender", "Education",
    "Urbanicity", "Urbanicity2", "EMP_2010", "INCOME_5", "HouseholdSize",
    "ChildrenInHousehold", "worry_score", "worry_score_core7",
    "worry_index_published", "experience_score", "experience_score_self",
    "experience_score_core7", "experience_index_published", "worry_exp_gap",
    "resilience_index", "resilience_index_100", "resilience_idv",
    "resilience_hhl", "resilience_com", "resilience_soc",
]

trend = reduce(vcat, (readwave(w)[:, HARMONISED_COLS] for w in WAVES))
println("\nPooled trend file: ", nrow(trend), " respondents across ", length(WAVES), " waves")

# Global worry_score by year, weighted by PROJWT (a population weight,
# appropriate here because the trend is pooled across countries -- use
# WGT instead for a within-country-only comparison).
println("\nGlobal worry_score by year (PROJWT-weighted):")
println(combine(groupby(trend, :Year),
    [:worry_score, :PROJWT] =>
        ((v, w) -> round(weighted_mean(v, w); digits = 3)) => :worry_score))

# --- A wave-specific question, trended by hand ------------------------
# "Climate change is a threat to [country] in the next 20 years" is asked
# in every wave, but it sits OUTSIDE the harmonised block and its variable
# name changes: L5 in 2019, WP20719 from 2021 on. Codes: 1 = very serious
# threat, 2 = somewhat serious, 3 = not a threat; 98/99 are DK/refused.
# This is the general recipe for any comparable question that isn't
# pre-harmonised: map the per-wave name, keep the substantive codes, then
# stack.

const CLIMATE_VAR = [
    "WRP_2019" => "L5",
    "WRP_2021" => "WP20719",
    "WRP_2023" => "WP20719",
    "WRP_2025" => "WP20719",
]

function load_climate((wave, var))
    df = readwave(wave)[:, ["Year", "PROJWT", var]]
    rename!(df, var => :climate_threat)
    filter!(:climate_threat => x -> !ismissing(x) && x in (1, 2, 3), df)
    df
end

climate = reduce(vcat, load_climate.(CLIMATE_VAR))
# "serious" = very serious (1) or somewhat serious (2).
climate.serious = Float64.(in.(climate.climate_threat, Ref((1, 2))))

println("\nClimate change seen as a serious threat, % by year (PROJWT-weighted):")
println(combine(groupby(climate, :Year),
    [:serious, :PROJWT] =>
        ((s, w) -> round(100 * weighted_mean(s, w); digits = 1)) => :pct_serious_threat))
