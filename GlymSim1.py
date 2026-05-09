# virtual pet idle simulator
import time
import random
import os
import shutil
import re
import sys

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"

GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

STAR = YELLOW
DREAM = MAGENTA
HEART = MAGENTA
SLEEP = BLUE

# Width used for text wrapping and the Glym/Boops header.
# This is Glym's little stage, not the whole terminal window.
# Keeping it conservative prevents Windows Terminal from chopping words.
DISPLAY_WIDTH = 34
MIN_DISPLAY_WIDTH = 24
LEFT_MARGIN = 3
TOP_PADDING = 2
STAGE_HEIGHT = 18


def tint(text, color):
    return color + text + RESET


def colorwave(text):
    colors = [CYAN, MAGENTA, YELLOW, GREEN]
    painted = ""

    for index, char in enumerate(text):
        if char == " ":
            painted = painted + char
        else:
            painted = painted + colors[index % len(colors)] + char + RESET

    return painted


def stylize_text(text):
    if "\033[" in text:
        return text

    multiline = "\n" in text.strip()
    lower = text.lower()
    base = ""

    if multiline == False:
        if "boop" in lower or "♡" in text or "♥" in text:
            base = HEART
        elif any(word in lower for word in ["tired", "yawn", "sleepy", "eyelid", "buffering", "battery", "wakefulness", "pre-napping"]):
            base = GRAY
        elif any(word in lower for word in ["dream", "sleep", "nap", "moon", "moth", "den", "hush"]):
            base = SLEEP
        elif any(word in lower for word in ["wakes", "wake", "awake", "fresh", "reboot", "morning", "released"]):
            base = GREEN
        elif any(word in lower for word in ["universe", "prophecy", "reality", "shadow", "linear time", "cosmic"]):
            base = DREAM

    styled = colorize_parts(text, base)

    if base != "":
        return base + styled + RESET

    return styled


def colorize_parts(text, resume=""):
    return_after = resume if resume != "" else RESET

    symbol_colors = {
        "★": STAR,
        "☆": WHITE,
        "✦": STAR,
        "✧": DREAM,
        "·": GRAY,
        "•": GRAY,
        "♡": HEART,
        "♥": RED,
        "←": CYAN,
        "→": CYAN,
        "↑": CYAN,
        "↓": CYAN,
        "↺": CYAN,
    }

    word_colors = [
        ("moonlit", BLUE),
        ("Moonlit", BLUE),
        ("moon", BLUE),
        ("Moon", BLUE),
        ("dreamland", DREAM),
        ("Dreamland", DREAM),
        ("dreaming", DREAM),
        ("Dreaming", DREAM),
        ("dreams", DREAM),
        ("Dreams", DREAM),
        ("dream", DREAM),
        ("Dream", DREAM),
        ("sleepy", SLEEP),
        ("Sleepy", SLEEP),
        ("sleep", SLEEP),
        ("Sleep", SLEEP),
        ("nap", SLEEP),
        ("Nap", SLEEP),
        ("shadow", GRAY),
        ("Shadow", GRAY),
        ("shadows", GRAY),
        ("Shadows", GRAY),
        ("universe", CYAN),
        ("Universe", CYAN),
        ("prophecy", DREAM),
        ("Prophecy", DREAM),
        ("secret", DREAM),
        ("Secret", DREAM),
        ("boops", HEART),
        ("Boops", HEART),
        ("boop", HEART),
        ("Boop", HEART),
        ("star", STAR),
        ("Star", STAR),
        ("stars", STAR),
        ("Stars", STAR),
        ("sparkle", STAR),
        ("Sparkle", STAR),
    ]

    for symbol, color in symbol_colors.items():
        text = text.replace(symbol, color + symbol + return_after)

    for word, color in word_colors:
        text = text.replace(word, color + word + return_after)

    return text


ANSI_CODE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text):
    return ANSI_CODE.sub("", text)


def visible_length(text):
    return len(strip_ansi(text))


def get_stage_width():
    # Keep the stage narrow enough that it survives small Windows Terminal
    # resizing, even when terminal-size detection is not perfectly honest.
    terminal_width = shutil.get_terminal_size((50, 20)).columns
    safe_width = terminal_width - LEFT_MARGIN - 2

    if safe_width < MIN_DISPLAY_WIDTH:
        return max(16, safe_width)

    return min(DISPLAY_WIDTH, safe_width)


def get_stage_height():
    terminal_height = shutil.get_terminal_size((50, 20)).lines
    safe_height = terminal_height - 1

    if safe_height < 8:
        return max(5, safe_height)

    return min(STAGE_HEIGHT, safe_height)


def center_ansi_line(line, width):
    visible = visible_length(line)
    padding = max(0, (width - visible) // 2)
    return " " * padding + line


def wrap_ansi_text(text, width):
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        if current_line == "":
            test_line = word
        else:
            test_line = current_line + " " + word

        if visible_length(test_line) <= width:
            current_line = test_line
        else:
            if current_line != "":
                lines.append(current_line)
            current_line = word

    if current_line != "":
        lines.append(current_line)

    return lines


def paint_fox_face(face):
    # Keep the expression readable without making Glym look half-finished.
    # The face shape stays fox-red; only the tiny expression details turn pale.
    if face == "( o.o )":
        return RED + "( " + RESET + WHITE + "o.o" + RESET + RED + " )" + RESET
    if face == "( -.- )":
        return RED + "( " + RESET + WHITE + "-.-" + RESET + RED + " )" + RESET
    if face == "( >.< )":
        return RED + "( " + RESET + WHITE + ">.<" + RESET + RED + " )" + RESET
    if face == "( o,o )":
        return RED + "( " + RESET + WHITE + "o,o" + RESET + RED + " )" + RESET

    return face


def paint_fox_muzzle(muzzle):
    # Make the little > ^ < line read as part of the red fox body,
    # with only the nose/caret kept pale for contrast.
    if muzzle == "> ^ <":
        return RED + "> " + RESET + WHITE + "^" + RESET + RED + " <" + RESET

    return muzzle


def colorize_ascii_art(text):
    # Leave already-colored multiline blocks, like the UFO, alone.
    if "\033[" in text:
        return text

    lines = []

    for line in text.split("\n"):
        painted = line

        # Fox ears/body. Basic colors only, so the console stays sturdy.
        painted = painted.replace("/\\_/\\", RED + "/\\_/\\" + RESET)
        painted = painted.replace("/|   |\\", RED + "/|   |\\" + RESET)
        painted = painted.replace("__/ > ^ <__", RED + "__/ " + RESET + paint_fox_muzzle("> ^ <") + RED + "__" + RESET)
        painted = painted.replace("/  > ^ <", RED + "/  " + RESET + paint_fox_muzzle("> ^ <"))
        painted = painted.replace("> ^ <~~~~", paint_fox_muzzle("> ^ <") + RED + "~~~~" + RESET)
        painted = painted.replace("> ^ <", paint_fox_muzzle("> ^ <"))

        for face in ["( o.o )", "( -.- )", "( >.< )", "( o,o )"]:
            painted = painted.replace(face, paint_fox_face(face))

        # Let existing symbols keep their little glow.
        painted = colorize_parts(painted)
        lines.append(painted)

    return "\n".join(lines)


def format_ascii_block(text, width):
    # Preserve the ASCII art's internal spacing.
    # We center the whole block as one object instead of centering each line.
    lines = text.split("\n")
    visible_lines = [line for line in lines if strip_ansi(line).strip() != ""]

    if visible_lines:
        block_width = max(visible_length(line) for line in visible_lines)
    else:
        block_width = 0

    padding = " " * max(0, (width - block_width) // 2)
    centered_lines = []

    for line in lines:
        # Keep blank/ANSI-only lines as-is so colored blocks like UFO stay colored.
        if strip_ansi(line).strip() == "":
            centered_lines.append(line)
        else:
            centered_lines.append(padding + line)

    return "\n".join(centered_lines)


def format_currentstate(text, width):
    plain = strip_ansi(text).strip()

    # ASCII/multiline art should keep exact internal spacing.
    # Only the whole block gets centered.
    if "\n" in plain:
        return format_ascii_block(colorize_ascii_art(text), width)

    # Text idles get wrapped by whole words, then centered line-by-line.
    wrapped_lines = wrap_ansi_text(stylize_text(text), width)
    centered_lines = [center_ansi_line(line, width) for line in wrapped_lines]

    return "\n".join(centered_lines)


def make_header(boops, width):
    left_plain = "Glym"
    right_plain = "Boops: " + str(boops)
    spaces = " " * max(1, width - len(left_plain) - len(right_plain))

    return GREEN + left_plain + RESET + spaces + HEART + right_plain + RESET


def clear_screen():
    # Stronger than cls: clear screen, clear scrollback, return cursor home.
    # This helps stop old ASCII frames from haunting the next text idle.
    sys.stdout.write("\033[2J\033[3J\033[H")


def print_stage(text, boops):
    clear_screen()

    stage_width = get_stage_width()
    stage_height = get_stage_height()
    terminal_height = shutil.get_terminal_size((50, 20)).lines
    margin = " " * LEFT_MARGIN
    stage_lines = []

    # Give the display a little breathing room so the header
    # does not sit flush against the top of the terminal window.
    for _ in range(TOP_PADDING):
        stage_lines.append("")

    stage_lines.append(make_header(boops, stage_width))
    stage_lines.append("")

    if "\n" not in strip_ansi(text).strip():
        stage_lines.append("")

    stage_lines.extend(format_currentstate(text, stage_width).split("\n"))

    # Fill the visible window with blank lines after the stage so a taller
    # previous ASCII frame cannot remain underneath a shorter text idle.
    total_lines = max(stage_height, terminal_height - 1)
    stage_lines = stage_lines[:total_lines]

    while len(stage_lines) < total_lines:
        stage_lines.append("")

    frame = "\n".join(margin + line for line in stage_lines)
    sys.stdout.write(frame + RESET)
    sys.stdout.flush()


alive = True
awake = True
sleepy = False
currentstate = ""

tick = 0
sleepiness = 0
glymcounter = 0

activeidles = [
"Glym's tail flicks like a tiny verdict. ✦",
"Glym lifts his nose and samples the air · something invisible answers.",
"The little fox pads in a careful circle ↺",
"Glym watches something that may or may not be an invisible forest ghost. ✧",
"One paw receives Glym's full and solemn attention.",
"Glym's ears perk at a sound too small for human business ·",
"Glym noses at the floor like it has been withholding evidence.",
"Glym stretches his spine into one long fox-shaped question mark ☆",
"Glym stares at nothing like nothing has finally confessed. · · ·",
"Glym settles down, then immediately decides settling was a mistake.",
"His tail gives another quick little flick ✦",
"Glym sniffs the floor with the seriousness of a detective in a tiny coat.",
"The little fox makes a neat circle around his chosen patch of reality.",
"Glym bats at a dust mote ✧ and nearly wins.",
"Glym scratches behind one ear with deep concentration.",
"Glym follows the baseboard with his nose like a suspicious border guard.",
"Glym crouches, wiggles, and pounces on an enemy no one else can perceive. ↓ ✦",
"Glym glances at his tail like it has been acting independently. ←",
"His front paws stretch far ahead while the rest of him slowly catches up.",
"Glym shakes out his fur and resets the fox machinery.",
"Glym trots from one side of the room to the other with tiny purpose. →",
"One paw pats the ground, testing conditions.",
"Glym's ears rise together at some microscopic drama. ↑",
"Glym sniffs the air, sneezes, and looks mildly betrayed.",
"Glym turns around three times before choosing absolutely nowhere.",
"The little fox sits upright like he has been summoned to court.",
"Glym noses at a speck that may only exist in theory ·",
"One paw drags lazily across the floor.",
"Glym tilts his head at the room, waiting for it to explain itself. ✧",
"Glym performs a tiny sideways hop for reasons lost to history. ← →",
"Glym licks his nose and seems satisfied with the maintenance.",
"One ear gets carefully smoothed back into place.",
"Glym steps over nothing with absurd caution.",
"Glym circles a spot he has apparently promoted to Important. ↺",
"The corner receives a quiet inspection.",
"Glym sniffs his own paw and considers the findings.",
"One paw lifts ↑, pauses, and forgets its assignment.",
"Glym gives himself a quick little shake.",
"Glym trots in place for one determined second.",
"His tail swishes across the floor like a soft broom with opinions.",
"Glym studies the wall with professional concern. · · ·",
"Glym noses at a crumb-sized mystery •",
"One paw reaches toward the edge of his little world →",
"Glym unfolds into a long, luxurious fox stretch. ☆",
"Glym looks left ← right → then left ← again, because procedure matters.",
"A tiny huff escapes him.",
"Glym leans forward to sniff whatever invisible nonsense has appeared.",
"Glym crouches low and watches the floor hold still.",
"Glym steps backward with great dignity.",
"Two soft pats are delivered to the ground.",
"One ear flicks, annoyed by a private frequency.",
"Glym walks a careful loop around an unmarked concern.",
"Glym sniffs under himself, then looks personally offended.",
"His cheek rubs against the floor in a small act of ownership.",
"Glym does a quick shoulder shimmy.",
"Glym paws at his whiskers as if adjusting important antennae.",
"The little fox prances two steps, then cancels the parade.",
"Glym noses at the air near his feet.",
"Glym performs a tiny patrol of the room.",
"Glym freezes mid-step like a secret just brushed past him. ✧",
"One claw scratches the ground once.",
"Glym sits ↓ stands ↑ and sits again, having explored both philosophies.",
"Both ears wiggle.",
"Glym stretches one back leg with delicate drama.",
"Glym turns his head sharply at nothing visible.",
"The tip of his tail gets inspected.",
"Glym sniffs the same spot twice, just to be certain.",
"Glym trots in a neat little square.",
"Glym lifts his chin and surveys his domain. ★",
"Glym paws at a harmless shadow that looked suspicious for half a second. ✦",
"The little fox gives a tiny bounce.",
"Glym noses the floor, then trots away with no comment.",
"His tail flicks like punctuation at the end of a private sentence.",
"Glym lowers his head and prowls a few soft steps.",
"Both paws scrub over his face in a quick little wash.",
"Glym steps around an imaginary obstacle with great care.",
"His paw gets one efficient lick.",
"Glym watches a dust mote drift through its brief, heroic life. · ✧ ·",
"Glym bumps the floor with his nose.",
"Glym makes a cautious little turn.",
"One paw taps impatiently.",
"Glym sniffs toward the ceiling, because answers may fall from above. ↑",
"The little fox pads in a quiet half-circle.",
"Glym checks behind himself.",
"Glym sits with his tail wrapped neatly around his paws.",
"Glym scoots forward exactly one inch.",
"Glym scratches at nothing important, but does it professionally.",
"Glym gives the air a thoughtful sniff.",
"Glym trots to the edge of his space and surveys the border. →",
"Glym fluffs himself up for no obvious reason.",
"Glym noses at his own tail.",
"The little fox pauses to look terribly important.",
"Glym licks one paw with the focus of a scholar translating ruins.",
"A tiny chirp slips out of him.",
"Glym steps in place like a decision is loading · · ·",
"Glym sniffs the seam in the floor.",
"Glym paces in a soft little line.",
"His ears turn toward a faint and probably imaginary sound. ✧",
"Glym lowers his chest in a playful crouch.",
"Glym hops forward once.",
"Glym looks around like he misplaced a thought. ·",
"His tail drags lazily behind him.",
"Glym gives a small shake of his head.",
"Glym noses the ground and huffs.",
"The little fox walks in a slow circle.",
"Glym licks his shoulder.",
"One paw reaches lightly into the air.",
"Glym stands very still with suspicious intensity. ✦",
"Glym curls his tail, then uncurls it.",
"Glym takes three careful steps. · · ·",
"Glym sniffs a perfectly normal patch of floor and remains unconvinced.",
"His fur gets a quick tidy.",
"Both ears flick backward.",
"Glym shuffles his paws.",
"Glym peers at the floor like it owes him money. •",
"A soft little snort escapes him.",
"Glym pads around with quiet confidence. ♡",
"Glym stretches, then immediately trots off.",
"Glym sniffs his own tail and looks thoughtful. ↺",
"One paw troubles a tiny bit of nothing.",
"Glym trots in a lazy curve.",
"The same corner gets checked again.",
"Glym turns in place very slowly. ↺",
"Glym noses along an invisible trail.",
"Glym gives a quick happy wiggle. ♡",
"One paw rises dramatically ↑ then waits for applause.",
"Glym rubs his cheek against his paw.",
"His tail sways from side to side.",
"Glym takes one tiny stalking step.",
"Glym investigates a speck only he respects. •",
"Glym sits down, then changes his mind immediately.",
"His neck stretches forward toward a possible mystery.",
"One claw scratches the floor.",
"Glym gives a tiny fox sneeze.",
"The little fox trots in a tight loop.",
"Glym looks over his shoulder.",
"Glym paws at the edge of his space.",
"Glym lifts his nose and takes one deep, important sniff. ↑",
"Glym blinks slowly at the room. ·",
"Glym grooms the fur on his chest.",
"Glym does a small side-step.",
"Glym watches the floor with dramatic suspicion. ✧",
"Glym noses at a soft patch of air.",
"Glym circles once, then trots away.",
"His tail gives one quick flick.",
"Glym presses a paw against the floor like he is testing reality's pulse. •",
"Glym stretches until his toes spread.",
"Glym turns his head at a tiny noise.",
"Glym sniffs and decides nothing is urgent.",
"The little fox pads lightly across his domain. ✦",
"Glym licks his lips.",
"Glym perks up ↑ then relaxes again ↓",
"One paw brushes at his muzzle.",
"Glym gives a tiny impatient hop.",
"Glym inspects the ground like a scholar with tenure.",
"Glym noses forward one careful inch.",
"Glym trots around with busy little steps. · · ·",
"Glym shakes his tail loose.",
"Glym crouches and watches an ordinary spot.",
"Glym scratches behind his other ear.",
"The little fox walks in a soft zigzag.",
"Glym lifts his head proudly. ★",
"His ears flick in opposite directions.",
"Glym sniffs the same invisible trail again. · · →",
"One paw nudges the floor.",
"Glym settles for half a second, then gets up.",
"Glym turns sharply and trots two steps. →",
"Glym puffs up, then deflates.",
"Glym gives the room a tiny inspection. ✧",
"Glym licks one toe.",
"Glym noses at something near his paws.",
"A quiet little grumble leaves him.",
"Glym moves like he has somewhere important to be.",
"Glym pauses to groom his shoulder.",
"His tail circles around his paws.",
"Glym trots forward, then backs up.",
"Glym stares at a harmless corner. ·",
"His tail flicks against the floor.",
"Glym paws at the air beside him.",
"Glym lowers his nose and follows a scent. · · →",
"Glym gives a pleased little wiggle. ♥",
"Glym looks deeply invested in nothing.",
"One ear gets rubbed with his paw.",
"Glym steps around his own tail.",
"Glym takes a tiny patrol lap. ↺",
"Glym sniffs, sneezes, and recovers his dignity.",
"Glym lifts one paw like a tiny gentleman.",
"Glym watches the room with bright little eyes. ✦",
"Glym scratches the ground, then sniffs it.",
"The little fox trots in a slow oval.",
"Glym pauses to tidy his whiskers.",
"His tail flicks twice. ✦ ✦",
"Glym noses at a mysterious floor spot.",
"Glym does a small full-body shake.",
"Glym sits very still, then darts forward.",
"Glym gives the air a careful taste. ·",
"Glym pads in a quiet figure-eight. ↺",
"Glym looks offended by an ordinary sound.",
"Glym stretches his back legs one at a time.",
"His tail swishes like a little banner. ★",
"One paw taps the floor.",
"Glym prowls around the edge of the room. ← · →",
"Glym pauses with one ear tilted.",
"Glym licks his paw and wipes his face.",
"A soft little fox huff appears.",
"Glym trots in a proud little circle.",
"Glym noses at the boundary of his space.",
"Glym gives a quick playful bow. ↓",
"Glym checks under his own tail.",
"Glym scratches his chin with one paw.",
"Glym watches a tiny movement only he noticed. ✧",
"Glym steps carefully, then ruins it with a hop.",
"Glym sniffs the floor like it changed overnight.",
"Glym flops briefly, then springs back up.",
"Glym pads around with tiny important footsteps.",
"Glym flicks his tail and looks satisfied. ♡",
"Glym pauses to consider whether doors are promises or threats. · · ·",
"The little fox stares into the room as if the room failed an exam.",
"Glym looks up like he suddenly remembered the moon exists. ↑ ✦",
"Glym tilts his head, possibly contemplating mortality, possibly a crumb.",
"Glym sits perfectly still and becomes a small question. ? ✧",
"Glym sniffs the air and seems disappointed by linear time. ← · →",
"Glym studies his paw like it contains a tiny prophecy. ✦",
"The little fox looks around as if reality just made a noise.",
"Glym decides privately that the universe is suspicious. ★",
"Glym stares at a shadow and wonders whether shadows know they are shadows. ✧",
"Glym blinks once, as though rebooting from an ancient fox dream.",
"Glym appears to ponder the difference between hunger and destiny.",
"The little fox pauses, briefly burdened by the concept of furniture.",
"Glym watches the wall with the quiet concern of someone who has seen beyond it. · · ·",
"Glym sniffs nothing and accepts no explanation. •",
"✦ · ✧ · ✦",
"☆ · ★ · ☆",
"← · · · →",
"↑ ✦ ↓",
"♡ · ♥ · ♡",
"↺ · ↺ · ↺",
"· · ✧ · ·",
"★     Glym     ★",
"Glym watches three tiny lights drift by. ✦ ✧ ✦",
"The little fox follows a sparkle trail with his eyes. · · ✧ →",
"Glym's ears tilt toward a star that is definitely not indoors. ★",
"Glym paws at a small bright thought before it escapes. ✧",
"A tiny constellation appears in Glym's expression, then vanishes. ☆",
"Glym blinks at a dot of light like it owes him rent. •",
"The room gets one slow fox scan. ← · Glym · →",
"Glym sits under an imaginary star and accepts tribute. ✦",
"A soft little heart sneaks into Glym's posture. ♡",
"Glym circles a private idea until it becomes a problem. ↺",
"For one silent second, Glym appears to understand everything. ★",
"Then Glym forgets everything and sniffs the floor. ·",
]

sleepidles = [
"Glym's little paw twitches like he is chasing something through a dream. · · →",
"A tiny dreaming noise slips out of Glym. ·",
"Glym curls tighter into his tail.",
"Somewhere in sleep, Glym chases moonlit moths. ✦",
"His ears flick at an invisible dream-sound. ✧",
"One paw gives a delicate little sleep-twitch.",
"Glym makes a soft noise, then sinks deeper into his nap.",
"The little fox tightens into a warmer curl.",
"Moonlit moths continue to suffer in Glym's dream kingdom. ☆",
"Both ears tremble once, then settle.",
"Glym lets out a soft sleepy sigh. · · ·",
"His nose disappears under his tail.",
"Glym shifts into a warmer little curl.",
"His whiskers twitch while some secret dream unfolds. ✧",
"A tiny sleep-huff escapes him.",
"One paw stretches without permission from the rest of him.",
"Glym mumbles at something only dreams can understand.",
"The little fox rolls slightly onto his side.",
"His tail gives one lazy flick.",
"Glym dreams of padding through soft moss. · · →",
"A faint little fox squeak escapes his sleep.",
"Glym tucks his paws closer to his chest.",
"His ears twitch twice, then go still.",
"Glym breathes in slow little waves.",
"Somewhere in dreamland, Glym confronts a suspicious beetle.",
"His nose wiggles in his sleep.",
"Glym curls into a tighter fox comma.",
"One back paw gives a tiny kick.",
"Glym sighs like the whole world has become warm.",
"Silver leaves scatter through his dreams. ✦ ✧",
"His tail slips over his nose.",
"Glym makes a soft sleepy chirr.",
"One ear stays half-raised, still technically on duty.",
"The little fox sinks deeper into his nap.",
"Glym dreams about a button that boops back. ♡",
"A tiny snore appears and vanishes.",
"His paws twitch like he is running through moon grass. →",
"Glym nestles his face against his tail.",
"A quiet dream-grumble rumbles out of him.",
"Warm stones glow somewhere in Glym's sleeping mind. ★",
"One ear flicks at nothing.",
"Glym relaxes into a fluffy little heap.",
"His nose twitches, then stills.",
"A sleepy little murmur slips from him.",
"Glym dreams about finding a hidden den.",
"His paws shift beneath him.",
"One tiny tail thump announces nothing in particular.",
"Glym curls his spine into a soft crescent.",
"A field full of moths opens behind his closed eyes. ✦",
"His whiskers quiver.",
"Glym sleeps with dramatic seriousness. ·",
"The little fox snuffles softly.",
"His chin tucks lower into his fur.",
"Glym dreams about a very important crumb.",
"One paw flexes once.",
"A faint little yip escapes the dream.",
"Glym presses his nose into his fur.",
"Rain taps on dream-leaves above him. · · ·",
"His tail wraps tighter around him.",
"Glym gives a tiny sleeping sneeze.",
"The little fox twitches like he heard a dream-door open. ✧",
"Glym breathes slow and even.",
"He sneaks through tall grass in his sleep.",
"His ears flatten, then perk slightly.",
"Glym settles into a deeper sleep.",
"One paw reaches gently through the dream-air. →",
"A tiny contented sound hums out of him.",
"Glym dreams of a warm den under tree roots. ♥",
"He shifts and gets comfortable again.",
"The tip of his tail flicks once.",
"Glym's nose gives a sleepy little wiggle.",
"A glowing bug escapes him in dreamland. ✦",
"Glym curls around himself like a cinnamon fox roll.",
"A soft breathy snore rises and fades.",
"His paws twitch in a tiny dream-run.",
"Glym sleeps through his own cuteness.",
"Crunchy leaves crackle under his dream-feet. · · ·",
"One ear rotates toward an imaginary sound.",
"Glym gives a faint sleepy squeak.",
"His nose burrows deeper into his tail.",
"Glym dreams about a secret tunnel. ↓",
"His shoulders soften completely.",
"The little fox gives a slow little exhale.",
"Glym dreams of warm hands and safe shadows. ♡",
"One back leg kicks once, very politely.",
"Glym sleeps like a small enchanted slipper.",
"A quiet foxy mumble escapes him.",
"Somewhere in sleep, Glym steals moonlight. ★",
"His whiskers tremble, then calm.",
"Glym rolls his head to the other side.",
"A tiny dream-growl rises from him.",
"Glym follows a silver scent trail through the dark. · · →",
"His paws curl inward.",
"Glym breathes like a little bellows.",
"The little fox settles into a soft knot.",
"Glym dreams about a forest no one else can find. ✧",
"His nose gives one delicate twitch.",
"Glym sleeps with his tail over his face.",
"A tiny satisfied huff escapes him.",
"Glym pounces through starlit grass in his sleep. ✦",
"His ears flick inside the dream.",
"Glym snuggles deeper into himself.",
"One soft sleepy chirp appears.",
"Glym dreams about guarding a little glowing door. ★",
"He lies perfectly still, except for one twitching paw.",
"Glym seems to be negotiating with a dream-moth.",
"His tail tightens like a blanket.",
"The little fox sleeps as if appointed guardian of the warm dark. ♥",
"Glym dreams of a den lined with moss and stolen stars. ✦ ★ ✧",
"A tiny paw paddles once, then gives up.",
"Glym's sleeping face looks extremely busy.",
"He dreams of following footprints that glow faintly blue. · · →",
"His ears twitch like the dream said something rude.",
"Glym gives a tiny sigh of cosmic exhaustion.",
"The little fox drifts through a forest made entirely of hush. · ✧ ·",
"Glym dreams that the moon has come down to sniff him back. ☆",
"One paw curls against his chest.",
"His tail tip writes one sleepy comma in the air.",
"Glym dreams of being very brave near a very small mushroom. ✦",
"A faint dream-yip escapes him, then silence returns.",
"The little fox appears to be processing ancient moon business. ★",
"Glym sleeps like he has solved one problem and created three more. ↺",
"His whiskers stir as if reading the weather in another world.",
"Glym dreams of a door opening under the roots of a tree. ↓ ✧",
"One ear flicks at a sound from the wrong universe.",
"Glym's paws twitch with tiny heroic purpose.",
"He breathes so softly the room seems to hush around him.",
"Glym dreams of chasing something silver and almost remembered. ✦ →",
"His nose nudges deeper into the soft dark.",
"The little fox curls tighter, guarding whatever dream he found. ♡",
"· · ·",
"✦ · ✧ · ✦",
"☆     ☆     ☆",
"↓ · · · ↓",
"♡ · Glym dreams softly · ♡",
"The dream gets quiet around Glym. · · ·",
"A tiny star settles on the edge of Glym's sleep. ✦",
"Glym drifts past a door marked only with a little ☆",
"His dream-paws follow a path of glowing dots. · · · →",
"Somewhere deep down, a small bright thing turns over. ✧",
]

ufo = CYAN + r"""
        ✦      ★      ✧

           _____________
      ____/__( O _ O )__\____
    _/_______________________\_
   /___________________________\
       \_____\_______/_____/
          /           \
         /    /\_/\    \
        /    ( o.o )    \
       /      > ^ <      \
      /   Glym licks one  \
     /  paw, unimpressed.  \
    /_______________________\

""" + RESET

asciiidles = [
r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym sits politely.
""",

r"""
      /\_/\
     ( -.- )
      > ^ <
   Glym blinks slowly.
""",

r"""
      /\_/\
     ( o.o )  . 
      > ^ <  /|
   Glym notices a dust mote.
""",

r"""
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
   Glym does a tiny stretch.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <    o
   Glym watches a tiny ball.
""",

r"""
      /\_/\
     ( o.o )  boop
      > ^ <    [ ]
   Glym studies the button.
""",

r"""
       /\_/\
      ( o.o )
    __/ > ^ <__
   Glym crouches dramatically.
""",

r"""
      /\_/\
     ( o.o )
      > ^ < ~~~
   Glym swishes his tail.
""",

r"""
        /\_/\
       ( o.o )
        > ^ <
     .-~~~~~-.
   Glym patrols the rug.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
      /   \
   Glym stands very importantly.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <     *
   Glym has found a sparkle.
""",

r"""
      /\_/\   
     ( o.o ) (***)
      > ^ <   |_|             
   Glym sniffs a mushroom.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   .----------.
   Glym guards the floor.
""",

r"""
      /\_/\
     ( >.< )
      > ^ <
   Glym sneezes.
""",

r"""
      /\_/\   ***
     ( o.o )  \|/
      > ^ <    |
    Glym inspects a tiny weed.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
    .-.
   (   )
    '-'
   Glym circles a pebble.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym lifts one paw.
        ___
       (...)
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym is thinking.
        ...
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym watches the wall.
   |              |
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym looks left.
   <-----
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym looks right.
          ----->
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym found nothing.
   This is suspicious.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
    \  |  /
     \ | /
   Glym sits under a tiny glow.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym paws at the air.
        \o/
""",

r"""
       /\_/\
      ( o.o )
       > ^ <
   Glym trots in place.
     step step
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym tidies one paw.
       lick
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
    _______
   /       \
   Glym finds a soft spot.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym sits beside nothing.
   Nothing sits back.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym's ears perk.
      !   !
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym scratches the floor.
      //// 
""",

r"""
      /\_/\
     ( o,o )
      > ^ <
   Glym follows a scent.
   .........>
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym loses the scent.
   <.........?
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym gives a tiny bow.
       \_/
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym checks his tail.
        ~~~
""",

r"""
       /\_/\
      ( o.o )
       > ^ <
    .--------.
   Glym claims this square.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym stares into space.
        *     .
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym taps the ground.
        tap
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym hears something.
        ???
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym ignores something.
        ...
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym approaches the button.
          [ ]
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym does not press it.
          [ ]
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym circles the button.
       [ ]  ↺
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym sits like a tiny judge.
        ___
       /___\
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym investigates a crumb.
        .
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym decides the crumb is fake.
        .
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym shakes out his fur.
      ~ ~ ~
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym does a little hop.
        hop
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym sits beneath a star.
        *
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym waits for a secret.
      hush
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
   Glym knows something.
   He will not explain.
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
""",

r"""
      /\_/\
     ( -.- )
      > ^ <
""",

r"""
       /\_/\
      ( o.o )
    __/ > ^ <__
""",

r"""
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
""",

r"""
      /\_/\
     ( o.o )
      > ^ <
        _
""",

r"""
      /\_/\
     ( o.o )
      > ^ <~~~~
""",

r"""
       /\_/\
      ( o.o )
     /  > ^ <
""",

r"""
      /\_/\
    _( o.o )_
      > ^ <
""",

r"""
      /\_/\
     ( o.o )  <
      > ^ <
""",

r"""
   >  ( o.o )
      /\_/\
      > ^ <
""",

r"""
          o
      /\_/\
     ( o.o )
      > ^ <
""",

r"""
          o
      /\_/\
     ( -.- )
      > ^ <
""",

r"""
          o
       /\_/\
      ( o.o )
    __/ > ^ <__
""",

r"""
          o
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
""",

r"""
          o
      /\_/\
     ( o.o )
      > ^ <
        _
""",

r"""
          o
      /\_/\
     ( o.o )
      > ^ <~~~~
""",

r"""
          o
       /\_/\
      ( o.o )
     /  > ^ <
""",

r"""
          o
      /\_/\
    _( o.o )_
      > ^ <
""",

r"""
          o
      /\_/\
     ( o.o )  <
      > ^ <
""",

r"""
         [ ]
      /\_/\
     ( o.o )
      > ^ <
""",

r"""
         [ ]
      /\_/\
     ( -.- )
      > ^ <
""",

r"""
         [ ]
       /\_/\
      ( o.o )
    __/ > ^ <__
""",

r"""
         [ ]
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
""",

r"""
         [ ]
      /\_/\
     ( o.o )
      > ^ <
        _
""",

r"""
         [ ]
      /\_/\
     ( o.o )
      > ^ <~~~~
""",

r"""
         [ ]
       /\_/\
      ( o.o )
     /  > ^ <
""",

r"""
         [ ]
      /\_/\
    _( o.o )_
      > ^ <
""",

r"""
         [ ]
      /\_/\
     ( o.o )  <
      > ^ <
""",

r"""
      \  |  /
       /\_/\
      ( o.o )
       > ^ <
        
""",

r"""
      \  |  /
       /\_/\
      ( -.- )
       > ^ <
        \|/
""",

r"""
      \  |  /
       /\_/\
      ( o.o )
     /  > ^ <
        \|/
""",

r"""
      \  |  /
      /\_/\
    _( o.o )_
      > ^ <
        \|/
""",

r"""
      \  |  /
      /\_/\
     ( o.o )  <
      > ^ <
        \|/
""",

r"""
       .-.
      /\_/\
     ( o.o )
      > ^ <
      (___)
""",

r"""
       .-.
      /\_/\
     ( -.- )
      > ^ <
      (___)
""",

r"""
       .-.
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
      (___)
""",

r"""
       .-.
      /\_/\
     ( o.o )
      > ^ <
        _
      (___)
""",

r"""
       .-.
      /\_/\
    _( o.o )_
      > ^ <
      (___)
""",

r"""
       .-.
      /\_/\
     ( o.o )  <
      > ^ <
      (___)
""",

r"""
          *
      /\_/\
     ( o.o )
      > ^ <
       .   .
""",

r"""
          *
      /\_/\
     ( -.- )
      > ^ <
       .   .
""",

r"""
          *
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
       .   .
""",

r"""
      .  *  .
      /\_/\
     ( -.- )
      > ^ <
         .
""",

r"""
      .  *  .
       /\_/\
      ( o.o )
    __/ > ^ <__
         .
""",

r"""
      .  *  .
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
         .
""",


r"""
      .  *  .
      /\_/\
     ( o.o )
      > ^ <~~~~
         .
""",


r"""
       .---.
      /\_/\
     ( o.o )
      > ^ <
      (     )
""",

r"""
       .---.
      /\_/\
     ( -.- )
      > ^ <
      (     )
""",

r"""
       .---.
       /\_/\
      ( o.o )
    __/ > ^ <__
      (     )
""",

r"""
       .---.
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
      (     )
""",

r"""
       .---.
       /\_/\
      ( o.o )
     /  > ^ <
      (     )
""",

r"""
       .---.
      /\_/\
    _( o.o )_
      > ^ <
      (     )
""",

r"""
          .
      /\_/\
     ( o.o )
      > ^ <
        ...
""",

r"""
          .
      /\_/\
     ( -.- )
      > ^ <
        ...
""",

r"""
          .
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
        ...
""",


r"""
          .
      /\_/\
     ( o.o )
      > ^ <~~~~
        ...
""",

r"""
          .
       /\_/\
      ( o.o )
       > ^ <
        ...
""",

r"""
          .
      /\_/\
    _( o.o )_
      > ^ <
        ...
""",

r"""
       ~~~
      /\_/\
     ( o.o )
      > ^ <
      ~~~~~
""",

r"""
       ~~~
      /\_/\
     ( -.- )
      > ^ <
      ~~~~~
""",

r"""
      .----.
      /\_/\
     ( o.o )
      > ^ <
      |____|
""",

r"""
      .----.
      /\_/\
     ( -.- )
      > ^ <
      |____|
""",

r"""
      .----.
       /\_/\
      ( o.o )
    __/ > ^ <__
      |____|
""",

r"""
      .----.
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
      |____|
""",

r"""
      .----.
       /\_/\
      ( o.o )
     /  > ^ <
      |____|
""",

r"""
      .----.
      /\_/\
    _( o.o )_
      > ^ <
      |____|
""",

r"""
        <3
      /\_/\
     ( o.o )
      > ^ <
""",

r"""
        <3
      /\_/\
     ( -.- )
      > ^ <
""",

r"""
        <3
       /\_/\
      ( o.o )
    __/ > ^ <__
""",

r"""
        <3
      /\_/\
     ( o.o )
     /|   |\
      > ^ <
""",

r"""
        <3
      /\_/\
     ( o.o )
      > ^ <
        _
""",

r"""
        <3
      /\_/\
     ( o.o )
      > ^ <~~~~
""",

r"""
        <3
       /\_/\
      ( o.o )
     /  > ^ <
""",

r"""
        <3
      /\_/\
    _( o.o )_
      > ^ <
""",

r"""
        <3
      /\_/\
     ( o.o )  <
      > ^ <
""",

r"""
          ✦
      /\_/\
     ( o.o )
      > ^ <
       · · ·
""",

r"""
       ☆   ✦
      /\_/\
     ( -.- )
      > ^ <
""",

r"""
      ← · · · →
        /\_/\
       ( o.o )
        > ^ <
""",

r"""
       ✧  ·  ✧
      /\_/\
     ( o.o )
      > ^ <
        ↺
""",

r"""
          ♡
      /\_/\
     ( o.o )
      > ^ <
          ♥
""",

r"""
      ✦   ★   ✦
        /\_/\
       ( o.o )
        > ^ <
""",

r"""
       ·   ·   ·
      /\_/\
     ( -.- )
      > ^ <
       ·   ·   ·
""",

r"""
          ↑
      /\_/\
     ( o.o )
      > ^ <
          ↓
""",

r"""
      ♡ · ♥ · ♡
        /\_/\
       ( o.o )
        > ^ <
""",

r"""
       ↺  ↺  ↺
      /\_/\
     ( o.o )
      > ^ <
""",

r"""
      ✦ · ✧ · ✦
""",

r"""
      ☆     ★     ☆
""",

r"""
      ← · · · · · →
""",

r"""
      ♡     ♥     ♡
""",

r"""
      ↑  ✦  ↓
""",
]

tiredidles = [
"Glym blinks slowly, then blinks again like the first one did not finish the job. ·",
"Glym's ears droop a little, softening him into a very small tragedy. ↓",
"Glym yawns so wide his whole tiny face briefly becomes a cave. ☆",
"Glym sits down ↓ remembers he had plans, and immediately questions the plans.",
"His tail drags sleepily behind him like it has resigned from public life. · ·",
"Glym stares at nothing with heavy little eyes.",
"A tiny tired huff escapes Glym.",
"Glym paws at the floor like bedtime might still be negotiable. •",
"The little fox wobbles slightly, then pretends the room moved. ↺",
"Glym gives one heroic sleepy blink and survives it. ✦",
"Glym curls his tail around his paws but refuses to admit this is basically pre-napping. ♡",
"Glym looks personally betrayed by consciousness. ·",
"Glym tries to groom one paw and forgets what paw maintenance is.",
"Glym lowers his head ↓ almost gives in, then perks up ↑ out of pure stubbornness.",
"A soft grumble leaves Glym at the sheer concept of being awake.",
"Glym's eyes narrow like the universe has become too bright and too long. ★",
"The little fox takes one slow step and seems offended by the effort.",
"Glym yawns, then looks embarrassed by how dramatic it was.",
"His ears sag, recover slightly, then sag again.",
"Glym stares at the floor as if sleep is written there in tiny letters.",
"Glym blinks so slowly he nearly leaves the room spiritually.",
"The little fox sways in place, bravely losing a war against nap gravity. ↓",
"Glym gives his paw one sleepy lick and decides that is enough hygiene for now.",
"Glym looks around like he is searching for the nearest acceptable dream.",
"His tail curls closer, preparing the nest without asking permission. ♡",
"Glym huffs softly, as if wakefulness has made a rude suggestion.",
"Glym sits very still, powered mostly by spite and fading battery.",
"The little fox's head dips, then snaps back up with fake confidence.",
"Glym appears to ponder whether being awake is legally required. ✧",
"His eyes grow heavy, but his dignity remains barely upright.",
"Glym takes a tiny step, pauses, and seems to forget the destination.",
"Glym yawns again, smaller this time, like a secret door opening. ·",
"The little fox looks ready to argue with sleep and lose immediately.",
"Glym's tail gives one tired flick, more suggestion than movement. ✦",
"Glym blinks at the room like the room has become a bedtime story. ☆",
"Glym's eyelids descend with theatrical gravity. ↓",
"The little fox seems to be buffering toward sleep. · · ·",
"Glym looks up at nothing and asks it for mercy. ✧",
"One ear remains awake. The rest of Glym has resigned. ·",
"Glym takes a slow breath and briefly becomes mostly blanket. ♡",
"Sleep circles him politely. ↺",
"Glym blinks at a tiny star only he can see. ✦",
]

freshidles = [
"Glym opens his eyes like the dream world has reluctantly released him. ✦",
"Glym wakes in a soft little curl, then remembers he has a body. ·",
"Glym blinks awake with the solemn expression of a fox returning from prophecy. ★",
"Glym stretches all four paws and shakes off the last crumbs of sleep. · · ✧",
"Glym uncurls from his tail and looks ready to recommit to nonsense. ↺",
"His ears rise first ↑ then the rest of Glym slowly reports for duty.",
"Glym yawns, stretches, and appears to permit the world to continue existing. ☆",
"The little fox wakes bright-eyed, suspiciously refreshed, and mildly mysterious. ✦",
"Glym gives one tiny shake and resumes being a creature. ·",
"Glym opens his eyes like he just remembered where he left reality. ✧",
"Glym wakes up and immediately looks pleased with himself.",
"Glym blinks twice, then seems to accept consciousness as today's arrangement. · ·",
"Glym's tail slips away from his nose as he returns to the waking world. ♡",
"Glym stretches so hard his toes briefly become important. ★",
"The little fox lifts his head like he heard morning whisper his name. ↑",
"Glym wakes with a tiny huff, as if sleep told him something rude.",
"Glym blinks at the room, freshly downloaded from dreamland. ✧",
"Glym uncurls one paw at a time, assembling himself from warm fluff.",
"Glym looks around like he expects the room to be impressed he survived his nap.",
"Glym wakes soft, bright-eyed, and already involved in private fox business.",
"Glym gives his fur a quick shake. Reboot complete. ✦",
"The little fox yawns like a small cave opening under the moon.",
"Glym wakes with the fragile dignity of someone who was absolutely never sleepy.",
"Glym lifts his nose and tests the air for post-nap accuracy. ↑",
"Glym blinks awake, carrying one tiny secret back from sleep. ✦",
"✦ · awake · ✦",
"Glym returns from sleep with one bright little star still caught in him. ☆",
"The little fox re-enters the world one paw at a time. · · ·",
"Glym wakes up and chooses life, snacks, and suspicious flooring. ♡",
"His ears rise like tiny banners. ↑ ↑",
"Glym blinks at the day as if the day has paperwork. ✧",
]

activeidles.extend([
    tint("Glym pauses under a small gold glimmer. ✦", YELLOW),
    tint("The little fox regards the void with suspicious green eyes.", GREEN),
    tint("Glym briefly understands the universe and refuses to elaborate. ★", CYAN),
    colorwave("Glym becomes a tiny celestial error."),
])

sleepidles.extend([
    tint("Glym dreams in soft blue fragments. · · ·", BLUE),
    tint("A purple door opens somewhere inside Glym's sleep. ✧", MAGENTA),
    tint("One gold star keeps watch over the little fox. ✦", YELLOW),
])

tiredidles.extend([
    tint("Glym's eyelids sink like little gray curtains. ↓", GRAY),
    tint("Sleep circles Glym in blue. ↺", BLUE),
])

freshidles.extend([
    tint("Glym wakes with a tiny green spark in his eyes. ✦", GREEN),
    tint("Morning arrives, and Glym permits it. ☆", YELLOW),
])

currentstate = r"""

✦ Glym wakes up 
and blinks hello ✦

     /\_/\
    ( -.- )
     > ^ <
"""

while alive == True :
    
    if awake == True :
        sleepiness = sleepiness + 1

    if awake == False :
        sleepiness = sleepiness - 5

    if awake == False and sleepiness <= 1 :
        currentstate = random.choice(freshidles)
        awake = True
        sleepiness = 0
        
    if awake == True and sleepiness > 1 and sleepiness <= 3 :
        currentstate = random.choice(freshidles)

    if awake == True and sleepiness > 3 and sleepiness < 20 :
        ufochance = random.randint(1, 50)

        if ufochance == 1 :
            currentstate = ufo + "\n" + tint("Something deeply illegal glows above Glym. ✦", CYAN)

        else :
            presschance = random.randint(1, 10)
            asciichance = random.randint(1, 5)

            if presschance == 10 :
                glymcounter = glymcounter + 1
                currentstate = tint("Glym boops you    ♡", HEART)
            elif asciichance == 1 :
                currentstate = random.choice(asciiidles)
            
            else :
                currentstate = random.choice(activeidles)
        
    if sleepiness <= 19 :
        sleepy = False

    if sleepiness >= 20 and sleepiness < 25:
        if awake == True :
            currentstate = random.choice(tiredidles)
        sleepy = True
            
    if sleepiness >= 25 :
        if awake == True :
            currentstate = tint("Glym curls up and drifts to sleep · · ·", BLUE)
        awake = False
    elif awake == False :
        currentstate = random.choice(sleepidles)

    tick = tick + 1
         
    print_stage(currentstate, glymcounter)

    if alive == True :
        time.sleep(10)
