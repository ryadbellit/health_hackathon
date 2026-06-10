import json
import re
import pandas as pd


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def normalize_dosis(value: str) -> str:
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = value.replace("µg", "mcg")
    value = value.replace("μg", "mcg")

    value = re.sub(r"(\d)\s*(mg|g|mcg|ml|ie|units?)", r"\1 \2", value)
    value = re.sub(r"\s+", " ", value)

    return value


def load_med_ref(med_ref_csv: str) -> dict:
    """
    Expected med_ref.csv columns:

    active ingredient,known_strengths
    Apixaban,"2.5 mg;5 mg"
    Ibuprofen,"200 mg;400 mg;600 mg"
    """

    df = pd.read_csv(med_ref_csv)

    reference = {}

    for _, row in df.iterrows():
        ingredient = normalize_text(row["active ingredient"])

        known_strengths = {
            normalize_dosis(strength)
            for strength in str(row.get("known_strengths", "")).split(";")
            if strength.strip()
        }

        reference[ingredient] = known_strengths

    return reference


def validate_medications(input_json_path: str, med_ref_csv_path: str):
    with open(input_json_path, "r", encoding="utf-8") as f:
        medications = json.load(f)

    med_ref = load_med_ref(med_ref_csv_path)

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

        dosage_flag = ""

        if normalized_ingredient in med_ref:
            known_strengths = med_ref[normalized_ingredient]

            if normalized_dosis and normalized_dosis not in known_strengths:
                dosage_flag = f'<span style="color:red"><b>{dosis}</b></span>'

        output.append({
            "active ingredient": active_ingredient,
            "dosis": dosis,
            "route": med.get("route", ""),
            "morning-midday-evening-night": schedule,
            "as needed": med.get("as needed", ""),
            "Comment": med.get("Comment", ""),
            "dosage flag": dosage_flag,
        })

    return output


def save_validated_output(
    input_json_path: str,
    med_ref_csv_path: str,
    output_json_path: str,
):
    result = validate_medications(
        input_json_path=input_json_path,
        med_ref_csv_path=med_ref_csv_path,
    )

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result
