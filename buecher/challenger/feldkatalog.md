# Feldkatalog (Auftrag 029, Schritt 2)

Alle Felder, die in 2822 Partien wirklich vorkommen. **da** = Feld vorhanden, **Wert** = vorhanden und ungleich 0/leer/falsch (bei Zaehlern also: kam vor). Nenner: Spieler-Partien (`spieler`), Teams (`team`), Spieler-Minuten (`minute`, aus der Zeitleiste), Ereignisse der jeweiligen Art (`ereignis.*`).

## Ereignisarten der Zeitleiste (Anzahl gesamt, je Partie)

| Art | Anzahl | je Partie |
|---|---:|---:|
| ITEM_PURCHASED | 641409 | 227.3 |
| ITEM_DESTROYED | 607522 | 215.3 |
| WARD_PLACED | 557891 | 197.7 |
| SKILL_LEVEL_UP | 413089 | 146.4 |
| LEVEL_UP | 377948 | 133.9 |
| CHAMPION_KILL | 155943 | 55.3 |
| TURRET_PLATE_DESTROYED | 151965 | 53.9 |
| WARD_KILL | 112845 | 40.0 |
| BUILDING_KILL | 34734 | 12.3 |
| ITEM_SOLD | 26227 | 9.3 |
| ELITE_MONSTER_KILL | 23941 | 8.5 |
| ITEM_UNDO | 22477 | 8.0 |
| CHAMPION_SPECIAL_KILL | 21758 | 7.7 |
| DRAGON_SOUL_GIVEN | 3287 | 1.2 |
| OBJECTIVE_BOUNTY_PRESTART | 2903 | 1.0 |
| PAUSE_END | 2822 | 1.0 |
| GAME_END | 2822 | 1.0 |
| OBJECTIVE_BOUNTY_FINISH | 992 | 0.4 |
| CHAMPION_TRANSFORM | 49 | 0.0 |

## ereignis.BUILDING_KILL (8 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `assistingParticipantIds` | 49% | 49% |
| `bounty` | 100% | 3% |
| `buildingType` | 100% | 100% |
| `killerId` | 100% | 96% |
| `laneType` | 100% | 100% |
| `position` | 100% | 100% |
| `teamId` | 100% | 100% |
| `towerType` | 89% | 89% |

## ereignis.CHAMPION_KILL (11 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `assistingParticipantIds` | 80% | 80% |
| `bounty` | 100% | 100% |
| `killStreakLength` | 100% | 52% |
| `killerId` | 100% | 100% |
| `position` | 100% | 100% |
| `shutdownBounty` | 100% | 16% |
| `victimDamageDealt` | 92% | 92% |
| `victimDamageReceived` | 100% | 100% |
| `victimId` | 100% | 100% |
| `victimTeamfightDamageDealt` | 95% | 95% |
| `victimTeamfightDamageReceived` | 100% | 100% |

## ereignis.CHAMPION_SPECIAL_KILL (4 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `killType` | 100% | 100% |
| `killerId` | 100% | 100% |
| `multiKillLength` | 75% | 75% |
| `position` | 100% | 100% |

## ereignis.CHAMPION_TRANSFORM (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `participantId` | 100% | 100% |
| `transformType` | 100% | 100% |

## ereignis.DRAGON_SOUL_GIVEN (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `name` | 100% | 100% |
| `teamId` | 100% | 18% |

## ereignis.ELITE_MONSTER_KILL (7 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `assistingParticipantIds` | 57% | 57% |
| `bounty` | 100% | 1% |
| `killerId` | 100% | 99% |
| `killerTeamId` | 100% | 100% |
| `monsterSubType` | 42% | 42% |
| `monsterType` | 100% | 100% |
| `position` | 100% | 100% |

## ereignis.GAME_END (3 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `gameId` | 100% | 100% |
| `realTimestamp` | 100% | 100% |
| `winningTeam` | 100% | 100% |

## ereignis.ITEM_DESTROYED (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `itemId` | 100% | 100% |
| `participantId` | 100% | 100% |

## ereignis.ITEM_PURCHASED (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `itemId` | 100% | 100% |
| `participantId` | 100% | 99% |

## ereignis.ITEM_SOLD (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `itemId` | 100% | 100% |
| `participantId` | 100% | 100% |

## ereignis.ITEM_UNDO (4 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `afterId` | 100% | 13% |
| `beforeId` | 100% | 86% |
| `goldGain` | 100% | 97% |
| `participantId` | 100% | 100% |

## ereignis.LEVEL_UP (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `level` | 100% | 100% |
| `participantId` | 100% | 100% |

## ereignis.OBJECTIVE_BOUNTY_FINISH (1 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `teamId` | 100% | 100% |

## ereignis.OBJECTIVE_BOUNTY_PRESTART (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `actualStartTime` | 100% | 100% |
| `teamId` | 100% | 100% |

## ereignis.PAUSE_END (1 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `realTimestamp` | 100% | 100% |

## ereignis.SKILL_LEVEL_UP (3 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `levelUpType` | 100% | 100% |
| `participantId` | 100% | 99% |
| `skillSlot` | 100% | 100% |

## ereignis.TURRET_PLATE_DESTROYED (4 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `killerId` | 100% | 68% |
| `laneType` | 100% | 100% |
| `position` | 100% | 100% |
| `teamId` | 100% | 100% |

## ereignis.WARD_KILL (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `killerId` | 100% | 100% |
| `wardType` | 100% | 100% |

## ereignis.WARD_PLACED (2 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `creatorId` | 100% | 95% |
| `wardType` | 100% | 100% |

## info (14 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `endOfGameResult` | 100% | 100% |
| `gameCreation` | 100% | 100% |
| `gameDuration` | 100% | 100% |
| `gameEndTimestamp` | 100% | 100% |
| `gameId` | 100% | 100% |
| `gameMode` | 100% | 100% |
| `gameName` | 100% | 100% |
| `gameStartTimestamp` | 100% | 100% |
| `gameType` | 100% | 100% |
| `gameVersion` | 100% | 100% |
| `mapId` | 100% | 100% |
| `platformId` | 100% | 100% |
| `queueId` | 100% | 100% |
| `tournamentCode` | 100% | 0% |

## minute (11 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `currentGold` | 100% | 98% |
| `goldPerSecond` | 100% | 20% |
| `jungleMinionsKilled` | 100% | 30% |
| `level` | 100% | 100% |
| `minionsKilled` | 100% | 89% |
| `participantId` | 100% | 100% |
| `position.x` | 100% | 100% |
| `position.y` | 100% | 100% |
| `timeEnemySpentControlled` | 100% | 90% |
| `totalGold` | 100% | 100% |
| `xp` | 100% | 93% |

## minute.championStats (25 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `abilityHaste` | 100% | 0% |
| `abilityPower` | 100% | 43% |
| `armor` | 100% | 100% |
| `armorPen` | 100% | 0% |
| `armorPenPercent` | 100% | 6% |
| `attackDamage` | 100% | 100% |
| `attackSpeed` | 100% | 100% |
| `bonusArmorPenPercent` | 100% | 0% |
| `bonusMagicPenPercent` | 100% | 0% |
| `ccReduction` | 100% | 20% |
| `cooldownReduction` | 100% | 0% |
| `health` | 100% | 90% |
| `healthMax` | 100% | 100% |
| `healthRegen` | 100% | 100% |
| `lifesteal` | 100% | 12% |
| `magicPen` | 100% | 9% |
| `magicPenPercent` | 100% | 5% |
| `magicResist` | 100% | 100% |
| `movementSpeed` | 100% | 100% |
| `omnivamp` | 100% | 26% |
| `physicalVamp` | 100% | 0% |
| `power` | 100% | 94% |
| `powerMax` | 100% | 97% |
| `powerRegen` | 100% | 90% |
| `spellVamp` | 100% | 0% |

## minute.damageStats (12 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `magicDamageDone` | 100% | 86% |
| `magicDamageDoneToChampions` | 100% | 83% |
| `magicDamageTaken` | 100% | 91% |
| `physicalDamageDone` | 100% | 95% |
| `physicalDamageDoneToChampions` | 100% | 91% |
| `physicalDamageTaken` | 100% | 94% |
| `totalDamageDone` | 100% | 95% |
| `totalDamageDoneToChampions` | 100% | 92% |
| `totalDamageTaken` | 100% | 94% |
| `trueDamageDone` | 100% | 88% |
| `trueDamageDoneToChampions` | 100% | 58% |
| `trueDamageTaken` | 100% | 76% |

## spieler (154 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `PlayerBehavior` | 100% | 100% |
| `PlayerScore0` | 100% | 0% |
| `PlayerScore1` | 100% | 0% |
| `PlayerScore10` | 100% | 0% |
| `PlayerScore11` | 100% | 0% |
| `PlayerScore2` | 100% | 0% |
| `PlayerScore3` | 100% | 0% |
| `PlayerScore4` | 100% | 0% |
| `PlayerScore5` | 100% | 0% |
| `PlayerScore6` | 100% | 0% |
| `PlayerScore7` | 100% | 0% |
| `PlayerScore8` | 100% | 0% |
| `PlayerScore9` | 100% | 0% |
| `allInPings` | 100% | 41% |
| `assistMePings` | 100% | 71% |
| `assists` | 100% | 96% |
| `baronKills` | 100% | 9% |
| `basicPings` | 100% | 0% |
| `causedGameEndFromIGNBSurrender` | 100% | 0% |
| `champExperience` | 100% | 100% |
| `champLevel` | 100% | 100% |
| `championId` | 100% | 100% |
| `championName` | 100% | 100% |
| `championTransform` | 100% | 0% |
| `commandPings` | 100% | 90% |
| `consumablesPurchased` | 100% | 94% |
| `damageDealtToBuildings` | 100% | 88% |
| `damageDealtToEpicMonsters` | 100% | 73% |
| `damageDealtToObjectives` | 100% | 96% |
| `damageDealtToTurrets` | 100% | 88% |
| `damageSelfMitigated` | 100% | 100% |
| `dangerPings` | 100% | 2% |
| `deaths` | 100% | 96% |
| `detectorWardsPlaced` | 100% | 57% |
| `doubleKills` | 100% | 32% |
| `dragonKills` | 100% | 19% |
| `eligibleForProgression` | 100% | 100% |
| `enemyMissingPings` | 100% | 90% |
| `enemyVisionPings` | 100% | 68% |
| `firstBloodAssist` | 100% | 8% |
| `firstBloodKill` | 100% | 10% |
| `firstTowerAssist` | 100% | 3% |
| `firstTowerKill` | 100% | 10% |
| `gameEndedInEarlySurrender` | 100% | 0% |
| `gameEndedInIGNBSurrender` | 100% | 0% |
| `gameEndedInSurrender` | 100% | 32% |
| `getBackPings` | 100% | 49% |
| `goldEarned` | 100% | 100% |
| `goldSpent` | 100% | 100% |
| `holdPings` | 100% | 0% |
| `individualPosition` | 100% | 100% |
| `inhibitorKills` | 100% | 12% |
| `inhibitorTakedowns` | 100% | 30% |
| `inhibitorsLost` | 100% | 43% |
| `item0` | 100% | 98% |
| `item1` | 100% | 97% |
| `item2` | 100% | 95% |
| `item3` | 100% | 95% |
| `item4` | 100% | 88% |
| `item5` | 100% | 73% |
| `item6` | 100% | 100% |
| `itemsPurchased` | 100% | 100% |
| `killingSprees` | 100% | 69% |
| `kills` | 100% | 92% |
| `lane` | 100% | 100% |
| `largestCriticalStrike` | 100% | 26% |
| `largestKillingSpree` | 100% | 69% |
| `largestMultiKill` | 100% | 92% |
| `longestTimeSpentLiving` | 100% | 97% |
| `magicDamageDealt` | 100% | 94% |
| `magicDamageDealtToChampions` | 100% | 93% |
| `magicDamageTaken` | 100% | 100% |
| `needVisionPings` | 100% | 24% |
| `neutralMinionsKilled` | 100% | 50% |
| `nexusKills` | 100% | 7% |
| `nexusLost` | 100% | 50% |
| `nexusTakedowns` | 100% | 25% |
| `objectivesStolen` | 100% | 1% |
| `objectivesStolenAssists` | 100% | 0% |
| `onMyWayPings` | 100% | 95% |
| `participantId` | 100% | 100% |
| `pentaKills` | 100% | 0% |
| `perks` | 100% | 100% |
| `physicalDamageDealt` | 100% | 100% |
| `physicalDamageDealtToChampions` | 100% | 100% |
| `physicalDamageTaken` | 100% | 100% |
| `placement` | 100% | 0% |
| `playerAugment1` | 100% | 0% |
| `playerAugment2` | 100% | 0% |
| `playerAugment3` | 100% | 0% |
| `playerAugment4` | 100% | 0% |
| `playerAugment5` | 100% | 0% |
| `playerAugment6` | 100% | 0% |
| `playerSubteamId` | 100% | 0% |
| `positionAssignedByMatchmaking` | 100% | 100% |
| `profileIcon` | 100% | 100% |
| `pushPings` | 100% | 29% |
| `puuid` | 100% | 100% |
| `quadraKills` | 100% | 1% |
| `retreatPings` | 100% | 56% |
| `riotIdGameName` | 100% | 100% |
| `riotIdTagline` | 100% | 100% |
| `role` | 100% | 100% |
| `roleBoundItem` | 100% | 100% |
| `selectedRolePreferences` | 100% | 100% |
| `sightWardsBoughtInGame` | 100% | 0% |
| `spell1Casts` | 100% | 100% |
| `spell2Casts` | 100% | 98% |
| `spell3Casts` | 100% | 97% |
| `spell4Casts` | 100% | 99% |
| `subteamPlacement` | 100% | 0% |
| `summoner1Casts` | 100% | 99% |
| `summoner1Id` | 100% | 100% |
| `summoner2Casts` | 100% | 99% |
| `summoner2Id` | 100% | 100% |
| `summonerId` | 100% | 100% |
| `summonerLevel` | 100% | 100% |
| `summonerName` | 100% | 0% |
| `teamEarlySurrendered` | 100% | 0% |
| `teamIGNBSurrendered` | 100% | 0% |
| `teamId` | 100% | 100% |
| `teamPosition` | 100% | 100% |
| `timeCCingOthers` | 100% | 98% |
| `timePlayed` | 100% | 100% |
| `totalAllyJungleMinionsKilled` | 100% | 38% |
| `totalDamageDealt` | 100% | 100% |
| `totalDamageDealtToChampions` | 100% | 100% |
| `totalDamageShieldedOnTeammates` | 100% | 19% |
| `totalDamageTaken` | 100% | 100% |
| `totalEnemyJungleMinionsKilled` | 100% | 32% |
| `totalHeal` | 100% | 100% |
| `totalHealsOnTeammates` | 100% | 20% |
| `totalMinionsKilled` | 100% | 100% |
| `totalTimeCCDealt` | 100% | 99% |
| `totalTimeSpentDead` | 100% | 96% |
| `totalUnitsHealed` | 100% | 100% |
| `tripleKills` | 100% | 6% |
| `trueDamageDealt` | 100% | 99% |
| `trueDamageDealtToChampions` | 100% | 82% |
| `trueDamageTaken` | 100% | 98% |
| `turretKills` | 100% | 53% |
| `turretTakedowns` | 100% | 69% |
| `turretsLost` | 100% | 92% |
| `unrealKills` | 100% | 0% |
| `visionClearedPings` | 100% | 0% |
| `visionScore` | 100% | 99% |
| `visionWardsBoughtInGame` | 100% | 60% |
| `wardsKilled` | 100% | 86% |
| `wardsPlaced` | 100% | 99% |
| `wasAfk` | 100% | 0% |
| `wasPremadeWithIGNBGameEndCauser` | 100% | 0% |
| `wasPremadeWithSevereTransgressor` | 100% | 0% |
| `wasSevereTransgressor` | 100% | 0% |
| `win` | 100% | 50% |

## spieler.challenges (142 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `12AssistStreakCount` | 100% | 8% |
| `HealFromMapSources` | 100% | 47% |
| `InfernalScalePickup` | 100% | 15% |
| `SWARM_DefeatAatrox` | 100% | 0% |
| `SWARM_DefeatBriar` | 100% | 0% |
| `SWARM_DefeatMiniBosses` | 100% | 0% |
| `SWARM_EvolveWeapon` | 100% | 0% |
| `SWARM_Have3Passives` | 100% | 0% |
| `SWARM_KillEnemy` | 100% | 0% |
| `SWARM_PickupGold` | 100% | 0% |
| `SWARM_ReachLevel50` | 100% | 0% |
| `SWARM_Survive15Min` | 100% | 0% |
| `SWARM_WinWith5EvolvedWeapons` | 100% | 0% |
| `abilityUses` | 100% | 100% |
| `acesBefore15Minutes` | 100% | 1% |
| `alliedJungleMonsterKills` | 100% | 40% |
| `baronBuffGoldAdvantageOverThreshold` | 24% | 24% |
| `baronTakedowns` | 100% | 34% |
| `blastConeOppositeOpponentCount` | 100% | 1% |
| `bountyGold` | 100% | 32% |
| `buffsStolen` | 100% | 17% |
| `completeSupportQuestInTime` | 100% | 14% |
| `controlWardTimeCoverageInRiverOrEnemyHalf` | 50% | 50% |
| `controlWardsPlaced` | 100% | 57% |
| `damagePerMinute` | 100% | 100% |
| `damageTakenOnTeamPercentage` | 100% | 100% |
| `dancedWithRiftHerald` | 100% | 0% |
| `deathsByEnemyChamps` | 100% | 96% |
| `dodgeSkillShotsSmallWindow` | 100% | 39% |
| `doubleAces` | 100% | 0% |
| `dragonTakedowns` | 100% | 44% |
| `earliestBaron` | 44% | 44% |
| `earliestDragonTakedown` | 44% | 44% |
| `earliestElderDragon` | 2% | 2% |
| `earlyLaningPhaseGoldExpAdvantage` | 99% | 9% |
| `effectiveHealAndShielding` | 100% | 26% |
| `elderDragonKillsWithOpposingSoul` | 100% | 1% |
| `elderDragonMultikills` | 100% | 0% |
| `enemyChampionImmobilizations` | 100% | 78% |
| `enemyJungleMonsterKills` | 100% | 34% |
| `epicMonsterKillsNearEnemyJungler` | 100% | 7% |
| `epicMonsterKillsWithin30SecondsOfSpawn` | 100% | 8% |
| `epicMonsterSteals` | 100% | 1% |
| `epicMonsterStolenWithoutSmite` | 100% | 1% |
| `fasterSupportQuestCompletion` | 5% | 5% |
| `fastestLegendary` | 6% | 6% |
| `firstTurretKilled` | 100% | 49% |
| `firstTurretKilledTime` | 49% | 49% |
| `fistBumpParticipation` | 100% | 11% |
| `flawlessAces` | 100% | 16% |
| `fullTeamTakedown` | 100% | 44% |
| `gameLength` | 100% | 100% |
| `getTakedownsInAllLanesEarlyJungleAsLaner` | 80% | 1% |
| `goldPerMinute` | 100% | 100% |
| `hadAfkTeammate` | 1% | 1% |
| `hadOpenNexus` | 100% | 1% |
| `highestChampionDamage` | 10% | 10% |
| `highestCrowdControlScore` | 10% | 10% |
| `highestWardKills` | 12% | 12% |
| `immobilizeAndKillWithAlly` | 100% | 71% |
| `initialBuffCount` | 100% | 20% |
| `initialCrabCount` | 100% | 18% |
| `jungleCsBefore10Minutes` | 100% | 23% |
| `junglerKillsEarlyJungle` | 20% | 2% |
| `junglerTakedownsNearDamagedEpicMonster` | 100% | 7% |
| `kTurretsDestroyedBeforePlatesFall` | 100% | 12% |
| `kda` | 100% | 99% |
| `killAfterHiddenWithAlly` | 100% | 60% |
| `killParticipation` | 100% | 99% |
| `killedChampTookFullTeamDamageSurvived` | 100% | 1% |
| `killingSprees` | 100% | 46% |
| `killsNearEnemyTurret` | 100% | 60% |
| `killsOnLanersEarlyJungleAsJungler` | 20% | 14% |
| `killsOnOtherLanesEarlyJungleAsLaner` | 80% | 12% |
| `killsOnRecentlyHealedByAramPack` | 100% | 0% |
| `killsUnderOwnTurret` | 100% | 41% |
| `killsWithHelpFromEpicMonster` | 100% | 10% |
| `knockEnemyIntoTeamAndKill` | 100% | 29% |
| `landSkillShotsEarlyGame` | 100% | 71% |
| `laneMinionsFirst10Minutes` | 100% | 95% |
| `laningPhaseGoldExpAdvantage` | 99% | 12% |
| `legendaryCount` | 100% | 6% |
| `legendaryItemUsed` | 100% | 99% |
| `lostAnInhibitor` | 100% | 4% |
| `maxCsAdvantageOnLaneOpponent` | 99% | 92% |
| `maxKillDeficit` | 100% | 35% |
| `maxLevelLeadLaneOpponent` | 99% | 94% |
| `mejaisFullStackInTime` | 100% | 0% |
| `moreEnemyJungleThanOpponent` | 100% | 20% |
| `multiKillOneSpell` | 100% | 4% |
| `multiTurretRiftHeraldCount` | 100% | 0% |
| `multikills` | 100% | 32% |
| `multikillsAfterAggressiveFlash` | 100% | 7% |
| `outerTurretExecutesBefore10Minutes` | 100% | 1% |
| `outnumberedKills` | 100% | 49% |
| `outnumberedNexusKill` | 100% | 0% |
| `perfectDragonSoulsTaken` | 100% | 6% |
| `perfectGame` | 100% | 0% |
| `pickKillWithAlly` | 100% | 98% |
| `playedChampSelectPosition` | 99% | 99% |
| `poroExplosions` | 100% | 0% |
| `quickCleanse` | 100% | 2% |
| `quickFirstTurret` | 100% | 0% |
| `quickSoloKills` | 100% | 5% |
| `riftHeraldTakedowns` | 100% | 15% |
| `saveAllyFromDeath` | 100% | 9% |
| `scuttleCrabKills` | 100% | 26% |
| `shortestTimeToAceFromFirstTakedown` | 22% | 22% |
| `skillshotsDodged` | 100% | 99% |
| `skillshotsHit` | 100% | 79% |
| `snowballsHit` | 100% | 0% |
| `soloBaronKills` | 100% | 0% |
| `soloKills` | 100% | 51% |
| `soloTurretsLategame` | 18% | 18% |
| `stealthWardsPlaced` | 100% | 99% |
| `survivedSingleDigitHpCount` | 100% | 5% |
| `survivedThreeImmobilizesInFight` | 100% | 55% |
| `takedownOnFirstTurret` | 100% | 13% |
| `takedowns` | 100% | 99% |
| `takedownsAfterGainingLevelAdvantage` | 100% | 3% |
| `takedownsBeforeJungleMinionSpawn` | 100% | 6% |
| `takedownsFirstXMinutes` | 100% | 96% |
| `takedownsInAlcove` | 100% | 13% |
| `takedownsInEnemyFountain` | 100% | 2% |
| `teamBaronKills` | 100% | 44% |
| `teamDamagePercentage` | 100% | 100% |
| `teamElderDragonKills` | 100% | 2% |
| `teamRiftHeraldKills` | 100% | 42% |
| `teleportTakedowns` | 8% | 8% |
| `tookLargeDamageSurvived` | 100% | 3% |
| `turretPlatesTaken` | 100% | 89% |
| `turretTakedowns` | 100% | 69% |
| `turretsTakenWithRiftHerald` | 100% | 19% |
| `twentyMinionsIn3SecondsCount` | 100% | 0% |
| `twoWardsOneSweeperCount` | 100% | 12% |
| `unseenRecalls` | 100% | 1% |
| `visionScoreAdvantageLaneOpponent` | 99% | 99% |
| `visionScorePerMinute` | 100% | 100% |
| `voidMonsterKill` | 100% | 48% |
| `wardTakedowns` | 100% | 86% |
| `wardTakedownsBefore20M` | 100% | 76% |
| `wardsGuarded` | 100% | 29% |

## spieler.missions (12 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `playerScore0` | 100% | 0% |
| `playerScore1` | 100% | 0% |
| `playerScore10` | 100% | 0% |
| `playerScore11` | 100% | 0% |
| `playerScore2` | 100% | 0% |
| `playerScore3` | 100% | 0% |
| `playerScore4` | 100% | 0% |
| `playerScore5` | 100% | 0% |
| `playerScore6` | 100% | 0% |
| `playerScore7` | 100% | 0% |
| `playerScore8` | 100% | 0% |
| `playerScore9` | 100% | 0% |

## team (3 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `bans` | 100% | 100% |
| `teamId` | 100% | 100% |
| `win` | 100% | 50% |

## team.objectives (9 Felder)

| Feld | da | Wert |
|---|---:|---:|
| `atakhan` | 58% | 58% |
| `baron` | 100% | 100% |
| `champion` | 100% | 100% |
| `dragon` | 100% | 100% |
| `horde` | 100% | 100% |
| `inhibitor` | 100% | 100% |
| `riftHerald` | 100% | 100% |
| `tower` | 100% | 100% |
| `voidGator` | 42% | 42% |

## Was fehlt (fuer niemanden in den Daten)

- **Wellen:** keine Vasallen-Positionen, kein Wellenstand; nur CS je Minute.
- **Ward-Orte:** `WARD_PLACED`/`WARD_KILL` ohne Position (nur Typ, Zeit, Setzer/Zerstoerer).
- **Nebel/Sicht:** wer wen wann sah, fehlt ganz.
- **Abklingzeiten:** Ult, Flash, TP im Spiel fehlen; nur die Summe der Einsaetze (`summonerXCasts`, `spellXCasts`) je Partie.
- **Wege zwischen den Minuten:** eine Position je Spieler und Minute; dazwischen nur Ereignis-Orte (Kills, Gebaeude, Platten, Monster).
- **Leben im Kampf:** `health` nur zur vollen Minute; Schaden je Faehigkeit nur beim Tod.
- **Recall selbst:** kein Ereignis; nur Kaeufe (Laden = Basis) und Positionen.
- **Ganks ohne Kill, Absichten, Pings mit Zeit/Ort:** Pings nur als Summe je Partie.
