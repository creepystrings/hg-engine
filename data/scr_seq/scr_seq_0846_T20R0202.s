.include "asm/include/interop_macros.inc"

.include "asm/include/scriptmacros.inc"
.include "asm/include/flags.inc"
.include "asm/include/soundeffects.inc"
.include "asm/include/vars.inc"

.include "asm/include/events.inc"
.include "asm/include/game_stats.inc"
.include "asm/include/maps.inc"
.include "asm/include/map_sections.inc"
.include "asm/include/movements.inc"
.include "asm/include/rankings.inc"
.include "asm/include/spawns.inc"
.include "asm/include/std_scripts.inc"
.include "asm/include/trainers.inc"

#include "config.h"
#include "constants/item.h"
#include "constants/moves.h"
#include "constants/species.h"

.include "data/scr_seq/include/event_T20R0202.inc"


// text archive to grab from: 546.txt

.data


scrdef scr_seq_T20R0202_000
scrdef scr_seq_T20R0202_001
scrdef_end

scr_seq_T20R0202_000:
	scrcmd_609
	lockall
	play_se SEQ_SE_DP_PC_ON
	buffer_players_name 0
	npc_msg 0
	closemsg
	scrcmd_377 VAR_SPECIAL_RESULT
	compare VAR_SPECIAL_RESULT, 0
	goto_if_eq _004B
	fade_screen 6, 1, 0, RGB_BLACK
	wait_fade
	scrcmd_376
	restore_overworld
	fade_screen 6, 1, 1, RGB_BLACK
	wait_fade
	releaseall
	end

_004B:
	npc_msg 1
	wait_button
	closemsg
	releaseall
	end

scr_seq_T20R0202_001:
	play_se SEQ_SE_DP_SELECT
	lockall
#ifdef MONSOON_TEST_MEGA
	// test only: the first time the Wii is checked, give the Mega Ring and the starters Mega Stones and enable Mega Evolution
	goto_if_set FLAG_MEGA_EVOLUTION_ENABLED, _wii_normal
	npc_msg 3
	setvar VAR_SPECIAL_x8004, ITEM_MEGA_RING
	setvar VAR_SPECIAL_x8005, 1
	callstd std_give_item_verbose
	setvar VAR_SPECIAL_x8004, ITEM_SCEPTILITE
	setvar VAR_SPECIAL_x8005, 1
	callstd std_give_item_verbose
	setvar VAR_SPECIAL_x8004, ITEM_BLAZIKENITE
	setvar VAR_SPECIAL_x8005, 1
	callstd std_give_item_verbose
	setvar VAR_SPECIAL_x8004, ITEM_SWAMPERTITE
	setvar VAR_SPECIAL_x8005, 1
	callstd std_give_item_verbose
	setflag FLAG_MEGA_EVOLUTION_ENABLED
	give_mon SPECIES_SCEPTILE, 36, ITEM_SCEPTILITE, 0, 0, VAR_SPECIAL_RESULT
	npc_msg 4
	wait_button
	closemsg
	releaseall
	end

_wii_normal:
#endif // MONSOON_TEST_MEGA
	npc_msg 2
	wait_button
	closemsg
	releaseall
	end
	.balign 4
