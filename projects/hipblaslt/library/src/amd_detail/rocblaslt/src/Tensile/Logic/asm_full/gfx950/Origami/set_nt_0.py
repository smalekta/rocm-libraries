#!/usr/bin/env python3
import os
import glob
import shutil
import yaml
from typing import Any, Tuple

def zero_nontemporals(node: Any) -> Tuple[bool, int]:
    """
    Recursively walk any Python structure produced by yaml.load and
    set NonTemporalA / NonTemporalB to 0 whenever they appear and are not 0.

    Returns (changed, num_fields_modified).
    """
    changed = False
    modified = 0

    if isinstance(node, dict):
        # Normalize in place
        for key in list(node.keys()):
            # Recurse first for nested structures
            ch, cnt = zero_nontemporals(node[key])
            if ch:
                changed = True
                modified += cnt

        # Now handle the specific keys on this dict
        for k in ("NonTemporalA", "NonTemporalB"):
            if k in node:
                try:
                    # Only modify if not already numeric zero
                    if node[k] != 0:
                        node[k] = 0
                        changed = True
                        modified += 1
                except Exception:
                    # If the value is something odd (e.g., string), force it to 0
                    if node[k] != 0:
                        node[k] = 0
                        changed = True
                        modified += 1

    elif isinstance(node, list):
        for i, item in enumerate(node):
            ch, cnt = zero_nontemporals(item)
            if ch:
                changed = True
                modified += cnt

    # other scalars: nothing to do
    return changed, modified

def process_file(path: str):
    yaml_args = {"default_flow_style": None, "sort_keys": False}
    with open(path, "rt") as fp:
        data = yaml.load(fp, Loader=yaml.SafeLoader)

    changed, count = zero_nontemporals(data)
    if not changed:
        print(f"[SKIP] {os.path.basename(path)} (no NonTemporalA/B to change)")
        return

    # Make a backup first
    backup = path + ".bak"
    shutil.copy2(path, backup)

    # Write changes atomically
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f_out:
        yaml.dump(data, f_out, **yaml_args)
    os.replace(tmp_path, path)

    print(f"[OK]   {os.path.basename(path)} — set {count} field(s) to 0 (backup: {backup})")

def main():
    paths = sorted(set(glob.glob("*.yaml") + glob.glob("*.yml")))
    if not paths:
        print("No .yaml or .yml files found in the current directory.")
        return

    for p in paths:
        try:
            process_file(p)
        except Exception as e:
            print(f"[ERR]  {p}: {e}")

if __name__ == "__main__":
    main()
