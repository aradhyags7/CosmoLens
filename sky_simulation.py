"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           C O S M O L E N S  —  D E E P  S K Y  A T L A S  v 5            ║
║                    "You have downloaded the Universe"                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  DRAG / WASD    Rotate sky          SCROLL       Zoom                       ║
║  R              Reset view          H            Help                       ║
║  C              Constellations      L            Labels                     ║
║  G              RA/Dec grid         M            Milky Way                  ║
║  N              Star names          B            Spectral colors            ║
║  T              Twinkling           F1           DSOs + Black Holes         ║
║  P              Meteor shower       A/E          Aurora toggle              ║
║  1 Stars  2 Planets  3 Both         +/-          Magnitude limit            ║
║  S              Star search         TAB          Cycle named stars          ║
║  F3             Screenshot          ESC          Deselect / Quit            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import pygame, numpy as np, sys, math, datetime, random, threading, time, os

for p in ["pygame","skyfield","numpy","pandas"]:
    import subprocess
    subprocess.run([sys.executable,"-m","pip","install","-q",p],check=False)

from skyfield.data import hipparcos
from skyfield.api  import load as skyload

# ═══════════════════════════════════════════════════════════════════════════════
#  STAR CATALOG  (HIP → name, bayer, spectral, constellation, distance_ly)
# ═══════════════════════════════════════════════════════════════════════════════
NAMED = {
    32349:("Sirius","α CMa","A1V","Canis Major",8.6),
    33579:("Adhara","ε CMa","B2II","Canis Major",430),
    34444:("Wezen","δ CMa","F8Ia","Canis Major",1600),
    35904:("Aludra","η CMa","B5Ia","Canis Major",2000),
    30324:("Mirzam","β CMa","B1II","Canis Major",500),
    24436:("Rigel","β Ori","B8Ia","Orion",860),
    27989:("Betelgeuse","α Ori","M2Ia","Orion",700),
    26727:("Bellatrix","γ Ori","B2III","Orion",250),
    25336:("Saiph","κ Ori","B0.5Ia","Orion",720),
    26311:("Alnitak","ζ Ori","O9.5Ib","Orion",800),
    26207:("Alnilam","ε Ori","B0Ia","Orion",1350),
    25930:("Mintaka","δ Ori","O9.5II","Orion",900),
    25428:("Meissa","λ Ori","O8III","Orion",1100),
    54061:("Dubhe","α UMa","K0IIIa","Ursa Major",124),
    53910:("Merak","β UMa","A1V","Ursa Major",79),
    58001:("Phecda","γ UMa","A0Ve","Ursa Major",84),
    59774:("Megrez","δ UMa","A3V","Ursa Major",81),
    62956:("Alioth","ε UMa","A0p","Ursa Major",81),
    65378:("Mizar","ζ UMa","A1V","Ursa Major",78),
    67301:("Alkaid","η UMa","B3V","Ursa Major",100),
    11767:("Polaris","α UMi","F7Ib","Ursa Minor",433),
    85822:("Kochab","β UMi","K4III","Ursa Minor",126),
    79822:("Pherkad","γ UMi","A3III","Ursa Minor",487),
    91262:("Vega","α Lyr","A0V","Lyra",25),
    93194:("Sheliak","β Lyr","B8II","Lyra",882),
    92420:("Sulafat","γ Lyr","B9III","Lyra",634),
    102098:("Deneb","α Cyg","A2Ia","Cygnus",2600),
    95947:("Sadr","γ Cyg","F8Ib","Cygnus",1800),
    100453:("Gienah","ε Cyg","K0III","Cygnus",72),
    97165:("Delta Cyg","δ Cyg","B9.5III","Cygnus",165),
    94779:("Albireo","β Cyg","K3II","Cygnus",430),
    97649:("Altair","α Aql","A7V","Aquila",17),
    98036:("Tarazed","γ Aql","K3II","Aquila",461),
    96229:("Alshain","β Aql","G8IV","Aquila",45),
    80763:("Antares","α Sco","M1.5Ib","Scorpius",550),
    82396:("Tau Sco","τ Sco","B0V","Scorpius",470),
    84143:("Shaula","λ Sco","B1.5IV","Scorpius",700),
    85927:("Lesath","υ Sco","B2IV","Scorpius",580),
    78401:("Dschubba","δ Sco","B0.3IV","Scorpius",400),
    76600:("Graffias","β Sco","B1V","Scorpius",530),
    85696:("Kappa Sco","κ Sco","B1.5III","Scorpius",480),
    49669:("Regulus","α Leo","B8IVn","Leo",79),
    57632:("Denebola","β Leo","A3V","Leo",36),
    50583:("Algieba","γ Leo","K0III","Leo",130),
    54872:("Zosma","δ Leo","A4V","Leo",58),
    47908:("Eta Leo","η Leo","A0Ib","Leo",2100),
    46390:("Al Jabbah","ζ Leo","F0III","Leo",260),
    37826:("Castor","α Gem","A1V","Gemini",52),
    45941:("Pollux","β Gem","K0IIIb","Gemini",34),
    36850:("Tejat","μ Gem","M3III","Gemini",230),
    35550:("Mebsuda","ε Gem","G8Ib","Gemini",900),
    44816:("Wasat","δ Gem","F0IV","Gemini",59),
    40526:("Alzirr","ξ Gem","F5IV","Gemini",58),
    21421:("Aldebaran","α Tau","K5III","Taurus",65),
    20205:("Alnath","β Tau","B7III","Taurus",134),
    20889:("Zeta Tau","ζ Tau","B2IVe","Taurus",440),
    27366:("Capella","α Aur","G8III","Auriga",43),
    28360:("Menkalinan","β Aur","A2IV","Auriga",82),
    15863:("Mirfak","α Per","F5Ib","Perseus",592),
    14576:("Algol","β Per","B8V","Perseus",90),
    14632:("Atik","ο Per","B1III","Perseus",1000),
    17358:("Miram","η Per","K3Ib","Perseus",1300),
    18532:("Menkib","ξ Per","O7.5III","Perseus",1200),
    69673:("Arcturus","α Boo","K1.5III","Boötes",37),
    72105:("Muphrid","η Boo","G0IV","Boötes",37),
    67927:("Seginus","γ Boo","A7III","Boötes",86),
    71075:("Nekkar","β Boo","G8IIIa","Boötes",219),
    71053:("Izar","ε Boo","K0II","Boötes",203),
    65474:("Spica","α Vir","B1V","Virgo",250),
    63608:("Zavijava","β Vir","F9V","Virgo",36),
    61941:("Porrima","γ Vir","F0V","Virgo",38),
    57380:("Heze","ζ Vir","A3V","Virgo",74),
    66249:("Zaniah","η Vir","A2V","Virgo",265),
    69427:("Vindemiatrix","ε Vir","G8IIIab","Virgo",109),
    37279:("Procyon","α CMi","F5IV","Canis Minor",11),
    36188:("Gomeisa","β CMi","B8Ve","Canis Minor",170),
    71683:("Rigil Kent.","α Cen","G2V","Centaurus",4),
    68702:("Hadar","β Cen","B1III","Centaurus",390),
    68933:("Menkent","θ Cen","K0III","Centaurus",61),
    60718:("Acrux","α Cru","B0.5IV","Crux",320),
    62434:("Mimosa","β Cru","B0.5III","Crux",280),
    59747:("Gacrux","γ Cru","M3.5III","Crux",88),
    63003:("Delta Cru","δ Cru","B2IV","Crux",345),
    30438:("Canopus","α Car","F0Ib","Carina",310),
    45080:("Avior","ε Car","K3III","Carina",630),
    50371:("Aspidiske","ι Car","A8Ib","Carina",690),
    7588:("Achernar","α Eri","B6Vep","Eridanus",139),
    17651:("Cursa","β Eri","A3IIIvar","Eridanus",89),
    15510:("Zaurak","γ Eri","M1IIIab","Eridanus",220),
    3179:("Schedar","α Cas","K0IIIa","Cassiopeia",228),
    4427:("Caph","β Cas","F2III","Cassiopeia",54),
    6686:("Gamma Cas","γ Cas","B0.5IVpe","Cassiopeia",610),
    8886:("Ruchbah","δ Cas","A5III","Cassiopeia",99),
    11569:("Segin","ε Cas","B3IV","Cassiopeia",440),
    677:("Alpheratz","α And","B9p","Andromeda",97),
    5447:("Mirach","β And","M0III","Andromeda",197),
    9640:("Almach","γ And","K3II","Andromeda",355),
    109176:("Markab","α Peg","B9III","Pegasus",140),
    113881:("Scheat","β Peg","M2.5II","Pegasus",196),
    3821:("Algenib","γ Peg","B2IV","Pegasus",335),
    112158:("Enif","ε Peg","K2Ib","Pegasus",672),
    113368:("Fomalhaut","α PsA","A3V","Piscis Austrinus",25),
    90185:("Kaus Austr.","ε Sgr","A0III","Sagittarius",145),
    89931:("Nunki","σ Sgr","B2.5V","Sagittarius",228),
    92855:("Ascella","ζ Sgr","A2III","Sagittarius",89),
    88635:("Kaus Med.","δ Sgr","K3III","Sagittarius",305),
    90496:("Kaus Bor.","λ Sgr","K1IIIb","Sagittarius",77),
    76267:("Alphecca","α CrB","A0V","Corona Borealis",75),
    80816:("Kornephoros","β Her","G8III","Hercules",139),
    84345:("Sarin","δ Her","A3IV","Hercules",78),
    81693:("Zeta Her","ζ Her","F9IV","Hercules",35),
    84970:("Rasalhague","α Oph","A5III","Ophiuchus",47),
    86742:("Cebalrai","β Oph","K2III","Ophiuchus",82),
    83000:("Yed Prior","δ Oph","M1III","Ophiuchus",172),
    9884:("Hamal","α Ari","K2IIIb","Aries",66),
    8903:("Sheratan","β Ari","A5V","Aries",60),
    87585:("Eltanin","γ Dra","K5III","Draco",148),
    85670:("Rastaban","β Dra","G2Ib","Draco",361),
    109074:("Sadalsuud","β Aqr","G0Ib","Aquarius",610),
    106278:("Sadalmelik","α Aqr","G2Ib","Aquarius",523),
    99240:("Peacock","α Pav","B2IV","Pavo",179),
    109268:("Alnair","α Gru","B7IV","Grus",101),
    39953:("Gamma Vel","γ Vel","WC8","Vela",840),
    38170:("Naos","ζ Pup","O4I","Puppis",1400),
    3419:("Ankaa","α Phe","K0.5IIIb","Phoenix",77),
    73273:("Alpha Lup","α Lup","B1.5III","Lupus",548),
    82514:("Alpha Ara","α Ara","B2Vne","Ara",242),
}

# Spectral color palette (physics-accurate blackbody approximation)
SPEC_C = {
    "O":(160,180,255),"B":(185,205,255),"A":(255,255,255),
    "F":(255,252,210),"G":(255,240,150),"K":(255,195,85),
    "M":(255,100,40),"W":(200,230,255),"L":(190,90,40),"?":(210,220,235),
}
def spcol(s): return SPEC_C.get((s or "?")[0].upper(), SPEC_C["?"])

SPEC_NOTE = {
    "O":"Ultra-hot blue giant  ·  >30,000 K",
    "B":"Hot blue-white  ·  10,000–30,000 K",
    "A":"White  ·  7,500–10,000 K",
    "F":"Yellow-white  ·  6,000–7,500 K",
    "G":"Yellow (Sun-like)  ·  5,200–6,000 K",
    "K":"Orange giant  ·  3,700–5,200 K",
    "M":"Cool red star  ·  <3,700 K",
    "W":"Wolf-Rayet  ·  stellar wind",
    "L":"Brown dwarf  ·  <2,200 K",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTELLATIONS
# ═══════════════════════════════════════════════════════════════════════════════
CONSTS = {
    "Orion":[(27989,26727),(26727,25930),(25930,26207),(26207,26311),(26311,24436),
             (24436,25930),(27989,25336),(25336,26311),(26727,25428)],
    "Ursa Major":[(54061,53910),(53910,58001),(58001,59774),(59774,62956),(62956,65378),(65378,67301)],
    "Ursa Minor":[(11767,85822),(85822,79822)],
    "Lyra":[(91262,92420),(92420,93194),(93194,91262)],
    "Cygnus":[(102098,95947),(95947,100453),(100453,97165),(97165,94779),(100453,102098)],
    "Aquila":[(97649,98036),(97649,96229)],
    "Scorpius":[(76600,78401),(78401,80763),(80763,82396),(82396,84143),(84143,85927),(85927,85696)],
    "Leo":[(49669,50583),(50583,47908),(49669,57632),(57632,54872),(50583,46390)],
    "Gemini":[(37826,44816),(44816,45941),(37826,36850),(36850,35550),(44816,40526)],
    "Taurus":[(21421,20889),(20889,20205),(21421,25428)],
    "Auriga":[(27366,28360)],
    "Cassiopeia":[(3179,4427),(4427,6686),(6686,8886),(8886,11569)],
    "Perseus":[(15863,14576),(15863,14632),(14632,17358),(17358,18532)],
    "Boötes":[(69673,72105),(69673,67927),(67927,71075),(69673,71053),(71053,72105)],
    "Virgo":[(65474,63608),(63608,61941),(61941,57380),(65474,66249),(66249,69427)],
    "Andromeda":[(677,5447),(5447,9640)],
    "Pegasus":[(109176,113881),(113881,677),(677,3821),(3821,109176),(109176,112158)],
    "Sagittarius":[(88635,90185),(90185,90496),(88635,89931),(89931,92855),(92855,90185)],
    "Canis Major":[(32349,30324),(32349,33579),(33579,34444),(34444,35904)],
    "Canis Minor":[(37279,36188)],
    "Crux":[(60718,63003),(62434,59747)],
    "Centaurus":[(71683,68702),(68702,68933)],
    "Carina":[(30438,45080),(45080,50371)],
    "Eridanus":[(7588,17651),(17651,15510)],
    "Hercules":[(80816,84345),(84345,81693),(81693,80816)],
    "Ophiuchus":[(84970,86742),(86742,83000),(83000,84970)],
    "Aquarius":[(106278,109074)],
    "Aries":[(9884,8903)],
    "Draco":[(87585,85670)],
}
CONSTS = {k:[(a,b) for a,b in v if a!=b] for k,v in CONSTS.items()}

CLABELS = {
    "Orion":(84.5,2.0),"Ursa Major":(168.0,57.0),"Ursa Minor":(230.0,73.0),
    "Lyra":(282.0,37.0),"Cygnus":(310.0,42.0),"Scorpius":(250.0,-28.0),
    "Leo":(165.0,16.0),"Gemini":(113.0,22.0),"Taurus":(67.0,16.0),
    "Aquila":(295.0,5.0),"Cassiopeia":(14.0,61.0),"Perseus":(48.0,46.0),
    "Boötes":(215.0,32.0),"Virgo":(201.0,1.0),"Andromeda":(20.0,38.0),
    "Pegasus":(340.0,20.0),"Sagittarius":(286.0,-27.0),"Canis Major":(103.0,-22.0),
    "Crux":(186.0,-60.0),"Centaurus":(210.0,-47.0),"Carina":(138.0,-60.0),
    "Eridanus":(55.0,-33.0),"Auriga":(78.0,42.0),"Hercules":(258.0,27.0),
    "Ophiuchus":(257.0,-4.0),"Aquarius":(335.0,-11.0),"Draco":(270.0,65.0),
    "Aries":(31.0,22.0),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  DSO CATALOG — extended
# ═══════════════════════════════════════════════════════════════════════════════
DSOS = [
    ("M1 Crab Nebula",     83.82, 22.01,"SNR",8.4,"Supernova remnant · Taurus · 6,500 ly"),
    ("M8 Lagoon",         270.92,-24.38,"NEB",5.8,"Emission nebula · Sagittarius · 4,100 ly"),
    ("M13 Hercules GC",   250.42, 36.46,"GC", 5.8,"Great Globular · 22,200 ly"),
    ("M20 Trifid",        270.62,-23.03,"NEB",8.5,"Emission+Reflection · 5,200 ly"),
    ("M22",               279.10,-23.90,"GC", 5.1,"Sagittarius globular · 10,600 ly"),
    ("M27 Dumbbell",      299.90, 22.72,"PN", 7.5,"Planetary nebula · Vulpecula · 1,360 ly"),
    ("M31 Andromeda",      10.68, 41.27,"GAL",3.4,"Nearest spiral · 2.537M ly"),
    ("M33 Triangulum",     23.46, 30.66,"GAL",5.7,"Local Group spiral · 2.73M ly"),
    ("M42 Orion Neb.",     83.82, -5.39,"NEB",4.0,"Giant star-forming · 1,344 ly"),
    ("M43 De Mairan",      83.88, -5.27,"NEB",9.0,"Comma-shaped nebula · Orion"),
    ("M44 Beehive",       130.10, 19.67,"OC", 3.1,"Open cluster · Cancer · 520 ly"),
    ("M45 Pleiades",       56.75, 24.12,"OC", 1.2,"Seven Sisters · 444 ly"),
    ("M51 Whirlpool",     202.47, 47.20,"GAL",8.4,"Interacting spiral · 31M ly"),
    ("M57 Ring Neb.",     283.40, 33.03,"PN", 8.8,"Planetary nebula · Lyra · 2,300 ly"),
    ("M64 Black Eye",     194.18, 21.69,"GAL",8.5,"Black Eye Galaxy · 24M ly"),
    ("M78",                86.68,  0.08,"NEB",8.3,"Reflection nebula · Orion"),
    ("M81 Bode's Gal.",   148.89, 69.07,"GAL",6.9,"Bright spiral · 12M ly"),
    ("M82 Cigar",         148.97, 69.68,"GAL",8.4,"Starburst irregular · 12M ly"),
    ("M87 Virgo A",       187.70, 12.39,"GAL",8.6,"Giant elliptical · BH · 53M ly"),
    ("M92 GC",            259.28, 43.14,"GC", 6.4,"Hercules globular · 26,700 ly"),
    ("M97 Owl Neb.",      168.70, 55.02,"PN", 9.9,"Planetary nebula · Ursa Major"),
    ("M101 Pinwheel",     210.80, 54.35,"GAL",7.9,"Face-on spiral · 21M ly"),
    ("M104 Sombrero",     189.99,-11.62,"GAL",8.0,"Edge-on spiral · 31M ly"),
    ("M106",              184.74, 47.30,"GAL",8.4,"Seyfert galaxy · 22M ly"),
    ("NGC 869 h Per",      34.75, 57.13,"OC", 4.3,"Perseus double cluster · 7,600 ly"),
    ("NGC 884 χ Per",      35.60, 57.13,"OC", 4.4,"Perseus double cluster · 7,600 ly"),
    ("NGC 891",            35.63, 42.35,"GAL",9.9,"Edge-on spiral · 27M ly"),
    ("NGC 2244",           97.98,  4.97,"OC", 4.8,"Rosette open cluster · 5,000 ly"),
    ("NGC 3372 Eta Car",  160.00,-59.68,"NEB",3.0,"Eta Carinae nebula · 7,500 ly"),
    ("NGC 5128 Cen A",    201.37,-43.02,"GAL",6.8,"Radio galaxy · BH · 13M ly"),
    ("NGC 6992 Veil",     312.73, 31.73,"SNR",7.0,"Cygnus Loop · 2,400 ly"),
    ("NGC 7293 Helix",    337.41,-20.83,"PN", 7.3,"Eye of God · 655 ly"),
    ("ω Centauri",        201.70,-47.48,"GC", 3.9,"Largest globular · 17,090 ly"),
    ("47 Tucanae",         24.04,-72.08,"GC", 4.0,"Second brightest · 14,800 ly"),
    ("NGC 4565 Needle",   189.09, 25.99,"GAL",9.6,"Edge-on needle galaxy"),
    ("Orion Molecular",    83.80, -5.90,"NEB",2.0,"Vast star-forming cloud"),
    ("Barnard 68",        259.77,-23.84,"NEB",10.0,"Dark nebula · molecular cloud"),
]
DSOCOL={"GAL":(255,172,80),"GC":(160,255,180),"OC":(255,255,130),
        "NEB":(100,190,255),"SNR":(255,100,100),"PN":(120,255,235)}

# ═══════════════════════════════════════════════════════════════════════════════
#  BLACK HOLES — expanded
# ═══════════════════════════════════════════════════════════════════════════════
BH_LIST = [
    ("Sgr A*",        266.40,-29.01,"SMBH",   4.1e6,   26000,  "Milky Way centre  ·  4.1M M☉"),
    ("M87*",          187.70, 12.39,"SMBH",   6.5e9, 55.0e6,   "First EHT image  ·  6.5B M☉"),
    ("Cygnus X-1",    299.59, 35.20,"Stellar",  21,     6070,   "First confirmed BH  ·  21 M☉"),
    ("V404 Cygni",    306.01, 33.87,"Stellar",   9,     7800,   "Binary system  ·  9 M☉"),
    ("GRS 1915+105",  288.80, 10.95,"Stellar",  12,    36000,   "Microquasar  ·  12 M☉"),
    ("GRO J1655-40",  253.50,-39.85,"Stellar",   7,     9000,   "Microquasar  ·  7 M☉"),
    ("XTE J1118+480", 169.56, 48.04,"Stellar",   7,     6200,   "Soft X-ray transient  ·  7 M☉"),
    ("NGC 1277 BH",    50.07, 41.58,"SMBH",  17e9, 240.0e6,    "Hypercompact  ·  17B M☉"),
    ("NGC 4889 BH",   195.03, 27.98,"SMBH",  21e9, 308.0e6,    "Coma cluster  ·  21B M☉"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  PLANET INFO
# ═══════════════════════════════════════════════════════════════════════════════
PLANET_INFO = {
    "sun":                ("Sun",    (255,248,80),  14, "G2V star · 5,778 K · 1.989×10³⁰ kg",  True),
    "mercury":            ("Mercury",(175,165,160),  4, "Rocky · 4,879 km dia · 430°C day",     False),
    "venus":              ("Venus",  (228,208,128),  7, "Sulphuric clouds · 462°C · 12,104 km", False),
    "mars":               ("Mars",   (193,89,57),    5, "Red Planet · Olympus Mons · moons: 2",  False),
    "jupiter barycenter": ("Jupiter",(210,175,120), 12, "Largest · Great Red Spot · 95 moons",  False),
    "saturn barycenter":  ("Saturn", (220,195,135), 10, "Ring giant · 145 moons · 9.5 AU",      False),
    "uranus barycenter":  ("Uranus", (172,229,238),  7, "Ice giant · tilted 98° · 27 moons",    False),
    "neptune barycenter": ("Neptune",(63,84,186),    6, "Supersonic winds · 30 AU · 16 moons",  False),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  MILKY WAY — high-density path (double band)
# ═══════════════════════════════════════════════════════════════════════════════
MW_BAND = [
    (266.4,-28.9),(275,-20),(285,-14),(295,-9),(305,-4),(315,1),(325,7),(335,13),
    (345,18),(355,22),(5,26),(15,28),(25,29),(35,29),(45,28),(55,26),(65,22),
    (75,18),(85,13),(95,7),(105,1),(115,-6),(125,-13),(135,-20),(145,-28),
    (155,-34),(165,-37),(175,-38),(185,-36),(195,-32),(205,-27),(215,-21),
    (225,-15),(235,-9),(245,-4),(255,1),(265,6),(275,11),(285,15),(295,18),
    (305,20),(315,21),(325,22),(335,22),(345,21),(355,19),
]
# Bright core points for the Galactic Centre bulge
MW_BULGE = [(266+i*0.8-4, -29+j*0.7-2) for i in range(12) for j in range(8)]

# ═══════════════════════════════════════════════════════════════════════════════
#  MATH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def rdxyz(ra, dec):
    r,d = math.radians(ra), math.radians(dec)
    return np.array([math.cos(d)*math.cos(r), math.cos(d)*math.sin(r), math.sin(d)])

def rotmat(yaw, pitch):
    cy,sy = math.cos(yaw),math.sin(yaw)
    cp,sp = math.cos(pitch),math.sin(pitch)
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rx = np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])
    return Rx @ Ry

def proj(v, R, W, H, fov):
    rv = R @ v
    if rv[2] <= 0.01: return None, None
    f = fov / rv[2]
    return int(rv[0]*f + W/2), int(-rv[1]*f + H/2)

def smooth_lerp(a, b, t):
    t = t*t*(3-2*t)   # smoothstep
    return a + (b-a)*t

def ease_out(t):
    return 1-(1-t)**3

# ═══════════════════════════════════════════════════════════════════════════════
#  DRAW HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def blit_text(surf, font, text, x, y, col=(220,240,255), shadow=True, alpha=255):
    if shadow:
        s = font.render(text, True, (0,0,0))
        if alpha < 255:
            s.set_alpha(alpha//2)
        surf.blit(s, (x+1, y+1))
    t = font.render(text, True, col)
    if alpha < 255:
        t.set_alpha(alpha)
    surf.blit(t, (x, y))
    return t.get_width()

def draw_panel(surf, x, y, w, h, alpha=220, border=(0,115,200), hdr_col=None, radius=4):
    """Rounded dark panel with optional glowing header bar"""
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    s.fill((0,0,0,0))
    # Main body
    pygame.draw.rect(s, (3,9,25,alpha), (0,0,w,h), border_radius=radius)
    # Inner glow along top
    for i in range(3):
        c = (*border[:3], 15-i*4)
        pygame.draw.rect(s, c, (0,i,w,1))
    surf.blit(s, (x,y))
    # Border
    pygame.draw.rect(surf, border, (x,y,w,h), 1, border_radius=radius)
    # Header accent
    if hdr_col:
        hs = pygame.Surface((w-2,26), pygame.SRCALPHA)
        hs.fill((*hdr_col[:3], 45))
        surf.blit(hs, (x+1, y+1))

# ═══════════════════════════════════════════════════════════════════════════════
#  PARTICLE SYSTEM  (meteors + sparkle effects)
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x','y','vx','vy','life','maxlife','col','sz','trail']
    def __init__(self, x, y, vx, vy, life, col, sz, trail=False):
        self.x=x; self.y=y; self.vx=vx; self.vy=vy
        self.life=life; self.maxlife=life; self.col=col; self.sz=sz
        self.trail=trail

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.meteor_timer = 0
        self.active = True

    def spawn_meteor(self, W, H):
        x = random.randint(0, W)
        y = random.randint(0, H//3)
        angle = random.uniform(math.pi*1.1, math.pi*1.6)
        speed = random.uniform(8, 18)
        vx = math.cos(angle)*speed
        vy = math.sin(angle)*speed
        col = random.choice([(255,255,220),(220,240,255),(255,235,180),(200,220,255)])
        life = random.uniform(0.5, 1.4)
        self.particles.append(Particle(x,y,vx,vy,life,col,2,trail=True))

    def spawn_sparkle(self, x, y, col):
        for _ in range(8):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(0.5, 3)
            self.particles.append(Particle(
                x+random.uniform(-3,3), y+random.uniform(-3,3),
                math.cos(ang)*spd, math.sin(ang)*spd,
                random.uniform(0.3,0.9), col, 1, False))

    def update(self, dt, W, H, active):
        if active:
            self.meteor_timer -= dt
            if self.meteor_timer <= 0:
                self.spawn_meteor(W, H)
                self.meteor_timer = random.uniform(1.8, 5.0)

        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx; p.y += p.vy
                p.vy += 0.04  # slight gravity on sparkles
                alive.append(p)
        self.particles = alive

    def draw(self, surf):
        for p in self.particles:
            t = p.life / p.maxlife
            a = int(255 * t)
            col = (*p.col[:3], a)
            # Trail
            if p.trail:
                tlen = min(12, int(p.vx**2+p.vy**2)**0.5 * 1.2 + 4)
                for ti in range(tlen):
                    tf = ti / tlen
                    tx = int(p.x - p.vx * tf * 0.7)
                    ty = int(p.y - p.vy * tf * 0.7)
                    ta = int(a * (1-tf)**1.8)
                    if 0 <= tx < surf.get_width() and 0 <= ty < surf.get_height():
                        r = max(1, int(p.sz*(1-tf*0.7)))
                        pygame.draw.circle(surf, (*p.col[:3],ta), (tx,ty), r)
            else:
                r = max(1, int(p.sz*t))
                if 0 <= int(p.x) < surf.get_width() and 0 <= int(p.y) < surf.get_height():
                    pygame.draw.circle(surf, (*p.col[:3],a), (int(p.x),int(p.y)), r)

# ═══════════════════════════════════════════════════════════════════════════════
#  AURORA SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class Aurora:
    def __init__(self, W, H):
        self.W = W; self.H = H
        self.phase = 0
        self.bands = [
            {'y_base': 0.12, 'amp': 0.06, 'speed': 0.18, 'col': (0,255,120), 'width': 80},
            {'y_base': 0.09, 'amp': 0.04, 'speed': 0.25, 'col': (80,200,255), 'width': 55},
            {'y_base': 0.16, 'amp': 0.07, 'speed': 0.12, 'col': (160,0,255), 'width': 45},
            {'y_base': 0.08, 'amp': 0.03, 'speed': 0.31, 'col': (0,255,200), 'width': 35},
        ]
        self.surf = pygame.Surface((W,H), pygame.SRCALPHA)

    def draw(self, surf, t, alpha_scale=1.0):
        self.surf.fill((0,0,0,0))
        W,H = self.W, self.H
        for band in self.bands:
            pts_top = []
            pts_bot = []
            col = band['col']
            for x in range(0, W+20, 20):
                wave1 = math.sin(x*0.008 + t*band['speed']) * band['amp']
                wave2 = math.sin(x*0.015 + t*band['speed']*1.4 + 1.2) * band['amp']*0.5
                cy = int((band['y_base'] + wave1 + wave2) * H)
                hw = band['width'] // 2
                pts_top.append((x, cy - hw))
                pts_bot.append((x, cy + hw))
            all_pts = pts_top + pts_bot[::-1]
            if len(all_pts) >= 3:
                pygame.draw.polygon(self.surf, (*col, int(28*alpha_scale)), all_pts)
                # Bright edge
                if len(pts_top) > 1:
                    pygame.draw.lines(self.surf, (*col, int(80*alpha_scale)), False, pts_top, 2)
        surf.blit(self.surf, (0,0))

# ═══════════════════════════════════════════════════════════════════════════════
#  PLANET MANAGER
# ═══════════════════════════════════════════════════════════════════════════════
class PlanetMgr:
    def __init__(self):
        self.pos={}; self.lock=threading.Lock()
        self.status="Loading ephemeris…"; self.ready=False
        self.ts=self.eph=None

    def start(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            ts = skyload.timescale()
            self.status = "Downloading DE421 (~17 MB on first run)…"
            eph = skyload('de421.bsp')
            self.ts=ts; self.eph=eph; self.ready=True
            self.status="Planets ready"
            self._calc()
        except Exception as e:
            self.status = f"Planet error: {e}"

    def _calc(self):
        if not self.ready: return
        try:
            dt = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            t = self.ts.from_datetime(dt)
            earth = self.eph['earth']; out={}
            for key,(name,col,sz,desc,is_sun) in PLANET_INFO.items():
                try:
                    obj = self.eph['sun'] if key=='sun' else self.eph[key]
                    a = earth.at(t).observe(obj)
                    ra,dec,dist = a.radec()
                    out[name]={'xyz':rdxyz(ra.degrees,dec.degrees),
                               'ra':ra.degrees,'dec':dec.degrees,
                               'dist':dist.au,'color':col,'sz':sz,
                               'desc':desc,'is_sun':is_sun}
                except: pass
            with self.lock: self.pos=out
        except: pass

    def refresh(self):
        if self.ready:
            threading.Thread(target=self._calc, daemon=True).start()

    def get(self):
        with self.lock: return dict(self.pos)

# ═══════════════════════════════════════════════════════════════════════════════
#  SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
class Search:
    def __init__(self, fm, fs):
        self.on=False; self.q=""; self.res=[]; self.cur=0; self.fm=fm; self.fs=fs
        self.fade=0.0

    def open(self):
        self.on=True; self.q=""; self.res=[]; self.cur=0; self.fade=0.0

    def close(self): self.on=False; self.fade=0.0

    def update(self):
        q=self.q.lower()
        self.res=[(h,n) for h,n in NAMED.items()
                  if q in n[0].lower() or q in n[1].lower() or q in n[3].lower()][:12]
        self.cur=max(0,min(self.cur,len(self.res)-1))

    def sel(self): return self.res[self.cur][0] if self.res else None

    def tick(self, dt):
        if self.on:
            self.fade=min(1.0, self.fade+dt*8)
        else:
            self.fade=max(0.0, self.fade-dt*8)

    def draw(self, surf, W, H):
        if self.fade<=0: return
        a=int(self.fade*255)
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,int(150*self.fade)))
        surf.blit(ov,(0,0))

        bw=580; bh=min(108+len(self.res)*32,470)
        bx=W//2-bw//2; by=int(H//2-bh//2 + (1-self.fade)*30)

        draw_panel(surf,bx,by,bw,bh,alpha=230,border=(0,115,235),hdr_col=(0,90,200))
        blit_text(surf,self.fm,"✦  STAR  SEARCH",bx+14,by+8,(60,180,255),alpha=a)

        # Input field
        pygame.draw.rect(surf,(6,14,40),(bx+12,by+34,bw-24,30),border_radius=3)
        pygame.draw.rect(surf,(0,100,215),(bx+12,by+34,bw-24,30),1,border_radius=3)
        caret="▋" if (time.time()*2)%2<1 else " "
        blit_text(surf,self.fm,self.q+caret,bx+18,by+40,(200,235,255),alpha=a)

        for i,(hip,info) in enumerate(self.res):
            ry=by+72+i*32
            if i==self.cur:
                hl=pygame.Surface((bw-24,28),pygame.SRCALPHA)
                hl.fill((0,60,155,int(120*self.fade)))
                surf.blit(hl,(bx+12,ry-2))
                # Glowing left accent
                pygame.draw.rect(surf,(0,155,255),(bx+12,ry-2,2,28))
            sc=spcol(info[2])
            # Spectral dot
            pygame.draw.circle(surf,sc,(bx+26,ry+12),6)
            pygame.draw.circle(surf,(255,255,255),(bx+26,ry+12),6,1)
            blit_text(surf,self.fm,f"{info[0]}  {info[1]}",bx+40,ry+2,sc,alpha=a)
            ds=f"{info[4]:.0f} ly" if len(info)>4 and info[4]>0 else ""
            blit_text(surf,self.fs,f"{info[3]}  ·  {info[2]}  ·  HIP {hip}  {ds}",
                      bx+40,ry+18,(90,140,195),alpha=a)

        if not self.res and self.q:
            blit_text(surf,self.fm,"No stars found.",bx+22,by+78,(110,85,125),alpha=a)
        blit_text(surf,self.fs,"↑↓  Navigate   ENTER  Select   ESC  Close",
                  bx+16,by+bh-18,(45,75,135),alpha=a)

# ═══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATION TOASTS
# ═══════════════════════════════════════════════════════════════════════════════
class Toast:
    def __init__(self):
        self.items = []   # (text, life, maxlife, col)

    def add(self, text, col=(0,200,255), duration=2.5):
        self.items.append([text, duration, duration, col])

    def update(self, dt):
        self.items = [[t,l-dt,m,c] for t,l,m,c in self.items if l-dt>0]

    def draw(self, surf, font, W, H):
        y = H - 80
        for text,life,maxlife,col in self.items:
            t = min(1.0, life/0.3, life/maxlife*3)
            a = int(255*t)
            tw = font.size(text)[0]+20
            tx = W//2-tw//2
            draw_panel(surf,tx-4,y-4,tw+8,24,alpha=int(190*t),border=col)
            blit_text(surf,font,text,tx+6,y,col,alpha=a)
            y -= 32

# ═══════════════════════════════════════════════════════════════════════════════
#  MILKY WAY RENDERER — volumetric multi-pass
# ═══════════════════════════════════════════════════════════════════════════════
def draw_milky_way(surf, R, W, H, fov, t):
    mw = pygame.Surface((W,H), pygame.SRCALPHA)
    pts = []
    for ra,dec in MW_BAND:
        p = proj(rdxyz(ra,dec),R,W,H,fov)
        if p[0] and -300<p[0]<W+300 and -300<p[1]<H+300:
            pts.append(p)

    if len(pts) > 4:
        # Wide outer glow
        pygame.draw.lines(mw,(255,245,210, 5),False,pts,80)
        # Mid band
        pygame.draw.lines(mw,(240,225,195, 9),False,pts,38)
        # Bright lane
        pygame.draw.lines(mw,(255,255,230,14),False,pts,12)
        # Core spine
        pygame.draw.lines(mw,(255,255,245,22),False,pts,4)
        # Dust rifts (dark lanes)
        pygame.draw.lines(mw,(0,0,0,35),False,pts,3)

    # Galactic core bulge
    core_pts = []
    for ra,dec in MW_BULGE:
        p = proj(rdxyz(ra,dec),R,W,H,fov)
        if p[0] and 0<p[0]<W and 0<p[1]<H:
            core_pts.append(p)
    for cx,cy in core_pts:
        pls = 0.7 + 0.3*math.sin(t*0.3+cx*0.1+cy*0.07)
        for ri in range(18,0,-3):
            a = int(12*(1-ri/18)**1.4*pls)
            pygame.draw.circle(mw,(255,240,185,a),(cx,cy),ri)

    surf.blit(mw,(0,0))

# ═══════════════════════════════════════════════════════════════════════════════
#  GRID
# ═══════════════════════════════════════════════════════════════════════════════
def draw_grid(surf, R, W, H, fov, fs):
    gs = pygame.Surface((W,H), pygame.SRCALPHA)
    for dec in range(-80,81,20):
        pts=[]
        for ra in range(0,362,4):
            p=proj(rdxyz(ra,dec),R,W,H,fov)
            if p[0] and 0<=p[0]<W and 0<=p[1]<H: pts.append(p)
            elif pts:
                if len(pts)>1: pygame.draw.lines(gs,(255,255,255,18),False,pts,1)
                pts=[]
        if len(pts)>1: pygame.draw.lines(gs,(255,255,255,18),False,pts,1)
    for ra in range(0,360,30):
        pts=[]
        for dec in range(-88,89,3):
            p=proj(rdxyz(ra,dec),R,W,H,fov)
            if p[0] and 0<=p[0]<W and 0<=p[1]<H: pts.append(p)
            elif pts:
                if len(pts)>1: pygame.draw.lines(gs,(255,255,255,18),False,pts,1)
                pts=[]
        if len(pts)>1: pygame.draw.lines(gs,(255,255,255,18),False,pts,1)
    surf.blit(gs,(0,0))
    for ra in range(0,360,30):
        p=proj(rdxyz(ra,0),R,W,H,fov)
        if p[0] and 20<p[0]<W-55 and 20<p[1]<H-20:
            blit_text(surf,fs,f"{ra//15}h",p[0],p[1],(50,80,130))
    for dec in range(-80,81,20):
        p=proj(rdxyz(0,dec),R,W,H,fov)
        if p[0] and 20<p[0]<W-65 and 20<p[1]<H-20:
            blit_text(surf,fs,f"{'+' if dec>=0 else ''}{dec}°",p[0],p[1],(50,80,130))

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTELLATIONS — with animated connection flash on selection
# ═══════════════════════════════════════════════════════════════════════════════
def draw_constellations(surf, sdata, R, W, H, fov, labels, fs, sel_hip=None, t=0):
    ls = pygame.Surface((W,H), pygame.SRCALPHA)
    for name,pairs in CONSTS.items():
        # Check if selected star is in this constellation
        in_const = sel_hip and any(sel_hip in (a,b) for a,b in pairs)
        for a,b in pairs:
            if a not in sdata or b not in sdata: continue
            pa=proj(sdata[a][0],R,W,H,fov); pb=proj(sdata[b][0],R,W,H,fov)
            if not pa[0] or not pb[0]: continue
            if in_const:
                # Glowing highlighted line
                pulse = 0.55+0.45*math.sin(t*3)
                pygame.draw.line(ls,(100,180,255,int(130*pulse)),pa,pb,2)
                pygame.draw.line(ls,(200,230,255,int(60*pulse)),pa,pb,4)
            else:
                pygame.draw.line(ls,(65,110,180,70),pa,pb,1)
    surf.blit(ls,(0,0))
    if labels:
        for name,(ra,dec) in CLABELS.items():
            p=proj(rdxyz(ra,dec),R,W,H,fov)
            if p[0] and 0<p[0]<W and 0<p[1]<H:
                blit_text(surf,fs,name.upper(),p[0],p[1],(55,110,185))

# ═══════════════════════════════════════════════════════════════════════════════
#  DSO ICON RENDERER — enhanced
# ═══════════════════════════════════════════════════════════════════════════════
def draw_dso_icon(surf, x, y, dt, sz, t=0):
    col = DSOCOL.get(dt,(200,200,200))
    pulse = 0.85+0.15*math.sin(t*1.5)

    if dt=="GAL":
        # Animated galaxy ellipse with gradient
        gsurf = pygame.Surface((sz*4+4, sz*2+4), pygame.SRCALPHA)
        for ri in range(sz,0,-1):
            a = int(80*(1-(ri/sz))**0.5*pulse)
            pygame.draw.ellipse(gsurf,(*col,a),(sz*2-ri*2, sz-ri//2, ri*4, ri),(0 if ri>2 else 0))
        pygame.draw.ellipse(gsurf,(*col,160),(0,sz//2,sz*4,sz),1)
        surf.blit(gsurf,(x-sz*2-2,y-sz-2))

    elif dt in("GC","OC"):
        # Starburst pattern
        for ri in range(sz,0,-1):
            a = int(55*(1-ri/sz)**0.8)
            pygame.draw.circle(surf,(*col,a),(x,y),ri)
        pygame.draw.circle(surf,col,(x,y),sz,1)
        pygame.draw.line(surf,(*col,180),(x-sz-3,y),(x+sz+3,y),1)
        pygame.draw.line(surf,(*col,180),(x,y-sz-3),(x,y+sz+3),1)
        # Diagonal for OC
        if dt=="OC":
            d=int(sz*0.7)
            pygame.draw.line(surf,(*col,110),(x-d,y-d),(x+d,y+d),1)
            pygame.draw.line(surf,(*col,110),(x-d,y+d),(x+d,y-d),1)

    elif dt in("NEB","SNR"):
        # Hex/hexagonal blob
        for ri in range(sz,0,-1):
            a = int(40*(1-ri/sz))
            pts = [(int(x+ri*math.cos(math.radians(i*60))),
                    int(y+ri*math.sin(math.radians(i*60)))) for i in range(6)]
            pygame.draw.polygon(surf,(*col,a),pts)
        pts = [(int(x+sz*math.cos(math.radians(i*60))),
                int(y+sz*math.sin(math.radians(i*60)))) for i in range(6)]
        pygame.draw.polygon(surf,col,pts,1)

    elif dt=="PN":
        # Planetary: concentric rings with glow
        for ri in range(sz,0,-1):
            a = int(30*(1-ri/sz))
            pygame.draw.circle(surf,(*col,a),(x,y),ri)
        pygame.draw.circle(surf,col,(x,y),sz,1)
        pygame.draw.circle(surf,(*col,150),(x,y),max(2,sz//2),1)
        pygame.draw.circle(surf,(*col,80),(x,y),max(1,sz//3))

def draw_dsos(surf, R, W, H, fov, fs, mlim, t):
    for name,ra,dec,dt,mag,desc in DSOS:
        if mag > mlim+2.5: continue
        p = proj(rdxyz(ra,dec),R,W,H,fov)
        if not p[0] or not(5<p[0]<W-5 and 5<p[1]<H-5): continue
        sz = max(5,int(14-mag))
        draw_dso_icon(surf,p[0],p[1],dt,sz,t)
        blit_text(surf,fs,name,p[0]+sz+5,p[1]-5,DSOCOL.get(dt,(200,200,200)))

# ═══════════════════════════════════════════════════════════════════════════════
#  BLACK HOLES — cinematic gravitational lensing effect
# ═══════════════════════════════════════════════════════════════════════════════
def draw_bhs(surf, glow, R, W, H, fov, fs, fm, tp, sel_bh):
    hover=None; bd=22; mx,my=pygame.mouse.get_pos()
    for i,(name,ra,dec,bt,mass,dist,desc) in enumerate(BH_LIST):
        p=proj(rdxyz(ra,dec),R,W,H,fov)
        if not p[0] or not(0<=p[0]<W and 0<=p[1]<H): continue
        sx,sy=p
        pulse=0.5+0.5*math.sin(tp*1.2+i*0.9)
        is_smb=(bt=="SMBH")
        gc=(255,175,20) if is_smb else (255,100,50)
        ring_col=(255,220,80) if is_smb else (255,140,80)

        # Accretion disk glow — wide diffuse
        for ri in range(30,0,-1):
            a=int(60*(1-ri/30)**1.6*pulse)
            pygame.draw.circle(glow,(*gc,a),(sx,sy),ri)

        # Photon ring — thin bright ring
        for ri in range(14,10,-1):
            a=int(200*(1-(ri-10)/4))
            pygame.draw.circle(surf,(*ring_col,a),(sx,sy),ri,1)

        # Innermost shadow (event horizon)
        pygame.draw.circle(surf,(0,0,0),(sx,sy),9)
        pygame.draw.circle(surf,ring_col,(sx,sy),9,1)

        # Rotating accretion jets (for SMBHs)
        if is_smb:
            for ang_off in [0, math.pi]:
                ang = tp*0.4 + ang_off
                for jl in range(25,0,-2):
                    jx=int(sx+math.cos(ang)*jl*0.6)
                    jy=int(sy+math.sin(ang)*jl*2.2)
                    ja=int(40*(1-jl/25)**0.8)
                    pygame.draw.circle(surf,(*gc,ja),(jx,jy),1)

        is_sel=(name==sel_bh)
        if is_sel:
            pygame.draw.circle(surf,(255,255,255),(sx,sy),22,2)
            pygame.draw.circle(surf,gc,(sx,sy),30,1)
        blit_text(surf, fm if is_sel else fs, name,
                  sx+18, sy-8, gc if is_sel else (185,140,55))

        d=math.hypot(mx-sx,my-sy)
        if d<bd: bd=d; hover=name
    return hover

# ═══════════════════════════════════════════════════════════════════════════════
#  PLANET SIZE HELPER
# ═══════════════════════════════════════════════════════════════════════════════
def planet_sz(base, dist, fov):
    fs=600.0/max(fov,30); ds=1.0/max(dist,0.3)
    return max(3,int(base*math.sqrt(fs)*ds**0.25))

# ═══════════════════════════════════════════════════════════════════════════════
#  SUN RENDERER — chromosphere + corona + solar wind
# ═══════════════════════════════════════════════════════════════════════════════
def draw_sun_obj(surf, glow, sx, sy, sz, tp):
    col=(255,248,80)
    # Wide corona (on glow layer)
    for ri in range(sz+50,0,-1):
        a=int(45*(1-ri/(sz+50))**1.4)
        pygame.draw.circle(glow,(*col,a),(sx,sy),ri)
    for ri in range(sz+20,0,-1):
        a=int(70*(1-ri/(sz+20))**1.8)
        pygame.draw.circle(glow,(255,200,80,a),(sx,sy),ri)

    # Chromosphere
    pygame.draw.circle(surf,(255,235,100),(sx,sy),sz)
    pygame.draw.circle(surf,(255,255,160),(sx,sy),max(2,sz-3))

    # Solar flares / prominences
    for ang_i in range(0,360,30):
        ang=math.radians(ang_i+tp*12)
        base_l=sz+1
        tip_l=sz+int(4+3*math.sin(tp*2.5+ang_i*0.3))
        x1=sx+int(base_l*math.cos(ang)); y1=sy+int(base_l*math.sin(ang))
        x2=sx+int(tip_l*math.cos(ang));  y2=sy+int(tip_l*math.sin(ang))
        pygame.draw.line(surf,(255,160,40),(x1,y1),(x2,y2),2)

    # Limb darkening
    for ri in range(sz,0,-2):
        t2=ri/sz
        a=int(40*(1-t2)**1.2)
        pygame.draw.circle(surf,(80,30,0,a),(sx,sy),ri)

# ═══════════════════════════════════════════════════════════════════════════════
#  PLANET RENDERER
# ═══════════════════════════════════════════════════════════════════════════════
def draw_planets(surf, glow, ppos, R, W, H, fov, sel, fs, fm, tp):
    hover=None; bd=26; mx,my=pygame.mouse.get_pos()
    fovd=math.degrees(math.atan(fov/500)*2)

    for name,info in ppos.items():
        p=proj(info['xyz'],R,W,H,fov)
        if not p[0] or not(0<=p[0]<W and 0<=p[1]<H): continue
        col=info['color']; dist=info['dist']
        sz=planet_sz(info['sz'],dist,fov)
        is_sel=(name==sel); is_sun=info.get('is_sun',False)
        sx,sy=p

        if is_sun:
            draw_sun_obj(surf,glow,sx,sy,sz,tp)
        else:
            # Glow halo
            for ri in range(sz+14,0,-1):
                a=int(55*(1-ri/(sz+14))**2)
                pygame.draw.circle(glow,(*col,a),(sx,sy),ri)

            if name=="Saturn":
                # Full ring system with gaps
                rw=sz*3; rh=max(3,sz//2)
                rs=pygame.Surface((rw*2+4,rh*2+8),pygame.SRCALPHA)
                for ri in range(rw,sz,-1):
                    # Cassini division at ~75% of ring
                    if 0.73*rw < ri < 0.77*rw:
                        continue
                    t2=(ri-sz)/(rw-sz)
                    at=int(85*math.sin(t2*math.pi)**0.8)
                    shade=(int(col[0]*0.9),int(col[1]*0.85),int(col[2]*0.75),at)
                    pygame.draw.ellipse(rs,shade,(rw-ri,rh-ri//4,ri*2,ri//2),1)
                surf.blit(rs,(sx-rw-2,sy-rh-4))
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Atmosphere bands
                pygame.draw.circle(surf,(240,215,155),(sx,sy),max(2,sz-1))

            elif name=="Jupiter":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Belt system
                belt_cols=[(185,150,105,70),(210,175,125,55),(195,162,112,65),
                           (220,190,140,45),(175,140,95,60)]
                for bi,(bc) in enumerate(belt_cols):
                    yo=int((bi/(len(belt_cols)-1)*2-1)*sz*0.85)
                    bw2=int(sz*1.9); bh2=max(2,sz//4+1)
                    bd2=pygame.Surface((bw2,bh2),pygame.SRCALPHA)
                    bd2.fill(bc); surf.blit(bd2,(sx-bw2//2,sy+yo-bh2//2))
                # Great Red Spot
                if sz>=6:
                    grs_x=sx+int(sz*0.4*math.cos(tp*0.15))
                    grs_y=sy+int(sz*0.3)
                    pygame.draw.ellipse(surf,(200,80,50),(grs_x-sz//4,grs_y-sz//8,sz//2,sz//4))

            elif name=="Mars":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Ice cap
                pc=max(1,sz//3)
                pygame.draw.ellipse(surf,(235,245,255),(sx-pc,sy-sz,pc*2,pc+1))
                # Surface detail
                if sz>=5:
                    pygame.draw.circle(surf,(150,60,30),(sx+sz//3,sy),(sz//4),)

            elif name=="Venus":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Cloud bands
                for ci in range(4):
                    cy2=int((ci/3*2-1)*sz*0.6)
                    vs=pygame.Surface((sz*2,max(3,sz//3)),pygame.SRCALPHA)
                    vs.fill((255,255,210,40)); surf.blit(vs,(sx-sz,sy+cy2-sz//6))
                # Limb brightening
                pygame.draw.circle(surf,(255,255,200,60),(sx,sy),sz,2)

            elif name=="Neptune":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Dark storm
                if sz>=4:
                    pygame.draw.circle(surf,(30,50,180),(sx+sz//4,sy-sz//4),max(1,sz//3))
                # Methane cloud
                pygame.draw.circle(surf,(160,200,255,80),(sx-sz//3,sy+sz//3),max(1,sz//4))

            elif name=="Uranus":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Tilted ring
                if sz>=5:
                    rs2=pygame.Surface((sz*3+2,sz+2),pygame.SRCALPHA)
                    pygame.draw.ellipse(rs2,(*col,60),(0,0,sz*3+2,sz+2),2)
                    surf.blit(rs2,(sx-sz*3//2-1,sy-sz//2))

            elif name=="Mercury":
                pygame.draw.circle(surf,col,(sx,sy),sz)
                # Crater hint
                if sz>=5:
                    pygame.draw.circle(surf,(155,145,140),(sx+sz//4,sy-sz//4),max(1,sz//4),1)

            else:
                pygame.draw.circle(surf,col,(sx,sy),sz)

            # Specular highlight
            pygame.draw.circle(surf,(255,255,255,90),(sx-sz//4,sy-sz//4),max(1,sz//3))
            pygame.draw.circle(surf,(255,255,255),(sx,sy),sz,1)

        if is_sel:
            # Animated selection ring
            pulse=0.6+0.4*math.sin(tp*4)
            pygame.draw.circle(surf,(255,255,255),(sx,sy),sz+int(9+3*pulse),2)
            pygame.draw.circle(surf,col,(sx,sy),sz+20,1)
            # Targeting reticle corners
            for ang in [45,135,225,315]:
                a=math.radians(ang); r=sz+28
                x1=sx+int(r*math.cos(a)); y1=sy+int(r*math.sin(a))
                x2=sx+int((r-8)*math.cos(a)); y2=sy+int((r-8)*math.sin(a))
                pygame.draw.line(surf,col,(x1,y1),(x2,y2),2)

        if fovd<60 or is_sel or sz>=7:
            blit_text(surf,fm,name,sx+sz+7,sy-8,col)
            if is_sel:
                blit_text(surf,fs,f"{dist:.4f} AU",sx+sz+7,sy+8,(175,205,235))

        d=math.hypot(mx-sx,my-sy)
        if d<bd: bd=d; hover=name
    return hover

# ═══════════════════════════════════════════════════════════════════════════════
#  INFO PANELS
# ═══════════════════════════════════════════════════════════════════════════════
def draw_star_info(surf, flg, fmd, fsm, hip, sdata, W, H):
    v,mag=sdata[hip]
    ra=math.degrees(math.atan2(v[1],v[0]))%360
    dec=math.degrees(math.asin(max(-1,min(1,v[2]))))
    rh=int(ra/15); rm=int((ra/15-rh)*60); rs=((ra/15-rh)*60-rm)*60
    bw,bh=310,310; bx,by=W-bw-14,52
    if hip in NAMED:
        nm,byr,sp,cn,dl=NAMED[hip]; col=spcol(sp)
    else:
        nm=f"HIP {hip}"; byr="—"; sp="?"; cn="—"; dl=0; col=(200,210,230)
    draw_panel(surf,bx,by,bw,bh,alpha=235,border=col,hdr_col=col)
    blit_text(surf,flg,"★  "+nm[:22],bx+10,by+8,col)
    rows=[("Bayer / Flamsteed",byr),("Constellation",cn),
          ("Spectral Type",sp),("Magnitude",f"{mag:.2f}"),
          ("Distance",f"{dl:,.1f} ly" if dl else "—"),
          ("RA",f"{rh:02d}h {rm:02d}m {rs:04.1f}s"),
          ("Dec",f"{'+' if dec>=0 else ''}{dec:.4f}°"),
          ("HIP ID",str(hip))]
    for i,(k,v2) in enumerate(rows):
        ry=by+34+i*28
        blit_text(surf,fsm,k,bx+10,ry+1,(60,110,175))
        blit_text(surf,fmd,v2,bx+168,ry,(215,240,255))
    note=SPEC_NOTE.get((sp or "?")[0],"")
    if note:
        blit_text(surf,fsm,note,bx+10,by+bh-24,(65,140,90))
    # Spectral color swatch
    pygame.draw.circle(surf,col,(bx+bw-22,by+15),8)
    pygame.draw.circle(surf,(255,255,255),(bx+bw-22,by+15),8,1)

def draw_planet_info(surf, flg, fmd, fsm, name, info, W, H):
    bw,bh=310,200; bx,by=W-bw-14,52
    col=info['color']
    draw_panel(surf,bx,by,bw,bh,alpha=235,border=col,hdr_col=col)
    blit_text(surf,flg,"⬤  "+name,bx+10,by+8,col)
    ra=info['ra']; dec=info['dec']
    rh=int(ra/15); rm=int((ra/15-rh)*60)
    is_sun=info.get('is_sun',False)
    rows=[("Type","Star (Sun)" if is_sun else "Planet"),
          ("RA",f"{rh:02d}h {rm:02d}m"),
          ("Dec",f"{'+' if dec>=0 else ''}{dec:.2f}°"),
          ("Distance",f"{info['dist']:.6f} AU")]
    for i,(k,v) in enumerate(rows):
        ry=by+34+i*28
        blit_text(surf,fsm,k,bx+10,ry+1,(60,110,175))
        blit_text(surf,fmd,v,bx+140,ry,(215,240,255))
    blit_text(surf,fsm,info['desc'],bx+10,by+bh-24,(65,140,90))

def draw_bh_info(surf, flg, fmd, fsm, name, W, H):
    bh=next((b for b in BH_LIST if b[0]==name),None)
    if not bh: return
    nm,ra,dec,bt,mass,dist,desc=bh
    bw,bh2=310,215; bx,by=W-bw-14,52
    col=(255,200,40)
    draw_panel(surf,bx,by,bw,bh2,alpha=235,border=col,hdr_col=col)
    blit_text(surf,flg,"◉  "+nm,bx+10,by+8,col)
    ms=f"{mass:.2e} M☉" if mass>=1e6 else f"{mass:.0f} M☉"
    ds=f"{dist/1e6:.1f}M ly" if dist>1e5 else f"{dist:,} ly"
    rows=[("Type",bt),("Mass",ms),("Distance",ds),
          ("RA/Dec",f"{ra:.2f}° / {dec:.2f}°"),
          ("Schwarzschild r.","≈ event horizon")]
    for i,(k,v) in enumerate(rows):
        ry=by+34+i*28
        blit_text(surf,fsm,k,bx+10,ry+1,(60,110,175))
        blit_text(surf,fmd,v,bx+168,ry,(215,240,255))
    blit_text(surf,fsm,desc,bx+10,by+bh2-24,(175,145,55))

def draw_dso_info(surf, flg, fmd, fsm, name, W, H):
    dso=next((d for d in DSOS if d[0]==name),None)
    if not dso: return
    nm,ra,dec,dt,mag,desc=dso
    bw,bh=310,185; bx,by=W-bw-14,52
    col=DSOCOL.get(dt,(200,200,200))
    draw_panel(surf,bx,by,bw,bh,alpha=235,border=col,hdr_col=col)
    blit_text(surf,flg,"✦  "+nm[:24],bx+10,by+8,col)
    rows=[("Type",{"GAL":"Galaxy","GC":"Globular Cluster","OC":"Open Cluster",
                   "NEB":"Nebula","SNR":"Supernova Remnant","PN":"Planetary Nebula"}.get(dt,dt)),
          ("Magnitude",f"{mag:.1f}"),("RA/Dec",f"{ra:.2f}° / {dec:.2f}°")]
    for i,(k,v) in enumerate(rows):
        ry=by+34+i*28
        blit_text(surf,fsm,k,bx+10,ry+1,(60,110,175))
        blit_text(surf,fmd,v,bx+168,ry,(215,240,255))
    blit_text(surf,fsm,desc,bx+10,by+bh-42,(65,140,90))
    blit_text(surf,fsm,f"Class: {dt}",bx+10,by+bh-22,(65,140,90))

# ═══════════════════════════════════════════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════════════════════════════════════════
HLINES=[
    ("NAVIGATION",None),("Mouse drag / WASD","Rotate sky view"),("Scroll","Zoom in/out"),
    ("R","Reset view"),("",""),
    ("OVERLAYS",None),("C","Constellations"),("L","Labels"),
    ("G","RA/Dec grid"),("M","Milky Way"),("N","Star names"),
    ("B","Spectral colors"),("T","Twinkling"),("F1","DSOs + Black holes"),
    ("P","Meteor shower toggle"),("E","Aurora toggle"),("",""),
    ("FILTER",None),("1","Stars only"),("2","Solar system only"),("3","Both"),("",""),
    ("STARS",None),("+/-","Magnitude limit"),("S","Search"),("TAB","Next named star"),("",""),
    ("OTHER",None),("F3","Screenshot"),("H","Help"),("ESC","Deselect / Quit"),
]

def draw_hud(surf, fxl, flg, fmd, fsm, W, H, total, vis, fov, yaw, pitch, mlim, spec, twinkle, mode, pcnt, aurora, meteors):
    # Top bar
    bg=pygame.Surface((W,44),pygame.SRCALPHA); bg.fill((2,6,20,230)); surf.blit(bg,(0,0))
    # Gradient separator
    for x in range(0,W,2):
        pygame.draw.line(surf,(0,80,180,80),(x,43),(x+1,43))
    blit_text(surf,fxl,"COSMO",12,3,(0,190,255))
    blit_text(surf,fxl,"LENS",100,3,(230,245,255))
    blit_text(surf,fsm,"DEEP SKY ATLAS  v5",14,28,(40,85,155))

    now=datetime.datetime.utcnow()
    blit_text(surf,fmd,now.strftime("UTC  %Y-%m-%d  %H:%M:%S"),W//2-130,8,(150,215,255))
    fovd=math.degrees(math.atan(fov/500)*2)
    mcols=[(0,215,255),(90,255,140),(255,210,90)]
    mstrs=["STARS ONLY","SOLAR SYSTEM","STARS + SOLAR SYSTEM"]
    blit_text(surf,fsm,mstrs[mode],W//2-60,28,mcols[mode])

    blit_text(surf,fsm,"[H]Help [S]Search [C]Consts [G]Grid [1/2/3]Mode",W-392,6,(40,72,138))
    blit_text(surf,fsm,"[B]Spectral [T]Twinkle [F1]DSO/BH [+/-]Mag [ESC]Quit",W-392,22,(32,62,118))

    # Bottom status bar
    bg2=pygame.Surface((W,22),pygame.SRCALPHA); bg2.fill((2,6,20,215)); surf.blit(bg2,(0,H-22))
    for x in range(0,W,2):
        pygame.draw.line(surf,(0,60,140,70),(x,H-22),(x+1,H-22))

    stats=[f"★ {vis:,}/{total:,}",f"FOV {fovd:.0f}°",f"MAG≤{mlim:.1f}",
           f"YAW {math.degrees(yaw):.0f}°",f"PITCH {math.degrees(pitch):.0f}°",
           f"{'SPECTRAL' if spec else 'MONO'}",
           "✦TWINKLE" if twinkle else "",
           f"☄ METEORS" if meteors else "",
           f"⌂ AURORA" if aurora else "",
           f"⬤ {pcnt} solar" if pcnt else ""]
    x=8
    for s in stats:
        if s: x+=blit_text(surf,fsm,s,x,H-16,(60,108,168))+14

def draw_help(surf, flg, fmd, fsm, W, H):
    bw=480; bh=32+len(HLINES)*18
    bx=W//2-bw//2; by=H//2-bh//2
    draw_panel(surf,bx,by,bw,bh,alpha=240,border=(0,110,235))
    blit_text(surf,flg,"  K E Y B O A R D   R E F E R E N C E",bx+14,by+8,(60,165,255))
    for i,(k,v) in enumerate(HLINES):
        ry=by+28+i*18
        if v is None:
            blit_text(surf,fsm,k,bx+14,ry,(52,96,180))
            pygame.draw.line(surf,(18,52,110),(bx+14,ry+14),(bx+bw-14,ry+14),1)
        elif k:
            blit_text(surf,fmd,k,bx+18,ry,(180,220,255))
            blit_text(surf,fmd,v,bx+205,ry,(110,165,225))

def draw_loading(scr, fxl, fmd, fsm, W, H, msg, pct):
    scr.fill((0,0,7))
    # Starfield
    rng=random.Random(99)
    for _ in range(200):
        x,y=rng.randint(0,W),rng.randint(0,H)
        br=rng.randint(40,120)
        pygame.draw.circle(scr,(br,br,min(br+20,255)),(x,y),rng.randint(0,1))

    # Logo
    blit_text(scr,fxl,"COSMO",W//2-105,H//2-75,(0,190,255))
    blit_text(scr,fxl,"LENS",W//2+2,H//2-75,(230,245,255))
    blit_text(scr,fmd,"DEEP SKY  ATLAS  v5",W//2-100,H//2-36,(40,80,155))
    blit_text(scr,fsm,"you have downloaded the universe",W//2-108,H//2-16,(35,65,115))

    # Progress bar
    bw=400; bx=W//2-bw//2; by=H//2+20
    pygame.draw.rect(scr,(12,24,55),(bx,by,bw,8),border_radius=4)
    fw=int(bw*min(1,pct))
    if fw>0:
        pygame.draw.rect(scr,(0,140,255),(bx,by,fw,8),border_radius=4)
        # Shimmer
        pygame.draw.rect(scr,(100,220,255),(bx+fw-3,by,3,8),border_radius=2)

    blit_text(scr,fsm,msg,W//2-150,H//2+36,(65,115,175))
    pygame.display.flip()

# ═══════════════════════════════════════════════════════════════════════════════
#  BACKGROUND BUILDER  — deep-space with nebula patches + vignette
# ═══════════════════════════════════════════════════════════════════════════════
def build_bg(W, H):
    surf=pygame.Surface((W,H)); surf.fill((0,0,6))
    # Gradient
    for y in range(H):
        t=y/H
        c=(int(1+t*2), int(1+t*1.5), int(5+t*9))
        pygame.draw.line(surf,c,(0,y),(W,y))

    # Background nebula patches
    rng=random.Random(42)
    for _ in range(18):
        nx=rng.randint(80,W-80); ny=rng.randint(80,H-80)
        nr=rng.randint(60,160)
        nc=(rng.randint(3,20), rng.randint(3,20), rng.randint(12,50))
        ns=pygame.Surface((nr*2,nr*2),pygame.SRCALPHA)
        for ri in range(nr,0,-5):
            a=int(14*(1-ri/nr)**1.8)
            pygame.draw.circle(ns,(*nc,a),(nr,nr),ri)
        surf.blit(ns,(nx-nr,ny-nr))

    # Vignette
    vig=pygame.Surface((W,H),pygame.SRCALPHA)
    for ri in range(min(W,H)//2,0,-8):
        a=int(100*(1-2*ri/min(W,H))**3)
        if a>0:
            pygame.draw.ellipse(vig,(0,0,0,a),(W//2-ri,H//2-ri,ri*2,ri*2),16)
    surf.blit(vig,(0,0))
    return surf

# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSITION SYSTEM  (smooth fade for navigation)
# ═══════════════════════════════════════════════════════════════════════════════
class ViewTransition:
    def __init__(self):
        self.active=False
        self.yaw_from=self.yaw_to=0
        self.pitch_from=self.pitch_to=0
        self.progress=0.0
        self.duration=0.8

    def start(self, yaw_from, pitch_from, yaw_to, pitch_to, duration=0.8):
        self.yaw_from=yaw_from; self.pitch_from=pitch_from
        self.yaw_to=yaw_to; self.pitch_to=pitch_to
        self.progress=0.0; self.duration=duration
        self.active=True

    def update(self, dt):
        if not self.active: return 0,0,False
        self.progress=min(1.0,self.progress+dt/self.duration)
        t=ease_out(self.progress)
        # Angle lerp (handle wrap)
        dy=((self.yaw_to-self.yaw_from+math.pi)%(math.tau))-math.pi
        yaw=self.yaw_from+dy*t
        pitch=self.pitch_from+(self.pitch_to-self.pitch_from)*t
        done=(self.progress>=1.0)
        if done: self.active=False
        return yaw,pitch,done

    def apply(self, cur_yaw, cur_pitch):
        if not self.active: return cur_yaw,cur_pitch
        y,p,_=self.update(0)
        return y,p

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    pygame.display.set_caption("CosmoLens — Deep Sky Atlas v5")
    W,H=1400,860
    flags=pygame.RESIZABLE
    try: flags|=pygame.HWSURFACE|pygame.DOUBLEBUF
    except: pass
    screen=pygame.display.set_mode((W,H),flags)

    fxl=pygame.font.SysFont("Courier New",24,bold=True)
    flg=pygame.font.SysFont("Courier New",16,bold=True)
    fmd=pygame.font.SysFont("Courier New",13)
    fsm=pygame.font.SysFont("Courier New",11)

    # ── LOAD HIPPARCOS ─────────────────────────────────────────────────────────
    draw_loading(screen,fxl,fmd,fsm,W,H,"Loading Hipparcos catalog…",0.08)
    with skyload.open(hipparcos.URL) as f:
        df=hipparcos.load_dataframe(f)

    draw_loading(screen,fxl,fmd,fsm,W,H,"Processing star vectors…",0.45)

    sdata={}
    for hip,row in df.iterrows():
        ra=row.get("ra_degrees",float('nan'))
        dec=row.get("dec_degrees",float('nan'))
        mag=row.get("magnitude",float('nan'))
        if any(math.isnan(v) for v in [ra,dec,mag]): continue
        if mag>8.5: continue
        sdata[hip]=(rdxyz(ra,dec), float(mag))

    draw_loading(screen,fxl,fmd,fsm,W,H,f"Indexed {len(sdata):,} stars…",0.72)

    hip_list=list(sdata.keys())
    vec_arr=np.array([sdata[h][0] for h in hip_list])
    mag_arr=np.array([sdata[h][1] for h in hip_list])

    draw_loading(screen,fxl,fmd,fsm,W,H,"Building universe…",0.88)
    bg=build_bg(W,H)
    glow=pygame.Surface((W,H),pygame.SRCALPHA)
    prtcl_layer=pygame.Surface((W,H),pygame.SRCALPHA)

    pmgr=PlanetMgr(); pmgr.start()
    ppos={}; ptimer=0.0

    psys=ParticleSystem()
    aurora_sys=Aurora(W,H)
    trans=ViewTransition()
    toast=Toast()

    draw_loading(screen,fxl,fmd,fsm,W,H,"Ready! Stars await…",1.0)
    pygame.time.wait(350)

    # ── STATE ──────────────────────────────────────────────────────────────────
    yaw,pitch=1.5,0.3; fov=620.0; mlim=5.5
    drag=False; dx0=dy0=0; yaw0=pitch0=0.0
    show_c=True; show_l=True; show_g=False; show_mw=True
    show_n=True; show_dso=True; show_bh=True
    spec=True; twinkle=True; show_hud=True; show_help=False
    show_aurora=False; show_meteors=True; mode=2
    sel_hip=sel_planet=sel_bh=sel_dso=None
    tab_i=0
    named_hips=[h for h in NAMED if h in sdata]
    srch=Search(fmd,fsm)
    tw_t=0.0; hover_planet=hover_bh=None
    clock=pygame.time.Clock()
    frame=0

    running=True
    while running:
        dt=min(clock.tick(60)/1000.0,0.05)
        tw_t+=dt*3.0; frame+=1

        # View transition
        if trans.active:
            ny,np2,done=trans.update(dt)
            yaw=ny; pitch=np2
        R=rotmat(yaw,pitch)

        # Planet refresh
        ptimer+=dt
        if ptimer>18.0 or (not ppos and pmgr.ready):
            ptimer=0.0; pmgr.refresh()
        ppos=pmgr.get()

        # Particles
        psys.update(dt,W,H,show_meteors)
        srch.tick(dt)
        toast.update(dt)

        # ── EVENTS ─────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False

            elif ev.type==pygame.VIDEORESIZE:
                W,H=ev.w,ev.h
                screen=pygame.display.set_mode((W,H),flags)
                glow=pygame.Surface((W,H),pygame.SRCALPHA)
                prtcl_layer=pygame.Surface((W,H),pygame.SRCALPHA)
                bg=build_bg(W,H)
                aurora_sys=Aurora(W,H)

            elif ev.type==pygame.MOUSEWHEEL:
                fov=max(30,min(1500,fov+ev.y*42))
                trans.active=False

            elif ev.type==pygame.MOUSEBUTTONDOWN:
                if not srch.on:
                    if ev.button==1:
                        drag=True; dx0,dy0=ev.pos; yaw0=yaw; pitch0=pitch
                        trans.active=False
                    elif ev.button==3:
                        sel_hip=sel_planet=sel_bh=sel_dso=None

            elif ev.type==pygame.MOUSEBUTTONUP:
                if ev.button==1 and drag:
                    drag=False; mx,my=ev.pos
                    if abs(mx-dx0)+abs(my-dy0)<5:
                        # Click-select
                        best=None; bd=18; sel_hip=sel_planet=sel_bh=sel_dso=None
                        if mode!=1:
                            rv=(R@vec_arr.T).T
                            vis=(rv[:,2]>0.01)&(mag_arr<=mlim)
                            rv_vis=rv[vis]; mi=np.where(vis)[0]
                            if len(rv_vis):
                                f2=fov/rv_vis[:,2]
                                sx2=(rv_vis[:,0]*f2+W/2).astype(int)
                                sy2=(-rv_vis[:,1]*f2+H/2).astype(int)
                                dists=np.sqrt((sx2-mx)**2+(sy2-my)**2)
                                idx=np.argmin(dists)
                                if dists[idx]<bd: bd=dists[idx]; best=("star",hip_list[mi[idx]])
                            # Check DSOs
                            if show_dso:
                                for dname,dra,ddec,ddt,dmag,ddesc in DSOS:
                                    if dmag>mlim+2.5: continue
                                    pp=proj(rdxyz(dra,ddec),R,W,H,fov)
                                    if not pp[0]: continue
                                    d2=math.hypot(mx-pp[0],my-pp[1])
                                    if d2<bd+8: bd=d2; best=("dso",dname)
                        if mode!=0:
                            for name,info in ppos.items():
                                pp=proj(info['xyz'],R,W,H,fov)
                                if not pp[0]: continue
                                d=math.hypot(mx-pp[0],my-pp[1])
                                if d<bd+6: bd=d; best=("planet",name)
                        if show_bh and mode!=1:
                            for bh in BH_LIST:
                                pp=proj(rdxyz(bh[1],bh[2]),R,W,H,fov)
                                if not pp[0]: continue
                                d=math.hypot(mx-pp[0],my-pp[1])
                                if d<bd+8: bd=d; best=("bh",bh[0])
                        if best:
                            t2=best[0]
                            if t2=="star":   sel_hip=best[1]
                            elif t2=="planet": sel_planet=best[1]
                            elif t2=="bh":   sel_bh=best[1]
                            elif t2=="dso":  sel_dso=best[1]

            elif ev.type==pygame.MOUSEMOTION:
                if drag:
                    sens=0.0028*(600/fov)
                    yaw=yaw0+(ev.pos[0]-dx0)*sens
                    pitch=max(-math.pi/2,min(math.pi/2,pitch0-(ev.pos[1]-dy0)*sens))

            elif ev.type==pygame.KEYDOWN:
                if srch.on:
                    if ev.key==pygame.K_ESCAPE: srch.close()
                    elif ev.key==pygame.K_RETURN:
                        h=srch.sel()
                        if h:
                            sel_hip=h; sel_planet=sel_bh=sel_dso=None; srch.close()
                            v=sdata[h][0]
                            ny2=math.atan2(v[1],v[0]); np3=math.asin(max(-1,min(1,v[2])))
                            trans.start(yaw,pitch,ny2,np3,0.9)
                            toast.add(f"Navigating to {NAMED[h][0]}",(0,200,255))
                        else: srch.close()
                    elif ev.key==pygame.K_UP:    srch.cur=max(0,srch.cur-1)
                    elif ev.key==pygame.K_DOWN:  srch.cur=min(len(srch.res)-1,srch.cur+1)
                    elif ev.key==pygame.K_BACKSPACE: srch.q=srch.q[:-1]; srch.update()
                    elif ev.unicode and ev.unicode.isprintable():
                        srch.q+=ev.unicode; srch.update()
                else:
                    k=ev.key
                    if k==pygame.K_ESCAPE:
                        if show_help: show_help=False
                        elif sel_hip or sel_planet or sel_bh or sel_dso:
                            sel_hip=sel_planet=sel_bh=sel_dso=None
                        else: running=False
                    elif k==pygame.K_r:
                        trans.start(yaw,pitch,1.5,0.3,0.7)
                        toast.add("View reset",(0,200,255))
                    elif k==pygame.K_c:
                        show_c=not show_c
                        toast.add(f"Constellations {'ON' if show_c else 'OFF'}",(80,180,255))
                    elif k==pygame.K_l:   show_l=not show_l
                    elif k==pygame.K_g:
                        show_g=not show_g
                        toast.add(f"Grid {'ON' if show_g else 'OFF'}",(80,200,160))
                    elif k==pygame.K_m:
                        show_mw=not show_mw
                        toast.add(f"Milky Way {'ON' if show_mw else 'OFF'}",(200,180,120))
                    elif k==pygame.K_n:   show_n=not show_n
                    elif k==pygame.K_b:
                        spec=not spec
                        toast.add(f"{'Spectral' if spec else 'Monochrome'} colors",(200,200,255))
                    elif k==pygame.K_t:   twinkle=not twinkle
                    elif k==pygame.K_h:   show_help=not show_help
                    elif k==pygame.K_s:   srch.open(); srch.update()
                    elif k==pygame.K_F1:
                        show_dso=not show_dso; show_bh=not show_bh
                        toast.add(f"DSOs + Black Holes {'ON' if show_dso else 'OFF'}",(255,200,80))
                    elif k==pygame.K_p:
                        show_meteors=not show_meteors
                        toast.add(f"Meteor shower {'ON' if show_meteors else 'OFF'}",(255,180,100))
                    elif k==pygame.K_e:
                        show_aurora=not show_aurora
                        toast.add(f"Aurora {'ON' if show_aurora else 'OFF'}",(0,255,150))
                    elif k==pygame.K_F3:
                        fn=f"cosmo_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                        pygame.image.save(screen,fn)
                        toast.add(f"Screenshot saved: {fn}",(100,255,150))
                    elif k in(pygame.K_PLUS,pygame.K_EQUALS,pygame.K_KP_PLUS):
                        mlim=min(8.5,mlim+0.25)
                        toast.add(f"Magnitude limit ≤ {mlim:.1f}",(200,230,255))
                    elif k in(pygame.K_MINUS,pygame.K_KP_MINUS):
                        mlim=max(0.5,mlim-0.25)
                        toast.add(f"Magnitude limit ≤ {mlim:.1f}",(200,230,255))
                    elif k==pygame.K_TAB:
                        if named_hips:
                            tab_i=(tab_i+1)%len(named_hips)
                            sel_hip=named_hips[tab_i]; sel_planet=sel_bh=sel_dso=None
                            v=sdata[sel_hip][0]
                            ny2=math.atan2(v[1],v[0]); np3=math.asin(max(-1,min(1,v[2])))
                            trans.start(yaw,pitch,ny2,np3,0.75)
                            toast.add(f"{NAMED[sel_hip][0]}  ·  {NAMED[sel_hip][3]}",(spcol(NAMED[sel_hip][2])))
                    elif k==pygame.K_1:
                        mode=0; toast.add("Mode: Stars only",(0,215,255))
                    elif k==pygame.K_2:
                        mode=1; toast.add("Mode: Solar system only",(90,255,140))
                    elif k==pygame.K_3:
                        mode=2; toast.add("Mode: Stars + Solar system",(255,215,90))

        # WASD
        if not srch.on and not trans.active:
            keys=pygame.key.get_pressed(); spd=0.011*(600/fov)
            if keys[pygame.K_a]: yaw-=spd
            if keys[pygame.K_d]: yaw+=spd
            if keys[pygame.K_w]: pitch=min(math.pi/2,pitch+spd)
            if keys[pygame.K_s]: pitch=max(-math.pi/2,pitch-spd)

        # ── RENDER ─────────────────────────────────────────────────────────────
        screen.blit(bg,(0,0))

        if show_aurora: aurora_sys.draw(screen,tw_t)
        if show_mw:     draw_milky_way(screen,R,W,H,fov,tw_t)
        if show_g:      draw_grid(screen,R,W,H,fov,fsm)
        if show_c and mode!=1:
            draw_constellations(screen,sdata,R,W,H,fov,show_l,fsm,sel_hip,tw_t)
        if show_dso and mode!=1:
            draw_dsos(screen,R,W,H,fov,fsm,mlim,tw_t)

        # ── GLOW LAYER ─────────────────────────────────────────────────────────
        glow.fill((0,0,0,0))
        vis_count=0
        star_screen={}
        hover_hip=None; bhd=16
        mx0,my0=pygame.mouse.get_pos()

        # ── BATCH STAR PROJECTION ───────────────────────────────────────────────
        if mode!=1:
            rv_all=(R@vec_arr.T).T
            vis_mask=(rv_all[:,2]>0.01)&(mag_arr<=mlim)
            rv_vis=rv_all[vis_mask]
            hi_vis=np.array(hip_list)[vis_mask]
            ma_vis=mag_arr[vis_mask]

            f_arr=fov/rv_vis[:,2]
            sx_arr=(rv_vis[:,0]*f_arr+W/2).astype(int)
            sy_arr=(-rv_vis[:,1]*f_arr+H/2).astype(int)

            on_screen=(sx_arr>=0)&(sx_arr<W)&(sy_arr>=0)&(sy_arr<H)
            sx_arr=sx_arr[on_screen]; sy_arr=sy_arr[on_screen]
            hi_vis=hi_vis[on_screen]; ma_vis=ma_vis[on_screen]
            vis_count=len(sx_arr)

            if vis_count:
                d2=(sx_arr-mx0)**2+(sy_arr-my0)**2
                ci=np.argmin(d2)
                if d2[ci]<bhd**2: hover_hip=int(hi_vis[ci])

            for i in range(vis_count):
                sx3,sy3=int(sx_arr[i]),int(sy_arr[i])
                mag=float(ma_vis[i]); hip=int(hi_vis[i])

                # Twinkling
                tw=1.0
                if twinkle and mag>1.2:
                    tw=0.82+0.18*math.sin(tw_t*1.3+(hip%97)*0.67+mag*0.5)

                # Color
                if spec and hip in NAMED:
                    col=spcol(NAMED[hip][2])
                    col=tuple(int(c*tw) for c in col)
                else:
                    br=int(max(70,min(255,(260-mag*30)*tw)))
                    col=(br,br,min(255,br+15))

                # Size
                if mag<-0.5: sz=7
                elif mag<0.5: sz=6
                elif mag<1.5: sz=4
                elif mag<2.5: sz=3
                elif mag<4.0: sz=2
                else: sz=1

                is_sel=(hip==sel_hip)

                # Diffraction spikes for brightest stars
                if mag<1.5 and sz>=4:
                    spike_len=int((2.5-mag)*14)
                    for ang in [0,math.pi/2]:
                        ex=int(math.cos(ang)*spike_len); ey=int(math.sin(ang)*spike_len)
                        for si in range(spike_len,0,-1):
                            sa=int(80*(si/spike_len)**2*tw)
                            pygame.draw.circle(screen,(*col[:3],sa),
                                (sx3+int(math.cos(ang)*si),sy3+int(math.sin(ang)*si)),1)
                            pygame.draw.circle(screen,(*col[:3],sa),
                                (sx3-int(math.cos(ang)*si),sy3-int(math.sin(ang)*si)),1)

                # Star glow
                if mag<3.0:
                    for ri in range(sz+8,0,-1):
                        a=int(65*((1-ri/(sz+8))**2)*tw)
                        pygame.draw.circle(glow,(*col[:3],a),(sx3,sy3),ri)

                pygame.draw.circle(screen,col,(sx3,sy3),sz)

                if is_sel:
                    pulse=0.6+0.4*math.sin(tw_t*4)
                    pygame.draw.circle(screen,(255,210,110),(sx3,sy3),sz+int(8+3*pulse),2)
                    pygame.draw.circle(screen,(255,255,255),(sx3,sy3),sz+18,1)
                    # Crosshair
                    for ang in [0,math.pi/2,math.pi,3*math.pi/2]:
                        x1=sx3+int(math.cos(ang)*(sz+20))
                        y1=sy3+int(math.sin(ang)*(sz+20))
                        x2=sx3+int(math.cos(ang)*(sz+28))
                        y2=sy3+int(math.sin(ang)*(sz+28))
                        pygame.draw.line(screen,(255,210,110),(x1,y1),(x2,y2),2)

                if show_n and hip in NAMED and mag<2.0:
                    c=spcol(NAMED[hip][2]) if spec else (175,210,255)
                    blit_text(screen,fsm,NAMED[hip][0],sx3+sz+4,sy3-6,c)

                star_screen[hip]=(sx3,sy3)

        # Planets
        if mode!=0:
            hover_planet=draw_planets(screen,glow,ppos,R,W,H,fov,sel_planet,fsm,fmd,tw_t)
        else:
            hover_planet=None

        # Black holes
        if show_bh and mode!=1:
            hover_bh=draw_bhs(screen,glow,R,W,H,fov,fsm,fmd,tw_t,sel_bh)
        else:
            hover_bh=None

        # Particles
        prtcl_layer.fill((0,0,0,0))
        psys.draw(prtcl_layer)
        screen.blit(prtcl_layer,(0,0))
        screen.blit(glow,(0,0))

        # ── TOOLTIPS ───────────────────────────────────────────────────────────
        if hover_hip and hover_hip!=sel_hip and mode!=1:
            sx4,sy4=star_screen.get(hover_hip,(0,0))
            _,mag=sdata[hover_hip]
            if hover_hip in NAMED:
                info=NAMED[hover_hip]
                ds=f"  {info[4]:,.0f} ly" if len(info)>4 and info[4]>0 else ""
                lbl=f"{info[0]}  {info[1]}  mag {mag:.2f}  {info[2]}{ds}"
                lcol=spcol(info[2]) if spec else (210,237,255)
            else:
                lbl=f"HIP {hover_hip}  mag {mag:.2f}"; lcol=(200,222,252)
            tw2=fmd.size(lbl)[0]+18; tx=min(sx4+15,W-tw2-5); ty=max(sy4-26,5)
            draw_panel(screen,tx,ty,tw2,26,alpha=210,border=(0,90,200))
            blit_text(screen,fmd,lbl,tx+8,ty+5,lcol)

        if hover_planet and hover_planet!=sel_planet and mode!=0:
            info=ppos.get(hover_planet,{}); col=info.get('color',(180,180,180))
            lbl=f"{hover_planet}  ·  {info.get('dist',0):.4f} AU  ·  {info.get('desc','')}"
            tw2=fmd.size(lbl)[0]+18; tx=min(mx0+16,W-tw2-5); ty=max(my0-26,5)
            draw_panel(screen,tx,ty,tw2,26,alpha=210,border=col)
            blit_text(screen,fmd,lbl,tx+8,ty+5,col)

        if hover_bh and hover_bh!=sel_bh:
            bh=next((b for b in BH_LIST if b[0]==hover_bh),None)
            if bh:
                col=(255,210,50)
                ds=f"{bh[5]/1e6:.1f}M ly" if bh[5]>1e5 else f"{bh[5]:,} ly"
                lbl=f"{bh[0]}  ·  {bh[3]}  ·  {ds}"
                tw2=fmd.size(lbl)[0]+18; tx=min(mx0+16,W-tw2-5); ty=max(my0-26,5)
                draw_panel(screen,tx,ty,tw2,26,alpha=210,border=col)
                blit_text(screen,fmd,lbl,tx+8,ty+5,col)

        # Info panels
        if sel_hip and sel_hip in sdata and mode!=1:
            draw_star_info(screen,flg,fmd,fsm,sel_hip,sdata,W,H)
        if sel_planet and sel_planet in ppos and mode!=0:
            draw_planet_info(screen,flg,fmd,fsm,sel_planet,ppos[sel_planet],W,H)
        if sel_bh:
            draw_bh_info(screen,flg,fmd,fsm,sel_bh,W,H)
        if sel_dso:
            draw_dso_info(screen,flg,fmd,fsm,sel_dso,W,H)

        # HUD
        if show_hud:
            draw_hud(screen,fxl,flg,fmd,fsm,W,H,len(sdata),vis_count,fov,yaw,pitch,
                     mlim,spec,twinkle,mode,len(ppos) if mode!=0 else 0,show_aurora,show_meteors)

        if show_help:
            draw_help(screen,flg,fmd,fsm,W,H)

        srch.draw(screen,W,H)
        toast.draw(screen,fsm,W,H)

        if not pmgr.ready:
            blit_text(screen,fsm,f"⚙  {pmgr.status}",10,H-42,(80,130,190))

        # FOV mini arc indicator (bottom right)
        fovd=math.degrees(math.atan(fov/500)*2)
        cx,cy=W-32,H-32
        pygame.draw.arc(screen,(22,60,130),(cx-20,cy-20,40,40),
                        math.radians(270-fovd*1.6),math.radians(270),2)
        pygame.draw.arc(screen,(0,140,255),(cx-20,cy-20,40,40),
                        math.radians(270-min(fovd*1.6,270)),math.radians(270),2)
        blit_text(screen,fsm,f"{fovd:.0f}°",cx-12,cy-6,(50,100,160))

        pygame.display.flip()

if __name__=="__main__":
    print(__doc__)
    main()