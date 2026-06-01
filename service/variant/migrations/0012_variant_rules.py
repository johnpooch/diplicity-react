from django.db import migrations, models


RULES = {
    "classical": (
        "The first to 18 Supply Centers (SC) is the winner.\n"
        "Kiel and Constantinople have a canal, so fleets can exit on either side.\n"
        "Armies can move from Denmark to Kiel."
    ),
    "italy-vs-germany": (
        "The first to 18 supply centers is the winner.\n"
        "The game only has two nations: Italy and Germany."
    ),
    "hundred": (
        "First to 9 Supply Centers (SC) is the winner.\n"
        "Units may be built on any owned SC.\n"
        "France starts with 5 units and 4 SCs, so needs to disband unless they "
        "gain a center before 1430.\n"
        "Yearly cycles of Spring & Fall are renamed to decade cycles with years "
        "ending with 5 and 0 respectively.\n"
        "Armies & fleets can move between London & Calais.\n"
        "Two provinces have dual coasts: Northumbria and Aragon."
    ),
    "youngstown-redux": (
        "First to 28 Supply Centers (SC) wins. If two nations have 28 SCs, the "
        "one with most wins. If drawn, the game continues an extra year.\n"
        "Fleets can move around the world via box sea regions, which are "
        "connected to the other ones in the same row and column.\n"
        "Six provinces have dual coasts: Spain, St. Petersburg, Levant, Arabia, "
        "Hebei, and Thailand.\n"
        "The Arctic region is impassable (Omsk & Siberia are land regions).\n"
        "This variant is based on the Youngstown variant by Rod Walker, "
        "A. Phillips, Ken Lowe and Jon Monsarret."
    ),
    "vietnam-war": (
        "First to 15 Supply Centers (SC) wins.\n"
        "All provinces connected to the Mekong river are coastal: Xuyen, Mekong, "
        "Pakxe and Ubon (e.g. Laos can build fleets in Pakxe).\n"
        "Two provinces have dual coasts: Xuyen and Mekong (South coast and River)."
    ),
    "canton": (
        "First to 19 Supply Centers (SC) is the winner.\n"
        "Constantinople and Egypt have a canal (similar to Kiel in Classic).\n"
        "Four provinces have dual coasts: Damascus, Bulgaria, Siam and Canton."
    ),
}


def backfill_rules(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    for variant_id, rules in RULES.items():
        Variant.objects.filter(id=variant_id).update(rules=rules)


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0011_variant_phase_progression"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="rules",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(backfill_rules, migrations.RunPython.noop),
    ]
