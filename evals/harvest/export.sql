with selected_games as (
    select id, variant_id, press_type, status
    from game_game
    where id = any(string_to_array(:'games', ','))
),
selected_phases as (
    select phase.id, phase.game_id, phase.ordinal, phase.season, phase.year, phase.type, phase.status,
           phase.contested_provinces
    from phase_phase phase
    join selected_games game on game.id = phase.game_id
)
select json_build_object(
    'games', (
        select coalesce(json_agg(json_build_object(
            'id', game.id,
            'variant', game.variant_id,
            'press_type', game.press_type,
            'status', game.status
        ) order by game.id), '[]')
        from selected_games game
    ),
    'phases', (
        select coalesce(json_agg(json_build_object(
            'id', phase.id,
            'game', phase.game_id,
            'ordinal', phase.ordinal,
            'season', phase.season,
            'year', phase.year,
            'type', phase.type,
            'status', phase.status,
            'contested_provinces', phase.contested_provinces
        ) order by phase.game_id, phase.ordinal, phase.id), '[]')
        from selected_phases phase
    ),
    'units', (
        select coalesce(json_agg(json_build_object(
            'phase', unit.phase_id,
            'province', province.province_id,
            'type', unit.type,
            'nation', nation.name,
            'dislodged', unit.dislodged,
            'dislodged_from', coalesce(dislodged_from_parent.province_id, dislodged_from.province_id)
        ) order by unit.phase_id, province.province_id), '[]')
        from unit_unit unit
        join selected_phases phase on phase.id = unit.phase_id
        join province_province province on province.id = unit.province_id
        join nation_nation nation on nation.id = unit.nation_id
        left join province_province dislodged_from on dislodged_from.id = unit.dislodged_from_id
        left join province_province dislodged_from_parent on dislodged_from_parent.id = dislodged_from.parent_id
    ),
    'supply_centers', (
        select coalesce(json_agg(json_build_object(
            'phase', supply_center.phase_id,
            'province', province.province_id,
            'nation', nation.name
        ) order by supply_center.phase_id, province.province_id), '[]')
        from supply_center_supplycenter supply_center
        join selected_phases phase on phase.id = supply_center.phase_id
        join province_province province on province.id = supply_center.province_id
        join nation_nation nation on nation.id = supply_center.nation_id
    ),
    'orders', (
        select coalesce(json_agg(json_build_object(
            'phase', phase_state.phase_id,
            'nation', nation.name,
            'order_type', orders.order_type,
            'source', source.province_id,
            'target', target.province_id,
            'aux', aux.province_id,
            'unit_type', orders.unit_type,
            'named_coast', named_coast.province_id,
            'resolution', resolution.status
        ) order by phase_state.phase_id, nation.name, source.province_id), '[]')
        from order_order orders
        join phase_phasestate phase_state on phase_state.id = orders.phase_state_id
        join selected_phases phase on phase.id = phase_state.phase_id
        join member_member member on member.id = phase_state.member_id
        join nation_nation nation on nation.id = member.nation_id
        join province_province source on source.id = orders.source_id
        left join province_province target on target.id = orders.target_id
        left join province_province aux on aux.id = orders.aux_id
        left join province_province named_coast on named_coast.id = orders.named_coast_id
        left join order_orderresolution resolution on resolution.order_id = orders.id
        where not orders.is_implicit
    ),
    'players', (
        select coalesce(json_agg(json_build_object(
            'phase', phase_state.phase_id,
            'nation', nation.name,
            'was_bot', coalesce(profile.kind <> 'human', false)
        ) order by phase_state.phase_id, nation.name), '[]')
        from phase_phasestate phase_state
        join selected_phases phase on phase.id = phase_state.phase_id
        join member_member member on member.id = phase_state.member_id
        join nation_nation nation on nation.id = member.nation_id
        left join user_profile_userprofile profile on profile.user_id = member.user_id
    )
);
