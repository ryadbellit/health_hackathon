from server.app.schema import MedicationEntry, medications_to_csv


def test_medications_to_csv_matches_fixed_format():
    entries = [
        MedicationEntry(
            trade_name="Novalgin",
            active_ingredient="Metamizole",
            dosis="500 mg",
            route="oral",
            morning=1,
            midday=0,
            evening=1,
            night=0,
            as_needed="Yes",
            comment="Take as needed for pain; maximum 4 doses per day",
        )
    ]

    csv_text = medications_to_csv(entries)

    lines = csv_text.splitlines()
    assert lines[0] == "trade name,active ingredient,dosis,route,morning,midday,evening,night,as needed,Comment"
    assert lines[1] == (
        "Novalgin,Metamizole,500 mg,oral,1.0,0.0,1.0,0.0,Yes,"
        "Take as needed for pain; maximum 4 doses per day"
    )
