# Nation handicaps derived from vDiplomacy per-country results. Each variant
# notes how many vDiplomacy games its values are based on.
#
# - Each vDiplomacy country row (solos, draws, survivals, eliminated) is
#   turned into the head-to-head pairings our design uses. A solo winner or a
#   drawer beats every non-winner, drawers tie with each other, and losers are
#   scored only against winners. The variant's draw-size distribution decides
#   how many opponents each result implies.
# - A rating offset is then fit per nation so expected and actual pairing
#   scores match, using the same Elo curve as rating/calculation.py, and each
#   variant is centred on 0.
# - Small samples are pulled toward 0, assuming nations in a variant typically
#   differ by about +-60, so thin data doesn't produce large offsets.

from django.db import migrations

HANDICAPS = {
    "classical": {  # 2,005 vDiplomacy games
        "France": 25,
        "Turkey": 21,
        "England": 15,
        "Germany": -3,
        "Russia": -11,
        "Italy": -17,
        "Austria": -30,
    },
    "italy-vs-germany": {  # 2,394 vDiplomacy games
        "Germany": 41,
        "Italy": -41,
    },
    "cold-war": {  # 3,438 vDiplomacy games
        "NATO": 3,
        "USSR": -3,
    },
    "ancient-mediterranean": {  # 806 vDiplomacy games
        "Carthage": 34,
        "Persia": 18,
        "Rome": 6,
        "Egypt": -27,
        "Greece": -30,
    },
    "hundred": {  # 415 vDiplomacy games
        "Burgundy": 43,
        "England": -7,
        "France": -37,
    },
    "youngstown-redux": {  # 206 vDiplomacy games
        "Japan": 65,
        "India": 48,
        "Austria": 12,
        "Italy": 3,
        "China": 2,
        "Germany": -6,
        "Britain": -25,
        "Russia": -29,
        "Turkey": -29,
        "France": -40,
    },
    "europe-1939": {  # 283 vDiplomacy games
        "Germany": 34,
        "Britain": 18,
        "USSR": 17,
        "Italy": 8,
        "Spain": -4,
        "Poland": -8,
        "Turkey": -31,
        "France": -34,
    },
    "155-france-vs-austria": {  # 3,624 vDiplomacy games
        "Austria": 26,
        "France": -26,
    },
    "canton": {  # 93 vDiplomacy games
        "Turkey": 23,
        "Britain": 15,
        "Holland": 10,
        "China": 8,
        "Japan": 4,
        "Russia": -22,
        "France": -38,
    },
    "spice-islands": {  # 66 vDiplomacy games
        "Sultanate of Ternate": 41,
        "Kingdom of Dai Viet": 26,
        "Sultanate of Malacca": 18,
        "Kingdom of Tondo": 6,
        "Sultanate of Brunei": -9,
        "Kingdom of Majapahit": -23,
        "Kingdom of Ayutthaya": -60,
    },
    "12-south-america": {  # 259 vDiplomacy games
        "Peru": 48,
        "Columbia": -1,
        "Chile": -8,
        "Argentina": -15,
        "Brazil": -25,
    },
    "1132-modern-diplomacy-two": {  # 463 vDiplomacy games
        "Poland": 25,
        "Egypt": 17,
        "United Kingdom": 11,
        "Ukraine": 5,
        "Germany": 3,
        "Turkey": -1,
        "Spain": -7,
        "Italy": -11,
        "Russia": -12,
        "France": -30,
    },
    "south-of-sahara": {  # 38 vDiplomacy games
        "Jolof": 48,
        "Bonoman": 23,
        "Benin": 8,
        "Mali": -38,
        "Bornu": -40,
    },
    "12-classical-fleet-rome": {  # 43 vDiplomacy games
        "Russia": 49,
        "Italy": 4,
        "Austria": -1,
        "Germany": -2,
        "England": -6,
        "Turkey": -18,
        "France": -26,
    },
}


def seed(apps, schema_editor):
    Nation = apps.get_model("nation", "Nation")
    NationHandicap = apps.get_model("rating", "NationHandicap")

    for variant_id, offsets in HANDICAPS.items():
        nations = {
            nation.name: nation
            for nation in Nation.objects.filter(
                variant_id=variant_id, non_playable=False
            )
        }
        if not nations:
            continue
        if set(nations) != set(offsets):
            raise ValueError(
                f"Handicaps for {variant_id} do not match its playable nations"
            )
        for name, offset in offsets.items():
            NationHandicap.objects.update_or_create(
                nation=nations[name], defaults={"offset": offset}
            )


def unseed(apps, schema_editor):
    NationHandicap = apps.get_model("rating", "NationHandicap")
    NationHandicap.objects.filter(nation__variant_id__in=list(HANDICAPS)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rating", "0001_initial"),
        ("nation", "0015_resanitize_nation_flags"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
