# Sys.setenv(RETICULATE_MINICONDA_PATH = "C:/conda/r-miniconda")
# reticulate::install_miniconda()

import pandas as pd
import numpy as np
import wbgapi as wb  # pip install wbgapi
import plotly.graph_objects as go
import plotly_express as px
import plotly.io as pio
import os
import pyarrow

# conda install -c conda-forge python-kaleido wbgapi
# pip install --upgrade "kaleido==0.1.*" https://stackoverflow.com/questions/69016568/unable-to-export-plotly-images-to-png-with-kaleido

# import chart_studio
# import chart_studio.plotly as py
# chart_studio.tools.set_config_file(world_readable=False, sharing='private')
# chart_studio.tools.set_credentials_file(username='weiaun', api_key='0ZS6uEgrS4qjtLKCW96t')

os.chdir(
    'C:\\Users\\Wei Aun\\OneDrive - Quanticlear Solutions Sdn Bhd\\WHO\\SEARO\\Covid-19 Vaccination Integration\\Analytics\\')
vaccine_schedule = pd.read_excel(
    r'C:\Users\Wei Aun\OneDrive - Quanticlear Solutions Sdn Bhd\WHO\SEARO\Covid-19 Vaccination Integration\Analytics\vaccine-schedule--2020.xlsx',
    sheet_name="Data", header=0)

vaccine_coverage = pd.read_excel(
    r'C:\Users\Wei Aun\OneDrive - Quanticlear Solutions Sdn Bhd\WHO\SEARO\Covid-19 Vaccination Integration\Analytics\coverage--2021.xlsx',
    sheet_name="Data", header=0)
vaccine_coverage.rename(columns={'CODE': 'ISO_3_CODE'}, inplace=True)


# Note: Problem is that the vaccination schedule is described qualitatively for many countries LKA, IND
vaccine_schedule_supplement = pd.read_excel(
    r'C:\Users\Wei Aun\OneDrive - Quanticlear Solutions Sdn Bhd\WHO\SEARO\Covid-19 Vaccination Integration\Analytics\vaccine-schedule--2020--supplement.xlsx',
    sheet_name="Data", header=0)
vaccine_schedule = pd.concat([vaccine_schedule, vaccine_schedule_supplement])
del vaccine_schedule_supplement
vaccine_schedule['index_original'] = vaccine_schedule.index
vaccine_schedule['SOURCECOMMENT'] = np.where(vaccine_schedule['SOURCECOMMENT'].isnull(), "",
                                             vaccine_schedule['SOURCECOMMENT'])

# Shorten name for Kosovo
vaccine_schedule['COUNTRYNAME'] = np.where(
    vaccine_schedule['COUNTRYNAME'] == "Kosovo (in accordance with UN Security Council resolution 1244 (1999))",
    "Kosovo UNSC 1244", vaccine_schedule['COUNTRYNAME'])
vaccine_schedule['COUNTRYNAME'] = np.where(
    vaccine_schedule['COUNTRYNAME'] == "Democratic People's Republic of Korea",
    "DPR Korea", vaccine_schedule['COUNTRYNAME'])
vaccine_schedule['COUNTRYNAME'] = np.where(
    vaccine_schedule['COUNTRYNAME'] == "Democratic Republic of the Congo",
    "DR Congo", vaccine_schedule['COUNTRYNAME'])
vaccine_schedule['COUNTRYNAME'] = np.where(
    vaccine_schedule['COUNTRYNAME'] == "occupied Palestinian territory, including east Jerusalem",
    "OPT/EJ Palestine", vaccine_schedule['COUNTRYNAME'])
vaccine_schedule['COUNTRYNAME'] = np.where(
    vaccine_schedule['COUNTRYNAME'] == "Lao People's Democratic Republic",
    "Lao PDR", vaccine_schedule['COUNTRYNAME'])

### Parameters
oldest_age = 'Y99'
chosen_year = 2020  # SEAR best represented in 2020
chosen_region = "SEARO"
mothers_age_at_firstbirth = 2  # https://www.cia.gov/the-world-factbook/field/mothers-mean-age-at-first-birth/
age_onset_chronicdisease = "Y40"  # Just an assumption
childhood_age_threshold = 6

### Limits
# Disregard subnational programs. Note: Rationale is that these are extraordinary vaccination lines
vaccine_schedule = vaccine_schedule[vaccine_schedule['GEOAREA'] == "NATIONAL"]
vaccine_schedule = vaccine_schedule[vaccine_schedule['YEAR'] == chosen_year]

# Drop VITAMINA VACCINECODE
vaccine_schedule = vaccine_schedule[vaccine_schedule['VACCINECODE'] != "VITAMINA"]

### Import WDI
# SP.POP.TOTL = Population, total
# NY.GNP.PCAP.CD = GNI per capita, Atlas method (current US$)
# SH.XPD.GHED.PC.CD Domestic general government health expenditure per capita (current US$)

wdi = wb.data.DataFrame({'SP.POP.TOTL', 'NY.GNP.PCAP.CD', 'SH.XPD.GHED.PC.CD'}, time=chosen_year, labels=True)
wdi.reset_index().to_feather("wdi.arrow")
wdi['ISO_3_CODE'] = wdi.index

### Import OWID 

#owid_date = '2022-07-05'
owid_date = '2022-09-30'
owid_vaccinations = pd.read_csv('https://covid.ourworldindata.org/data/owid-covid-data.csv')
owid_vaccinations.rename(columns={'iso_code': 'ISO_3_CODE'}, inplace=True)

owid_latest_vaccinated = owid_vaccinations[(owid_vaccinations.date == owid_date)][['ISO_3_CODE','people_fully_vaccinated_per_hundred']]
owid_latest_vaccinated.people_fully_vaccinated_per_hundred = owid_latest_vaccinated.people_fully_vaccinated_per_hundred / 100

## Generate list of Member States - WHO_REGION COUNTRYNAME ISO_3_CODE
WHO_member_states = vaccine_schedule[['WHO_REGION', 'COUNTRYNAME', 'ISO_3_CODE']].groupby('ISO_3_CODE').first()
WHO_member_states['ISO_3_CODE'] = WHO_member_states.index
WHO_member_states.reset_index(drop=True, inplace=True)

# Merge in population data and GNP per capita
WHO_member_states = WHO_member_states.merge(wdi, on='ISO_3_CODE', how='left')
del wdi
WHO_member_states = WHO_member_states[
    ['WHO_REGION', 'ISO_3_CODE', 'COUNTRYNAME', 'SP.POP.TOTL', 'NY.GNP.PCAP.CD', 'SH.XPD.GHED.PC.CD']].sort_values(
    ['WHO_REGION', 'ISO_3_CODE'])

# Merge in OWID
WHO_member_states = WHO_member_states.merge(owid_latest_vaccinated, on='ISO_3_CODE', how='left')


## Generate list of WHO Regions - CODE NAME
# 2020 data  # WHO_Regions = vaccine_coverage[vaccine_coverage['GROUP'] == 'WHO Regions'][['ISO_3_CODE', 'NAME']].groupby('ISO_3_CODE').first()
WHO_Regions = vaccine_coverage[vaccine_coverage['GROUP'] == 'WHO_REGIONS'][['ISO_3_CODE', 'NAME']].groupby('ISO_3_CODE').first()
WHO_Regions['WHO_REGION_CODE'] = WHO_Regions.index
WHO_Regions['WHO_REGION_CODE'] = WHO_Regions['WHO_REGION_CODE'].str.upper() + 'O'
WHO_Regions.reset_index(drop=True, inplace=True)

## Generate list of SEARO member states
SEAR_memberstates = sorted(set(vaccine_schedule[vaccine_schedule['WHO_REGION'] == "SEARO"]['COUNTRYNAME'].unique()))
SEAR_memberstates_regex = '|'.join(SEAR_memberstates)
# SEAR_memberstates_regex = SEAR_memberstates_regex + "|South-East Asia Region"

# 2020 data # WHO_Regions2 = sorted(set(vaccine_coverage[vaccine_coverage['GROUP'] == 'WHO Regions']['NAME'].unique()))
WHO_Regions2 = sorted(set(vaccine_coverage[vaccine_coverage['GROUP'] == 'WHO_REGIONS']['NAME'].unique()))
WHO_Regions_regex = '|'.join(WHO_Regions2)
del WHO_Regions2

name_regex = WHO_Regions_regex + "|" + SEAR_memberstates_regex

###
### Vaccination coverage
###

# GROUP: Countries
# CODE: 
# ANTIGEN: DTPCV3
# YEAR: All for now
# COVERAGE_CATEGORY: HPV
# COVERAGE: --> change to percent

vaccine_coverage['COVERAGE'] = (vaccine_coverage['COVERAGE'].astype(float) / 100)
# 2020 data # vaccine_coverage_countries = vaccine_coverage[vaccine_coverage['GROUP'] == "Countries"]
# 2020 data # vaccine_coverage_whoregions = vaccine_coverage[vaccine_coverage['GROUP'] == "WHO Regions"]
vaccine_coverage_countries = vaccine_coverage[vaccine_coverage['GROUP'] == "COUNTRIES"]
vaccine_coverage_whoregions = vaccine_coverage[vaccine_coverage['GROUP'] == "WHO_REGIONS"]
vaccine_coverage = pd.concat([vaccine_coverage_whoregions, vaccine_coverage_countries])
vaccine_coverage = vaccine_coverage[vaccine_coverage['NAME'].str.contains(name_regex, regex=True)]

###
### Vaccination schedules
###

### Typology

vaccine_schedule['type'] = np.NaN

## Type 1:
## 1 = General / routine. Whole population, by age group, incl.
#     - Scheduled rounds
#     - Gender-specific (i.e., HPV, HPV2, HPV4, HPV9)
#       For BOTH male and female, treat as general / routine
#       For FEMALE, treat as general / routine but make note of half coverage
#     - "ADULTS" ... hard to interpret (when, how often, and what age)
#       (For SEARO)
#       INFLUENZA_ADULT, MEN_ACYW_135CONJ, TD_S
#       --> Manually check Thailand and Bhutan
#       
#     Add context MCH | 
#     --> Analytical output is simulate vaccines by context and age group, across the life course

# [ ] Drop Vitamin A

# Errors and exceptions (SEARO only)
vaccine_schedule['AGEADMINISTERED'] = np.where(vaccine_schedule.index_original == 430, "Y65",
                                               vaccine_schedule['AGEADMINISTERED'])
vaccine_schedule['SCHEDULEROUNDS'] = np.where(vaccine_schedule.index_original == 2399, 2,
                                              vaccine_schedule['SCHEDULEROUNDS'])

vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'General/routine', 1,
                                    vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'HPV administered to females and males',
                                    1, vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'HPV for females only', 1,
                                    vaccine_schedule['type'])

# GENDER: 0 = BOTH; 1 = MALE; 2 = FEMALE
vaccine_schedule['gender'] = 0  # by default, both male and female
vaccine_schedule['gender'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'HPV for females only', 2,
                                      vaccine_schedule['gender'])
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'HPV for females only', 1,
                                    vaccine_schedule['type'])

# Adults - coding only for SEARO as there's too much country specificity
vaccine_schedule['type'] = np.where(
    (vaccine_schedule.TARGETPOP_DESCRIPTION == 'Adults') & (vaccine_schedule.WHO_REGION == 'SEARO') & (
            vaccine_schedule.VACCINECODE == 'INFLUENZA_ADULT'), 1, vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(
    (vaccine_schedule.TARGETPOP_DESCRIPTION == 'Adults') & (vaccine_schedule.WHO_REGION == 'SEARO') & (
            vaccine_schedule.VACCINECODE == 'TD_S'), 1, vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(
    (vaccine_schedule.TARGETPOP_DESCRIPTION == 'Adults') & (vaccine_schedule.WHO_REGION == 'SEARO') & (
            vaccine_schedule.VACCINECODE == 'MEN_ACYW_135CONJ'), 1, vaccine_schedule['type'])

## Type 2:
## 2 = Health workers | Context is healthcare facility
#     (For SEARO:)
#     - INFLUENZA_ADULT (unclear if these are regularly/annually given) --> check manually
#     - MR (once per career)
#     --> Analytical output = just list these # of vaccination lines. There is not enough information on how often these vaccines are given to do a deeper analysis
#     (Beyond SEARO:)
#     - HEPA_ADULT, HEPB_ADULT,
# Typing
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'Health workers', 2,
                                    vaccine_schedule['type'])

## Type 3:
## 3 = Pregnant women | Context is MCH
#     (For SEARO)
#     - INFLUENZA_ADULT
#     - TD_S
#     - TT
#     --> Analytical output = total number of vaccinations per pregnancy; assume that these are all needed
# Since the key analytical question is the number of vaccines and its spread, make an assumption that vaccines start at booking. Also assume that pregnancy starts at age 

# Errors and exceptions (SEARO only)
vaccine_schedule['AGEADMINISTERED'] = np.where(vaccine_schedule.index_original == 5852, "+M1",
                                               vaccine_schedule['AGEADMINISTERED'])
vaccine_schedule['AGEADMINISTERED'] = np.where(vaccine_schedule.index_original == 6300, "1st contact",
                                               vaccine_schedule['AGEADMINISTERED'])

vaccine_schedule['SCHEDULEROUNDS'] = np.where(vaccine_schedule.index_original == 5936, 1,
                                              vaccine_schedule['SCHEDULEROUNDS'])
vaccine_schedule['SCHEDULEROUNDS'] = np.where(vaccine_schedule.index_original == 5938, 2,
                                              vaccine_schedule['SCHEDULEROUNDS'])
vaccine_schedule['SCHEDULEROUNDS'] = np.where(vaccine_schedule.index_original == 5939, 3,
                                              vaccine_schedule['SCHEDULEROUNDS'])

# Typing
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'Pregnant women', 3,
                                    vaccine_schedule['type'])

## For visualizations, add an assumption for PW. One child at a particular age
vaccine_schedule['AGEADMINISTERED'] = np.where(
    (vaccine_schedule.TARGETPOP_DESCRIPTION == 'Pregnant women') & (vaccine_schedule['SCHEDULEROUNDS'] == 1),
    "B", vaccine_schedule['AGEADMINISTERED'])

## Type 4:
## 4 = Chronic conditions (adults and children) besides criteria based only on age
# (SEARO only)
# Typing
vaccine_schedule['type'] = np.where(vaccine_schedule.SOURCECOMMENT.str.contains('chronic', case=False, regex=True), 4,
                                    vaccine_schedule['type'])

# For visualizations, add an assumption - chronic disease begins at a particular age
# vaccine_schedule['AGEADMINISTERED'] = np.where((vaccine_schedule.TARGETPOP_DESCRIPTION == 'Pregnant women') & (vaccine_schedule['SCHEDULEROUNDS']==1), age_onset_chronicdisease, vaccine_schedule['AGEADMINISTERED'])

## Type 5:
## 5 - Travel-related
# (SEARO only)
# Keywords: travellers, pilgrims
# Typing
vaccine_schedule['type'] = np.where(
    vaccine_schedule.SOURCECOMMENT.str.contains('travellers|pilgrims', case=False, regex=True), 5,
    vaccine_schedule['type'])

## Type 99:
## 99 = Disregard
# Disregard - food handlers - this is a small, unique program
# (SEARO only)
vaccine_schedule['type'] = np.where(vaccine_schedule.index_original == 6836, 99, vaccine_schedule['type'])

# Disregard the carrier mother program
# (SEARO only)
vaccine_schedule['type'] = np.where(vaccine_schedule.index_original == 4874, 99, vaccine_schedule['type'])

# Unclear what this is - who and when
vaccine_schedule['type'] = np.where(vaccine_schedule.index_original == 5937, 99, vaccine_schedule['type'])

# Duplicates
vaccine_schedule['type'] = np.where(vaccine_schedule.index_original == 2950, 99, vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(vaccine_schedule.index_original == 2951, 99, vaccine_schedule['type'])

# Disregard catch-up programs
# Note: Rationale is that these are extraordinary vaccination lines
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'Catch-up adults', 99,
                                    vaccine_schedule['type'])
vaccine_schedule['type'] = np.where(vaccine_schedule.TARGETPOP_DESCRIPTION == 'Catch-up children', 99,
                                    vaccine_schedule['type'])

# Logic checks / tests
# Testing: type1 = vaccine_schedule[vaccine_schedule['type']==1]

### Age analysis

# EXCEPTIONS (typos and other oddities / inconsistencies)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("B-<H24", "B", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("Y2-Y65+", ">Y2", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("Y65+", ">Y65", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("P", "B", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("^<", "B-", regex=True)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("-4444", "W6-M23", regex=False)
# vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("clinical indications","", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("+Y1 for older age group", "+Y1",
                                                                                      regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("1er contacto", "1st contact",
                                                                                      regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("Contact pregnancy",
                                                                                      "1st contact", regex=False)
vaccine_schedule['AGEADMINISTERED'] = vaccine_schedule['AGEADMINISTERED'].str.replace("1st Contact", "1st contact",
                                                                                      regex=False)

# Notes: For 'life course' vaccines, incl. gender specific - HPV, : Take the earliest age (disregard the older range)
# AGEADMINISTERED - take the youngest age (for future analysis, consider the whole range)
# >= or > .... How to interpret these? If interested in the youngest eligible age - then just remove these.
# Interpretation of greater or equal than vs greater than --> just treat as greater or equal than ( https://apps.who.int/iris/rest/bitstreams/1261961/retrieve ) as this seems to be what is described in MDV's schedule

vaccine_schedule['Age_isrange'] = vaccine_schedule['AGEADMINISTERED'].str.contains('-|>=|>', regex=True)
vaccine_schedule['Age_earliest'] = vaccine_schedule['AGEADMINISTERED'].str.extract(r'(^[^-]*)', expand=False)
vaccine_schedule['Age_earliest'] = vaccine_schedule['Age_earliest'].str.replace(">=", "", regex=True)
vaccine_schedule['Age_earliest'] = vaccine_schedule['Age_earliest'].str.replace(">", "", regex=True)
vaccine_schedule['Age_latest'] = np.where(vaccine_schedule['Age_isrange'],
                                          vaccine_schedule['AGEADMINISTERED'].str.extract(r'([^-]+$)', expand=False),
                                          np.NAN)
vaccine_schedule['Age_latest'] = np.where(
    vaccine_schedule['AGEADMINISTERED'].str.contains('>=|>', regex=True) & vaccine_schedule['Age_isrange'] == True,
    oldest_age, vaccine_schedule['Age_latest'])

# Is earliest age absolute or relative?
condlist1 = [
    vaccine_schedule['Age_earliest'].str[:1].eq('+')
]
choicelist1 = [True]
vaccine_schedule['Age_earliest_isrelative'] = np.select(condlist1, choicelist1, False)

# If relative age, remove the +
vaccine_schedule['Age_earliest'] = np.where(vaccine_schedule['Age_earliest_isrelative'],
                                            vaccine_schedule['Age_earliest'].str[1:], vaccine_schedule['Age_earliest'])

# '1st contact'
vaccine_schedule['First_contact'] = np.where(vaccine_schedule['Age_earliest'] == "1st contact", True, False)
vaccine_schedule['Age_earliest'] = np.where(vaccine_schedule['First_contact'], np.NAN, vaccine_schedule['Age_earliest'])

# Denominator
condlist2earliest = [
    vaccine_schedule['Age_earliest'].str[:1].eq('B'),
    vaccine_schedule['Age_earliest'].str[:1].eq('D'),
    vaccine_schedule['Age_earliest'].str[:1].eq('W'),
    vaccine_schedule['Age_earliest'].str[:1].eq('M'),
    vaccine_schedule['Age_earliest'].str[:1].eq('Y')
]

condlist2latest = [
    vaccine_schedule['Age_latest'].str[:1].eq('B'),
    vaccine_schedule['Age_latest'].str[:1].eq('D'),
    vaccine_schedule['Age_latest'].str[:1].eq('W'),
    vaccine_schedule['Age_latest'].str[:1].eq('M'),
    vaccine_schedule['Age_latest'].str[:1].eq('Y')
]

choicelist2 = [0, 1 / 365, 7 / 365, 1 / 12, 1]

vaccine_schedule['Age_denominator_earliest'] = np.select(condlist2earliest, choicelist2, np.NAN)
vaccine_schedule['Age_denominator_latest'] = np.select(condlist2latest, choicelist2, np.NAN)

vaccine_schedule['Age_earliest'] = vaccine_schedule['Age_earliest'].str.replace("B", "B0", regex=False)

vaccine_schedule['Age_numerator_earliest'] = vaccine_schedule['Age_earliest'].str[1:].astype(float)
vaccine_schedule['Age_numerator_latest'] = vaccine_schedule['Age_latest'].str[1:].astype(float)

vaccine_schedule['Age_earliest_inyears'] = vaccine_schedule['Age_denominator_earliest'] * vaccine_schedule[
    'Age_numerator_earliest']
vaccine_schedule['Age_latest_inyears'] = vaccine_schedule['Age_denominator_latest'] * vaccine_schedule[
    'Age_numerator_latest']

# Logic checks / tests
vaccine_schedule[['AGEADMINISTERED', 'Age_earliest_inyears', 'Age_latest_inyears']][
    vaccine_schedule['Age_latest_inyears'] < vaccine_schedule['Age_earliest_inyears']]

del condlist1
del condlist2earliest
del condlist2latest
del choicelist1
del choicelist2

### Scheduled rounds of the same vaccine

vaccine_schedule['TARGETPOP'] = vaccine_schedule['TARGETPOP'].replace(np.NaN, "GENERAL")
vaccine_schedule['Vaccination_Line'] = vaccine_schedule['ISO_3_CODE'] + "_" + vaccine_schedule['VACCINECODE'] + "_" + \
                                       vaccine_schedule['TARGETPOP']
vaccine_schedule = vaccine_schedule.sort_values(by=['WHO_REGION', 'Vaccination_Line', 'SCHEDULEROUNDS'])
vaccine_schedule['Age_earliest_schedule_inyears'] = vaccine_schedule.groupby(['Vaccination_Line'])[
    'Age_earliest_inyears'].cumsum()

### Type specific analyses + adding context

vaccine_schedule['ones'] = 1

## Contexts: MCH | Education | Workplace | Other
vaccine_schedule['Context'] = ""

## Type 1: General / Routine
vaccine_schedule['Context'] = np.where(
    (vaccine_schedule['type'] == 1) & (vaccine_schedule['TARGETPOP_DESCRIPTION'] == "General/routine"), "MCH",
    vaccine_schedule['Context'])
vaccine_schedule['Context'] = np.where(
    (vaccine_schedule['type'] == 1) & (vaccine_schedule['TARGETPOP_DESCRIPTION'] == "General/routine") & (
            vaccine_schedule['VACCINECODE'] == "MEN_ACYW_135CONJ"), "Other", vaccine_schedule['Context'])

vaccine_schedule['Context'] = np.where(
    (vaccine_schedule['type'] == 1) & (vaccine_schedule['TARGETPOP_DESCRIPTION'] == "Adults"), "Other",
    vaccine_schedule['Context'])
vaccine_schedule['Context'] = np.where(
    (vaccine_schedule['type'] == 1) & (vaccine_schedule['TARGETPOP_DESCRIPTION'] == "Adults") & (
            vaccine_schedule['VACCINECODE'] == "TD_S"), "Education", vaccine_schedule['Context'])

vaccine_schedule['Context'] = np.where(
    (vaccine_schedule['type'] == 1) & (vaccine_schedule['TARGETPOP_DESCRIPTION'] == "HPV for females only"),
    "Education", vaccine_schedule['Context'])

## Type 2: Health Workers
# vaccine_schedule2 = vaccine_schedule[vaccine_schedule['type']==2]
# There are just 3 - 2x for THA and 1x for BTH ... no clear year
vaccine_schedule['Context'] = np.where(vaccine_schedule['type'] == 2, "Workplace", vaccine_schedule['Context'])

# [ ] ... this needs more work
# vaccines_bytype2_grouped = vaccine_schedule[vaccine_schedule['type'] == 2].groupby(['ISO_3_CODE'],as_index = False).count()

## Type 3: Pregnant women
# Special note: Only THA and BTN provide INFLUENZA_ADULT ... the rest only do TT / TD_S
# vaccine_schedule3 = vaccine_schedule[vaccine_schedule['type']==3]
vaccine_schedule['Context'] = np.where(vaccine_schedule['type'] == 3, "MCH", vaccine_schedule['Context'])
# vaccines_bytype3_grouped = vaccine_schedule[vaccine_schedule['type'] == 3].groupby(['ISO_3_CODE'],as_index = False).count()

# IND "Pregnant women x2 doses; 2nd dose of Td vaccine is administered after 4 weeks of 1st dose, at least 4 weeks before delivery"
# vaccines_bytype3_grouped['ones'] = np.where(vaccines_bytype3_grouped['ISO_3_CODE']=="IND",2,vaccines_bytype3_grouped['ones'])
# LKA "x2 doses 6 weeks apart in 1st pregnancy, and x3 doses in subsequent pregnancies"
# vaccines_bytype3_grouped['ones'] = np.where(vaccines_bytype3_grouped['ISO_3_CODE']=="LKA",2,vaccines_bytype3_grouped['ones'])

vaccine_schedule['Months_from_start_of_pregnancy'] = np.where((vaccine_schedule['type'] == 3),
                                                              12 * vaccine_schedule['Age_earliest_schedule_inyears'],
                                                              np.NaN)

## Type 4: Risk groups (Chronic conditions)
# Basically only BTN and THA - influenza pediatric and adult
# vaccine_schedule4 = vaccine_schedule[vaccine_schedule['type']==4]
vaccine_schedule['Context'] = np.where(vaccine_schedule['type'] == 4, "Other", vaccine_schedule['Context'])

## Type 5: Travellers
# vaccine_schedule5 = vaccine_schedule[vaccine_schedule['type']==5]
vaccine_schedule['Context'] = np.where(vaccine_schedule['type'] == 5, "Other", vaccine_schedule['Context'])
# vaccines_bytype5_grouped = vaccine_schedule[vaccine_schedule['type'] == 5].groupby(['ISO_3_CODE'],as_index = False).count()

### Counting totals --> aggregating to Member States and WHO Regions

# The standardized person is a female + one complete pregnancy in her lifetime but no high-risk status (disease, occupation, or travel)
# Applies to General / Routine, HPV, and Pregnant Women only
# Age buckets: (1) Early Childhood, (2) After Early Childhood, (3) First pregnancy

vaccine_schedule['Age_Group_EarlyChildhood'] = np.where(
    (vaccine_schedule['Age_earliest_schedule_inyears'] < childhood_age_threshold) & (
        vaccine_schedule['TARGETPOP_DESCRIPTION'].str.contains("General|HPV", regex=True)), True, np.NAN)
vaccine_schedule['Age_Group_AfterEarlyChildhood'] = np.where(
    (vaccine_schedule['Age_earliest_schedule_inyears'] >= childhood_age_threshold) & (
        vaccine_schedule['TARGETPOP_DESCRIPTION'].str.contains("General|HPV", regex=True)), True, np.NAN)
vaccine_schedule['Age_Group_Pregnancy'] = np.where(
    vaccine_schedule['TARGETPOP_DESCRIPTION'].str.contains("Pregnant", regex=True), True, np.NAN)

## Aggregation at Member State-level

vaccines_percountry = vaccine_schedule[
    {'COUNTRYNAME', 'Age_Group_EarlyChildhood', 'Age_Group_AfterEarlyChildhood', 'Age_Group_Pregnancy'}].groupby(
    ['COUNTRYNAME'], as_index=False).count()
vaccines_percountry['Age_Group_Total'] = vaccines_percountry[
    ['Age_Group_EarlyChildhood', 'Age_Group_AfterEarlyChildhood', 'Age_Group_Pregnancy']].sum(axis=1)
WHO_member_states = WHO_member_states.merge(vaccines_percountry, on=['COUNTRYNAME'], how='left')

## Aggregation at WHO Regional-level
# Ridiculous that pandas doesn't natively supported weighted average
global_population = WHO_member_states['SP.POP.TOTL'].sum()
WHO_member_states['Pop_Global'] = global_population
del global_population

regional_population = WHO_member_states[['WHO_REGION', 'SP.POP.TOTL']].groupby(['WHO_REGION']).sum()
regional_population['WHO_REGION'] = regional_population.index
regional_population.rename(columns={'SP.POP.TOTL': 'Pop_Regional'}, inplace=True)
regional_population.reset_index(drop=True, inplace=True)
WHO_member_states = WHO_member_states.merge(regional_population, on='WHO_REGION', how='left')
WHO_member_states.rename(columns={'WHO_REGION': 'WHO_REGION_CODE'}, inplace=True)
del regional_population

WHO_member_states['Age_Group_EarlyChildhood_wt'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states[
    'Pop_Regional']) * WHO_member_states['Age_Group_EarlyChildhood']
WHO_member_states['Age_Group_AfterEarlyChildhood_wt'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states[
    'Pop_Regional']) * WHO_member_states['Age_Group_AfterEarlyChildhood']
WHO_member_states['Age_Group_Pregnancy_wt'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states['Pop_Regional']) * WHO_member_states['Age_Group_Pregnancy']
vaccines_perregion = WHO_member_states[
    {'WHO_REGION_CODE', 'Age_Group_EarlyChildhood_wt', 'Age_Group_AfterEarlyChildhood_wt',
     'Age_Group_Pregnancy_wt'}].groupby(['WHO_REGION_CODE'], as_index=False).sum()
vaccines_perregion['Age_Group_Total_wt'] = vaccines_perregion[
    ['Age_Group_EarlyChildhood_wt', 'Age_Group_AfterEarlyChildhood_wt', 'Age_Group_Pregnancy_wt']].sum(axis=1)
WHO_Regions = WHO_Regions.merge(vaccines_perregion, on=['WHO_REGION_CODE'], how='left')
del vaccines_perregion

WHO_member_states['Age_Group_EarlyChildhood_wt_global'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states[
    'Pop_Global']) * WHO_member_states['Age_Group_EarlyChildhood']
WHO_member_states['Age_Group_AfterEarlyChildhood_wt_global'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states[
    'Pop_Global']) * WHO_member_states['Age_Group_AfterEarlyChildhood']
WHO_member_states['Age_Group_Pregnancy_wt_global'] = (WHO_member_states['SP.POP.TOTL'] / WHO_member_states[
    'Pop_Global']) * WHO_member_states['Age_Group_Pregnancy']
vaccines_global = WHO_member_states[
    {'WHO_REGION_CODE', 'Age_Group_EarlyChildhood_wt_global', 'Age_Group_AfterEarlyChildhood_wt_global',
     'Age_Group_Pregnancy_wt_global'}].sum()
vaccines_global['Age_Group_Total_wt_global'] = vaccines_global[
    ['Age_Group_EarlyChildhood_wt_global', 'Age_Group_AfterEarlyChildhood_wt_global',
     'Age_Group_Pregnancy_wt_global']].sum()
print(vaccines_global)

## Vaccination Coverage
# HPV
vaccine_coverage_HPV = vaccine_coverage[
    (vaccine_coverage['COVERAGE_CATEGORY'] == "HPV") & (vaccine_coverage['ANTIGEN'] == "PRHPVC_F")]
# DPT3
vaccine_coverage_DPT3 = vaccine_coverage[
    ((vaccine_coverage['COVERAGE_CATEGORY'] == "OFFICIAL") | (vaccine_coverage['GROUP'] == "WHO_REGIONS")) & (
            vaccine_coverage['ANTIGEN'] == "DTPCV3")]

# OWID
vaccine_coverage_DPT3 = vaccine_coverage_DPT3.merge(owid_latest_vaccinated, on='ISO_3_CODE', how='left')




###
### Exports
###

# vaccine_schedule = vaccine_schedule[vaccine_schedule['WHO_REGION'] == chosen_region]
# vaccines_bytype = vaccine_schedule[vaccine_schedule['type'] != 99].sort_values(
#    by=['type', 'ISO_3_CODE', 'Age_earliest_schedule_inyears'])
# vaccines_bytype.reset_index().to_feather("vaccine_schedule.arrow")
# vaccines_bytype.to_excel("vaccination_schedule_export.xlsx", sheet_name='Schedule')

vaccine_coverage = vaccine_coverage.sort_values(by=['GROUP', 'ISO_3_CODE', 'COVERAGE_CATEGORY', 'ANTIGEN', 'YEAR'])
vaccine_coverage.reset_index().to_feather("vaccine_coverage.arrow")
vaccine_coverage.to_excel("vaccination_coverage_export.xlsx", sheet_name='Coverage')

WHO_member_states.to_excel("Vaccination_bymemberstate.xlsx", sheet_name='Data')
WHO_Regions.to_excel("Vaccination_byregion.xlsx", sheet_name='Data')

###
### Visualizations
###

A4_width_minusmargins_inch = 8.25 - (2 * 1)
A4_height_minusmargins_inch = 11.75 - (2 * 1)
Target_DPI = 150
Target_Scale = 4
font_family = "Cambria"

### Visualization parameters
# A4 @ 600 dpi = 4960 x 7016
pio.kaleido.scope.default_format = "webp"
pio.kaleido.scope.default_width = (A4_width_minusmargins_inch / 2) * Target_DPI
pio.kaleido.scope.default_height = A4_height_minusmargins_inch * Target_DPI

## Vaccination schedules

category_orders = {"VACCINE_DESCRIPTION": [
    "Adult Hepatitis A vaccine",
    "Adult Hepatitis B vaccine",
    "Adult TBE (tick borne encephalitis) vaccine",
    "Adult seasonal influenza vaccine",
    "Anthrax vaccine",
    "Auto-disable (AD) syringes",
    "Auto-disable syringes BCG",
    "BCG (Baccille Calmette Guérin) vaccine",
    "Cholera vaccine",
    "DT (Tetanus toxoid and diphtheria, children's dose) vaccine",
    "DT-IPV (Diphtheria and tetanus toxoid and IPV) vaccine",
    "DTaP (acellular) vaccine",
    "DTaP-HepB-IPV (acellular) vaccine",
    "DTaP-Hib (acellular) vaccine",
    "DTaP-Hib-HepB (acellular) vaccine",
    "DTaP-Hib-HepB-IPV (acellular) vaccine",
    "DTaP-Hib-IPV (acellular) vaccine",
    "DTaP-IPV (acellular) vaccine",
    "DTwP (Whole cell) vaccine",
    "DTwP-HepB (Whole cell) vaccine",
    "DTwP-Hib (Whole cell) vaccine",
    "DTwP-Hib-HepB (Whole cell) vaccine",
    "Deworming",
    "Diphtheria vaccine for older children and adults",
    "Diphtheria vaccine, children's dose",
    "HPV (Human Papilloma Virus) vaccine",
    "HPV-2 (Human Papilloma Virus 2-valent) vaccine",
    "HPV-4 (Human Papilloma Virus 4-valent) vaccine",
    "HPV-9 (Human Papilloma Virus 9-valent) vaccine",
    "Hepatitis A live attenuated",
    "Hepatitis A, Hepatitis B vaccine",
    "Hib (Haemophilus influenzae type B) vaccine",
    "Hib (Haemophilus influenzae type B), Meningococcal C",
    "IPV (Inactivated polio vaccine)",
    "IPVf (Inactivated polio vaccine fractional dose)",
    "JE-Inact (Japanese Encephalitis inactivated) vaccine",
    "JE-Livatd (Japanese Encephalitis live-attenuated) vaccine",
    "Leptospirosis",
    "MM (Measles and mumps) vaccine",
    "MMR (Measles, mumps and rubella) vaccine",
    "MMRV (Measles, mumps, rubella and varicella) vaccine",
    "MR (Measles and rubella) vaccine",
    "Measles vaccine",
    "Meningococcal A conjugate vaccine",
    "Meningococcal A polysaccharide vaccine",
    "Meningococcal AC vaccine",
    "Meningococcal ACW vaccine",
    "Meningococcal ACYW conjugate vaccine",
    "Meningococcal ACYW polysaccharide vaccine",
    "Meningococcal B vaccine",
    "Meningococcal BC vaccine",
    "Meningococcal C conjugate vaccine",
    "Mumps vaccine",
    "OPV (Oral polio vaccine)",
    "PCV (Pneumococcal conjugate vaccine)",
    "PCV-10 (Pneumococcal conjugate vaccine 10-valent) vaccine",
    "PCV-13 (Pneumococcal conjugate vaccine 13-valent) vaccine",
    "PCV-7 (Pneumococcal conjugate vaccine 7-valent) vaccine",
    "PPV (Pneumococcal polysaccharide vaccine)",
    "PPV-23 (Pneumococcal polysaccharide 23 valent) vaccine",
    "Pediatric Hepatitis A vaccine",
    "Pediatric Hepatitis B vaccine",
    "Pediatric TBE (tick borne encephalitis) vaccine",
    "Pediatric seasonal influenza vaccine",
    "RV-1 (Rotavirus 1-valent) vaccine",
    "RV-5 (Rotavirus 5-valent) vaccine",
    "Rabies vaccine",
    "Reconstitution syringes",
    "Rotavirus vaccine",
    "Rubella vaccine",
    "Shingles (Herpes zoster for older adults) vaccine",
    "TBE (Tick borne encephalitis)",
    "TT (Tetanus toxoid) vaccine",
    "Td (Tetanus toxoid and diphtheria for older children and adults) vaccine",
    "Td-IPV (Tetanus, diphtheria for older children and adults and IPV) vaccine",
    "Tdap (Tetanus, diphtheria for older children and adults and acellular pertussis) vaccine",
    "Tdap-IPV (Tetanus, diphtheria for older children and adults, acellular pertussis and IPV) vaccine",
    "Tularemia vaccine",
    "Typhoid and Hepatitis A",
    "Typhoid conjugate vaccine",
    "Typhoid polysaccharide vaccine",
    "Varicella vaccine",
    "Vitamin A supplements",
    "YF (Yellow fever) vaccine",
    "aP (acellular pertussis) vaccine"
]}

## Figure 1a: Global | Lifecourse

fig1a = px.strip(vaccine_schedule[(vaccine_schedule['type'] == 1)].sort_values(by=['ISO_3_CODE'], ascending=False),
                 x='Age_earliest_schedule_inyears', y='COUNTRYNAME', hover_name='VACCINE_DESCRIPTION',
                 custom_data=['type', 'gender', 'Context'],
                 color='VACCINE_DESCRIPTION',
                 facet_row='WHO_REGION',
                 range_x=(0, 70),
                 labels={"COUNTRYNAME": "", "Age_earliest_schedule_inyears": "Earliest Age (Years)",
                         "VACCINE_DESCRIPTION": "Vaccine Name", "SCHEDULEROUNDS": "Schedule Rounds",
                         "WHO_REGION": "WHO Region", },
                 title="Life course vaccines, all regions, 2020",
                 template="plotly_white",
                 category_orders=category_orders
                 )
for trace in fig1a.select_traces():
    trace.marker.update(size=4)
trace.marker.update(opacity=0.7)
trace.marker.update(symbol='triangle-up')
fig1a.update_yaxes(matches=None)
fig1a.update_layout(
    showlegend=False,
    font_family=font_family,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70],
        titlefont=dict(size=16), tickfont=dict(size=12)
    )
)
fig1a.for_each_xaxis(lambda x: x.update(tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70]))
fig1a.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
for axis in fig1a.layout:
    if type(fig1a.layout[axis]) == go.layout.YAxis: fig1a.layout[axis].title.text = ''

fig1a.show()

fig1a.write_image("images/fig1a.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=A4_height_minusmargins_inch * Target_DPI)

# Variation of fig1a
# for trace in fig1a.select_traces(selector=dict(name='Adult seasonal influenza vaccine')):
#    trace.marker.update(size=8)
#    trace.marker.update(opacity=1)
#    trace.marker.update(symbol='triangle-up')

# for trace in fig1a.select_traces(selector=dict(name="HPV-2 (Human Papilloma Virus 2-valent) vaccine")):
#    trace.marker.update(size=8)
#    trace.marker.update(opacity=1)
#    trace.marker.update(symbol='circle')

# for trace in fig1a.select_traces(selector=dict(name="HPV-4 (Human Papilloma Virus 4-valent) vaccine")):
#    trace.marker.update(size=8)
#    trace.marker.update(opacity=1)
#    trace.marker.update(symbol='circle')

# fig1a.show()

## Figure 1b: Global | Pregnant Women
fig1b = px.strip(vaccine_schedule[(vaccine_schedule['type'] == 3)].sort_values(by=['ISO_3_CODE'], ascending=False),
                 x='Months_from_start_of_pregnancy', y='COUNTRYNAME', hover_name='VACCINE_DESCRIPTION',
                 custom_data=['type', 'gender', 'Context'],
                 color='VACCINE_DESCRIPTION',
                 facet_row='WHO_REGION',
                 range_x=(0, 36),
                 labels={"COUNTRYNAME": "",
                         "Months_from_start_of_pregnancy": "Months from start of routine antenatal care",
                         "VACCINE_DESCRIPTION": "Vaccine Name", "SCHEDULEROUNDS": "Schedule Rounds",
                         "WHO_REGION": "WHO Region", },
                 title="Vaccines for pregnant women, all regions, 2020",
                 template="plotly_white",
                 category_orders=category_orders
                 )

for trace in fig1b.select_traces():
    trace.marker.update(size=4)
trace.marker.update(opacity=0.7)
trace.marker.update(symbol='circle')

fig1b.update_yaxes(matches=None)

fig1b.update_layout(
    showlegend=False,
    font_family=font_family,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 6, 12, 18, 24, 30, 36],
        titlefont=dict(size=16), tickfont=dict(size=12)
    )
)

fig1b.for_each_xaxis(lambda x: x.update(tickvals=[0, 6, 12, 18, 24, 30, 36]))
fig1b.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

for axis in fig1b.layout:
    if type(fig1b.layout[axis]) == go.layout.YAxis:
fig1b.layout[axis].title.text = ''

fig1b.show()
fig1b.write_image("images/fig1b.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=A4_height_minusmargins_inch * Target_DPI)

## Immunization schedules sorted by GDP per capita
fig1c = px.bar(WHO_member_states.sort_values('NY.GNP.PCAP.CD'), y='COUNTRYNAME',
               x=['Age_Group_EarlyChildhood', 'Age_Group_AfterEarlyChildhood', 'Age_Group_Pregnancy'],
               title='Life course vaccines. all member states sorted by GNP per capita in descending order, 2020',
               template="plotly_white",
               labels={"COUNTRYNAME": "", "value": "Scheduled vaccine doses","variable": "Legend","Age_Group_EarlyChildhood": "Early Childhood (age < 6 years)",
                    "Age_Group_AfterEarlyChildhood": "After Early Childhood",
                    "Age_Group_Pregnancy": "Vaccines for Pregnant Women", },
               )
fig1c_legend_newnames={"Age_Group_EarlyChildhood": "Early Childhood (age < 6 years)",
                    "Age_Group_AfterEarlyChildhood": "After Early Childhood",
                    "Age_Group_Pregnancy": "Vaccines for Pregnant Women", }
fig1c.for_each_trace(lambda t: t.update(name = fig1c_legend_newnames[t.name],
                                      legendgroup = fig1c_legend_newnames[t.name],
                                      offsetgroup = fig1c_legend_newnames[t.name],
                                      alignmentgroup = fig1c_legend_newnames[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, fig1c_legend_newnames[t.name])
                                     )

fig1c.update_layout(
    showlegend=True,
    font_family=font_family
)
fig1c.data[0].name = "Early Childhood (age < 6 years)"
fig1c.data[1].name = "After Early Childhood"
fig1c.data[2].name = "Vaccines for Pregnant Women"
fig1c.show()
fig1c.write_image("images/fig1c.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch+1) * Target_DPI)

## Immunization schedules by region
fig1d = px.bar(WHO_Regions, y='NAME',
               x=['Age_Group_EarlyChildhood_wt', 'Age_Group_AfterEarlyChildhood_wt', 'Age_Group_Pregnancy_wt'],
               labels={"variable": "Legend", "NAME": "WHO Region", "value": "Scheduled vaccine doses"},
               title='Average number of life course vaccines by region, 2020',
               template="plotly_white"
               )
fig1d_legend_newnames={"Age_Group_EarlyChildhood_wt": "Early Childhood (age < 6 years)",
                    "Age_Group_AfterEarlyChildhood_wt": "After Early Childhood",
                    "Age_Group_Pregnancy_wt": "Vaccines for Pregnant Women", }
fig1d.for_each_trace(lambda t: t.update(name = fig1d_legend_newnames[t.name],
                                      legendgroup = fig1d_legend_newnames[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, fig1d_legend_newnames[t.name])
                                     )
                  )
fig1d.update_layout(
    showlegend=True,
    font_family=font_family
)
fig1d.show()
fig1d.write_image("images/fig1d.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 3) * Target_DPI)

# Fig 2a: SEARO | Lifecourse
fig2a = px.strip(
    vaccine_schedule[(vaccine_schedule['type'] == 1) & (vaccine_schedule['WHO_REGION'] == chosen_region)].sort_values(
        by=['ISO_3_CODE'], ascending=False), x='Age_earliest_schedule_inyears', y='COUNTRYNAME',
    hover_name='VACCINE_DESCRIPTION', custom_data=['type', 'gender', 'Context'],
    color='VACCINE_DESCRIPTION',
    range_x=(0, 70),
    labels={"COUNTRYNAME": "Member State", "Age_earliest_schedule_inyears": "Earliest Age (Years)",
            "VACCINE_DESCRIPTION": "Vaccine Name", "SCHEDULEROUNDS": "Schedule Rounds", "WHO_REGION": "WHO Region", },
    title="Life course vaccines, SEAR, 2020",
    template="plotly_white",
    category_orders=category_orders
)

for trace in fig2a.select_traces():
    trace.marker.update(size=6)
trace.marker.update(opacity=0.7)
trace.marker.update(symbol='triangle-up')

for trace in fig2a.select_traces(selector=dict(name='Adult seasonal influenza vaccine')):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='triangle-up')

for trace in fig2a.select_traces(selector=dict(name="HPV-2 (Human Papilloma Virus 2-valent) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

for trace in fig2a.select_traces(selector=dict(name="HPV-4 (Human Papilloma Virus 4-valent) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

fig2a.update_yaxes(matches=None)

fig2a.update_layout(
    showlegend=True,
    font_family=font_family,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70],
        titlefont=dict(size=16), tickfont=dict(size=12)
    )
)

fig2a.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

for axis in fig2a.layout:
    if type(fig2a.layout[axis]) == go.layout.YAxis: fig2a.layout[axis].title.text = ''

fig2a.show()

fig2a.write_image("images/fig2a.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)


# Fig 2b: WPRO | Lifecourse
fig2b = px.strip(
    vaccine_schedule[(vaccine_schedule['type'] == 1) & (vaccine_schedule['WHO_REGION'] == "WPRO")].sort_values(
        by=['ISO_3_CODE'], ascending=False), x='Age_earliest_schedule_inyears', y='COUNTRYNAME',
    hover_name='VACCINE_DESCRIPTION', custom_data=['type', 'gender', 'Context'],
    color='VACCINE_DESCRIPTION',
    range_x=(0, 70),
    labels={"COUNTRYNAME": "Member State", "Age_earliest_schedule_inyears": "Earliest Age (Years)",
            "VACCINE_DESCRIPTION": "Vaccine Name", "SCHEDULEROUNDS": "Schedule Rounds", "WHO_REGION": "WHO Region", },
    title="Life course vaccines, WPR, 2020",
    template="plotly_white",
    category_orders=category_orders
)

for trace in fig2b.select_traces():
    trace.marker.update(size=6)
trace.marker.update(opacity=0.7)
trace.marker.update(symbol='triangle-up')

for trace in fig2b.select_traces(selector=dict(name='Adult seasonal influenza vaccine')):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='triangle-up')

for trace in fig2b.select_traces(selector=dict(name="HPV (Human Papilloma Virus) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

for trace in fig2b.select_traces(selector=dict(name="HPV-2 (Human Papilloma Virus 2-valent) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

for trace in fig2b.select_traces(selector=dict(name="HPV-4 (Human Papilloma Virus 4-valent) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

for trace in fig2b.select_traces(selector=dict(name="HPV-9 (Human Papilloma Virus 9-valent) vaccine")):
    trace.marker.update(size=10)
trace.marker.update(opacity=1)
trace.marker.update(symbol='circle')

fig2b.update_yaxes(matches=None)

fig2b.update_layout(
    showlegend=True,
    font_family=font_family,
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70],
        titlefont=dict(size=16), tickfont=dict(size=12)
    )
)

fig2b.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

for axis in fig2b.layout:
    if type(fig2b.layout[axis]) == go.layout.YAxis: fig2b.layout[axis].title.text = ''

fig2b.show()

fig2b.write_image("images/fig2b.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)


## Fig 3: Vaccination Coverage
# ANTIGEN: DTPCV3
# YEAR: All for now
# COVERAGE_CATEGORY: HPV

# DTP3
fig3dpt3 = px.line(vaccine_coverage_DPT3, x='YEAR', y='COVERAGE',range_y=(0,1),facet_col='NAME', facet_col_wrap=4,
                  title="DPT coverage, WHO regions and SEAR member states, 1980-2021",
                  template="plotly_white",
                  labels={"COVERAGE": "Coverage", "YEAR": "Year"},
                  )
fig3dpt3.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3dpt3.for_each_yaxis(lambda a: a.update(tickmode='linear',tick0=0,dtick=0.2,tickformat=',.0%'))
fig3dpt3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig3dpt3.show()
fig3dpt3.write_image("images/fig3dpt3.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)


fig3dpt3_regions = px.line(vaccine_coverage_DPT3[(vaccine_coverage_DPT3.GROUP=='WHO_REGIONS')], x='YEAR', y='COVERAGE',range_y=(0,1),facet_col='NAME', facet_col_wrap=3,
                  title="DPT coverage, WHO regions, 1980-2021",
                  template="plotly_white",
                  labels={"COVERAGE": "Coverage", "YEAR": "Year"},
                  )
fig3dpt3_regions.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3dpt3_regions.for_each_yaxis(lambda a: a.update(tickmode='linear',tick0=0,dtick=0.2,tickformat=',.0%'))
fig3dpt3_regions.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig3dpt3_regions.show()
fig3dpt3_regions.write_image("images/fig3dpt3_regions.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)


fig3dpt3_states = px.line(vaccine_coverage_DPT3[(vaccine_coverage_DPT3.GROUP=='COUNTRIES')], x='YEAR', y='COVERAGE',range_y=(0,1),facet_col='NAME', facet_col_wrap=3,
                  title="DPT coverage, SEAR member states, 1980-2021",
                  template="plotly_white",
                  labels={"COVERAGE": "Coverage", "YEAR": "Year"},
                  )
fig3dpt3_states.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3dpt3_states.for_each_yaxis(lambda a: a.update(tickmode='linear',tick0=0,dtick=0.2,tickformat=',.0%'))
fig3dpt3_states.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig3dpt3_states.show()
fig3dpt3_states.write_image("images/fig3dpt3_states.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)

# https://stackoverflow.com/questions/70327566/plotly-enabling-text-label-in-line-graph-for-for-the-last-value
#fig3dpt3.add_scatter(x=vaccine_coverage_DPT3[(vaccine_coverage_DPT3['YEAR']==2020)].YEAR, y=vaccine_coverage_DPT3[(vaccine_coverage_DPT3['YEAR']==2020)].COVERAGE,facet_col=vaccine_coverage_DPT3[(vaccine_coverage_DPT3['YEAR']==2020)].NAME)
#figtest = px.scatter(vaccine_coverage_DPT3[(vaccine_coverage_DPT3['YEAR']==2020)],x='YEAR', y='COVERAGE',facet_col='NAME')
#figtest.show()

fig3_dpt3_covid = px.scatter(vaccine_coverage_DPT3[(vaccine_coverage_DPT3.YEAR==2019)], x='COVERAGE', y='people_fully_vaccinated_per_hundred',text='NAME',range_x=(0.8,1),range_y=(0.4,1),trendline="ols",
                            title="DPT (2019) and Covid-19 (May 2022) vaccination coverage, SEAR member states",
                            template="plotly_white",
                            labels={"COVERAGE": "DPT3 Coverage", "people_fully_vaccinated_per_hundred": "Covid-19 Vaccination Coverage (Primary Course)"},
                            )
fig3_dpt3_covid.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3_dpt3_covid.update_traces(textposition='top center')
fig3_dpt3_covid.update_traces(marker_size=10)
fig3_dpt3_covid.update_yaxes(tickformat=',.0%')
fig3_dpt3_covid.update_xaxes(tickformat=',.0%')
fig3_dpt3_covid.show()
fig3_dpt3_covid.write_image("images/fig3_dpt3_covid.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 3) * Target_DPI)

#fig3_dpt3_covid.add_annotation(
#            x=0.2,
#            y=0.8,
#            text="Covid-19 vaccination coverage not adjusted for ineligble age groups")

# HPV

fig3hpv_regions = px.line(vaccine_coverage_HPV[(vaccine_coverage_HPV.GROUP=='WHO_REGIONS')], x='YEAR', y='COVERAGE', facet_col='NAME', facet_col_wrap=3,
                  title="HPV coverage, WHO regions, 2010-2021",
                  template="plotly_white",
                  labels={"COVERAGE": "Coverage", "YEAR": "Year"},
                  )
fig3hpv_regions.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3hpv_regions.for_each_yaxis(lambda a: a.update(tickmode='linear',tick0=0,dtick=0.1,tickformat=',.0%'))
fig3hpv_regions.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig3hpv_regions.show()
fig3hpv_regions.write_image("images/fig3hpv_regions.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)


fig3hpv_states = px.line(vaccine_coverage_HPV[(vaccine_coverage_HPV.GROUP=='COUNTRIES')], x='YEAR', y='COVERAGE', facet_col='NAME', facet_col_wrap=3,
                  title="HPV coverage, SEAR member states, 2010-2021",
                  template="plotly_white",
                  labels={"COVERAGE": "Coverage", "YEAR": "Year"},
                  )
fig3hpv_states.update_layout(
    showlegend=False,
    font_family=font_family,
    )
fig3hpv_states.for_each_yaxis(lambda a: a.update(tickmode='linear',tick0=0,dtick=0.2,tickformat=',.0%'))
fig3hpv_states.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig3hpv_states.show()
fig3hpv_states.write_image("images/fig3hpv_states.webp", format="webp", scale=Target_Scale, width=A4_width_minusmargins_inch * Target_DPI,
                  height=(A4_height_minusmargins_inch / 2) * Target_DPI)




# y - scale
# 0 - 1
# show
# gap in red;
# legend if possible
# color
# scheme
# region
# comparisons
