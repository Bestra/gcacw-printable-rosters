import json
import sys

# Compare parsers or inspect raw tables
mode = sys.argv[1] if len(sys.argv) > 1 else "compare"

if mode == "compare":
    # Compare first scenario units between old and new parser
    with open("all_scenarios.json") as f:
        old = json.load(f)

    with open("otr2_parsed.json") as f:
        new = json.load(f)

    print("=== Comparison: Scenario 1 Confederate Units ===")
    print()
    print("OLD PARSER:")
    for u in old[0]["confederate_units"][:5]:
        print(f"  {u['unit_leader']:15} {u['size']:10} {u['command']:5} {u['unit_type']:4} {u['manpower_value']:5} {u['hex_location'][:30]}")

    print()
    print("NEW PARSER:")
    for u in new[0]["confederate_units"][:5]:
        print(f"  {u['unit_leader']:15} {u['size']:10} {u['command']:5} {u['unit_type']:4} {u['manpower_value']:5} {u['hex_location'][:30]}")

elif mode == "hcr7":
    # Check HCR scenario 7 - should have Turn column
    with open("hcr_parsed.json") as f:
        hcr = json.load(f)
    s7 = [s for s in hcr if s["number"] == 7][0]
    print("=== HCR Scenario 7: From Frederick to Sharpsburg ===")
    print("Union units with turn info:")
    for u in s7["union_units"][:8]:
        turn = u.get("turn") or "None"
        print(f"  Turn={turn:4}  {u['unit_leader']:15} {u['hex_location'][:25]}")

elif mode == "rtg10":
    # Check RTG2 scenario 10 reinforcement tracks
    with open("rtg2_parsed.json") as f:
        rtg = json.load(f)
    s10 = [s for s in rtg if s["number"] == 10][0]
    print("=== RTG2 Scenario 10: The Gettysburg Campaign ===")
    print("Confederate units with reinforcement set:")
    for u in s10["confederate_units"]:
        rs = u.get("reinforcement_set")
        if rs:
            print(f"  Set={rs}  {u['unit_leader']:15} {u['hex_location'][:25]}")

else:
    # Original raw table inspection
    game = mode
    scenario_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    with open(f'raw/{game}_raw_tables.json') as f:
        data = json.load(f)

    s = data[scenario_idx]
    print(f"Scenario {s['scenario_number']}: {s['scenario_name']}")
    print()

    for side_name, tables in [("Confederate", s["confederate_tables"]), ("Union", s["union_tables"])]:
        print(f"=== {side_name} Tables ===")
        for t in tables:
            print(f"\n  [{t['name']}]")
            if t.get("header_row"):
                print(f"    Header: {t['header_row']}")
            for row in t["rows"][:8]:
                print(f"    {row}")
            if len(t["rows"]) > 8:
                print(f"    ... ({len(t['rows'])} rows total)")
            if t.get("annotations"):
                print(f"    Annotations: {t['annotations']}")
