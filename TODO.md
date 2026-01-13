# TODO

## TPC Image Extraction

### Remaining Unmatched Units (2)

**Not in VMOD:**

- `Hartsuff` - Union infantry, not found in VMOD at all
- `Hardaway` (Art) - exists in VMOD but uses non-standard image naming (`Art-CSA_tmp18413` without .jpg)

These are genuine gaps in the VMOD module itself - no counter images exist for these units.

### Completed

- ✅ Fixed TPC leader classification (was using 1862 Peninsula Campaign leaders, now uses 1864-65 Petersburg Campaign leaders)
- ✅ Added name variants for TPC-specific typos (Warrent/Warren, Torber/Torbert, Barlett/Bartlett, etc.)
- ✅ Fixed skip filter for "heat" (was catching "Wheaton") and "ferry" (was catching "Ferry" unit)
- ✅ Added variant for corps suffix stripping (Devens-24th → Devens)
- ✅ Went from 47 unmatched to 2 unmatched (96% improvement)
