import pandas as pd
import numpy as np
import streamlit as st

def get_local_csv_data():
    #Data loading
    df = pd.read_csv("src/data/llm_enhancement_aerlingus_defects_droppedna_19-9-2025.csv", sep = ';')
    df['Date'] = pd.to_datetime(df['issue_date'])
    return df

def enhance_dataframe(df):
    df['ac_model'] = np.random.choice(["A333", "A320", "A21N", "A332", "A20N", "A321", "A319"], 12)
    df['ac_description'] = np.random.choice(["AIRBUS A320-214", "AIRBUS A320-251N", "AIRBUS A330-302", "AIRBUS A330-200"], 12)
    df['reg_number'] = np.random.choice(["EI-DEE", "EI-DVM", "EI-NSD", "EI-DEH", "EI-DVM"], 12)
    df['finding_source'] = np.random.choice(["CHECK 1000 FH", "TASKCARD", "NRC DOCUMENT"], 12)
    df['ata'] = np.random.choice(["25-21", "05-20", "25-00", "20-00", "20-00"], 12)
    df['taskcard'] = np.random.choice(["ALT-25-0002", "ALT-28-0001", "323000-01-1", "ZL-500-03-1", "ALT-74-0001-RH"], 12)
    df['amm_code'] = np.random.choice(["74-00-00-710-802", "21-28-00-710-802-A", "11-00-00", "53-00-14-283-002", "51-72-11"], 12)
    return df

def get_data_va_1():
    ata_codes = ["ZL_05", "ZL_04", "ZL_01", "57_00", "53_41", "53_21", "32_40", "32_11", "27_54", "05_24"]
    findings_sum = [324, 298, 268, 150, 123, 100, 90, 83, 77, 70]
    df = pd.DataFrame({
        "ata_codes": ata_codes,
        "total_findings": findings_sum
    })
    df["ata_codes"] = df["ata_codes"].astype(str)   # force text
    df["ata_codes"] = pd.Categorical(df["ata_codes"], categories=df["ata_codes"], ordered=True)
    return df

def get_data_va_2():
    ata_code = ["ZL_05", "ZL_04", "ZL_01", "57_00", "53_41", "53_21", "32_40", "32_11", "27_54", "05_24"]

    ac_type = ["A333", "A320", "A21N", "A332", "A20N", "A321", "A319"]

    data = {
        "ATA Code": np.repeat(ata_code, len(ac_type)),
        "Aircraft Type": ac_type * len(ata_code),
        "Findings": np.random.randint(0, 100, len(ata_code) * len(ac_type))
    }
    return pd.DataFrame(data)