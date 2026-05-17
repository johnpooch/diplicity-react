from common.constants import ProvinceType


SCHEMA_VERSION = 1


def variant_to_canonical_dict(variant):
    nations = list(variant.nations.all())
    provinces = list(variant.provinces.all())
    nation_id_by_pk = {nation.pk: nation.nation_id for nation in nations}
    province_id_by_pk = {province.pk: province.province_id for province in provinces}
    template_phase = variant.template_phase

    canonical_provinces = []
    canonical_named_coasts = []
    for province in provinces:
        if province.type == ProvinceType.NAMED_COAST:
            canonical_named_coasts.append(
                {
                    "id": province.province_id,
                    "name": province.name,
                    "parentProvince": province_id_by_pk[province.parent_id],
                    "adjacencies": province.adjacencies,
                }
            )
            continue
        canonical_province = {
            "id": province.province_id,
            "name": province.name,
            "type": province.type,
            "supplyCenter": province.supply_center,
            "adjacencies": province.adjacencies,
        }
        if province.home_nation_id is not None:
            canonical_province["homeNation"] = nation_id_by_pk[province.home_nation_id]
        canonical_provinces.append(canonical_province)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "id": variant.id,
        "name": variant.name,
        "description": variant.description,
        "author": variant.author,
        "rules": variant.rules,
        "victoryConditions": variant.victory_conditions,
        "adjudicationModifiers": variant.adjudication_modifiers,
        "phaseProgression": variant.phase_progression,
        "nations": [
            {"id": nation.nation_id, "name": nation.name, "color": nation.color}
            for nation in nations
        ],
        "provinces": canonical_provinces,
        "namedCoasts": canonical_named_coasts,
        "initialState": {
            "phase": {
                "season": template_phase.season,
                "year": template_phase.year,
                "type": template_phase.type,
            },
            "units": [
                {
                    "nation": nation_id_by_pk[unit.nation_id],
                    "type": unit.type,
                    "location": province_id_by_pk[unit.province_id],
                }
                for unit in template_phase.units.all()
            ],
            "supplyCenters": [
                {
                    "nation": nation_id_by_pk[supply_center.nation_id],
                    "province": province_id_by_pk[supply_center.province_id],
                }
                for supply_center in template_phase.supply_centers.all()
            ],
        },
    }
