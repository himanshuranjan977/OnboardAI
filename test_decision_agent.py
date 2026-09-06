from agents.decision import (
    make_decision,
)


identity = {

    "identity_status":
        "MATCH",

    "match_score":
        1.0,
}


risk = {

    "risk_score":
        0,

    "risk_level":
        "LOW",

    "risk_factors":
        [],

    "recommendation":
        "CONTINUE",
}


result = make_decision(

    identity_verification=
        identity,

    risk_assessment=
        risk,
)


print(
    "\nDECISION RESULT"
)

print(
    "================"
)

print(
    f"Decision: "
    f"{result['decision']}"
)

print(
    f"Reason: "
    f"{result['reason']}"
)

print(
    f"Risk Level: "
    f"{result['risk_level']}"
)

print(
    f"Risk Score: "
    f"{result['risk_score']}"
)

print(
    "Decision Basis:"
)

for item in result[
    "decision_basis"
]:

    print(
        f"- {item}"
    )