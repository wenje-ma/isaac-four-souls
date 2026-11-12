"""Accessory reference cards: four quick references and four keyword cards.

The text is lifted from rules/rulebook.md, cut down to what a player needs at
the table. Fronts and backs are the same two CSV files the other decks use,
so build_deck.py renders them and merge_duplex.py pairs the pages.
"""

import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PRINT = os.path.join(BASE, "print")
BUILD = os.path.join(HERE, "build")

CARDS = [
  ("SETUP", "Rule Card",
   "Shuffle the treasure, loot, monster and room decks and give each its own "
   "discard. Put at least 100\u00a2 in the pool. Place 2 shop items, 2 monsters and "
   "1 room face up in their slots; an event drawn for a monster slot goes to the "
   "bottom and is replaced. Deal each player a character card, that character's "
   "starting item, 3 loot and 3\u00a2. Characters start deactivated, starting "
   "items charged, and the turn order is clockwise from whoever goes first."),
  ("START PHASE", "Rule Card",
   "1. Recharge everything you control; shop items the game owns stay  "
   "deactivated. 2. Start-of-turn abilities trigger. 3. Loot 1."),
  ("ACTION PHASE", "Rule Card",
   "You get one loot play. While the stack is empty you may declare one  "
   "attack, one purchase, or end the turn. Any time you have priority you may  "
   "also activate abilities and play loot."),
  ("END PHASE", "Rule Card",
   "1. End-of-turn abilities trigger. 2. Discard down to your max hand size,  "
   "10. 3. If a monster died this turn you may put a room into discard. 4. The  "
   "turn passes; every object with an HP stat heals to full, dead players  "
   "included."),
  ("ATTACK / ATK", "Rule Card",
   "Declare an attack in your action phase while the stack is empty. Priority  "
   "passes first, then you pick a monster in a slot or the top card of the monster  "
   "deck; the top card is revealed and put on a slot you choose, covering what was  "
   "there.  An attack is a series of attack rolls. Roll a D6 and compare it with  "
   "the target's evasion: equal or higher, you hit and it takes combat damage  "
   "equal to your ATK; lower, you miss and it deals combat damage equal to  "
   "its ATK to you.  The attack only ends when one of you dies, when either  "
   "side has 0 HP before the next roll, or when it is cancelled. Use the TRACK  "
   "card to track the HP of the monster you are fighting. ATK is short for attack: the damage an attack deals."),
  ("DAMAGE", "Rule Card",
   "Damage lowers HP. At 0 HP a player dies and a monster dies, and a dead monster pays its reward. A source deals damage and whatever it hits takes it, so an unqualified take lands on the active player. Damage a source cannot reach is not dealt."),
  ("PURCHASE", "Rule Card",
   "Declare in your action phase while the stack is empty. Priority passes,  "
   "then you pick a shop item or the top card of the treasure deck. It costs  "
   "10\u00a2 by default; if you cannot pay, the purchase fails."),
  ("SLOTS", "Rule Card",
   "Every shop, monster and room slot must hold a card. An empty slot is  "
   "refilled from its deck the next time any player would gain priority."),
  ("CROWD SLOT", "Rule Card",
   "An extra monster slot beside the monster row, made by the card that names it. It is not one of the shop, monster or room slots, so nothing refills it; a monster there can be attacked and pays its reward when it dies."),
  ("ROOM", "Rule Card",
   "A room card goes in a room slot and changes the rules for every player while it is in play. When a monster dies, the active player may put a room card into discard."),
  ("DEATH", "Rule Card",
   "At 0 HP the death goes on the stack. Death penalty: destroy one non-eternal  "
   "item you control, discard a loot, lose 1\u00a2, deactivate every object you  "
   "control with a Tap ability, skipping what you cannot pay. If the active  "
   "player dies, the turn goes to its end phase. You can only die once per turn."),
  ("WIN", "Rule Card",
   "Control souls worth 4 to win; check between things resolving."),
  ("DICE / DC", "Rule Card",
   "Every roll is a D6 unless the card says otherwise, and a roll never leaves 1 to 6. A roll goes on the stack and is read by whatever made it. DC is short for dice: it is a monster's dice value, so you roll that or higher to hit it, and an attack that misses deals no damage."),
  ("ABILITY", "Rule Card",
   "Text on a card that does something. Static abilities always apply, triggered ones start with when, at or each time, activated ones put a cost before the colon and can be used any time you have priority."),
  ("STACK", "Rule Card",
   "Loot, abilities and rolls wait on the stack and resolve last in, first out,  "
   "each one only when every player passes priority."),
  ("PRIORITY", "Rule Card",
   "Goes to the active player first, then passes clockwise; whoever has it may  "
   "keep responding until they pass. Targeting happens when a thing goes on the  "
   "stack, not on resolution; if the target is gone by then the ability fizzles.  "
   "Bartering \u00a2 and promises never uses the stack."),
  ("SOUL", "Rule Card",
   "A reward card from the soul deck. Control souls worth 4 to win; each soul is worth 1 unless its card says otherwise. A soul stays in play under whoever gained it."),
  ("REWARD", "Rule Card",
   "The box at the foot of a monster card. When that monster dies or is destroyed "
   "the active player gains every reward in it, no matter who landed the last "
   "damage: +1 treasure takes the top card of the treasure deck, +1\u00a2 comes out "
   "of the pool, +1 soul is taken from the soul deck. An ability that adds to a "
   "reward pays out that way too, and one that changes it lasts as long as it "
   "says."),
  ("COUNTER", "Rule Card",
   "A marker placed on a card, and a die at this table. It does nothing by "
   "itself; an ability that names it reads it. A card that just says counter "
   "means a generic one, while a named one such as an ATK counter changes that "
   "stat as long as it is there. A die shows 1 to 6, so a bigger pile is a 6 "
   "and a second die: 9 counters are 6 and 3."),
  ("TRACK", "Rule Card",
   "The 8 to 0 ladder, one card you keep in sight. In solo and co-op it is the "
   "timer: it starts on 8, ticks down 1 when both characters' turns are over "
   "and 1 more whenever a character dies, and the run is lost when it reaches "
   "0. In any game it also shows a monster's HP: put a marker on the row for "
   "what is left. No monster starts above 8, so the nine rows cover it."),
  ("ETERNAL", "Rule Card",
   "Static. This object cannot be destroyed or put into discard. Only works  "
   "while it is in play."),
  ("INDOMITABLE", "Rule Card",
   "Two static abilities on a monster: if this would be put into a monster slot, "
   "instead expand monster slots by 1 and put it in the new slot; and this "
   "cannot be covered, so nothing is ever put on top of it."),
  ("ROLL", "Rule Card",
   "Creates a roll and a triggered ability that checks its result; the trigger  "
   "goes on the stack after the roll is made, and both belong to whoever rolled."),
  ("FLIP", "Rule Card",
   "Turn the card over and read the face on the other side. Only a card that "
   "says it has a second face can flip; in this printing that is Trick/Treat "
   "alone, and its two faces sit on the two sides of one card."),
  ("TAP", "Rule Card",
   "The tag means the cost is deactivating this object, turned 90 degrees. Use  "
   "it only while the object is charged, that is upright; it recharges in your  "
   "start phase."),
  ("LOOT", "Rule Card",
   "Both a card and a verb. A loot card you play resolves, then goes into discard unless its ability says it becomes something else; Loot 2 draws two cards from the loot deck."),
  ("TREASURE", "Rule Card",
   "An item from the treasure deck. A treasure card stays in play and keeps its ability while it is charged. A shop item is a treasure card the game owns, not you."),
  ("ITEM", "Rule Card",
   "Any treasure card in play is an item, whoever controls it. A shop item is "
   "an item the game controls, and an item given eternal stops being destroyable. "
   "A character card is not an item, and a loot card becomes one only once its "
   "text says it does."),
  ("BOSS", "Rule Card",
   "A monster card marked boss. It takes a monster slot like any other monster, but only a card with this word is a boss, so an effect that says reveal 2 bosses counts only these."),
  ("EVENT", "Rule Card",
   "A monster card with no stat block. In play it is an event: it holds a "
   "monster slot but cannot be attacked. Its abilities are triggered abilities "
   "that all fire when it enters play, and once they have resolved or been "
   "cancelled the card goes into the monster discard."),
  ("CURSE", "Rule Card",
   "Two triggered abilities, printed as one word: when this enters play it "
   "becomes a curse and the active player chooses the player who gains it; when "
   "you die, put it into discard. It sits face up beside that player's "
   "character, and a card that tells you to reveal a curse gives it to the "
   "player the active player picks."),
  ("TRINKET", "Rule Card",
   "A triggered ability on a loot card: when the loot resolves it becomes an "
   "item and you gain it. Any other text on the card only works once it is in "
   "play, so a loot that is a trinket is not an item while it is on the stack."),
  ("AMBUSH", "Rule Card",
   "A triggered ability on a loot card: when the loot resolves you choose a "
   "monster slot, the card becomes a monster in that slot, and the active "
   "player must make one more attack against it this turn. Any other text on "
   "the card only works once it is in play."),
  ("GUPPY", "Rule Card",
   "Static and empty: the word does nothing on its own and is only a marker for "
   "other cards to look for, so a guppy item is any item whose name or text "
   "carries it."),
  ("CENT", "Rule Card",
   "A cost or an amount of \u00a2."),
  ("HP", "Rule Card",
   "How much damage an object takes before it dies. A monster's HP is printed "
   "on its card; a player's is on the character card, and both are tracked with "
   "the heart tokens or a die, and heal to full at the end of every turn."),
  ("EVERY CHARACTER", "Rule Card",
   "Every character card has this ability, so it is no longer printed on the  "
   "card: Tap: Play an additional loot card this turn. Tap means deactivate the  "
   "character, turned 90 degrees; it recharges in your start phase."),
]


def clean(s):
  return s.replace('"', "'").replace("|", "/")


def main():
  front_cols = ["n", "name", "subtitle", "stats", "body", "footer", "set", "slug"]
  back_cols = front_cols + ["back"]
  fronts, backs = [], []
  for i, (title, sub, body) in enumerate(CARDS, 1):
    fronts.append([str(i), clean(title), sub, "", clean(body), "", "REFERENCE", "rule-%d" % i])
  for i in range(1, 10):
    row = [""] * len(back_cols)
    row[0] = str(i)
    row[back_cols.index("back")] = "RULE"
    backs.append(row)

  for name, cols, rows in (("cards_fronts_rule.csv", front_cols, fronts),
                           ("cards_back_rule.csv", back_cols, backs)):
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
      w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
      w.writerow(cols)
      w.writerows(rows)
    print("written", name, "rows", len(rows))

  # the same renderer the card decks use, so the eight references sit on the
  # same 63 x 88 grid; merge_duplex.py pairs the two pages into the duplex file
  subprocess.run([sys.executable, os.path.join(HERE, "render_cards_tex.py"), "rule"], check=True)


main()
