def generate_copy_profile(asset, logic_profile=None):
    logic = logic_profile or {}

    asset_name = asset.get("title") or asset.get("name") or "Your Asset"
    audience = asset.get("audience") or logic.get("audiences", ["Business professionals"])[0] if logic.get("audiences") else "Business professionals"
    problem = asset.get("problem") or logic.get("problemStatements", ["Make a faster, clearer business decision."])[0] if logic.get("problemStatements") else "Make a faster, clearer business decision."

    benefits = asset.get("benefits", [])
    if not benefits and logic.get("outputs"):
        benefits = logic.get("outputs")
    if not benefits:
        benefits = ["Understand your current position", "Identify hidden opportunities", "Make data-driven decisions"]

    outputs_text = "result"
    if logic.get("outputs"):
        outputs_text = ", ".join(logic["outputs"][:2]).lower()

    return {
        "heroEyebrow": f"For {audience}",
        "heroTitle": f"The {asset_name}",
        "heroSubtitle": f"Solve this problem: {problem} Get a clear {outputs_text}.",
        "formTitle": "Enter your details to generate your result.",
        "resultTitle": "Your Calculated Result",
        "benefitBullets": benefits[:3],
        "faq": [
            {
                "q": "Why do I need this?",
                "a": f"Because you need to solve: {problem}"
            },
            {
                "q": "What do I get?",
                "a": f"A clear, personalized {outputs_text}."
            }
        ],
        "primaryCta": asset.get("primaryAction", "Get My Result")
    }
