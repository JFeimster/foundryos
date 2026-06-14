import os
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def run_tests():
    failures = 0

    print("Running Smoke Test...")

    # 1. Test Registry Loading
    try:
        from scripts.foundry import load_assets
        assets = load_assets()
        print(f"✅ Registry loading works. Found {len(assets)} assets.")
    except Exception as e:
        print(f"❌ Registry loading failed: {e}")
        failures += 1

    # 2. Test Engine: Design
    try:
        from engines.design_engine import get_design_system
        ds = get_design_system()
        if ds:
            print("✅ Design system loads successfully.")
        else:
            print("❌ Design system returned empty.")
            failures += 1
    except Exception as e:
        print(f"❌ Design system loading failed: {e}")
        failures += 1

    # 3. Test Engine: Logic Profile Match
    try:
        from engines.logic_engine import get_logic_profile, load_all_profiles
        profiles = load_all_profiles()
        if len(profiles) >= 15:
            print(f"✅ Logic profiles load properly. Found {len(profiles)}.")
        else:
            print(f"❌ Logic profiles load properly? Found only {len(profiles)}.")
            failures += 1

        sample_asset = {"title": "Cash Flow Gap Estimator", "domain": "funding", "keywords": ["working capital"]}
        best = get_logic_profile(sample_asset)
        if best.get("id") == "cash-flow-gap":
            print(f"✅ Logic matching works. Matched 'cash-flow-gap' correctly.")
        else:
            print(f"❌ Logic matching failed. Matched '{best.get('id')}' instead of 'cash-flow-gap'.")
            failures += 1
    except Exception as e:
        print(f"❌ Logic engine failed: {e}")
        failures += 1

    # 4. Test Engine: Copy & Lead Flow
    try:
        from engines.copy_engine import generate_copy_profile
        from engines.lead_flow_engine import generate_lead_flow

        copy_res = generate_copy_profile(sample_asset, best)
        if copy_res.get("heroTitle"):
            print("✅ Copy profile generation works.")
        else:
            print("❌ Copy profile generation failed.")
            failures += 1

        out_dir = ROOT / "tests" / "temp_output"
        lead_res = generate_lead_flow(sample_asset, best, str(out_dir))

        if lead_res.get("primaryAction"):
            print("✅ Lead flow object generation works.")
        else:
            print("❌ Lead flow generation failed.")
            failures += 1

        if (out_dir / "lead-flow.json").exists():
            print("✅ Lead-flow.json was written to output folder.")
        else:
            print("❌ Lead-flow.json was not written.")
            failures += 1

    except Exception as e:
        print(f"❌ Copy/Lead flow engines failed: {e}")
        failures += 1

    # 5. Test Builders CLI execution
    try:
        from scripts.foundry import build

        # Test calculator build
        target1 = ROOT / "tests" / "temp_calc"

        # Test scorecard build
        target2 = ROOT / "tests" / "temp_scorecard"

        # Test simulator build
        target3 = ROOT / "tests" / "temp_simulator"

        required_files = ["index.html", "styles.css", "app.js", "asset.json", "asset-spec.json", "lead-flow.json", "README.md"]

        calc_asset = next((a for a in assets if a.get("assetType") == "calculator"), assets[0])
        score_asset = next((a for a in assets if a.get("assetType") in ["scorecard", "qualifier", "assessment"]), assets[1] if len(assets)>1 else assets[0])
        sim_asset = next((a for a in assets if a.get("assetType") in ["simulator", "generator"]), assets[2] if len(assets)>2 else assets[0])

        build(calc_asset, brand="Test", outdir=str(target1), flat=True, force=True)
        if all((target1 / f).exists() for f in required_files):
            print("✅ Calculator build works and generates all required output files.")
        else:
            print("❌ Calculator build failed to generate all required outputs.")
            failures += 1

        build(score_asset, brand="Test", outdir=str(target2), flat=True, force=True)
        if all((target2 / f).exists() for f in required_files):
            print("✅ Scorecard build works and generates all required output files.")
        else:
            print("❌ Scorecard build failed to generate all required outputs.")
            failures += 1

        build(sim_asset, brand="Test", outdir=str(target3), flat=True, force=True)
        if all((target3 / f).exists() for f in required_files):
            print("✅ Simulator build works and generates all required output files.")
        else:
            print("❌ Simulator build failed to generate all required outputs.")
            failures += 1

    except Exception as e:
        print(f"❌ CLI build failed: {e}")
        failures += 1

    # Cleanup temp
    try:
        if (ROOT / "tests" / "temp_output").exists():
            pass
            # shutil.rmtree(ROOT / "tests" / "temp_output")
        if (ROOT / "tests" / "temp_calc").exists():
            pass
            # shutil.rmtree(ROOT / "tests" / "temp_calc")
        if (ROOT / "tests" / "temp_scorecard").exists():
            pass
            # shutil.rmtree(ROOT / "tests" / "temp_scorecard")
        if (ROOT / "tests" / "temp_simulator").exists():
            pass
            # shutil.rmtree(ROOT / "tests" / "temp_simulator")
    except Exception:
        pass

    if failures == 0:
        print("\n🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Smoke test completed with {failures} failures.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
