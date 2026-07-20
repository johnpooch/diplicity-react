from django.dispatch import Signal

game_deleted_by_master = Signal()
game_deadline_extended = Signal()
member_kicked_from_staging = Signal()
member_removed_from_staging = Signal()
nmr_extensions_applied = Signal()
