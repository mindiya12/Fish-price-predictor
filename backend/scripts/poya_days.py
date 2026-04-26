"""
Sri Lanka Poya Day Lookup
=========================
Poya days are full-moon public holidays observed in Sri Lanka every month.
Fish markets typically see a demand spike in the 1-2 days BEFORE Poya and
a sharp DROP on the day itself (market closed). This is a major signal
the model was previously blind to.

Sources:
  - Department of Buddhist Affairs, Sri Lanka
  - Government holiday notifications (Gazette Extraordinary)

Coverage: 2020-01-01 to 2028-12-31
"""

from datetime import date

# Full set of Sri Lanka Poya dates
POYA_DATES: set[date] = {
    # 2020
    date(2020, 1, 10),   # Duruthu
    date(2020, 2, 9),    # Navam
    date(2020, 3, 9),    # Medin
    date(2020, 4, 8),    # Bak
    date(2020, 5, 7),    # Vesak
    date(2020, 6, 5),    # Poson
    date(2020, 7, 5),    # Esala
    date(2020, 8, 3),    # Nikini
    date(2020, 9, 2),    # Binara
    date(2020, 10, 1),   # Vap
    date(2020, 10, 31),  # Il
    date(2020, 11, 30),  # Unduvap
    date(2020, 12, 30),  # Duruthu

    # 2021
    date(2021, 1, 28),   # Duruthu
    date(2021, 2, 27),   # Navam
    date(2021, 3, 28),   # Medin
    date(2021, 4, 27),   # Bak
    date(2021, 5, 26),   # Vesak
    date(2021, 6, 24),   # Poson
    date(2021, 7, 24),   # Esala
    date(2021, 8, 22),   # Nikini
    date(2021, 9, 20),   # Binara
    date(2021, 10, 20),  # Vap
    date(2021, 11, 19),  # Il
    date(2021, 12, 19),  # Unduvap

    # 2022
    date(2022, 1, 17),   # Duruthu
    date(2022, 2, 16),   # Navam
    date(2022, 3, 18),   # Medin
    date(2022, 4, 16),   # Bak
    date(2022, 5, 16),   # Vesak
    date(2022, 6, 14),   # Poson
    date(2022, 7, 13),   # Esala
    date(2022, 8, 12),   # Nikini
    date(2022, 9, 10),   # Binara
    date(2022, 10, 9),   # Vap
    date(2022, 11, 8),   # Il
    date(2022, 12, 8),   # Unduvap

    # 2023
    date(2023, 1, 7),    # Duruthu
    date(2023, 2, 5),    # Navam
    date(2023, 3, 7),    # Medin
    date(2023, 4, 6),    # Bak
    date(2023, 5, 5),    # Vesak
    date(2023, 6, 4),    # Poson
    date(2023, 7, 3),    # Esala
    date(2023, 8, 1),    # Nikini
    date(2023, 8, 31),   # Binara (Blue Moon month)
    date(2023, 9, 29),   # Vap
    date(2023, 10, 28),  # Il
    date(2023, 11, 27),  # Unduvap
    date(2023, 12, 27),  # Duruthu

    # 2024
    date(2024, 1, 25),   # Duruthu
    date(2024, 2, 24),   # Navam
    date(2024, 3, 25),   # Medin
    date(2024, 4, 23),   # Bak
    date(2024, 5, 23),   # Vesak
    date(2024, 6, 22),   # Poson
    date(2024, 7, 21),   # Esala
    date(2024, 8, 19),   # Nikini
    date(2024, 9, 17),   # Binara
    date(2024, 10, 17),  # Vap
    date(2024, 11, 15),  # Il
    date(2024, 12, 15),  # Unduvap

    # 2025
    date(2025, 1, 13),   # Duruthu
    date(2025, 2, 12),   # Navam
    date(2025, 3, 14),   # Medin
    date(2025, 4, 13),   # Bak
    date(2025, 5, 12),   # Vesak
    date(2025, 6, 11),   # Poson
    date(2025, 7, 10),   # Esala
    date(2025, 8, 9),    # Nikini
    date(2025, 9, 7),    # Binara
    date(2025, 10, 7),   # Vap
    date(2025, 11, 5),   # Il
    date(2025, 12, 5),   # Unduvap

    # 2026
    date(2026, 1, 3),    # Duruthu
    date(2026, 2, 1),    # Navam
    date(2026, 3, 3),    # Medin
    date(2026, 4, 2),    # Bak
    date(2026, 5, 1),    # Vesak
    date(2026, 5, 31),   # Poson
    date(2026, 6, 30),   # Esala
    date(2026, 7, 29),   # Nikini
    date(2026, 8, 28),   # Binara
    date(2026, 9, 26),   # Vap
    date(2026, 10, 26),  # Il
    date(2026, 11, 25),  # Unduvap
    date(2026, 12, 25),  # Duruthu

    # 2027
    date(2027, 1, 23),
    date(2027, 2, 22),
    date(2027, 3, 24),
    date(2027, 4, 22),
    date(2027, 5, 22),
    date(2027, 6, 20),
    date(2027, 7, 20),
    date(2027, 8, 18),
    date(2027, 9, 16),
    date(2027, 10, 16),
    date(2027, 11, 14),
    date(2027, 12, 14),

    # 2028
    date(2028, 1, 13),
    date(2028, 2, 11),
    date(2028, 3, 12),
    date(2028, 4, 11),
    date(2028, 5, 11),
    date(2028, 6, 9),
    date(2028, 7, 9),
    date(2028, 8, 7),
    date(2028, 9, 5),
    date(2028, 10, 5),
    date(2028, 11, 3),
    date(2028, 12, 3),
}

# Sorted list for distance calculations
_POYA_SORTED = sorted(POYA_DATES)


def days_to_nearest_poya(d: date) -> int:
    """
    Returns the number of days to the nearest Poya day (past or future).
    Returns 0 if the day itself is a Poya.
    """
    if d in POYA_DATES:
        return 0
    return min(abs((d - p).days) for p in _POYA_SORTED)


def days_until_next_poya(d: date) -> int:
    """
    Returns the number of days until the NEXT upcoming Poya day.
    Returns 0 on a Poya day.
    """
    if d in POYA_DATES:
        return 0
    future = [p for p in _POYA_SORTED if p >= d]
    return (future[0] - d).days if future else 30  # fallback


def days_since_last_poya(d: date) -> int:
    """
    Returns the number of days since the LAST Poya day.
    Returns 0 on a Poya day.
    """
    if d in POYA_DATES:
        return 0
    past = [p for p in _POYA_SORTED if p <= d]
    return (d - past[-1]).days if past else 30  # fallback
