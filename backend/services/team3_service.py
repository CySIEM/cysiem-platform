class Team3Service:

    def get_threats(self):
        return [
            {"day": "Mon", "critical": 3, "high": 5, "medium": 8},
            {"day": "Tue", "critical": 4, "high": 6, "medium": 10},
            {"day": "Wed", "critical": 2, "high": 4, "medium": 7},
            {"day": "Thu", "critical": 5, "high": 7, "medium": 9},
            {"day": "Fri", "critical": 3, "high": 6, "medium": 8},
            {"day": "Sat", "critical": 1, "high": 3, "medium": 5},
            {"day": "Sun", "critical": 2, "high": 4, "medium": 6}
        ]

    def get_recommendations(self):
        return [
            {
                "id": 1,
                "priority": "High",
                "title": "Patch Critical Vulnerabilities",
                "description": "Apply the latest security patches to all critical servers."
            },
            {
                "id": 2,
                "priority": "Medium",
                "title": "Enable Multi-Factor Authentication",
                "description": "Enable MFA for all administrator accounts."
            },
            {
                "id": 3,
                "priority": "Low",
                "title": "Review Firewall Rules",
                "description": "Remove unused firewall rules and close unnecessary ports."
            }
        ]