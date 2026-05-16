# Backfills Province.adjacencies for classical, italy-vs-germany and hundred.
#
# Adjacency data was extracted from the godip Go library. Each province's
# adjacencies are stored as a list of {"to", "pass"} entries. The migration
# verifies that every edge is mirrored on its other endpoint before writing;
# an asymmetric edge aborts the migration.

from django.db import migrations


ADJACENCIES = {
    "classical": {
        "adr": [{"to": "alb", "pass": "fleet"}, {"to": "apu", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "tri", "pass": "fleet"}, {"to": "ven", "pass": "fleet"}],
        "aeg": [{"to": "bul", "pass": "fleet"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "eas", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "smy", "pass": "fleet"}],
        "alb": [{"to": "adr", "pass": "fleet"}, {"to": "gre", "pass": "both"}, {"to": "ion", "pass": "fleet"}, {"to": "ser", "pass": "army"}, {"to": "tri", "pass": "both"}],
        "ank": [{"to": "arm", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "both"}, {"to": "smy", "pass": "army"}],
        "apu": [{"to": "adr", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "nap", "pass": "both"}, {"to": "rom", "pass": "army"}, {"to": "ven", "pass": "both"}],
        "arm": [{"to": "ank", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "sev", "pass": "both"}, {"to": "smy", "pass": "army"}, {"to": "syr", "pass": "army"}],
        "bal": [{"to": "ber", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "den", "pass": "fleet"}, {"to": "kie", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}, {"to": "pru", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "bar": [{"to": "nrg", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "stp", "pass": "fleet"}, {"to": "stp/nc", "pass": "fleet"}],
        "bel": [{"to": "bur", "pass": "army"}, {"to": "eng", "pass": "fleet"}, {"to": "hol", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "pic", "pass": "both"}, {"to": "ruh", "pass": "army"}],
        "ber": [{"to": "bal", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "mun", "pass": "army"}, {"to": "pru", "pass": "both"}, {"to": "sil", "pass": "army"}],
        "bla": [{"to": "ank", "pass": "fleet"}, {"to": "arm", "pass": "fleet"}, {"to": "bul", "pass": "fleet"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "rum", "pass": "fleet"}, {"to": "sev", "pass": "fleet"}],
        "boh": [{"to": "gal", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "tyr", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "bot": [{"to": "bal", "pass": "fleet"}, {"to": "fin", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}, {"to": "stp", "pass": "fleet"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "bre": [{"to": "eng", "pass": "fleet"}, {"to": "gas", "pass": "both"}, {"to": "mid", "pass": "fleet"}, {"to": "par", "pass": "army"}, {"to": "pic", "pass": "both"}],
        "bud": [{"to": "gal", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "bul": [{"to": "aeg", "pass": "fleet"}, {"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "army"}, {"to": "gre", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "ser", "pass": "army"}],
        "bul/ec": [{"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "rum", "pass": "fleet"}],
        "bul/sc": [{"to": "aeg", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}],
        "bur": [{"to": "bel", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "mar", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "par", "pass": "army"}, {"to": "pic", "pass": "army"}, {"to": "ruh", "pass": "army"}],
        "cly": [{"to": "edi", "pass": "both"}, {"to": "lvp", "pass": "both"}, {"to": "nat", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}],
        "con": [{"to": "aeg", "pass": "fleet"}, {"to": "ank", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "bul", "pass": "army"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "smy", "pass": "both"}],
        "den": [{"to": "bal", "pass": "fleet"}, {"to": "hel", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "eas": [{"to": "aeg", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "smy", "pass": "fleet"}, {"to": "syr", "pass": "fleet"}],
        "edi": [{"to": "cly", "pass": "both"}, {"to": "lvp", "pass": "army"}, {"to": "nrg", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "yor", "pass": "both"}],
        "eng": [{"to": "bel", "pass": "fleet"}, {"to": "bre", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "pic", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "fin": [{"to": "bot", "pass": "fleet"}, {"to": "nwy", "pass": "army"}, {"to": "stp", "pass": "army"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "gal": [{"to": "boh", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "ukr", "pass": "army"}, {"to": "vie", "pass": "army"}, {"to": "war", "pass": "army"}],
        "gas": [{"to": "bre", "pass": "both"}, {"to": "bur", "pass": "army"}, {"to": "mar", "pass": "army"}, {"to": "mid", "pass": "fleet"}, {"to": "par", "pass": "army"}, {"to": "spa", "pass": "army"}, {"to": "spa/nc", "pass": "fleet"}],
        "gol": [{"to": "mar", "pass": "fleet"}, {"to": "pie", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "tus", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "gre": [{"to": "aeg", "pass": "fleet"}, {"to": "alb", "pass": "both"}, {"to": "bul", "pass": "army"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "ser", "pass": "army"}],
        "hel": [{"to": "den", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "kie", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}],
        "hol": [{"to": "bel", "pass": "both"}, {"to": "hel", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "ruh", "pass": "army"}],
        "ion": [{"to": "adr", "pass": "fleet"}, {"to": "aeg", "pass": "fleet"}, {"to": "alb", "pass": "fleet"}, {"to": "apu", "pass": "fleet"}, {"to": "eas", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}, {"to": "nap", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}],
        "iri": [{"to": "eng", "pass": "fleet"}, {"to": "lvp", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "kie": [{"to": "bal", "pass": "fleet"}, {"to": "ber", "pass": "both"}, {"to": "den", "pass": "both"}, {"to": "hel", "pass": "fleet"}, {"to": "hol", "pass": "both"}, {"to": "mun", "pass": "army"}, {"to": "ruh", "pass": "army"}],
        "lon": [{"to": "eng", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "wal", "pass": "both"}, {"to": "yor", "pass": "both"}],
        "lvn": [{"to": "bal", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "mos", "pass": "army"}, {"to": "pru", "pass": "both"}, {"to": "stp", "pass": "army"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "war", "pass": "army"}],
        "lvp": [{"to": "cly", "pass": "both"}, {"to": "edi", "pass": "army"}, {"to": "iri", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "wal", "pass": "both"}, {"to": "yor", "pass": "army"}],
        "mar": [{"to": "bur", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "gol", "pass": "fleet"}, {"to": "pie", "pass": "both"}, {"to": "spa", "pass": "army"}, {"to": "spa/sc", "pass": "fleet"}],
        "mid": [{"to": "bre", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "gas", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "naf", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "por", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/nc", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "mos": [{"to": "lvn", "pass": "army"}, {"to": "sev", "pass": "army"}, {"to": "stp", "pass": "army"}, {"to": "ukr", "pass": "army"}, {"to": "war", "pass": "army"}],
        "mun": [{"to": "ber", "pass": "army"}, {"to": "boh", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "kie", "pass": "army"}, {"to": "ruh", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "naf": [{"to": "mid", "pass": "fleet"}, {"to": "tun", "pass": "both"}, {"to": "wes", "pass": "fleet"}],
        "nap": [{"to": "apu", "pass": "both"}, {"to": "ion", "pass": "fleet"}, {"to": "rom", "pass": "both"}, {"to": "tys", "pass": "fleet"}],
        "nat": [{"to": "cly", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lvp", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}],
        "nrg": [{"to": "bar", "pass": "fleet"}, {"to": "cly", "pass": "fleet"}, {"to": "edi", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}],
        "nth": [{"to": "bel", "pass": "fleet"}, {"to": "den", "pass": "fleet"}, {"to": "edi", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "hel", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "yor", "pass": "fleet"}],
        "nwy": [{"to": "bar", "pass": "fleet"}, {"to": "fin", "pass": "army"}, {"to": "nrg", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "stp", "pass": "army"}, {"to": "stp/nc", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "par": [{"to": "bre", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "pic", "pass": "army"}],
        "pic": [{"to": "bel", "pass": "both"}, {"to": "bre", "pass": "both"}, {"to": "bur", "pass": "army"}, {"to": "eng", "pass": "fleet"}, {"to": "par", "pass": "army"}],
        "pie": [{"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "both"}, {"to": "tus", "pass": "both"}, {"to": "tyr", "pass": "army"}, {"to": "ven", "pass": "army"}],
        "por": [{"to": "mid", "pass": "fleet"}, {"to": "spa", "pass": "army"}, {"to": "spa/nc", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}],
        "pru": [{"to": "bal", "pass": "fleet"}, {"to": "ber", "pass": "both"}, {"to": "lvn", "pass": "both"}, {"to": "sil", "pass": "army"}, {"to": "war", "pass": "army"}],
        "rom": [{"to": "apu", "pass": "army"}, {"to": "nap", "pass": "both"}, {"to": "tus", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "ven", "pass": "army"}],
        "ruh": [{"to": "bel", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "hol", "pass": "army"}, {"to": "kie", "pass": "army"}, {"to": "mun", "pass": "army"}],
        "rum": [{"to": "bla", "pass": "fleet"}, {"to": "bud", "pass": "army"}, {"to": "bul", "pass": "army"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "gal", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "sev", "pass": "both"}, {"to": "ukr", "pass": "army"}],
        "ser": [{"to": "alb", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "bul", "pass": "army"}, {"to": "gre", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "tri", "pass": "army"}],
        "sev": [{"to": "arm", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "mos", "pass": "army"}, {"to": "rum", "pass": "both"}, {"to": "ukr", "pass": "army"}],
        "sil": [{"to": "ber", "pass": "army"}, {"to": "boh", "pass": "army"}, {"to": "gal", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "pru", "pass": "army"}, {"to": "war", "pass": "army"}],
        "ska": [{"to": "den", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "smy": [{"to": "aeg", "pass": "fleet"}, {"to": "ank", "pass": "army"}, {"to": "arm", "pass": "army"}, {"to": "con", "pass": "both"}, {"to": "eas", "pass": "fleet"}, {"to": "syr", "pass": "both"}],
        "spa": [{"to": "gas", "pass": "army"}, {"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "army"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "army"}, {"to": "wes", "pass": "fleet"}],
        "spa/nc": [{"to": "gas", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "fleet"}],
        "spa/sc": [{"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "stp": [{"to": "bar", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "fin", "pass": "army"}, {"to": "lvn", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "nwy", "pass": "army"}],
        "stp/nc": [{"to": "bar", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}],
        "stp/sc": [{"to": "bot", "pass": "fleet"}, {"to": "fin", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}],
        "swe": [{"to": "bal", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "den", "pass": "both"}, {"to": "fin", "pass": "both"}, {"to": "nwy", "pass": "both"}, {"to": "ska", "pass": "fleet"}],
        "syr": [{"to": "arm", "pass": "army"}, {"to": "eas", "pass": "fleet"}, {"to": "smy", "pass": "both"}],
        "tri": [{"to": "adr", "pass": "fleet"}, {"to": "alb", "pass": "both"}, {"to": "bud", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "tyr", "pass": "army"}, {"to": "ven", "pass": "both"}, {"to": "vie", "pass": "army"}],
        "tun": [{"to": "ion", "pass": "fleet"}, {"to": "naf", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "tus": [{"to": "gol", "pass": "fleet"}, {"to": "pie", "pass": "both"}, {"to": "rom", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "ven", "pass": "army"}],
        "tyr": [{"to": "boh", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "pie", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "ven", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "tys": [{"to": "gol", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "nap", "pass": "fleet"}, {"to": "rom", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tus", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "ukr": [{"to": "gal", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "sev", "pass": "army"}, {"to": "war", "pass": "army"}],
        "ven": [{"to": "adr", "pass": "fleet"}, {"to": "apu", "pass": "both"}, {"to": "pie", "pass": "army"}, {"to": "rom", "pass": "army"}, {"to": "tri", "pass": "both"}, {"to": "tus", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "vie": [{"to": "boh", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "gal", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "wal": [{"to": "eng", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lon", "pass": "both"}, {"to": "lvp", "pass": "both"}, {"to": "yor", "pass": "army"}],
        "war": [{"to": "gal", "pass": "army"}, {"to": "lvn", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "pru", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "ukr", "pass": "army"}],
        "wes": [{"to": "gol", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "naf", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}],
        "yor": [{"to": "edi", "pass": "both"}, {"to": "lon", "pass": "both"}, {"to": "lvp", "pass": "army"}, {"to": "nth", "pass": "fleet"}, {"to": "wal", "pass": "army"}],
    },
    "italy-vs-germany": {
        "adr": [{"to": "alb", "pass": "fleet"}, {"to": "apu", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "tri", "pass": "fleet"}, {"to": "ven", "pass": "fleet"}],
        "aeg": [{"to": "bul", "pass": "fleet"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "eas", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "smy", "pass": "fleet"}],
        "alb": [{"to": "adr", "pass": "fleet"}, {"to": "gre", "pass": "both"}, {"to": "ion", "pass": "fleet"}, {"to": "ser", "pass": "army"}, {"to": "tri", "pass": "both"}],
        "ank": [{"to": "arm", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "both"}, {"to": "smy", "pass": "army"}],
        "apu": [{"to": "adr", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "nap", "pass": "both"}, {"to": "rom", "pass": "army"}, {"to": "ven", "pass": "both"}],
        "arm": [{"to": "ank", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "sev", "pass": "both"}, {"to": "smy", "pass": "army"}, {"to": "syr", "pass": "army"}],
        "bal": [{"to": "ber", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "den", "pass": "fleet"}, {"to": "kie", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}, {"to": "pru", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "bar": [{"to": "nrg", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "stp", "pass": "fleet"}, {"to": "stp/nc", "pass": "fleet"}],
        "bel": [{"to": "bur", "pass": "army"}, {"to": "eng", "pass": "fleet"}, {"to": "hol", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "pic", "pass": "both"}, {"to": "ruh", "pass": "army"}],
        "ber": [{"to": "bal", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "mun", "pass": "army"}, {"to": "pru", "pass": "both"}, {"to": "sil", "pass": "army"}],
        "bla": [{"to": "ank", "pass": "fleet"}, {"to": "arm", "pass": "fleet"}, {"to": "bul", "pass": "fleet"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "rum", "pass": "fleet"}, {"to": "sev", "pass": "fleet"}],
        "boh": [{"to": "gal", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "tyr", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "bot": [{"to": "bal", "pass": "fleet"}, {"to": "fin", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}, {"to": "stp", "pass": "fleet"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "bre": [{"to": "eng", "pass": "fleet"}, {"to": "gas", "pass": "both"}, {"to": "mid", "pass": "fleet"}, {"to": "par", "pass": "army"}, {"to": "pic", "pass": "both"}],
        "bud": [{"to": "gal", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "bul": [{"to": "aeg", "pass": "fleet"}, {"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "army"}, {"to": "gre", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "ser", "pass": "army"}],
        "bul/ec": [{"to": "bla", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "rum", "pass": "fleet"}],
        "bul/sc": [{"to": "aeg", "pass": "fleet"}, {"to": "con", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}],
        "bur": [{"to": "bel", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "mar", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "par", "pass": "army"}, {"to": "pic", "pass": "army"}, {"to": "ruh", "pass": "army"}],
        "cly": [{"to": "edi", "pass": "both"}, {"to": "lvp", "pass": "both"}, {"to": "nat", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}],
        "con": [{"to": "aeg", "pass": "fleet"}, {"to": "ank", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "bul", "pass": "army"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "smy", "pass": "both"}],
        "den": [{"to": "bal", "pass": "fleet"}, {"to": "hel", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "eas": [{"to": "aeg", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "smy", "pass": "fleet"}, {"to": "syr", "pass": "fleet"}],
        "edi": [{"to": "cly", "pass": "both"}, {"to": "lvp", "pass": "army"}, {"to": "nrg", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "yor", "pass": "both"}],
        "eng": [{"to": "bel", "pass": "fleet"}, {"to": "bre", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "pic", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "fin": [{"to": "bot", "pass": "fleet"}, {"to": "nwy", "pass": "army"}, {"to": "stp", "pass": "army"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "gal": [{"to": "boh", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "ukr", "pass": "army"}, {"to": "vie", "pass": "army"}, {"to": "war", "pass": "army"}],
        "gas": [{"to": "bre", "pass": "both"}, {"to": "bur", "pass": "army"}, {"to": "mar", "pass": "army"}, {"to": "mid", "pass": "fleet"}, {"to": "par", "pass": "army"}, {"to": "spa", "pass": "army"}, {"to": "spa/nc", "pass": "fleet"}],
        "gol": [{"to": "mar", "pass": "fleet"}, {"to": "pie", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "tus", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "gre": [{"to": "aeg", "pass": "fleet"}, {"to": "alb", "pass": "both"}, {"to": "bul", "pass": "army"}, {"to": "bul/sc", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "ser", "pass": "army"}],
        "hel": [{"to": "den", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "kie", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}],
        "hol": [{"to": "bel", "pass": "both"}, {"to": "hel", "pass": "fleet"}, {"to": "kie", "pass": "both"}, {"to": "nth", "pass": "fleet"}, {"to": "ruh", "pass": "army"}],
        "ion": [{"to": "adr", "pass": "fleet"}, {"to": "aeg", "pass": "fleet"}, {"to": "alb", "pass": "fleet"}, {"to": "apu", "pass": "fleet"}, {"to": "eas", "pass": "fleet"}, {"to": "gre", "pass": "fleet"}, {"to": "nap", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}],
        "iri": [{"to": "eng", "pass": "fleet"}, {"to": "lvp", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "kie": [{"to": "bal", "pass": "fleet"}, {"to": "ber", "pass": "both"}, {"to": "den", "pass": "both"}, {"to": "hel", "pass": "fleet"}, {"to": "hol", "pass": "both"}, {"to": "mun", "pass": "army"}, {"to": "ruh", "pass": "army"}],
        "lon": [{"to": "eng", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "wal", "pass": "both"}, {"to": "yor", "pass": "both"}],
        "lvn": [{"to": "bal", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "mos", "pass": "army"}, {"to": "pru", "pass": "both"}, {"to": "stp", "pass": "army"}, {"to": "stp/sc", "pass": "fleet"}, {"to": "war", "pass": "army"}],
        "lvp": [{"to": "cly", "pass": "both"}, {"to": "edi", "pass": "army"}, {"to": "iri", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "wal", "pass": "both"}, {"to": "yor", "pass": "army"}],
        "mar": [{"to": "bur", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "gol", "pass": "fleet"}, {"to": "pie", "pass": "both"}, {"to": "spa", "pass": "army"}, {"to": "spa/sc", "pass": "fleet"}],
        "mid": [{"to": "bre", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "gas", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "naf", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "por", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/nc", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "mos": [{"to": "lvn", "pass": "army"}, {"to": "sev", "pass": "army"}, {"to": "stp", "pass": "army"}, {"to": "ukr", "pass": "army"}, {"to": "war", "pass": "army"}],
        "mun": [{"to": "ber", "pass": "army"}, {"to": "boh", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "kie", "pass": "army"}, {"to": "ruh", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "naf": [{"to": "mid", "pass": "fleet"}, {"to": "tun", "pass": "both"}, {"to": "wes", "pass": "fleet"}],
        "nap": [{"to": "apu", "pass": "both"}, {"to": "ion", "pass": "fleet"}, {"to": "rom", "pass": "both"}, {"to": "tys", "pass": "fleet"}],
        "nat": [{"to": "cly", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lvp", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}],
        "nrg": [{"to": "bar", "pass": "fleet"}, {"to": "cly", "pass": "fleet"}, {"to": "edi", "pass": "fleet"}, {"to": "nat", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}],
        "nth": [{"to": "bel", "pass": "fleet"}, {"to": "den", "pass": "fleet"}, {"to": "edi", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "hel", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "nrg", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "yor", "pass": "fleet"}],
        "nwy": [{"to": "bar", "pass": "fleet"}, {"to": "fin", "pass": "army"}, {"to": "nrg", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "ska", "pass": "fleet"}, {"to": "stp", "pass": "army"}, {"to": "stp/nc", "pass": "fleet"}, {"to": "swe", "pass": "both"}],
        "par": [{"to": "bre", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "gas", "pass": "army"}, {"to": "pic", "pass": "army"}],
        "pic": [{"to": "bel", "pass": "both"}, {"to": "bre", "pass": "both"}, {"to": "bur", "pass": "army"}, {"to": "eng", "pass": "fleet"}, {"to": "par", "pass": "army"}],
        "pie": [{"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "both"}, {"to": "tus", "pass": "both"}, {"to": "tyr", "pass": "army"}, {"to": "ven", "pass": "army"}],
        "por": [{"to": "mid", "pass": "fleet"}, {"to": "spa", "pass": "army"}, {"to": "spa/nc", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}],
        "pru": [{"to": "bal", "pass": "fleet"}, {"to": "ber", "pass": "both"}, {"to": "lvn", "pass": "both"}, {"to": "sil", "pass": "army"}, {"to": "war", "pass": "army"}],
        "rom": [{"to": "apu", "pass": "army"}, {"to": "nap", "pass": "both"}, {"to": "tus", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "ven", "pass": "army"}],
        "ruh": [{"to": "bel", "pass": "army"}, {"to": "bur", "pass": "army"}, {"to": "hol", "pass": "army"}, {"to": "kie", "pass": "army"}, {"to": "mun", "pass": "army"}],
        "rum": [{"to": "bla", "pass": "fleet"}, {"to": "bud", "pass": "army"}, {"to": "bul", "pass": "army"}, {"to": "bul/ec", "pass": "fleet"}, {"to": "gal", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "sev", "pass": "both"}, {"to": "ukr", "pass": "army"}],
        "ser": [{"to": "alb", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "bul", "pass": "army"}, {"to": "gre", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "tri", "pass": "army"}],
        "sev": [{"to": "arm", "pass": "both"}, {"to": "bla", "pass": "fleet"}, {"to": "mos", "pass": "army"}, {"to": "rum", "pass": "both"}, {"to": "ukr", "pass": "army"}],
        "sil": [{"to": "ber", "pass": "army"}, {"to": "boh", "pass": "army"}, {"to": "gal", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "pru", "pass": "army"}, {"to": "war", "pass": "army"}],
        "ska": [{"to": "den", "pass": "fleet"}, {"to": "nth", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}, {"to": "swe", "pass": "fleet"}],
        "smy": [{"to": "aeg", "pass": "fleet"}, {"to": "ank", "pass": "army"}, {"to": "arm", "pass": "army"}, {"to": "con", "pass": "both"}, {"to": "eas", "pass": "fleet"}, {"to": "syr", "pass": "both"}],
        "spa": [{"to": "gas", "pass": "army"}, {"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "army"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "army"}, {"to": "wes", "pass": "fleet"}],
        "spa/nc": [{"to": "gas", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "fleet"}],
        "spa/sc": [{"to": "gol", "pass": "fleet"}, {"to": "mar", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "por", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "stp": [{"to": "bar", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "fin", "pass": "army"}, {"to": "lvn", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "nwy", "pass": "army"}],
        "stp/nc": [{"to": "bar", "pass": "fleet"}, {"to": "nwy", "pass": "fleet"}],
        "stp/sc": [{"to": "bot", "pass": "fleet"}, {"to": "fin", "pass": "fleet"}, {"to": "lvn", "pass": "fleet"}],
        "swe": [{"to": "bal", "pass": "fleet"}, {"to": "bot", "pass": "fleet"}, {"to": "den", "pass": "both"}, {"to": "fin", "pass": "both"}, {"to": "nwy", "pass": "both"}, {"to": "ska", "pass": "fleet"}],
        "syr": [{"to": "arm", "pass": "army"}, {"to": "eas", "pass": "fleet"}, {"to": "smy", "pass": "both"}],
        "tri": [{"to": "adr", "pass": "fleet"}, {"to": "alb", "pass": "both"}, {"to": "bud", "pass": "army"}, {"to": "ser", "pass": "army"}, {"to": "tyr", "pass": "army"}, {"to": "ven", "pass": "both"}, {"to": "vie", "pass": "army"}],
        "tun": [{"to": "ion", "pass": "fleet"}, {"to": "naf", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "tus": [{"to": "gol", "pass": "fleet"}, {"to": "pie", "pass": "both"}, {"to": "rom", "pass": "both"}, {"to": "tys", "pass": "fleet"}, {"to": "ven", "pass": "army"}],
        "tyr": [{"to": "boh", "pass": "army"}, {"to": "mun", "pass": "army"}, {"to": "pie", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "ven", "pass": "army"}, {"to": "vie", "pass": "army"}],
        "tys": [{"to": "gol", "pass": "fleet"}, {"to": "ion", "pass": "fleet"}, {"to": "nap", "pass": "fleet"}, {"to": "rom", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tus", "pass": "fleet"}, {"to": "wes", "pass": "fleet"}],
        "ukr": [{"to": "gal", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "rum", "pass": "army"}, {"to": "sev", "pass": "army"}, {"to": "war", "pass": "army"}],
        "ven": [{"to": "adr", "pass": "fleet"}, {"to": "apu", "pass": "both"}, {"to": "pie", "pass": "army"}, {"to": "rom", "pass": "army"}, {"to": "tri", "pass": "both"}, {"to": "tus", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "vie": [{"to": "boh", "pass": "army"}, {"to": "bud", "pass": "army"}, {"to": "gal", "pass": "army"}, {"to": "tri", "pass": "army"}, {"to": "tyr", "pass": "army"}],
        "wal": [{"to": "eng", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "lon", "pass": "both"}, {"to": "lvp", "pass": "both"}, {"to": "yor", "pass": "army"}],
        "war": [{"to": "gal", "pass": "army"}, {"to": "lvn", "pass": "army"}, {"to": "mos", "pass": "army"}, {"to": "pru", "pass": "army"}, {"to": "sil", "pass": "army"}, {"to": "ukr", "pass": "army"}],
        "wes": [{"to": "gol", "pass": "fleet"}, {"to": "mid", "pass": "fleet"}, {"to": "naf", "pass": "fleet"}, {"to": "spa", "pass": "fleet"}, {"to": "spa/sc", "pass": "fleet"}, {"to": "tun", "pass": "fleet"}, {"to": "tys", "pass": "fleet"}],
        "yor": [{"to": "edi", "pass": "both"}, {"to": "lon", "pass": "both"}, {"to": "lvp", "pass": "army"}, {"to": "nth", "pass": "fleet"}, {"to": "wal", "pass": "army"}],
    },
    "hundred": {
        "als": [{"to": "can", "pass": "army"}, {"to": "lor", "pass": "army"}],
        "ang": [{"to": "dev", "pass": "army"}, {"to": "lon", "pass": "both"}, {"to": "nos", "pass": "fleet"}, {"to": "not", "pass": "army"}, {"to": "not/ec", "pass": "fleet"}, {"to": "str", "pass": "fleet"}, {"to": "thw", "pass": "fleet"}],
        "anj": [{"to": "brt", "pass": "army"}, {"to": "nom", "pass": "army"}, {"to": "orl", "pass": "army"}],
        "ara": [{"to": "cas", "pass": "army"}, {"to": "guy", "pass": "army"}, {"to": "tou", "pass": "army"}],
        "ara/nc": [{"to": "bis", "pass": "fleet"}, {"to": "cas", "pass": "fleet"}, {"to": "guy", "pass": "fleet"}],
        "ara/sc": [{"to": "cas", "pass": "fleet"}, {"to": "med", "pass": "fleet"}, {"to": "tou", "pass": "fleet"}],
        "atl": [{"to": "bis", "pass": "fleet"}, {"to": "brs", "pass": "fleet"}, {"to": "cas", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "med", "pass": "fleet"}, {"to": "thp", "pass": "fleet"}],
        "bis": [{"to": "ara/nc", "pass": "fleet"}, {"to": "atl", "pass": "fleet"}, {"to": "brs", "pass": "fleet"}, {"to": "brt", "pass": "fleet"}, {"to": "cas", "pass": "fleet"}, {"to": "guy", "pass": "fleet"}],
        "brs": [{"to": "atl", "pass": "fleet"}, {"to": "bis", "pass": "fleet"}, {"to": "brt", "pass": "fleet"}, {"to": "dev", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "brt": [{"to": "anj", "pass": "army"}, {"to": "bis", "pass": "fleet"}, {"to": "brs", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "guy", "pass": "both"}, {"to": "nom", "pass": "both"}, {"to": "orl", "pass": "army"}, {"to": "poi", "pass": "army"}],
        "cal": [{"to": "dij", "pass": "army"}, {"to": "fla", "pass": "both"}, {"to": "lon", "pass": "both"}, {"to": "nom", "pass": "both"}, {"to": "par", "pass": "army"}, {"to": "str", "pass": "fleet"}],
        "can": [{"to": "als", "pass": "army"}, {"to": "dau", "pass": "army"}, {"to": "dij", "pass": "army"}, {"to": "lor", "pass": "army"}, {"to": "sav", "pass": "army"}],
        "cas": [{"to": "ara", "pass": "army"}, {"to": "ara/nc", "pass": "fleet"}, {"to": "ara/sc", "pass": "fleet"}, {"to": "atl", "pass": "fleet"}, {"to": "bis", "pass": "fleet"}, {"to": "med", "pass": "fleet"}],
        "cha": [{"to": "dau", "pass": "army"}, {"to": "dij", "pass": "army"}, {"to": "par", "pass": "army"}],
        "dau": [{"to": "can", "pass": "army"}, {"to": "cha", "pass": "army"}, {"to": "dij", "pass": "army"}, {"to": "lim", "pass": "army"}, {"to": "orl", "pass": "army"}, {"to": "par", "pass": "army"}, {"to": "pro", "pass": "army"}, {"to": "sav", "pass": "army"}],
        "dev": [{"to": "ang", "pass": "army"}, {"to": "brs", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "lon", "pass": "both"}, {"to": "not", "pass": "army"}, {"to": "wal", "pass": "both"}],
        "dij": [{"to": "cal", "pass": "army"}, {"to": "can", "pass": "army"}, {"to": "cha", "pass": "army"}, {"to": "dau", "pass": "army"}, {"to": "fla", "pass": "army"}, {"to": "lor", "pass": "army"}, {"to": "lux", "pass": "army"}, {"to": "par", "pass": "army"}],
        "eng": [{"to": "brs", "pass": "fleet"}, {"to": "brt", "pass": "fleet"}, {"to": "dev", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "nom", "pass": "fleet"}, {"to": "str", "pass": "fleet"}],
        "fla": [{"to": "cal", "pass": "both"}, {"to": "dij", "pass": "army"}, {"to": "hol", "pass": "both"}, {"to": "lux", "pass": "army"}, {"to": "str", "pass": "fleet"}],
        "fri": [{"to": "hol", "pass": "both"}, {"to": "lux", "pass": "army"}, {"to": "thw", "pass": "fleet"}],
        "guy": [{"to": "ara", "pass": "army"}, {"to": "ara/nc", "pass": "fleet"}, {"to": "bis", "pass": "fleet"}, {"to": "brt", "pass": "both"}, {"to": "poi", "pass": "army"}, {"to": "tou", "pass": "army"}],
        "hol": [{"to": "fla", "pass": "both"}, {"to": "fri", "pass": "both"}, {"to": "lux", "pass": "army"}, {"to": "str", "pass": "fleet"}, {"to": "thw", "pass": "fleet"}],
        "iri": [{"to": "atl", "pass": "fleet"}, {"to": "brs", "pass": "fleet"}, {"to": "min", "pass": "fleet"}, {"to": "not/wc", "pass": "fleet"}, {"to": "sco", "pass": "fleet"}, {"to": "thp", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "lim": [{"to": "dau", "pass": "army"}, {"to": "orl", "pass": "army"}, {"to": "poi", "pass": "army"}, {"to": "pro", "pass": "army"}, {"to": "tou", "pass": "army"}],
        "lon": [{"to": "ang", "pass": "both"}, {"to": "cal", "pass": "both"}, {"to": "dev", "pass": "both"}, {"to": "eng", "pass": "fleet"}, {"to": "str", "pass": "fleet"}],
        "lor": [{"to": "als", "pass": "army"}, {"to": "can", "pass": "army"}, {"to": "dij", "pass": "army"}, {"to": "lux", "pass": "army"}],
        "lux": [{"to": "dij", "pass": "army"}, {"to": "fla", "pass": "army"}, {"to": "fri", "pass": "army"}, {"to": "hol", "pass": "army"}, {"to": "lor", "pass": "army"}],
        "med": [{"to": "ara/sc", "pass": "fleet"}, {"to": "atl", "pass": "fleet"}, {"to": "cas", "pass": "fleet"}, {"to": "pro", "pass": "fleet"}, {"to": "sav", "pass": "fleet"}, {"to": "tou", "pass": "fleet"}],
        "min": [{"to": "iri", "pass": "fleet"}, {"to": "nos", "pass": "fleet"}, {"to": "sco", "pass": "fleet"}, {"to": "thp", "pass": "fleet"}],
        "nom": [{"to": "anj", "pass": "army"}, {"to": "brt", "pass": "both"}, {"to": "cal", "pass": "both"}, {"to": "eng", "pass": "fleet"}, {"to": "orl", "pass": "army"}, {"to": "par", "pass": "army"}, {"to": "str", "pass": "fleet"}],
        "nos": [{"to": "ang", "pass": "fleet"}, {"to": "min", "pass": "fleet"}, {"to": "not/ec", "pass": "fleet"}, {"to": "sco", "pass": "fleet"}, {"to": "thw", "pass": "fleet"}],
        "not": [{"to": "ang", "pass": "army"}, {"to": "dev", "pass": "army"}, {"to": "sco", "pass": "army"}, {"to": "wal", "pass": "army"}],
        "not/ec": [{"to": "ang", "pass": "fleet"}, {"to": "nos", "pass": "fleet"}, {"to": "sco", "pass": "fleet"}],
        "not/wc": [{"to": "iri", "pass": "fleet"}, {"to": "sco", "pass": "fleet"}, {"to": "wal", "pass": "fleet"}],
        "orl": [{"to": "anj", "pass": "army"}, {"to": "brt", "pass": "army"}, {"to": "dau", "pass": "army"}, {"to": "lim", "pass": "army"}, {"to": "nom", "pass": "army"}, {"to": "par", "pass": "army"}, {"to": "poi", "pass": "army"}],
        "par": [{"to": "cal", "pass": "army"}, {"to": "cha", "pass": "army"}, {"to": "dau", "pass": "army"}, {"to": "dij", "pass": "army"}, {"to": "nom", "pass": "army"}, {"to": "orl", "pass": "army"}],
        "poi": [{"to": "brt", "pass": "army"}, {"to": "guy", "pass": "army"}, {"to": "lim", "pass": "army"}, {"to": "orl", "pass": "army"}, {"to": "tou", "pass": "army"}],
        "pro": [{"to": "dau", "pass": "army"}, {"to": "lim", "pass": "army"}, {"to": "med", "pass": "fleet"}, {"to": "sav", "pass": "both"}, {"to": "tou", "pass": "both"}],
        "sav": [{"to": "can", "pass": "army"}, {"to": "dau", "pass": "army"}, {"to": "med", "pass": "fleet"}, {"to": "pro", "pass": "both"}],
        "sco": [{"to": "iri", "pass": "fleet"}, {"to": "min", "pass": "fleet"}, {"to": "nos", "pass": "fleet"}, {"to": "not", "pass": "army"}, {"to": "not/ec", "pass": "fleet"}, {"to": "not/wc", "pass": "fleet"}],
        "str": [{"to": "ang", "pass": "fleet"}, {"to": "cal", "pass": "fleet"}, {"to": "eng", "pass": "fleet"}, {"to": "fla", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "lon", "pass": "fleet"}, {"to": "nom", "pass": "fleet"}, {"to": "thw", "pass": "fleet"}],
        "thp": [{"to": "atl", "pass": "fleet"}, {"to": "iri", "pass": "fleet"}, {"to": "min", "pass": "fleet"}],
        "thw": [{"to": "ang", "pass": "fleet"}, {"to": "fri", "pass": "fleet"}, {"to": "hol", "pass": "fleet"}, {"to": "nos", "pass": "fleet"}, {"to": "str", "pass": "fleet"}],
        "tou": [{"to": "ara", "pass": "army"}, {"to": "ara/sc", "pass": "fleet"}, {"to": "guy", "pass": "army"}, {"to": "lim", "pass": "army"}, {"to": "med", "pass": "fleet"}, {"to": "poi", "pass": "army"}, {"to": "pro", "pass": "both"}],
        "wal": [{"to": "brs", "pass": "fleet"}, {"to": "dev", "pass": "both"}, {"to": "iri", "pass": "fleet"}, {"to": "not", "pass": "army"}, {"to": "not/wc", "pass": "fleet"}],
    },
}


def _check_symmetry(variant_id, adjacency_map):
    edges = set()
    for source, adjacencies in adjacency_map.items():
        for adjacency in adjacencies:
            edges.add((source, adjacency["to"], adjacency["pass"]))
    for source, target, pass_ in sorted(edges):
        if (target, source, pass_) not in edges:
            raise ValueError(
                f"{variant_id}: adjacency {source} -> {target} ({pass_}) "
                f"is not mirrored on the other side"
            )


def backfill_adjacencies(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Province = apps.get_model("province", "Province")
    for variant_id, adjacency_map in ADJACENCIES.items():
        _check_symmetry(variant_id, adjacency_map)
        variant = Variant.objects.get(id=variant_id)
        for province_id, adjacencies in adjacency_map.items():
            province = Province.objects.get(variant=variant, province_id=province_id)
            province.adjacencies = adjacencies
            province.save(update_fields=["adjacencies"])


def clear_adjacencies(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Province = apps.get_model("province", "Province")
    for variant_id in ADJACENCIES:
        variant = Variant.objects.get(id=variant_id)
        Province.objects.filter(variant=variant).update(adjacencies=[])


class Migration(migrations.Migration):

    dependencies = [
        ("province", "0015_add_province_adjacencies"),
    ]

    operations = [
        migrations.RunPython(backfill_adjacencies, clear_adjacencies),
    ]
