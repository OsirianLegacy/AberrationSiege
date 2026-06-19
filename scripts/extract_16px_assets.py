from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aberration_siege.core.constants import DATA_DIR, ROOT_DIR
from aberration_siege.core.extraction import extract_from_asset_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract 16x16 sprites from configured assets.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DATA_DIR / "asset_manifest.json",
        help="Asset manifest to read.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT_DIR / "assets" / "extracted",
        help="Directory for extracted PNG sprites.",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=DATA_DIR / "extracted_assets.json",
        help="Generated extracted sprite manifest.",
    )
    args = parser.parse_args()

    extracted = extract_from_asset_manifest(args.manifest, args.out, args.output_manifest)
    print(f"Extracted {len(extracted)} sprites")
    print(f"Wrote {args.output_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
