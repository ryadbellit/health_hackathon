import json
import re
import pandas as pd
from pathlib import Path


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def normalize_dosis(value: str) -> str:
    if value is None:
        return ""
    value = str(value).lower().strip()
    value = value.replace("µg", "mcg")
    value = re.sub(r"(\d)\s*(mg|g|mcg|ml|ie|units?)", r"\1 \2", value)
    value = re.sub(r"\s+", " ", value)
    return value


def load_med_ref(med_ref_csv: str):
    """
    Expected med_ref.csv columns:
    active ingredient,known_strengths

    Example:
    Apixaban,"2.5 mg;5 mg"
    Ibuprofen,"200 mg;400 mg;600 mg"
    """

    df = pd.read_csv(med_ref_csv)

    reference = {}

    for _, row in df.iterrows():
        ingredient = normalize_text(row["active ingredient"])
        strengths_raw = str(row.get("known_strengths", ""))

        strengths = {
            normalize_dosis(x)
            for x in strengths_raw.split(";")
            if x.strip()
        }

        reference[ingredient] = strengths

    return reference


def validate_medications(input_json: str, med_ref_csv: str):
    with open(input_json, "r", encoding="utf-8") as f:
        medications = json.load(f)

    med_ref = load_med_ref(med_ref_csv)

    output = []

    for med in medications:
        active_ingredient = med.get("active ingredient", "")
        dosis = med.get("dosis", "")

        normalized_ingredient = normalize_text(active_ingredient)
        normalized_dosis = normalize_dosis(dosis)

        schedule = "-".join([
            str(med.get("morning", "")),
            str(med.get("midday", "")),
            str(med.get("evening", "")),
            str(med.get("night", "")),
        ])

        medication_flag = ""
        dosage_flag = ""

        if normalized_ingredient in med_ref:
            medication_flag = f"**{active_ingredient}**"

            known_strengths = med_ref[normalized_ingredient]

            if normalized_dosis and normalized_dosis not in known_strengths:
                dosage_flag = (
                    f'<span style="color:red"><b>{dosis}</b></span>'
                )

        output.append({
            "active ingredient": active_ingredient,
            "dosis": dosis,
            "route": med.get("route", ""),
            "morning-midday-evening-night": schedule,
            "as needed": med.get("as needed", ""),
            "Comment": med.get("Comment", ""),
            "medication flag": medication_flag,
            "dosage flag": dosage_flag,
        })

    return output


def save_validated_output(
    input_json: str,
    med_ref_csv: str,
    output_json: str,
):
    result = validate_medications(input_json, med_ref_csv)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result
