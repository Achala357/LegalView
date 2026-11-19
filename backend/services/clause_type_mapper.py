def normalize_clause_type(question: str) -> str:
    q = (question or "").lower()

    # Termination clauses
    if "termination without cause" in q:
        return "termination_without_cause"
    if "termination for cause" in q:
        return "termination_for_cause"
    if "termination" in q:
        return "termination"

    # Restrictive covenants
    if "non-compete" in q:
        return "non_compete"
    if "non-solicitation" in q:
        return "non_solicitation"

    # Compensation & employment
    if "compensation" in q:
        return "compensation"
    if "bonus" in q or "commission" in q:
        return "bonus_or_commission"
    if "benefits" in q:
        return "benefits"
    if "severance" in q:
        return "severance"
    if "employment term" in q:
        return "employment_term"
    if "notice period" in q:
        return "notice_period"
    if "duties and responsibilities" in q:
        return "duties_and_responsibilities"
    if "working hours" in q:
        return "working_hours"
    if "overtime" in q:
        return "overtime"
    if "probation period" in q:
        return "probation_period"
    if "performance review" in q:
        return "performance_review"
    if "employee transition" in q or "retention" in q:
        return "employee_transition_or_retention"


    # M&A–specific
    if "purchase price" in q:
        return "purchase_price"
    if "post-closing" in q:
        return "post_closing_obligations"
    if "closing conditions" in q:
        return "closing_conditions"
    if "representations and warranties" in q:
        return "representations_and_warranties"
    if "buyer representations" in q:
        return "buyer_representations"
    if "seller representations" in q:
        return "seller_representations"
    if "escrow" in q or "holdback" in q:
        return "escrow_or_holdback"
    if "working capital adjustment" in q:
        return "working_capital_adjustment"
    if "material adverse effect" in q or "mae" in q:
        return "material_adverse_effect"
    if "earn-out" in q or "contingent payment" in q:
        return "earn_out_or_contingent_payment"
    if "intellectual property transfer" in q:
        return "intellectual_property_transfer"
    if "indemnification" in q and ("basket" in q or "cap" in q):
        return "indemnification_basket_cap"
    if "indemnification clause" in q or "indemnification" in q:
        return "indemnification"

    # Legal boilerplate
    if "governing law" in q:
        return "governing_law"
    if "assignment" in q:
        return "assignment"
    if "waiver" in q:
        return "waiver"
    if "integration" in q or "entire agreement" in q:
        return "integration_entire_agreement"
    if "amendment" in q or "modification" in q:
        return "amendment"
    if "severability" in q:
        return "severability"
    if "limitation of liability" in q:
        return "limitation_of_liability"
    if "dispute resolution" in q or "arbitration" in q:
        return "dispute_resolution"
    if "notices clause" in q or "notices" in q:
        return "notices"

    # NDA / confidentiality family
    if "definition of confidential information" in q:
        return "confidentiality_definition"
    if "obligations of the receiving party" in q:
        return "confidentiality_obligations"
    if "permitted disclosure" in q:
        return "confidentiality_permitted_disclosure"
    if "return or destruction" in q:
        return "return_or_destruction"
    if "residual knowledge" in q:
        return "residual_knowledge"
    if "no-license-granted" in q or "no license granted" in q:
        return "no_license_granted"
    if "non-use clause" in q or "non use clause" in q:
        return "confidentiality_non_use"
    if "exclusions from confidentiality" in q:
        return "confidentiality_exclusion"
    if "confidentiality" in q:
        return "confidentiality"

    return "other"
