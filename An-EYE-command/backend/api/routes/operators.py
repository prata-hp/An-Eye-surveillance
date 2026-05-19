from datetime import datetime

from fastapi import APIRouter


router = APIRouter(tags=["operators"])

FAKE_OPERATORS = {
    "operator1": {
        "name": "Nitish Sinha",
        "role": "Operator",
        "city": "Patna",
        "precinct": "South Belt",
        "desk": "Command Desk 02",
    },
    "supervisor1": {
        "name": "Rahul Verma",
        "role": "Supervisor",
        "city": "Patna",
        "precinct": "Central Belt",
        "desk": "Supervisor Desk Alpha",
    },
    "admin1": {
        "name": "Admin Command",
        "role": "Admin",
        "city": "Patna",
        "precinct": "Central Command",
        "desk": "Admin Desk",
    },
}


def get_shift():
    hour = datetime.now().hour

    if 6 <= hour < 14:
        return "Shift A"

    if 14 <= hour < 22:
        return "Shift B"

    return "Shift C"


@router.get("/me")
def get_me(username: str = "operator1"):
    operator = FAKE_OPERATORS.get(username)

    if not operator:
        return {
            "error": "Operator not found",
        }

    return {
        **operator,
        "shift": get_shift(),
    }
