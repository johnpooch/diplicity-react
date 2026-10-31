class ReportReason:
    ABUSE_AND_HARASSMENT = "abuse_and_harassment"
    MULTIPLE_ACCOUNTS = "multiple_accounts"
    SECRET_TEAMING = "secret_teaming"
    OTHER = "other"

    REASONS = (
        {
            "key": ABUSE_AND_HARASSMENT,
            "label": "Abuse and harassment",
            "description": (
                "This player insulted or demeaned other players, used slurs, or "
                "attacked someone's race, ethnicity, nationality, religion, gender, "
                "sexuality, disability or age."
            ),
        },
        {
            "key": MULTIPLE_ACCOUNTS,
            "label": "Multiple accounts",
            "description": (
                "This player is using a second account to play more than one power "
                "in this game."
            ),
        },
        {
            "key": SECRET_TEAMING,
            "label": "Secret teaming",
            "description": (
                "This player entered the game with someone they know outside of it "
                "and is secretly coordinating with them as a team."
            ),
        },
        {
            "key": OTHER,
            "label": "Other",
            "description": (
                "This player broke the code of conduct in a way not listed here."
            ),
        },
    )

    REASON_CHOICES = tuple((reason["key"], reason["label"]) for reason in REASONS)


class ReportDecision:
    APPROVED = "approved"
    REJECTED = "rejected"

    DECISION_CHOICES = (
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    )


class ReportStatus:
    PENDING = "pending"
    APPROVED = ReportDecision.APPROVED
    REJECTED = ReportDecision.REJECTED

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        *ReportDecision.DECISION_CHOICES,
    )
