#include "config.h"
#include "types.h"
#include "save.h"

/**
 *  Pokémon Monsoon difficulty rules.
 *
 *  DIFFICULTY_VARIABLE is set when the player picks a difficulty at the start of the game: 0 = Normal, 1 = Insane.
 *  Insane trainer teams are handled in src/field/enemy_party.c.  This file holds the other Insane rules:
 *  a badge-based level cap and the forced Set battle style.
 */

#ifdef DIFFICULTY_VARIABLE

/**
 *  @brief whether the player chose Insane difficulty
 *
 *  @return TRUE on Insane, FALSE on Normal
 */
BOOL LONG_CALL IsInsaneDifficulty(void)
{
    return GetScriptVar(DIFFICULTY_VARIABLE) == 1;
}

// Insane level cap by number of badges owned (index = badge count).
// Placeholder values follow HeartGold's gym leader aces until the Varsha gyms replace them.
static const u8 sInsaneLevelCaps[] = {
    13,  // 0 badges: Falkner's Pidgeotto
    17,  // 1: Bugsy's Scyther
    19,  // 2: Whitney's Miltank
    25,  // 3: Morty's Gengar
    31,  // 4: Chuck's Poliwrath
    35,  // 5: Jasmine's Steelix
    35,  // 6: Pryce's Piloswine is 34, so the cap holds at 35
    41,  // 7: Clair's Kingdra
    50,  // 8: Champion Lance's Dragonite
    54,  // 9 and up: Kanto gym leaders
    56,
    56,
    57,
    58,
    59,
    60,
    100, // 16 badges: no cap
};

/**
 *  @brief count the badges the player owns (Johto and Kanto)
 *
 *  @return number of badges, 0-16
 */
static u32 CountPlayerBadges(void)
{
    struct PlayerProfile *profile = Sav2_PlayerData_GetProfileAddr(SaveBlock2_get());
    u32 count = 0;

    for (int i = 0; i < 16; i++) {
        if (PlayerProfile_TestBadgeFlag(profile, i) == TRUE) {
            count++;
        }
    }

    return count;
}

/**
 *  @brief level cap for the current difficulty
 *
 *  @return the Insane cap for the player's badge count, or 0 (no cap) on Normal
 */
u32 LONG_CALL GetDifficultyLevelCap(void)
{
    if (!IsInsaneDifficulty()) {
        return 0;
    }

    u32 badges = CountPlayerBadges();
    if (badges >= NELEMS(sInsaneLevelCaps)) {
        badges = NELEMS(sInsaneLevelCaps) - 1;
    }

    return sInsaneLevelCaps[badges];
}

/**
 *  @brief replaces the battle style getter at 0x0202AD90 (see hooks).  Insane always battles in Set style;
 *         Normal uses the player's option.
 *
 *  @param options the player's options
 *  @return 1 for Set, 0 for Shift
 */
u32 LONG_CALL Options_GetBattleStyle_Difficulty(struct OPTIONS *options)
{
    if (IsInsaneDifficulty()) {
        return 1;
    }

    return options->battleStyle;
}

#endif // DIFFICULTY_VARIABLE
