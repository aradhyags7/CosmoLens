"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         COSMO LENS  —  STAR ATLAS  v2                                       ║
║   pip install pygame skyfield numpy pandas                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
DRAG      Rotate sky          SCROLL  Zoom / FOV
W/A/S/D   Keyboard rotate     R       Reset view
C         Constellations       L       Const labels    G  RA/Dec grid
M         Milky Way            N       Star names       B  Spectral colors
T         Twinkling            P       Planets          F1 Deep sky objects
1         Stars only           2       Planets only     3  Both (default)
S         Search star          TAB     Next named star  H  Help
+/-       Magnitude limit      F3      Screenshot       ESC Quit
"""

import pygame, numpy as np, sys, os, math, time, datetime, random, subprocess
for pkg in ["pygame","skyfield","numpy","pandas"]:
    subprocess.run([sys.executable,"-m","pip","install","-q",pkg],check=False)

from skyfield.data import hipparcos
from skyfield.api  import load as skyload, Star

# ─────────────────────────────────────────────────────────────────────────────
#  NAMED STARS  — 150 + entries  (HIP → name, Bayer, spectral, constellation)
# ─────────────────────────────────────────────────────────────────────────────
NAMED_STARS = {
    # Canis Major
    32349:("Sirius",     "α CMa","A1V",  "Canis Major"),
    33579:("Adhara",     "ε CMa","B2II", "Canis Major"),
    34444:("Wezen",      "δ CMa","F8Ia", "Canis Major"),
    35904:("Aludra",     "η CMa","B5Ia", "Canis Major"),
    30324:("Mirzam",     "β CMa","B1II-III","Canis Major"),
    # Orion
    24436:("Rigel",      "β Ori","B8Ia", "Orion"),
    27989:("Betelgeuse", "α Ori","M2Ia", "Orion"),
    26727:("Bellatrix",  "γ Ori","B2III","Orion"),
    25336:("Saiph",      "κ Ori","B0.5Ia","Orion"),
    26311:("Alnitak",    "ζ Ori","O9.5Ib","Orion"),
    26207:("Alnilam",    "ε Ori","B0Ia", "Orion"),
    25930:("Mintaka",    "δ Ori","O9.5II","Orion"),
    25428:("Meissa",     "λ Ori","O8III","Orion"),
    22449:("Rigel",      "β Ori","B8Ia", "Orion"),   # duplicate guard
    # Ursa Major
    54061:("Dubhe",      "α UMa","K0IIIa","Ursa Major"),
    53910:("Merak",      "β UMa","A1V",  "Ursa Major"),
    58001:("Phecda",     "γ UMa","A0Ve", "Ursa Major"),
    59774:("Megrez",     "δ UMa","A3V",  "Ursa Major"),
    62956:("Alioth",     "ε UMa","A0p",  "Ursa Major"),
    65378:("Mizar",      "ζ UMa","A1V",  "Ursa Major"),
    67301:("Alkaid",     "η UMa","B3V",  "Ursa Major"),
    # Ursa Minor
    11767:("Polaris",    "α UMi","F7Ib", "Ursa Minor"),
    85822:("Kochab",     "β UMi","K4III","Ursa Minor"),
    79822:("Pherkad",    "γ UMi","A3III","Ursa Minor"),
    # Lyra
    91262:("Vega",       "α Lyr","A0V",  "Lyra"),
    93194:("Sheliak",    "β Lyr","B8II", "Lyra"),
    92420:("Sulafat",    "γ Lyr","B9III","Lyra"),
    # Cygnus
    102098:("Deneb",     "α Cyg","A2Ia", "Cygnus"),
    95947:("Sadr",       "γ Cyg","F8Ib", "Cygnus"),
    100453:("Gienah",    "ε Cyg","K0III","Cygnus"),
    97165:("Delta Cyg",  "δ Cyg","B9.5III","Cygnus"),
    94779:("Albireo",    "β Cyg","K3II", "Cygnus"),
    # Aquila
    97649:("Altair",     "α Aql","A7V",  "Aquila"),
    98036:("Tarazed",    "γ Aql","K3II", "Aquila"),
    96229:("Alshain",    "β Aql","G8IV", "Aquila"),
    # Scorpius
    80763:("Antares",    "α Sco","M1.5Ib","Scorpius"),
    82396:("Tau Sco",    "τ Sco","B0V",  "Scorpius"),
    84143:("Shaula",     "λ Sco","B1.5IV","Scorpius"),
    85927:("Lesath",     "υ Sco","B2IV", "Scorpius"),
    78401:("Dschubba",   "δ Sco","B0.3IV","Scorpius"),
    76600:("Graffias",   "β Sco","B1V",  "Scorpius"),
    85696:("Kappa Sco",  "κ Sco","B1.5III","Scorpius"),
    # Leo
    49669:("Regulus",    "α Leo","B8IVn","Leo"),
    57632:("Denebola",   "β Leo","A3V",  "Leo"),
    50583:("Algieba",    "γ Leo","K0III","Leo"),
    54872:("Zosma",      "δ Leo","A4V",  "Leo"),
    47908:("Eta Leo",    "η Leo","A0Ib", "Leo"),
    46390:("Al Jabbah",  "ζ Leo","F0III","Leo"),
    # Gemini
    37826:("Castor",     "α Gem","A1V",  "Gemini"),
    45941:("Pollux",     "β Gem","K0IIIb","Gemini"),
    36850:("Tejat Post.","μ Gem","M3III","Gemini"),
    35550:("Mebsuda",    "ε Gem","G8Ib", "Gemini"),
    44816:("Wasat",      "δ Gem","F0IV", "Gemini"),
    40526:("Alzirr",     "ξ Gem","F5IV", "Gemini"),
    # Taurus
    21421:("Aldebaran",  "α Tau","K5III","Taurus"),
    20205:("Alnath",     "β Tau","B7III","Taurus"),
    20889:("Zeta Tau",   "ζ Tau","B2IVe","Taurus"),
    # Auriga
    27366:("Capella",    "α Aur","G8III","Auriga"),
    28360:("Menkalinan", "β Aur","A2IV", "Auriga"),
    26207:("Bogardus",   "ε Aur","F0Ia", "Auriga"),
    # Perseus
    15863:("Mirfak",     "α Per","F5Ib", "Perseus"),
    14576:("Algol",      "β Per","B8V",  "Perseus"),
    14632:("Atik",       "ο Per","B1III","Perseus"),
    17358:("Miram",      "η Per","K3Ib", "Perseus"),
    18532:("Menkib",     "ξ Per","O7.5III","Perseus"),
    12777:("Gorgonea T.",  "π Per","A2Vp","Perseus"),
    # Boötes
    69673:("Arcturus",   "α Boo","K1.5III","Boötes"),
    72105:("Muphrid",    "η Boo","G0IV", "Boötes"),
    67927:("Seginus",    "γ Boo","A7III","Boötes"),
    71075:("Nekkar",     "β Boo","G8IIIa","Boötes"),
    71053:("Izar",       "ε Boo","K0II", "Boötes"),
    # Virgo
    65474:("Spica",      "α Vir","B1V",  "Virgo"),
    63608:("Zavijava",   "β Vir","F9V",  "Virgo"),
    61941:("Porrima",    "γ Vir","F0V",  "Virgo"),
    57380:("Heze",       "ζ Vir","A3V",  "Virgo"),
    66249:("Zaniah",     "η Vir","A2V",  "Virgo"),
    69427:("Vindemiatrix","ε Vir","G8IIIab","Virgo"),
    # Canis Minor
    37279:("Procyon",    "α CMi","F5IV", "Canis Minor"),
    36188:("Gomeisa",    "β CMi","B8Ve", "Canis Minor"),
    # Centaurus
    71683:("Rigil Kent.","α Cen","G2V",  "Centaurus"),
    68702:("Hadar",      "β Cen","B1III","Centaurus"),
    68933:("Menkent",    "θ Cen","K0III","Centaurus"),
    # Crux
    60718:("Acrux",      "α Cru","B0.5IV","Crux"),
    62434:("Mimosa",     "β Cru","B0.5III","Crux"),
    59747:("Gacrux",     "γ Cru","M3.5III","Crux"),
    63003:("Delta Cru",  "δ Cru","B2IV", "Crux"),
    # Carina
    30438:("Canopus",    "α Car","F0Ib", "Carina"),
    45080:("Avior",      "ε Car","K3III+B2V","Carina"),
    50371:("Aspidiske",  "ι Car","A8Ib", "Carina"),
    41037:("Eta Car",    "η Car","LBV",  "Carina"),
    # Eridanus
    7588: ("Achernar",   "α Eri","B6Vep","Eridanus"),
    17651:("Cursa",      "β Eri","A3IIIvar","Eridanus"),
    15510:("Zaurak",     "γ Eri","M1IIIab","Eridanus"),
    # Cassiopeia
    3179: ("Schedar",    "α Cas","K0IIIa","Cassiopeia"),
    4427: ("Caph",       "β Cas","F2III","Cassiopeia"),
    6686: ("Gamma Cas",  "γ Cas","B0.5IVpe","Cassiopeia"),
    8886: ("Ruchbah",    "δ Cas","A5III","Cassiopeia"),
    11569:("Segin",      "ε Cas","B3IV", "Cassiopeia"),
    # Andromeda
    677:  ("Alpheratz",  "α And","B9p",  "Andromeda"),
    5447: ("Mirach",     "β And","M0III","Andromeda"),
    9640: ("Almach",     "γ And","K3II", "Andromeda"),
    # Pegasus
    109176:("Markab",    "α Peg","B9III","Pegasus"),
    113881:("Scheat",    "β Peg","M2.5II","Pegasus"),
    3821: ("Algenib",    "γ Peg","B2IV", "Pegasus"),
    112158:("Enif",      "ε Peg","K2Ib", "Pegasus"),
    # Piscis Austrinus / others
    113368:("Fomalhaut", "α PsA","A3V",  "Piscis Austrinus"),
    # Sagittarius
    90185:("Kaus Austr.","ε Sgr","A0III","Sagittarius"),
    89931:("Nunki",      "σ Sgr","B2.5V","Sagittarius"),
    92855:("Ascella",    "ζ Sgr","A2III","Sagittarius"),
    88635:("Kaus Med.",  "δ Sgr","K3III","Sagittarius"),
    90496:("Kaus Bor.",  "λ Sgr","K1IIIb","Sagittarius"),
    93506:("Phi Sgr",    "φ Sgr","B8III","Sagittarius"),
    # Capricornus
    100064:("Algedi",    "α Cap","G3Ib", "Capricornus"),
    100345:("Dabih",     "β Cap","F8V",  "Capricornus"),
    104139:("Nashira",   "γ Cap","F0p",  "Capricornus"),
    104139:("Deneb Alg.","δ Cap","A5mF2","Capricornus"),
    # Aquarius
    109074:("Sadalsuud", "β Aqr","G0Ib", "Aquarius"),
    106278:("Sadalmelik","α Aqr","G2Ib", "Aquarius"),
    112961:("Skat",      "δ Aqr","A3V",  "Aquarius"),
    # Corona Borealis
    76267:("Alphecca",   "α CrB","A0V",  "Corona Borealis"),
    # Hercules
    80816:("Kornephoros","β Her","G8III","Hercules"),
    84345:("Sarin",      "δ Her","A3IV", "Hercules"),
    81693:("Zeta Her",   "ζ Her","F9IV", "Hercules"),
    # Ophiuchus
    84970:("Rasalhague", "α Oph","A5III","Ophiuchus"),
    86742:("Cebalrai",   "β Oph","K2III","Ophiuchus"),
    83000:("Yed Prior",  "δ Oph","M1III","Ophiuchus"),
    # Pisces
    9487: ("Eta Psc",    "η Psc","G8III","Pisces"),
    # Aries
    9884: ("Hamal",      "α Ari","K2IIIb","Aries"),
    8903: ("Sheratan",   "β Ari","A5V",  "Aries"),
    # Draco
    87585:("Eltanin",    "γ Dra","K5III","Draco"),
    85670:("Rastaban",   "β Dra","G2Ib", "Draco"),
    # Lupus
    73273:("Alpha Lup",  "α Lup","B1.5III","Lupus"),
    74395:("Beta Lup",   "β Lup","B2III","Lupus"),
    # Ara
    82514:("Alpha Ara",  "α Ara","B2Vne","Ara"),
    # Pavo
    99240:("Peacock",    "α Pav","B2IV", "Pavo"),
    # Tucana
    110130:("Alpha Tuc", "α Tuc","K3III","Tucana"),
    # Grus
    109268:("Alnair",    "α Gru","B7IV", "Grus"),
    # Vela
    39953:("Gamma Vel",  "γ Vel","WC8",  "Vela"),
    42913:("Delta Vel",  "δ Vel","A1V",  "Vela"),
    # Puppis
    38170:("Naos",       "ζ Pup","O4I",  "Puppis"),
    # Gemini extra
    29655:("Propus",     "η Gem","M6III","Gemini"),
    # Phoenix
    3419: ("Ankaa",      "α Phe","K0.5IIIb","Phoenix"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  SPECTRAL COLORS
# ─────────────────────────────────────────────────────────────────────────────
SPEC_COLORS={"O":(155,176,255),"B":(170,191,255),"A":(255,255,255),
             "F":(255,255,205),"G":(255,244,155),"K":(255,198,95),
             "M":(255,115,55),"W":(180,220,255),"L":(200,100,50),"?": (200,210,230)}

def spec_color(s):
    if not s: return SPEC_COLORS["?"]
    return SPEC_COLORS.get(s[0].upper(),SPEC_COLORS["?"])

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTELLATIONS  — 46 constellations
# ─────────────────────────────────────────────────────────────────────────────
CONSTELLATIONS = {
    "Orion":[(27989,26727),(26727,25930),(25930,26207),(26207,26311),(26311,24436),
             (24436,25930),(27989,25336),(25336,26311),(26727,25428),(25428,27989)],
    "Ursa Major":[(54061,53910),(53910,58001),(58001,59774),(59774,62956),(62956,65378),(65378,67301)],
    "Ursa Minor":[(11767,85822),(85822,79822),(79822,77055)],
    "Lyra":[(91262,92420),(92420,93194),(93194,91262)],
    "Cygnus":[(102098,95947),(95947,100453),(100453,97165),(97165,94779),(100453,102098)],
    "Aquila":[(97649,98036),(97649,96229),(98036,96229)],
    "Scorpius":[(76600,78401),(78401,80763),(80763,82396),(82396,84143),(84143,85927),(85927,85696)],
    "Leo":[(49669,50583),(50583,47908),(49669,57632),(57632,54872),(50583,46390)],
    "Gemini":[(37826,44816),(44816,45941),(37826,36850),(36850,35550),(35550,29655),(44816,40526)],
    "Taurus":[(21421,20889),(20889,20205),(21421,25428)],
    "Auriga":[(27366,28360),(28360,26207),(26207,27366)],
    "Cassiopeia":[(3179,4427),(4427,6686),(6686,8886),(8886,11569)],
    "Perseus":[(15863,14576),(15863,14632),(14632,17358),(17358,18532),(15863,12777)],
    "Boötes":[(69673,72105),(69673,67927),(67927,71075),(69673,71053),(71053,72105)],
    "Virgo":[(65474,63608),(63608,61941),(61941,57380),(65474,66249),(66249,69427)],
    "Andromeda":[(677,5447),(5447,9640)],
    "Pegasus":[(109176,113881),(113881,677),(677,3821),(3821,109176),(109176,112158)],
    "Sagittarius":[(88635,90185),(90185,90496),(88635,89931),(89931,92855),(92855,90185),(90496,93506)],
    "Canis Major":[(32349,30324),(32349,33579),(33579,34444),(34444,35904)],
    "Canis Minor":[(37279,36188)],
    "Crux":[(60718,63003),(62434,59747)],  # N-S and E-W bars
    "Centaurus":[(71683,68702),(68702,68933)],
    "Carina":[(30438,45080),(45080,50371)],
    "Eridanus":[(7588,17651),(17651,15510)],
    "Corona Borealis":[(76267,76267)],  # small arc — placeholder
    "Hercules":[(80816,84345),(84345,81693),(81693,80816)],
    "Ophiuchus":[(84970,86742),(86742,83000),(83000,84970)],
    "Capricornus":[(100064,100345),(100345,104139)],
    "Aquarius":[(106278,109074),(109074,112961)],
    "Aries":[(9884,8903)],
    "Draco":[(87585,85670)],
    "Grus":[(109268,109268)],
    "Canis Major extra":[(32349,34444)],
    "Vela":[(39953,42913)],
    "Scorpius tail":[(84143,84970)],
}

# Remove self-loops
CONSTELLATIONS = {k:[(a,b) for a,b in v if a!=b] for k,v in CONSTELLATIONS.items()}

CONST_LABELS = {
    "Orion":(84.5,2.0),"Ursa Major":(168.0,57.0),"Ursa Minor":(230.0,73.0),
    "Lyra":(282.0,37.0),"Cygnus":(310.0,42.0),"Scorpius":(250.0,-28.0),
    "Leo":(165.0,16.0),"Gemini":(113.0,22.0),"Taurus":(67.0,16.0),
    "Aquila":(295.0,5.0),"Cassiopeia":(14.0,61.0),"Perseus":(48.0,46.0),
    "Boötes":(215.0,32.0),"Virgo":(201.0,1.0),"Andromeda":(20.0,38.0),
    "Pegasus":(340.0,20.0),"Sagittarius":(286.0,-27.0),"Canis Major":(103.0,-22.0),
    "Crux":(186.0,-60.0),"Centaurus":(210.0,-47.0),"Carina":(138.0,-60.0),
    "Eridanus":(55.0,-33.0),"Auriga":(78.0,42.0),"Hercules":(258.0,27.0),
    "Ophiuchus":(257.0,-4.0),"Aquarius":(335.0,-11.0),"Capricornus":(306.0,-19.0),
    "Draco":(270.0,65.0),"Aries":(31.0,22.0),
}

# ─────────────────────────────────────────────────────────────────────────────
#  PLANET DATA
# ─────────────────────────────────────────────────────────────────────────────
PLANET_INFO = {
    "mercury":  ("Mercury",  (180,180,185), 3,  "Rocky, 0.39 AU"),
    "venus":    ("Venus",    (255,248,200), 5,  "Hottest planet, 0.72 AU"),
    "mars":     ("Mars",     (255,110,65),  4,  "Red Planet, 1.52 AU"),
    "jupiter barycenter": ("Jupiter",(255,225,185), 7, "Largest planet, 5.2 AU"),
    "saturn barycenter":  ("Saturn", (240,215,150), 6, "Ring giant, 9.6 AU"),
    "uranus barycenter":  ("Uranus", (150,230,230), 5, "Ice giant, 19.2 AU"),
    "neptune barycenter": ("Neptune",(100,145,255), 5, "Farthest, 30.1 AU"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  DSO CATALOG
# ─────────────────────────────────────────────────────────────────────────────
DSO_CATALOG = [
    ("M1  Crab Nebula",      83.82, 22.01,"SNR", 8.4,"Supernova remnant in Taurus"),
    ("M8  Lagoon Nebula",   270.92,-24.38,"NEB", 5.8,"Emission nebula in Sagittarius"),
    ("M13 Hercules Cluster",250.42, 36.46,"GC",  5.8,"Great globular cluster"),
    ("M20 Trifid Nebula",   270.62,-23.03,"NEB", 8.5,"Emission+reflection nebula"),
    ("M22 Glob. Cluster",   279.10,-23.90,"GC",  5.1,"Bright globular in Sagittarius"),
    ("M27 Dumbbell",        299.90, 22.72,"PN",  7.5,"Planetary nebula in Vulpecula"),
    ("M31 Andromeda",        10.68, 41.27,"GAL", 3.4,"Nearest spiral galaxy, 2.5M ly"),
    ("M33 Triangulum",       23.46, 30.66,"GAL", 5.7,"Local Group spiral, 2.7M ly"),
    ("M42 Orion Nebula",     83.82, -5.39,"NEB", 4.0,"Giant emission nebula"),
    ("M44 Beehive",         130.10, 19.67,"OC",  3.1,"Open cluster in Cancer"),
    ("M45 Pleiades",         56.75, 24.12,"OC",  1.2,"Seven Sisters, 444 ly"),
    ("M51 Whirlpool",       202.47, 47.20,"GAL", 8.4,"Interacting spiral galaxy"),
    ("M57 Ring Nebula",     283.40, 33.03,"PN",  8.8,"Classic planetary nebula in Lyra"),
    ("M64 Black Eye",       194.18, 21.68,"GAL", 8.5,"Galaxy with dark dust lane"),
    ("M81 Bode's Galaxy",   148.89, 69.07,"GAL", 6.9,"Bright spiral in Ursa Major"),
    ("M82 Cigar Galaxy",    148.97, 69.68,"GAL", 8.4,"Starburst irregular galaxy"),
    ("M104 Sombrero",       189.99,-11.62,"GAL", 8.0,"Edge-on spiral with dust lane"),
    ("NGC 869 h Per",        34.75, 57.13,"OC",  4.3,"Perseus double cluster"),
    ("NGC 884 χ Per",        35.60, 57.13,"OC",  4.4,"Perseus double cluster"),
    ("NGC 3372 Eta Car Neb",160.00,-59.68,"NEB", 3.0,"Largest nebula, 7500 ly"),
    ("Omega Centauri",      201.70,-47.48,"GC",  3.9,"Largest globular cluster"),
    ("47 Tucanae",           24.04,-72.08,"GC",  4.0,"2nd brightest globular"),
]
DSO_COLORS={"GAL":(255,160,80),"GC":(200,255,200),"OC":(255,255,155),
            "NEB":(120,200,255),"SNR":(255,120,120),"PN":(155,255,255)}

MILKY_WAY = [
    (266.4,-28.9),(275,-20),(285,-14),(295,-9),(305,-4),(315,1),(325,7),(335,13),
    (345,18),(355,22),(5,26),(15,28),(25,29),(35,29),(45,28),(55,26),(65,22),
    (75,18),(85,13),(95,7),(105,1),(115,-6),(125,-13),(135,-20),(145,-28),
    (155,-34),(165,-37),(175,-38),(185,-36),(195,-32),(205,-27),(215,-21),
    (225,-15),(235,-9),(245,-4),(255,1),(265,6),(275,11),(285,15),(295,18),
    (305,20),(315,21),(325,22),(335,22),(345,21),(355,19),
]

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def radec_xyz(ra_deg,dec_deg):
    ra=math.radians(ra_deg); dec=math.radians(dec_deg)
    return np.array([math.cos(dec)*math.cos(ra),math.cos(dec)*math.sin(ra),math.sin(dec)])

def rot_matrix(yaw,pitch):
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
    Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rx=np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])
    return Rx@Ry

def project(vec,rot,W,H,fov):
    rv=rot@vec
    if rv[2]<=0.01: return None,None,None
    f=fov/rv[2]
    return int(rv[0]*f+W/2), int(-rv[1]*f+H/2), rv[2]

def txt(surf,font,text,x,y,col=(220,240,255),sh=True):
    if sh: surf.blit(font.render(text,True,(0,0,0)),(x+1,y+1))
    t=font.render(text,True,col); surf.blit(t,(x,y)); return t.get_width()

def panel(surf,x,y,w,h,a=215,border=(0,115,200),hdr=None):
    s=pygame.Surface((w,h),pygame.SRCALPHA); s.fill((2,8,22,a)); surf.blit(s,(x,y))
    pygame.draw.rect(surf,border,(x,y,w,h),1)
    if hdr:
        hs=pygame.Surface((w-2,26),pygame.SRCALPHA); hs.fill((*hdr[:3],35)); surf.blit(hs,(x+1,y+1))

# ─────────────────────────────────────────────────────────────────────────────
#  PLANET MANAGER  (runs in background thread)
# ─────────────────────────────────────────────────────────────────────────────
class PlanetManager:
    def __init__(self):
        self.positions={}; self.lock=threading.Lock()
        self.status="Loading ephemeris…"; self.ready=False
        self.ts=None; self.eph=None
    def load(self):
        import threading
        threading.Thread(target=self._load,daemon=True).start()
    def _load(self):
        try:
            ts=skyload.timescale()
            self.status="Downloading DE421 ephemeris (~17 MB first run)…"
            eph=skyload('de421.bsp')
            self.ts=ts; self.eph=eph; self.ready=True
            self.status="Planets ready"
        except Exception as ex:
            self.status=f"Planet error: {ex}"
    def update(self,dt_utc):
        if not self.ready: return
        try:
            t=self.ts.from_datetime(dt_utc.replace(tzinfo=datetime.timezone.utc))
            earth=self.eph['earth']
            positions={}
            for key,(name,col,sz,desc) in PLANET_INFO.items():
                try:
                    astr=earth.at(t).observe(self.eph[key])
                    ra,dec,dist=astr.radec()
                    positions[name]={"ra":ra.degrees,"dec":dec.degrees,
                                     "xyz":radec_xyz(ra.degrees,dec.degrees),
                                     "color":col,"size":sz,"dist":dist.au,"desc":desc}
                except: pass
            with self.lock: self.positions=positions
        except: pass
    def get(self):
        with self.lock: return dict(self.positions)

import threading

# ─────────────────────────────────────────────────────────────────────────────
#  DSO ICONS
# ─────────────────────────────────────────────────────────────────────────────
def draw_dso_icon(surf,x,y,dtype,sz=8):
    col=DSO_COLORS.get(dtype,(200,200,200))
    if dtype=="GAL":
        pygame.draw.ellipse(surf,col,(x-sz,y-sz//2,sz*2,sz),1)
    elif dtype in("GC","OC"):
        pygame.draw.circle(surf,col,(x,y),sz,1)
        pygame.draw.line(surf,col,(x-sz-2,y),(x+sz+2,y),1)
        pygame.draw.line(surf,col,(x,y-sz-2),(x,y+sz+2),1)
    elif dtype in("NEB","SNR"):
        pts=[(int(x+sz*math.cos(math.radians(i*60))),int(y+sz*math.sin(math.radians(i*60)))) for i in range(6)]
        pygame.draw.polygon(surf,col,pts,1)
    elif dtype=="PN":
        pygame.draw.circle(surf,col,(x,y),sz,1); pygame.draw.circle(surf,col,(x,y),max(2,sz//2),1)

# ─────────────────────────────────────────────────────────────────────────────
#  GRID
# ─────────────────────────────────────────────────────────────────────────────
def draw_grid(surf,rot,W,H,fov,fsm):
    gs=pygame.Surface((W,H),pygame.SRCALPHA)
    for dec in range(-80,81,20):
        pts=[]
        for ra in range(0,362,4):
            v=radec_xyz(ra,dec); sx,sy,_=project(v,rot,W,H,fov)
            if sx and 0<=sx<W and 0<=sy<H: pts.append((sx,sy))
            elif pts:
                if len(pts)>1: pygame.draw.lines(gs,(255,255,255,17),False,pts,1)
                pts=[]
        if len(pts)>1: pygame.draw.lines(gs,(255,255,255,17),False,pts,1)
    for ra in range(0,360,30):
        pts=[]
        for dec in range(-88,89,3):
            v=radec_xyz(ra,dec); sx,sy,_=project(v,rot,W,H,fov)
            if sx and 0<=sx<W and 0<=sy<H: pts.append((sx,sy))
            elif pts:
                if len(pts)>1: pygame.draw.lines(gs,(255,255,255,17),False,pts,1)
                pts=[]
        if len(pts)>1: pygame.draw.lines(gs,(255,255,255,17),False,pts,1)
    surf.blit(gs,(0,0))
    for ra in range(0,360,30):
        sx,sy,_=project(radec_xyz(ra,0),rot,W,H,fov)
        if sx and 20<sx<W-50 and 20<sy<H-20: txt(surf,fsm,f"{ra//15}h",sx,sy,(55,85,135))
    for dec in range(-80,81,20):
        sx,sy,_=project(radec_xyz(0,dec),rot,W,H,fov)
        if sx and 20<sx<W-60 and 20<sy<H-20: txt(surf,fsm,f"{'+' if dec>=0 else ''}{dec}°",sx,sy,(55,85,135))

# ─────────────────────────────────────────────────────────────────────────────
#  MILKY WAY BAND
# ─────────────────────────────────────────────────────────────────────────────
def draw_mw(surf,rot,W,H,fov):
    mw=pygame.Surface((W,H),pygame.SRCALPHA); pts=[]
    for ra,dec in MILKY_WAY:
        sx,sy,_=project(radec_xyz(ra,dec),rot,W,H,fov)
        if sx and -300<sx<W+300 and -300<sy<H+300: pts.append((sx,sy))
    if len(pts)>4:
        pygame.draw.lines(mw,(255,255,255,9),False,pts,14)
        pygame.draw.lines(mw,(255,255,255,6),False,pts,28)
    surf.blit(mw,(0,0))

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTELLATIONS
# ─────────────────────────────────────────────────────────────────────────────
def draw_consts(surf,star_data,rot,W,H,fov,show_labels,fsm):
    ls=pygame.Surface((W,H),pygame.SRCALPHA)
    for name,pairs in CONSTELLATIONS.items():
        for a,b in pairs:
            if a not in star_data or b not in star_data: continue
            va,_=star_data[a]; vb,_=star_data[b]
            ax,ay,_=project(va,rot,W,H,fov); bx,by,_=project(vb,rot,W,H,fov)
            if ax and bx: pygame.draw.line(ls,(60,105,165,78),(ax,ay),(bx,by),1)
    surf.blit(ls,(0,0))
    if show_labels:
        for name,(ra_c,dec_c) in CONST_LABELS.items():
            sx,sy,_=project(radec_xyz(ra_c,dec_c),rot,W,H,fov)
            if sx and 0<sx<W and 0<sy<H: txt(surf,fsm,name.upper(),sx,sy,(58,112,182))

# ─────────────────────────────────────────────────────────────────────────────
#  DSOs
# ─────────────────────────────────────────────────────────────────────────────
def draw_dsos(surf,rot,W,H,fov,fsm,mag_lim):
    for name,ra,dec,dt,mag,desc in DSO_CATALOG:
        if mag>mag_lim+2: continue
        sx,sy,_=project(radec_xyz(ra,dec),rot,W,H,fov)
        if not sx or not(5<sx<W-5 and 5<sy<H-5): continue
        sz=max(5,int(13-mag)); draw_dso_icon(surf,sx,sy,dt,sz)
        col=DSO_COLORS.get(dt,(200,200,200)); txt(surf,fsm,name,sx+sz+4,sy-5,col)

# ─────────────────────────────────────────────────────────────────────────────
#  PLANET RENDERING
# ─────────────────────────────────────────────────────────────────────────────
def draw_planets(surf,glow,planet_positions,rot,W,H,fov,sel_planet,fov_deg,fsm,fmd):
    hover_planet=None; best_d=20
    mx0,my0=pygame.mouse.get_pos()
    for name,info in planet_positions.items():
        sx,sy,depth=project(info["xyz"],rot,W,H,fov)
        if not sx or not(0<=sx<W and 0<=sy<H): continue
        col=info["color"]; sz=info["size"]
        # Glow
        for ri in range(sz+8,0,-1):
            a=int(70*(1-ri/(sz+8))**1.5)
            pygame.draw.circle(glow,(*col,a),(sx,sy),ri)
        pygame.draw.circle(surf,col,(sx,sy),sz)
        pygame.draw.circle(surf,(255,255,255),(sx,sy),sz,1)
        # Saturn rings
        if name=="Saturn":
            rs=pygame.Surface((sz*5,sz*2),pygame.SRCALPHA)
            pygame.draw.ellipse(rs,(240,215,150,60),(0,0,sz*5,sz*2),2)
            surf.blit(rs,(sx-sz*2,sy-sz))
        # Selection
        if name==sel_planet:
            pygame.draw.circle(surf,(255,255,255),(sx,sy),sz+8,2)
            pygame.draw.circle(surf,col,(sx,sy),sz+14,1)
        # Label when zoomed in
        if fov_deg<60 or name==sel_planet:
            txt(surf,fmd,name,sx+sz+5,sy-6,col)
            if name==sel_planet:
                dist_str=f"{info['dist']:.2f} AU"
                txt(surf,fsm,dist_str,sx+sz+5,sy+8,(180,200,230))
        # Hover
        d=math.sqrt((mx0-sx)**2+(my0-sy)**2)
        if d<best_d: best_d=d; hover_planet=name
    return hover_planet

# ─────────────────────────────────────────────────────────────────────────────
#  INFO PANEL  (star)
# ─────────────────────────────────────────────────────────────────────────────
def draw_star_info(surf,flg,fmd,fsm,hip,star_data,W,H):
    vec,mag=star_data[hip]
    ra_deg=math.degrees(math.atan2(vec[1],vec[0]))%360
    dec_deg=math.degrees(math.asin(max(-1,min(1,vec[2]))))
    ra_h=int(ra_deg/15); ra_m=int((ra_deg/15-ra_h)*60)
    ra_s=((ra_deg/15-ra_h)*60-ra_m)*60
    bw,bh=285,265; bx,by=W-bw-12,48
    if hip in NAMED_STARS:
        nm,byr,sp,cn=NAMED_STARS[hip]; col=spec_color(sp)
    else:
        nm=f"HIP {hip}"; byr="—"; sp="?"; cn="—"; col=(200,210,230)
    panel(surf,bx,by,bw,bh,border=col,hdr=col)
    txt(surf,flg,nm,bx+10,by+7,col)
    rows=[("Bayer/Flamsteed",byr),("Constellation",cn),("Spectral",sp),
          ("Magnitude",f"{mag:.2f}"),("RA",f"{ra_h:02d}h {ra_m:02d}m {ra_s:04.1f}s"),
          ("Dec",f"{'+' if dec_deg>=0 else ''}{dec_deg:.4f}°"),("HIP ID",str(hip))]
    for i,(k,v) in enumerate(rows):
        ry=by+30+i*28
        txt(surf,fsm,k,bx+10,ry+1,(65,115,175)); txt(surf,fmd,v,bx+155,ry,(210,240,255))
    spec_notes={"O":"Very hot blue giant","B":"Hot blue-white","A":"White/blue-white",
                "F":"Yellow-white","G":"Yellow (Sun-like)","K":"Orange giant","M":"Cool red star",
                "W":"Wolf-Rayet","L":"Brown dwarf"}
    note=spec_notes.get(sp[0] if sp else "","")
    if note: txt(surf,fsm,note,bx+10,by+bh-20,(75,140,95))

# ─────────────────────────────────────────────────────────────────────────────
#  PLANET INFO PANEL
# ─────────────────────────────────────────────────────────────────────────────
def draw_planet_info(surf,flg,fmd,fsm,name,info,W,H):
    bw,bh=285,160; bx,by=W-bw-12,48
    col=info["color"]
    panel(surf,bx,by,bw,bh,border=col,hdr=col)
    txt(surf,flg,name,bx+10,by+7,col)
    ra_deg=info["ra"]; dec_deg=info["dec"]
    ra_h=int(ra_deg/15); ra_m=int((ra_deg/15-ra_h)*60)
    rows=[("Type","Planet"),("RA",f"{ra_h:02d}h {ra_m:02d}m"),
          ("Dec",f"{'+' if dec_deg>=0 else ''}{dec_deg:.2f}°"),
          ("Distance",f"{info['dist']:.3f} AU")]
    for i,(k,v) in enumerate(rows):
        ry=by+30+i*27
        txt(surf,fsm,k,bx+10,ry+1,(65,115,175)); txt(surf,fmd,v,bx+130,ry,(210,240,255))
    txt(surf,fsm,info["desc"],bx+10,by+bh-22,(75,140,95))

# ─────────────────────────────────────────────────────────────────────────────
#  SEARCH OVERLAY
# ─────────────────────────────────────────────────────────────────────────────
class Search:
    def __init__(self,fmd,fsm):
        self.active=False;self.q="";self.results=[];self.cur=0;self.fmd=fmd;self.fsm=fsm
    def open(self): self.active=True;self.q="";self.results=[];self.cur=0
    def close(self): self.active=False
    def update(self):
        q=self.q.lower()
        self.results=[(h,n) for h,n in NAMED_STARS.items() if q in n[0].lower() or q in n[1].lower() or q in n[3].lower()][:12]
        self.cur=max(0,min(self.cur,len(self.results)-1))
    def sel(self): return self.results[self.cur][0] if self.results else None
    def draw(self,surf,W,H):
        if not self.active: return
        ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,155)); surf.blit(ov,(0,0))
        bw,bh=530,min(92+len(self.results)*30,440); bx,by=W//2-bw//2,H//2-bh//2
        panel(surf,bx,by,bw,bh,border=(0,100,200))
        txt(surf,self.fmd,"STAR SEARCH",bx+16,by+9,(80,175,255))
        pygame.draw.rect(surf,(8,16,45),(bx+12,by+32,bw-24,28))
        pygame.draw.rect(surf,(0,105,215),(bx+12,by+32,bw-24,28),1)
        txt(surf,self.fmd,self.q+"▍",bx+18,by+38,(200,230,255))
        for i,(hip,info) in enumerate(self.results):
            ry=by+66+i*30
            if i==self.cur:
                hl=pygame.Surface((bw-24,26),pygame.SRCALPHA); hl.fill((0,55,135,120)); surf.blit(hl,(bx+12,ry-2))
            sc=spec_color(info[2]); pygame.draw.circle(surf,sc,(bx+26,ry+11),5)
            txt(surf,self.fmd,f"{info[0]}  {info[1]}",bx+40,ry+2,sc)
            txt(surf,self.fsm,f"{info[3]}  ·  Spec: {info[2]}  ·  HIP {hip}",bx+40,ry+17,(100,150,200))
        if not self.results and self.q: txt(surf,self.fmd,"No stars found.",bx+20,by+70,(110,90,130))
        txt(surf,self.fsm,"↑↓ Navigate   ENTER Select   ESC Close",bx+16,by+bh-17,(50,80,138))

# ─────────────────────────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────────────────────────
HELP_LINES=[
    ("NAVIGATION",None),("Left-drag","Rotate sky"),("Scroll","Zoom / FOV"),
    ("W/A/S/D","Keyboard rotate"),("R","Reset"),("",""),
    ("OVERLAYS",None),("C","Constellations"),("L","Const labels"),
    ("G","RA/Dec grid"),("M","Milky Way"),("N","Star names"),
    ("B","Spectral colors"),("T","Twinkling"),("F1","Deep sky objects"),("P","Planets"),("",""),
    ("FILTER",None),("1","Stars only"),("2","Planets only"),("3","Both"),("",""),
    ("STARS",None),("+/-","Magnitude limit"),("S","Search"),("TAB","Next named star"),("",""),
    ("OTHER",None),("F3","Screenshot"),("H","Help"),("ESC","Quit"),
]

def draw_hud(surf,fxl,flg,fmd,fsm,W,H,total,visible,fov,yaw,pitch,mag_lim,spectral,twinkle,show_mode,planet_count):
    bg=pygame.Surface((W,38),pygame.SRCALPHA); bg.fill((2,5,18,210)); surf.blit(bg,(0,0))
    txt(surf,fxl,"COSMO",12,3,(0,180,255)); txt(surf,fxl,"LENS",92,3,(220,240,255))
    txt(surf,fsm,"STAR ATLAS  v2",13,27,(38,78,138))
    txt(surf,fmd,datetime.datetime.utcnow().strftime("UTC  %Y-%m-%d  %H:%M:%S"),W//2-115,9,(148,208,255))
    fov_deg=math.degrees(math.atan(fov/500)*2)
    mode_str=["STARS ONLY","PLANETS ONLY","STARS + PLANETS"][show_mode]
    mode_col=[(0,200,255),(80,255,120),(255,200,80)][show_mode]
    txt(surf,fsm,mode_str,W//2-50,26,mode_col)
    txt(surf,fsm,"[H]Help [S]Search [C]Consts [G]Grid [1/2/3]Mode",W-390,9,(38,68,128))
    txt(surf,fsm,"[B]Spectral [T]Twinkle [P]Planets [+/-]Mag [ESC]Quit",W-390,22,(32,58,112))
    # bottom bar
    bg2=pygame.Surface((W,21),pygame.SRCALPHA); bg2.fill((2,5,18,195)); surf.blit(bg2,(0,H-21))
    stats=[f"STARS {visible:,}/{total:,}",f"FOV {fov_deg:.0f}°",f"MAG≤{mag_lim:.1f}",
           f"YAW {math.degrees(yaw):.0f}°",f"PITCH {math.degrees(pitch):.0f}°",
           f"{'SPECTRAL' if spectral else 'MONO'}",f"{'✦TWINKLE' if twinkle else ''}",
           f"{planet_count} PLANETS" if planet_count else ""]
    x=8
    for s in stats:
        if s: x+=txt(surf,fsm,s,x,H-16,(58,98,158))+16

def draw_help_ov(surf,flg,fmd,fsm,W,H):
    bw,bh=440,30+len(HELP_LINES)*17; bx,by=W//2-bw//2,H//2-bh//2
    panel(surf,bx,by,bw,bh,border=(0,100,200))
    txt(surf,flg,"KEYBOARD REFERENCE",bx+14,by+7,(60,155,255))
    for i,(k,v) in enumerate(HELP_LINES):
        ry=by+26+i*17
        if v is None:
            txt(surf,fsm,k,bx+12,ry,(50,92,172))
            pygame.draw.line(surf,(18,48,98),(bx+12,ry+12),(bx+bw-12,ry+12),1)
        elif k: txt(surf,fmd,k,bx+16,ry,(175,212,255)); txt(surf,fmd,v,bx+192,ry,(108,158,218))

def draw_loading(scr,fxl,fmd,fsm,W,H,msg,pct):
    scr.fill((0,0,5))
    txt(scr,fxl,"COSMO",W//2-88,H//2-62,(0,180,255)); txt(scr,fxl,"LENS",W//2+2,H//2-62,(220,240,255))
    txt(scr,fmd,"STAR ATLAS  v2",W//2-80,H//2-22,(38,78,138))
    bw,bh=360,6; bx,by=W//2-bw//2,H//2+20
    pygame.draw.rect(scr,(14,28,58),(bx,by,bw,bh)); pygame.draw.rect(scr,(0,115,215),(bx,by,int(bw*pct),bh))
    txt(scr,fsm,msg,W//2-120,H//2+34,(58,98,158)); pygame.display.flip()

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    W,H=1280,780
    try:
        screen=pygame.display.set_mode((W,H),pygame.RESIZABLE|pygame.HWSURFACE|pygame.DOUBLEBUF)
    except:
        screen=pygame.display.set_mode((W,H),pygame.RESIZABLE)
    pygame.display.set_caption("CosmoLens — Star Atlas v2")
    clock=pygame.time.Clock()
    fxl=pygame.font.SysFont("Courier New",22,bold=True)
    flg=pygame.font.SysFont("Courier New",15,bold=True)
    fmd=pygame.font.SysFont("Courier New",13)
    fsm=pygame.font.SysFont("Courier New",11)

    draw_loading(screen,fxl,fmd,fsm,W,H,"Loading Hipparcos catalog…",0.1)
    with skyload.open(hipparcos.URL) as f:
        df=hipparcos.load_dataframe(f)
    draw_loading(screen,fxl,fmd,fsm,W,H,"Processing star data…",0.5)

    star_data={}  # hip → (xyz, mag)
    for hip,row in df.iterrows():
        ra=row.get("ra_degrees",float("nan")); dec=row.get("dec_degrees",float("nan"))
        mag=row.get("magnitude",float("nan"))
        if any(math.isnan(v) for v in [ra,dec,mag]): continue
        if mag>7.2: continue
        star_data[hip]=(radec_xyz(ra,dec),mag)

    draw_loading(screen,fxl,fmd,fsm,W,H,f"Loaded {len(star_data):,} stars. Starting planets…",0.85)

    planet_mgr=PlanetManager(); planet_mgr.load()
    planet_update_t=0.0
    planet_positions={}

    draw_loading(screen,fxl,fmd,fsm,W,H,"Ready.",1.0)
    pygame.time.wait(300)

    # State
    yaw,pitch=1.5,0.3; fov=600.0; mag_limit=5.5
    dragging=False; drag_start=(0,0); drag_yaw0=yaw; drag_pit0=pitch
    show_consts=True; show_labels=True; show_grid=False; show_milky=True
    show_names=True; show_hud=True; show_help=False; show_dso=True
    show_planets=True; spectral=True; twinkle=True
    show_mode=2  # 0=stars only, 1=planets only, 2=both
    sel_hip=None; sel_planet=None; tab_i=0
    search=Search(fmd,fsm)
    glow_surf=pygame.Surface((W,H),pygame.SRCALPHA)
    twinkle_t=0.0; hover_planet=None

    named_hips=[h for h in NAMED_STARS if h in star_data]

    # Pre-build background starfield texture for performance
    bg_surf=pygame.Surface((W,H))
    bg_surf.fill((0,0,5))
    rng=random.Random(1337)
    for _ in range(8000):
        bx2=rng.randint(0,W-1); by2=rng.randint(0,H-1)
        b=rng.randint(5,45); sz=rng.choices([0,1,2],weights=[75,22,3])[0]
        if sz==0: bg_surf.set_at((bx2,by2),(b,b,min(50,b+5)))
        else: pygame.draw.circle(bg_surf,(b,b,min(50,b+5)),(bx2,by2),sz)
    # Subtle nebula patches
    for _ in range(6):
        nbx=rng.randint(50,W-50); nby=rng.randint(50,H-50)
        nr=rng.randint(80,180); nc=(rng.randint(5,25),rng.randint(5,25),rng.randint(15,55))
        ns=pygame.Surface((nr*2,nr*2),pygame.SRCALPHA)
        for ri in range(nr,0,-4):
            a=int(18*(1-ri/nr)**2); pygame.draw.circle(ns,(nc[0],nc[1],nc[2],a),(nr,nr),ri)
        bg_surf.blit(ns,(nbx-nr,nby-nr))

    running=True
    while running:
        dt=min(clock.tick(60)/1000.0,0.05); twinkle_t+=dt*3.0
        rot=rot_matrix(yaw,pitch)

        # Update planets every 10s
        planet_update_t+=dt
        if planet_update_t>10.0:
            planet_update_t=0.0
            planet_mgr.update(datetime.datetime.utcnow())
            planet_positions=planet_mgr.get()
            if not planet_positions: planet_positions=planet_mgr.get()
        if not planet_positions:
            planet_mgr.update(datetime.datetime.utcnow())
            planet_positions=planet_mgr.get()

        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False
            elif event.type==pygame.VIDEORESIZE:
                W,H=event.w,event.h
                try: screen=pygame.display.set_mode((W,H),pygame.RESIZABLE|pygame.HWSURFACE|pygame.DOUBLEBUF)
                except: screen=pygame.display.set_mode((W,H),pygame.RESIZABLE)
                glow_surf=pygame.Surface((W,H),pygame.SRCALPHA)
            elif event.type==pygame.MOUSEWHEEL:
                fov=max(50,min(1400,fov+event.y*35))
            elif event.type==pygame.MOUSEBUTTONDOWN:
                if not search.active:
                    if event.button==1:
                        dragging=True; drag_start=event.pos; drag_yaw0=yaw; drag_pit0=pitch
                    elif event.button==3:
                        sel_hip=None; sel_planet=None
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button==1 and dragging:
                    dragging=False; mx,my=event.pos
                    if abs(mx-drag_start[0])+abs(my-drag_start[1])<5:
                        # Click — try stars then planets
                        best=None; best_d=15
                        if show_mode!=1:  # not planets-only
                            for hip,(v,mag) in star_data.items():
                                if mag>mag_limit: continue
                                sx,sy,_=project(v,rot,W,H,fov)
                                if not sx: continue
                                d=math.sqrt((mx-sx)**2+(my-sy)**2)
                                if d<best_d: best_d=d; best=("star",hip)
                        if show_mode!=0:  # not stars-only
                            for name,info in planet_positions.items():
                                sx,sy,_=project(info["xyz"],rot,W,H,fov)
                                if not sx: continue
                                d=math.sqrt((mx-sx)**2+(my-sy)**2)
                                if d<best_d+5: best_d=d; best=("planet",name)
                        if best:
                            if best[0]=="star": sel_hip=best[1]; sel_planet=None
                            else: sel_planet=best[1]; sel_hip=None
                        else: sel_hip=None; sel_planet=None
            elif event.type==pygame.MOUSEMOTION:
                if dragging:
                    dx=event.pos[0]-drag_start[0]; dy=event.pos[1]-drag_start[1]
                    sens=0.003*(600/fov)
                    yaw=drag_yaw0+dx*sens; pitch=max(-math.pi/2,min(math.pi/2,drag_pit0-dy*sens))
            elif event.type==pygame.KEYDOWN:
                if search.active:
                    if event.key==pygame.K_ESCAPE:    search.close()
                    elif event.key==pygame.K_RETURN:
                        hip=search.sel()
                        if hip:
                            sel_hip=hip; sel_planet=None; search.close()
                            v=star_data[hip][0]; yaw=math.atan2(v[1],v[0]); pitch=math.asin(max(-1,min(1,v[2])))
                        else: search.close()
                    elif event.key==pygame.K_UP:    search.cur=max(0,search.cur-1)
                    elif event.key==pygame.K_DOWN:  search.cur=min(len(search.results)-1,search.cur+1)
                    elif event.key==pygame.K_BACKSPACE: search.q=search.q[:-1]; search.update()
                    elif event.unicode and event.unicode.isprintable():
                        search.q+=event.unicode; search.update()
                else:
                    k=event.key
                    if k==pygame.K_ESCAPE:
                        if show_help: show_help=False
                        elif sel_hip or sel_planet: sel_hip=None; sel_planet=None
                        else: running=False
                    elif k==pygame.K_r:   yaw=1.5;pitch=0.3;fov=600.0
                    elif k==pygame.K_c:   show_consts=not show_consts
                    elif k==pygame.K_l:   show_labels=not show_labels
                    elif k==pygame.K_g:   show_grid=not show_grid
                    elif k==pygame.K_m:   show_milky=not show_milky
                    elif k==pygame.K_n:   show_names=not show_names
                    elif k==pygame.K_b:   spectral=not spectral
                    elif k==pygame.K_t:   twinkle=not twinkle
                    elif k==pygame.K_h:   show_help=not show_help
                    elif k==pygame.K_p:   show_planets=not show_planets
                    elif k==pygame.K_s:   search.open(); search.update()
                    elif k==pygame.K_F1:  show_dso=not show_dso
                    elif k==pygame.K_F3:
                        fn=f"cosmo_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                        pygame.image.save(screen,fn)
                    elif k in(pygame.K_PLUS,pygame.K_EQUALS,pygame.K_KP_PLUS): mag_limit=min(8.0,mag_limit+0.25)
                    elif k in(pygame.K_MINUS,pygame.K_KP_MINUS): mag_limit=max(0.5,mag_limit-0.25)
                    elif k==pygame.K_TAB:
                        if named_hips:
                            tab_i=(tab_i+1)%len(named_hips); sel_hip=named_hips[tab_i]; sel_planet=None
                            v=star_data[sel_hip][0]; yaw=math.atan2(v[1],v[0]); pitch=math.asin(max(-1,min(1,v[2])))
                    elif k==pygame.K_1:   show_mode=0
                    elif k==pygame.K_2:   show_mode=1
                    elif k==pygame.K_3:   show_mode=2

        if not search.active:
            keys=pygame.key.get_pressed(); spd=0.012*(600/fov)
            if keys[pygame.K_a]: yaw-=spd
            if keys[pygame.K_d]: yaw+=spd
            if keys[pygame.K_w]: pitch=min(math.pi/2,pitch+spd)
            if keys[pygame.K_s]: pitch=max(-math.pi/2,pitch-spd)

        # ── RENDER ───────────────────────────────────────────────────────────
        # Background
        screen.blit(bg_surf,(0,0))
        # Subtle gradient on top of starfield
        for y in range(0,H,2):
            t=y/H; c=(int(3+2*t),int(2+3*t),int(8+10*t))
            pygame.draw.line(screen,c,(0,y),(W,y)); pygame.draw.line(screen,c,(0,y+1),(W,y+1))

        if show_milky: draw_mw(screen,rot,W,H,fov)
        if show_grid:  draw_grid(screen,rot,W,H,fov,fsm)
        if show_consts and show_mode!=1: draw_consts(screen,star_data,rot,W,H,fov,show_labels,fsm)
        if show_dso and show_mode!=1:   draw_dsos(screen,rot,W,H,fov,fsm,mag_limit)

        glow_surf.fill((0,0,0,0))
        visible_count=0
        star_screen={}
        hover_hip=None; best_hd=15
        mx0,my0=pygame.mouse.get_pos()
        fov_deg=math.degrees(math.atan(fov/500)*2)

        # ── STARS ────────────────────────────────────────────────────────────
        if show_mode!=1:  # not planets-only
            for hip,(v,mag) in star_data.items():
                if mag>mag_limit: continue
                sx,sy,depth=project(v,rot,W,H,fov)
                if not sx or not(0<=sx<W and 0<=sy<H): continue
                visible_count+=1
                star_screen[hip]=(sx,sy)
                # Twinkle
                tw=1.0
                if twinkle and mag>1.5: tw=0.85+0.15*math.sin(twinkle_t*1.3+(hip%97)*0.7)
                # Color
                if spectral and hip in NAMED_STARS:
                    col=spec_color(NAMED_STARS[hip][2])
                else:
                    br=int(max(80,min(255,(255-mag*28)*tw))); col=(br,br,min(255,br+12))
                if twinkle: col=tuple(int(c*tw) for c in col)
                # Size
                if mag<-0.5: sz=6
                elif mag<0.5: sz=5
                elif mag<1.5: sz=4
                elif mag<2.5: sz=3
                elif mag<3.5: sz=2
                else: sz=1
                is_sel=(hip==sel_hip)
                # Glow for bright stars
                if mag<2.5:
                    for ri in range(sz+5,0,-1):
                        a=int(65*((1-ri/(sz+5))**2)*tw)
                        pygame.draw.circle(glow_surf,(*col[:3],a),(sx,sy),ri)
                pygame.draw.circle(screen,col,(sx,sy),sz)
                if is_sel:
                    pygame.draw.circle(screen,(255,200,100),(sx,sy),sz+8,2)
                    pygame.draw.circle(screen,(255,255,255),(sx,sy),sz+15,1)
                d=math.sqrt((mx0-sx)**2+(my0-sy)**2)
                if d<best_hd: best_hd=d; hover_hip=hip
                if show_names and hip in NAMED_STARS and mag<2.0:
                    c=spec_color(NAMED_STARS[hip][2]) if spectral else (175,208,255)
                    txt(screen,fsm,NAMED_STARS[hip][0],sx+sz+4,sy-6,c)

        # ── PLANETS ──────────────────────────────────────────────────────────
        if show_mode!=0 and show_planets:
            hover_planet=draw_planets(screen,glow_surf,planet_positions,rot,W,H,fov,sel_planet,fov_deg,fsm,fmd)

        screen.blit(glow_surf,(0,0))

        # ── HOVER TOOLTIPS ───────────────────────────────────────────────────
        if hover_hip and hover_hip!=sel_hip and show_mode!=1:
            sx,sy=star_screen[hover_hip]; _,mag=star_data[hover_hip]
            if hover_hip in NAMED_STARS:
                info=NAMED_STARS[hover_hip]; lbl=f"{info[0]}  {info[1]}  mag {mag:.2f}  {info[2]}"
                lcol=spec_color(info[2]) if spectral else (210,235,255)
            else: lbl=f"HIP {hover_hip}  mag {mag:.2f}"; lcol=(200,220,250)
            tw2=fmd.size(lbl)[0]+14; tx=min(sx+14,W-tw2-4); ty=max(sy-22,4)
            panel(screen,tx,ty,tw2,28,border=(0,80,180))
            txt(screen,fmd,lbl,tx+7,ty+4,lcol)

        if hover_planet and hover_planet!=sel_planet and show_mode!=0 and show_planets:
            info=planet_positions.get(hover_planet,{})
            if info:
                col=info["color"]; lbl=f"{hover_planet}  ·  {info['dist']:.2f} AU"
                tw2=fmd.size(lbl)[0]+14; tx=min(mx0+14,W-tw2-4); ty=max(my0-22,4)
                panel(screen,tx,ty,tw2,28,border=col)
                txt(screen,fmd,lbl,tx+7,ty+4,col)

        # Info panels
        if sel_hip and sel_hip in star_data and show_mode!=1:
            draw_star_info(screen,flg,fmd,fsm,sel_hip,star_data,W,H)
        if sel_planet and sel_planet in planet_positions and show_mode!=0:
            draw_planet_info(screen,flg,fmd,fsm,sel_planet,planet_positions[sel_planet],W,H)

        if show_hud:
            draw_hud(screen,fxl,flg,fmd,fsm,W,H,len(star_data),visible_count,fov,yaw,pitch,
                     mag_limit,spectral,twinkle,show_mode,len(planet_positions) if show_mode!=0 else 0)

        if show_help: draw_help_ov(screen,flg,fmd,fsm,W,H)
        search.draw(screen,W,H)

        # Planet status indicator
        if not planet_mgr.ready:
            txt(screen,fsm,f"⚙ {planet_mgr.status}",10,H-38,(80,120,180))

        # FOV arc
        pygame.draw.arc(screen,(28,55,115),(W-48,H-48,34,34),0,math.radians(min(360,fov_deg*3.8)),2)

        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__=="__main__":
    print(__doc__); main()