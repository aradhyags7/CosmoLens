"""
[V] Flat ↔ Globe   [SPACE] Pause   [S] Search   [H] Help   [ESC] Quit
[1-9] Time warp    [R] Reset       [E] Export   [F3] Screenshot
[F] Footprint  [O] Orbit  [T] Trails  [G] Grid  [N] Names  [C] Cities
[F1] Night  [F2] Terminator  [+/-] Trail length  [TAB] Next satellite
"""
import pygame, math, time, threading, requests, datetime, csv, os, sys, random, json
import numpy as np
from sgp4.api import Satrec, jday

# ── CONFIG ────────────────────────────────────────────────────────────────────
W0, H0        = 1440, 820
FPS           = 60
EARTH_R       = 6371.0
MAX_TRAIL     = 120
VIEW_FLAT     = 0
VIEW_GLOBE    = 1

WARP_LEVELS   = [1, 2, 5, 10, 30, 60, 300, 1800, 3600]
WARP_LABELS   = ["1×","2×","5×","10×","30×","1m/s","5m/s","30m/s","1h/s"]

TLE_SOURCES = {
    "ISS/CSS":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "Starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "GPS":      "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle",
    "Galileo":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle",
    "GLONASS":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=glonass&FORMAT=tle",
    "BeiDou":   "https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle",
    "Iridium":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle",
    "Weather":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
    "Science":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
    "OneWeb":   "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
    "Amateur":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle",
    "Debris":   "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-1408-debris&FORMAT=tle",
}
# Increased limits for more satellites
MAX_PER = {
    "ISS/CSS": 8, "Starlink": 350, "GPS": 32, "Galileo": 36, "GLONASS": 30,
    "BeiDou": 50, "Iridium": 75, "Weather": 40, "Science": 40,
    "OneWeb": 80, "Amateur": 50, "Debris": 200,
}

SAT_COLORS = {
    "ISS/CSS":(255,215,0),"Starlink":(0,190,255),"GPS":(0,255,140),
    "Galileo":(80,220,255),"GLONASS":(255,100,220),"BeiDou":(255,165,50),
    "Iridium":(180,255,100),"Weather":(255,255,120),"Science":(200,160,255),
    "OneWeb":(100,200,255),"Amateur":(160,255,200),"Debris":(160,70,70),
    "Other":(140,140,160),
}
FAMOUS_KEYS = ["iss","zarya","tianhe","hubble","terra","aqua","suomi","noaa","envisat"]

# ── NATURAL EARTH COASTLINES ──────────────────────────────────────────────────
NE_CACHE = "ne_110m_land_cache.json"
NE_URL   = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"

def fetch_natural_earth():
    """Download + cache Natural Earth 110m land polygons. Returns list of (lat,lon) segments."""
    if os.path.exists(NE_CACHE):
        try:
            with open(NE_CACHE) as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 20:
                print(f"[NE] Loaded {len(data)} land segments from cache.")
                return data
        except Exception:
            pass
    print("[NE] Downloading Natural Earth 110m land data (cached after first run)…")
    try:
        r = requests.get(NE_URL, timeout=30); r.raise_for_status()
        gj = r.json(); segs = []
        for feat in gj.get("features", []):
            geom = feat.get("geometry", {})
            gtype = geom.get("type", ""); coords = geom.get("coordinates", [])
            def add_ring(ring):
                seg = [(float(c[1]), float(c[0])) for c in ring if len(c) >= 2]
                if len(seg) >= 3:
                    segs.append(seg)
            if gtype == "Polygon":
                for ring in coords: add_ring(ring)
            elif gtype == "MultiPolygon":
                for poly in coords:
                    for ring in poly: add_ring(ring)
        with open(NE_CACHE, "w") as f:
            json.dump(segs, f, separators=(",",":"))
        print(f"[NE] Cached {len(segs)} land segments.")
        return segs
    except Exception as e:
        print(f"[NE] Download failed ({e}). Using built-in fallback.")
        return None

def split_antimeridian(coast):
    """Split a (lat,lon) segment at the antimeridian to avoid rendering artifacts."""
    if len(coast) < 2:
        return [coast]
    segs, cur = [], [coast[0]]
    for i in range(1, len(coast)):
        if abs(coast[i][1] - coast[i-1][1]) > 180:
            if len(cur) >= 2: segs.append(cur)
            cur = [coast[i]]
        else:
            cur.append(coast[i])
    if cur: segs.append(cur)
    return segs if segs else [coast]

# ── BUILT-IN FALLBACK COASTLINES (simplified, used if NE download fails) ──────
COASTLINES_BUILTIN = [
    [(71,-141),(68,-166),(64,-162),(60,-147),(58,-137),(55,-132),(50,-127),
     (48,-124),(42,-124),(37,-122),(32,-117),(28,-110),(22,-97),(18,-88),
     (14,-87),(10,-83),(8,-77),(10,-75),(18,-66),(23,-82),(25,-80),(30,-81),
     (35,-75),(40,-74),(42,-70),(44,-67),(47,-54),(52,-56),(57,-61),(62,-64),
     (65,-83),(68,-84),(70,-86),(71,-90),(72,-100),(72,-114),(72,-130),(71,-141)],
    [(60,-141),(62,-144),(66,-164),(65,-168),(62,-162),(58,-152),(55,-162),(56,-158),(58,-156),(60,-148),(60,-141)],
    [(12,-72),(8,-60),(4,-52),(0,-50),(-5,-35),(-10,-37),(-15,-39),(-22,-43),
     (-26,-48),(-33,-52),(-38,-58),(-42,-64),(-50,-68),(-54,-65),(-55,-68),
     (-50,-75),(-42,-74),(-36,-72),(-26,-70),(-18,-70),(-15,-75),(-8,-79),(0,-80),(4,-77),(8,-77),(10,-72)],
    [(60,5),(54,8),(54,12),(55,14),(57,10),(59,11),(60,5),(58,4),(52,4),
     (50,2),(46,-2),(43,-2),(42,3),(40,0),(36,-5),(36,-7),(38,-9),(40,-8),(42,-9),(44,-2),(44,4),(43,5),(41,1)],
    [(71,28),(68,18),(65,13),(62,6),(60,5),(58,5),(56,8),(54,10),(55,14),
     (54,18),(56,21),(57,24),(60,22),(62,22),(65,25),(66,26),(68,17),(70,20),(71,28)],
    [(50,-5),(51,-1),(53,1),(55,-2),(57,-4),(58,-5),(57,-6),(54,-6),(53,-4),(52,-5),(50,-5)],
    [(37,10),(33,12),(32,25),(30,33),(28,34),(24,38),(15,42),(12,44),(12,52),
     (5,41),(0,42),(-5,39),(-11,40),(-18,35),(-22,35),(-26,33),(-34,26),
     (-35,18),(-28,17),(-20,13),(-15,12),(-8,13),(-4,8),(0,4),(5,2),(6,1),
     (4,-5),(5,-9),(4,-13),(8,-17),(15,-17),(18,-16),(20,-17),(25,-15),(34,-12),(37,11),(37,10)],
    [(71,30),(68,40),(60,40),(55,37),(52,33),(50,30),(47,38),(42,45),(40,50),
     (38,55),(32,60),(25,62),(20,58),(12,45),(12,52),(5,41),(0,42),(0,37),
     (5,34),(8,36),(12,43),(20,58),(24,57),(28,55),(30,48),(32,38),(34,36),
     (38,36),(40,36),(40,40),(42,45),(44,42),(48,38),(50,30)],
    [(71,140),(68,142),(64,140),(60,130),(56,134),(52,141),(50,142),(50,135),
     (44,130),(40,122),(34,120),(28,120),(22,114),(10,104),(0,104),
     (-4,108),(-8,112),(-8,114),(-4,110),(0,100),(6,100),(10,100),(14,102),
     (16,100),(20,106),(24,110),(28,120),(30,122),(34,120),(40,122),(44,130),
     (50,135),(54,138),(58,130),(60,130),(64,140),(68,142),(71,140)],
    [(-14,128),(-12,130),(-14,136),(-12,141),(-14,142),(-18,148),(-22,150),
     (-26,152),(-28,154),(-32,152),(-36,150),(-38,147),(-36,140),(-32,132),(-28,114),(-22,114),(-18,122),(-14,128)],
    [(76,-18),(80,-18),(82,-20),(83,-34),(80,-52),(76,-68),(72,-56),(65,-40),(66,-38),(68,-18),(72,-18),(76,-18)],
    [(-70,-180),(-72,-150),(-74,-120),(-72,-90),(-70,-60),(-72,-30),(-74,0),(-72,30),(-70,60),(-72,90),(-74,120),(-72,150),(-70,180)],
]

COASTLINES = COASTLINES_BUILTIN  # overridden at startup if NE download succeeds

GEO_LINES = [
    (23.4,  "Tropic of Cancer",    (50,100,70)),
    (-23.4, "Tropic of Capricorn", (50,100,70)),
    (66.6,  "Arctic Circle",       (50,100,160)),
    (-66.6, "Antarctic Circle",    (50,100,160)),
    (0,     "Equator",             (60,130,90)),
]

CITIES = [
    (40.7,-74.0,"New York",3),(51.5,-0.1,"London",3),(48.9,2.3,"Paris",3),
    (55.8,37.6,"Moscow",3),(35.7,139.7,"Tokyo",3),(39.9,116.4,"Beijing",3),
    (31.2,121.5,"Shanghai",3),(28.6,77.2,"Delhi",2),(19.1,72.9,"Mumbai",2),
    (-23.6,-46.6,"São Paulo",2),(34.1,-118.2,"Los Angeles",2),(41.9,12.5,"Rome",2),
    (52.5,13.4,"Berlin",2),(-33.9,151.2,"Sydney",2),(1.3,103.8,"Singapore",2),
    (25.2,55.3,"Dubai",2),(-26.2,28.0,"Johannesburg",2),(30.0,31.2,"Cairo",2),
    (6.5,3.4,"Lagos",2),(-34.6,-58.4,"Buenos Aires",2),(19.4,-99.1,"Mexico City",2),
    (28.6,-80.6,"Cape Canaveral",3),(45.9,63.3,"Baikonur",3),(31.1,121.2,"Jiuquan",3),
    (59.9,30.3,"St. Petersburg",1),(22.3,114.2,"Hong Kong",2),(-1.3,36.8,"Nairobi",1),
    (37.6,-122.4,"San Francisco",1),(41.8,-87.6,"Chicago",1),(43.7,-79.4,"Toronto",1),
    (55.7,12.6,"Copenhagen",1),(59.3,18.1,"Stockholm",1),(48.2,16.4,"Vienna",1),
    (50.1,14.4,"Prague",1),(52.2,21.0,"Warsaw",1),(47.5,19.1,"Budapest",1),
    (-33.9,-70.7,"Santiago",1),(-12.0,-77.0,"Lima",1),(4.6,-74.1,"Bogotá",1),
    (33.7,-84.4,"Atlanta",1),(29.8,-95.4,"Houston",1),(33.4,-112.1,"Phoenix",1),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def draw_text(surf, font, text, x, y, color=(220,240,255), shadow=True):
    if shadow:
        surf.blit(font.render(text, True, (0,0,0)), (x+1, y+1))
    t = font.render(text, True, color)
    surf.blit(t, (x, y))
    return t.get_width()

def draw_panel(surf, rx, ry, rw, rh, alpha=210, border=(0,120,200), hdr=None):
    s = pygame.Surface((rw, rh), pygame.SRCALPHA)
    s.fill((2, 8, 22, alpha))
    surf.blit(s, (rx, ry))
    pygame.draw.rect(surf, border, (rx, ry, rw, rh), 1)
    if hdr:
        h = pygame.Surface((rw-2, 26), pygame.SRCALPHA)
        h.fill((*hdr, 40))
        surf.blit(h, (rx+1, ry+1))

class Fonts:
    def __init__(self):
        pygame.font.init()
        self.xl  = pygame.font.SysFont("Courier New", 22, bold=True)
        self.lg  = pygame.font.SysFont("Courier New", 14, bold=True)
        self.md  = pygame.font.SysFont("Courier New", 12)
        self.sm  = pygame.font.SysFont("Courier New", 10)
        self.xs  = pygame.font.SysFont("Courier New", 9)
        self.btn = pygame.font.SysFont("Arial", 13, bold=True)

# ── SUN ───────────────────────────────────────────────────────────────────────
def get_sun_pos(dt):
    n = (dt - datetime.datetime(2000,1,1,12)).total_seconds()/86400.0
    L = (280.460 + 0.9856474*n) % 360
    g = math.radians((357.528 + 0.9856003*n) % 360)
    lam = math.radians(L + 1.915*math.sin(g) + 0.020*math.sin(2*g))
    eps = math.radians(23.439 - 0.0000004*n)
    ra  = math.atan2(math.cos(eps)*math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps)*math.sin(lam))
    ut  = dt.hour + dt.minute/60 + dt.second/3600
    gmst = (6.697375 + 0.0657098242*n + ut) % 24 * 15
    lon = math.degrees(ra) - gmst
    lon = ((lon+180) % 360) - 180
    return math.degrees(dec), lon

# ── NIGHT OVERLAY ─────────────────────────────────────────────────────────────
class NightCache:
    _flat_surf=None; _flat_key=None
    _globe_surf=None; _globe_key=None

    @staticmethod
    def flat(W, H, zoom, ox, oy, sun_lat, sun_lon, step=6):
        key = (round(sun_lat,1), round(sun_lon,1), round(zoom,2), round(ox,0), round(oy,0))
        if key == NightCache._flat_key and NightCache._flat_surf:
            return NightCache._flat_surf
        sw, sh = W//step+2, H//step+2
        lon_arr = ((np.arange(sw)*step - ox) / (W*zoom)) * 360 - 180
        lat_arr = 90 - ((np.arange(sh)*step - oy) / (H*zoom)) * 180
        lonG, latG = np.meshgrid(lon_arr, lat_arr)
        slr = math.radians(sun_lat); sln = math.radians(sun_lon)
        lr = np.radians(latG); ln = np.radians(lonG)
        dot = np.sin(lr)*math.sin(slr) + np.cos(lr)*np.cos(slr)*np.cos(ln-sln)
        alpha = np.zeros((sh, sw), dtype=np.uint8)
        night = (dot < 0); twi = (dot >= 0) & (dot < 0.08)
        alpha[night] = np.clip(150*np.sqrt(-dot[night]), 0, 150).astype(np.uint8)
        alpha[twi] = 10
        ns = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pxa = pygame.surfarray.pixels3d(ns)
        pxa[:,:,:] = np.array([0, 0, 20], dtype=np.uint8)
        del pxa
        av = pygame.surfarray.pixels_alpha(ns)
        av[:] = alpha.T
        del av
        full = pygame.transform.scale(ns, (W, H))
        NightCache._flat_surf = full; NightCache._flat_key = key
        return full

    @staticmethod
    def globe(R, cx, cy, lon_off, tilt, sun_lat, sun_lon, W, H):
        key = (round(lon_off,1), round(tilt,2), round(sun_lat,1), round(sun_lon,1), R)
        if key == NightCache._globe_key and NightCache._globe_surf:
            return NightCache._globe_surf
        step=4; size=R*2; n=size//step+2
        c = np.arange(n, dtype=np.float32)*step
        xx, yy = np.meshgrid(c, c)
        xn = (xx-R)/R; yn = -(yy-R)/R
        on_sph = (xn*xn + yn*yn) <= 1.0
        zs = np.sqrt(np.maximum(0.0, 1-xn*xn-yn*yn))
        ct = math.cos(tilt); st = math.sin(tilt)
        yw = yn*ct + zs*st; zw = (-yn)*st + zs*ct
        lat_r = np.arcsin(np.clip(yw, -1, 1))
        lon_r = np.arctan2(xn, zw) - math.radians(lon_off)
        slr = math.radians(sun_lat); sln = math.radians(sun_lon)
        dot = np.sin(lat_r)*math.sin(slr) + np.cos(lat_r)*np.cos(slr)*np.cos(lon_r-sln)
        alpha = np.zeros((n, n), dtype=np.uint8)
        night = on_sph & (dot < 0); twi = on_sph & (dot >= 0) & (dot < 0.08)
        alpha[night] = np.clip(150*np.sqrt(-dot[night]), 0, 150).astype(np.uint8)
        alpha[twi] = 10
        ns = pygame.Surface((n, n), pygame.SRCALPHA)
        ns.fill((0, 0, 20))
        pygame.surfarray.pixels_alpha(ns)[:] = alpha.T
        full = pygame.transform.scale(ns, (size, size))
        NightCache._globe_surf = full; NightCache._globe_key = key
        return full

# ── FLAT MAP (pre-baked texture) ──────────────────────────────────────────────
class FlatMap:
    def __init__(self, w, h):
        self.w = w; self.h = h; self._surf = None
        self._build()

    def _px(self, lat, lon):
        return int((lon+180)/360*self.w), int((90-lat)/180*self.h)

    def _build(self):
        s = pygame.Surface((self.w, self.h))
        # Ocean gradient
        for y in range(self.h):
            c = lerp_color((2,14,44), (1,8,26), y/self.h)
            pygame.draw.line(s, c, (0,y), (self.w,y))
        # Subtle latitude banding
        bs = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for lat in range(-80, 81, 10):
            yp = int((90-lat)/180*self.h)
            pygame.draw.line(bs, (0,30,80, 3+abs(lat)//8), (0,yp), (self.w,yp))
        s.blit(bs, (0,0))

        # Draw land from COASTLINES (NE data or fallback)
        # Pass 1: fill
        for coast in COASTLINES:
            sub_segs = split_antimeridian(coast)
            for seg in sub_segs:
                pts = [self._px(la, lo) for la, lo in seg]
                if len(pts) > 2:
                    pygame.draw.polygon(s, (16, 38, 64), pts)

        # Pass 2: better fill + coastline glow
        gl = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for coast in COASTLINES:
            sub_segs = split_antimeridian(coast)
            for seg in sub_segs:
                pts = [self._px(la, lo) for la, lo in seg]
                if len(pts) > 2:
                    pygame.draw.polygon(s, (22, 46, 76), pts)
                    pygame.draw.lines(s, (40, 72, 115), True, pts, 1)
                if len(pts) > 1:
                    pygame.draw.lines(gl, (55, 110, 168, 38), False, pts, 3)
                    pygame.draw.lines(gl, (75, 150, 210, 18), False, pts, 6)
        s.blit(gl, (0,0))

        # Geo reference lines
        for lat, _, col in GEO_LINES:
            yp = int((90-lat)/180*self.h)
            if lat == 0:
                pygame.draw.line(s, (25, 65, 55), (0, yp), (self.w, yp), 1)
            else:
                for x in range(0, self.w, 10):
                    pygame.draw.line(s, col, (x, yp), (min(x+5, self.w), yp))
        self._surf = s

    def get_scaled(self, zoom, ox, oy):
        sw, sh = int(self.w*zoom), int(self.h*zoom)
        return pygame.transform.smoothscale(self._surf, (sw, sh)), (int(ox), int(oy))

# ── GLOBE RENDERER ────────────────────────────────────────────────────────────
class Globe:
    def __init__(self, W, H):
        self.W=W; self.H=H
        self.cx=W//2; self.cy=H//2+10
        self.R=min(W,H)//2-55
        self.lon_off=0.0; self.tilt=0.2; self.zoom=1.0
        self._stars=None
        self._make_stars(); self._bake_land()

    @property
    def R2(self): return int(self.R*self.zoom)

    def _make_stars(self):
        s = pygame.Surface((self.W, self.H)); s.fill((0, 0, 5))
        rng = random.Random(42)
        for _ in range(3500):
            x = rng.randint(0, self.W-1); y = rng.randint(0, self.H-1)
            b = rng.randint(30, 220); sz = rng.choices([1,2,3], weights=[72,23,5])[0]
            pygame.draw.circle(s, (b, b, min(255, b+20)), (x, y), sz)
        self._stars = s

    def _bake_land(self):
        """Convert COASTLINES to numpy arrays for fast batch projection."""
        self._coast_arrays = []
        for coast in COASTLINES:
            arr = np.array(coast, dtype=np.float32)  # shape (N,2): lat,lon
            if len(arr) >= 2:
                self._coast_arrays.append(arr)

    def project(self, lat, lon):
        R = self.R2
        lr = math.radians(lat); ln = math.radians(lon + self.lon_off)
        x = math.cos(lr)*math.sin(ln)
        y = math.sin(lr)
        z = math.cos(lr)*math.cos(ln)
        ct = math.cos(self.tilt); st = math.sin(self.tilt)
        y2 = y*ct - z*st; z2 = y*st + z*ct
        if z2 < -0.04: return None, None, -1
        return self.cx + int(x*R), self.cy - int(y2*R), z2

    def project_batch(self, lat_arr, lon_arr):
        R = self.R2
        lr = np.radians(lat_arr); ln = np.radians(lon_arr + self.lon_off)
        x = np.cos(lr)*np.sin(ln)
        y = np.sin(lr)
        z = np.cos(lr)*np.cos(ln)
        ct = math.cos(self.tilt); st = math.sin(self.tilt)
        y2 = y*ct - z*st; z2 = y*st + z*ct
        sx = (self.cx + x*R).astype(int)
        sy = (self.cy - y2*R).astype(int)
        return sx, sy, z2

    def draw_stars(self, surf): surf.blit(self._stars, (0,0))

    def draw_ocean(self, surf):
        R=self.R2; cx=self.cx; cy=self.cy
        atm = pygame.Surface((R*2+50, R*2+50), pygame.SRCALPHA)
        for ri in range(R+22, R, -2):
            prog = (ri-R)/22
            a = int(55*prog*(1-prog)*4)
            pygame.draw.circle(atm, (40,100,255,min(a,55)), (R+25,R+25), ri, 2)
        surf.blit(atm, (cx-R-25, cy-R-25))
        pygame.draw.circle(surf, (3,14,50), (cx,cy), R)

    def draw_land(self, surf):
        land = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for arr in self._coast_arrays:
            lat_a = arr[:,0]; lon_a = arr[:,1]
            sx, sy, z2 = self.project_batch(lat_a, lon_a)
            visible = z2 >= 0
            cur = []
            for i in range(len(visible)):
                if visible[i]:
                    cur.append((int(sx[i]), int(sy[i])))
                else:
                    if len(cur) > 2:
                        pygame.draw.polygon(land, (20, 44, 70), cur)
                    if len(cur) > 1:
                        pygame.draw.lines(land, (38, 70, 108), False, cur, 1)
                    cur = []
            if len(cur) > 2:
                pygame.draw.polygon(land, (20, 44, 70), cur)
            if len(cur) > 1:
                pygame.draw.lines(land, (38, 70, 108), False, cur, 1)
        # Coastline glow
        for arr in self._coast_arrays:
            lat_a = arr[:,0]; lon_a = arr[:,1]
            sx, sy, z2 = self.project_batch(lat_a, lon_a)
            visible = z2 >= 0; cur = []
            for i in range(len(visible)):
                if visible[i]:
                    cur.append((int(sx[i]), int(sy[i])))
                elif len(cur) > 1:
                    pygame.draw.lines(glow, (55,115,175,32), False, cur, 4)
                    cur = []
            if len(cur) > 1:
                pygame.draw.lines(glow, (55,115,175,32), False, cur, 4)
        land.blit(glow, (0,0))
        surf.blit(land, (0,0))

    def draw_grid(self, surf):
        gs = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for lat in range(-80, 81, 20):
            lon_a = np.arange(-180, 182, 4, dtype=np.float32)
            lat_a = np.full_like(lon_a, lat)
            sx, sy, z2 = self.project_batch(lat_a, lon_a)
            pts = [(int(sx[i]),int(sy[i])) for i in range(len(z2)) if z2[i]>0]
            if len(pts)>1: pygame.draw.lines(gs, (255,255,255,13), False, pts, 1)
        for lon in range(-180, 181, 30):
            lat_a = np.arange(-88, 89, 3, dtype=np.float32)
            lon_a = np.full_like(lat_a, lon)
            sx, sy, z2 = self.project_batch(lat_a, lon_a)
            pts = [(int(sx[i]),int(sy[i])) for i in range(len(z2)) if z2[i]>0]
            if len(pts)>1: pygame.draw.lines(gs, (255,255,255,13), False, pts, 1)
        # Equator highlight
        lon_a = np.arange(-180, 182, 2, dtype=np.float32)
        lat_a = np.zeros_like(lon_a)
        sx, sy, z2 = self.project_batch(lat_a, lon_a)
        pts = [(int(sx[i]),int(sy[i])) for i in range(len(z2)) if z2[i]>0]
        if len(pts)>1: pygame.draw.lines(gs, (60,135,90,50), False, pts, 1)
        surf.blit(gs, (0,0))

    def draw_terminator(self, surf, sun_lat, sun_lon):
        slr = math.radians(sun_lat); sln = math.radians(sun_lon)
        ts = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        lon_d = np.arange(-180, 182, 2, dtype=np.float32)
        denom = math.sin(slr)
        if abs(denom) > 1e-6:
            dlon = np.radians(lon_d) - sln
            lat_t = np.degrees(np.arctan(-np.cos(slr)*np.cos(dlon)/denom))
        else:
            lat_t = np.full_like(lon_d, 90 if sun_lat>0 else -90)
        sx, sy, z2 = self.project_batch(lat_t, lon_d)
        pts = [(int(sx[i]),int(sy[i])) for i in range(len(z2)) if z2[i]>0]
        if len(pts)>1: pygame.draw.lines(ts, (255,210,50,65), False, pts, 2)
        surf.blit(ts, (0,0))
        sx2, sy2, z2_ = self.project(sun_lat, sun_lon)
        if sx2 and z2_>0:
            gs = pygame.Surface((30,30), pygame.SRCALPHA)
            for ri in range(13,0,-1):
                pygame.draw.circle(gs, (255,220,80,int(80*(1-ri/13)**1.5)), (15,15), ri)
            pygame.draw.circle(gs, (255,240,120), (15,15), 4)
            surf.blit(gs, (sx2-15, sy2-15))

    def draw_atmosphere(self, surf):
        R=self.R2; cx=self.cx; cy=self.cy
        fs = pygame.Surface((R*2+40, R*2+40), pygame.SRCALPHA)
        for ri in range(R+16, R-1, -2):
            prog = (ri-R)/16; a = int(70*math.sin(math.pi*prog))
            pygame.draw.circle(fs, (50,120,255,min(a,60)), (R+20,R+20), ri, 2)
        pygame.draw.circle(fs, (20,50,180,25), (R+20,R+20), R, 3)
        surf.blit(fs, (cx-R-20, cy-R-20))
        sr = R//4; ss = pygame.Surface((sr*2, sr*2), pygame.SRCALPHA)
        for ri in range(sr, 0, -1):
            pygame.draw.circle(ss, (255,255,255,int(16*(1-ri/sr)**1.2)), (sr,sr), ri)
        surf.blit(ss, (cx-int(R*0.3)-sr, cy-int(R*0.3)-sr))

    def draw_orbit(self, surf, pts_ll, color):
        vs = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        if len(pts_ll) < 2: return
        lats = np.array([p[0] for p in pts_ll], dtype=np.float32)
        lons = np.array([p[1] for p in pts_ll], dtype=np.float32)
        sx, sy, z2 = self.project_batch(lats, lons)
        prev = None; prev_lon = None
        for i in range(len(pts_ll)):
            if z2[i] > 0:
                pt = (int(sx[i]), int(sy[i]))
                if prev and abs(lons[i]-prev_lon) < 180:
                    pygame.draw.line(vs, (*color[:3],105), prev, pt, 2)
                prev = pt; prev_lon = lons[i]
            else:
                prev = None
        surf.blit(vs, (0,0))

    def draw_footprint(self, surf, sat):
        col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
        n = 90; angles = np.linspace(0, 2*math.pi, n)
        lat_fp = sat.lat + sat.footprint_r*np.cos(angles)
        lon_fp = sat.lon + sat.footprint_r*np.sin(angles)/max(0.01, math.cos(math.radians(sat.lat)))
        lat_fp = np.clip(lat_fp, -89, 89)
        sx, sy, z2 = self.project_batch(lat_fp, lon_fp)
        pts = [(int(sx[i]),int(sy[i])) for i in range(n) if z2[i]>0]
        if len(pts) > 3:
            fp = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            pygame.draw.polygon(fp, (*col[:3],16), pts)
            pygame.draw.lines(fp, (*col[:3],85), True, pts, 1)
            surf.blit(fp, (0,0))

# ── SATELLITE ─────────────────────────────────────────────────────────────────
class Satellite:
    __slots__ = ["name","group","satrec","lat","lon","alt","vel","trail",
                 "visible","footprint_r","inclination","period_min",
                 "apogee","perigee","norad_id","pulse_ph"]
    def __init__(self, name, group, satrec):
        self.name=name; self.group=group; self.satrec=satrec
        self.lat=self.lon=self.alt=self.vel=0.0
        self.trail=[]; self.visible=True; self.footprint_r=0.0
        self.pulse_ph=random.uniform(0, 6.28)
        e = satrec.ecco
        try:
            a = (8681663.653/satrec.no_kozai)**(2/3)
            self.inclination = math.degrees(satrec.inclo)
            self.period_min  = 2*math.pi/satrec.no_kozai
            self.apogee      = round(a*(1+e)-EARTH_R, 1)
            self.perigee     = round(a*(1-e)-EARTH_R, 1)
        except:
            self.inclination=self.period_min=self.apogee=self.perigee=0.0
        self.norad_id = satrec.satnum

    def propagate(self, jd, fr):
        e, r, v = self.satrec.sgp4(jd, fr)
        if e != 0: return False
        x, y, z = r; vx, vy, vz = v
        self.vel = math.sqrt(vx*vx+vy*vy+vz*vz)
        t_ut1 = (jd-2451545.0+fr)/36525.0
        gmst = (280.46061837 + 360.98564736629*(jd-2451545.0+fr) +
                t_ut1*t_ut1*(0.000387933-t_ut1/38710000)) % 360
        gr = math.radians(gmst)
        lr = math.atan2(y, x) - gr
        lr = (lr+math.pi) % (2*math.pi) - math.pi
        p = math.sqrt(x*x+y*y)
        la = math.atan2(z, p*(1-0.00669437999014))
        for _ in range(5):
            N = 6378.137/math.sqrt(1-0.00669437999014*math.sin(la)**2)
            la = math.atan2(z+0.00669437999014*N*math.sin(la), p)
        self.lat = math.degrees(la); self.lon = math.degrees(lr)
        self.alt = p/math.cos(la) - 6378.137/math.sqrt(1-0.00669437999014*math.sin(la)**2)
        try:
            rho = math.acos(EARTH_R/max(EARTH_R+self.alt, EARTH_R+1))
            self.footprint_r = math.degrees(rho)
        except:
            self.footprint_r = 0.0
        return True

    def get_type(self):
        if self.alt < 2000: return "LEO"
        if self.alt < 35000: return "MEO"
        return "GEO"

    def is_famous(self):
        n = self.name.lower()
        return any(k in n for k in FAMOUS_KEYS)

# ── TLE MANAGER ───────────────────────────────────────────────────────────────
class TLEManager:
    def __init__(self):
        self.satellites=[]; self.lock=threading.Lock()
        self.status="Connecting…"; self.progress=0.0

    def fetch_all(self):
        sats = []
        for i, (grp, url) in enumerate(TLE_SOURCES.items()):
            self.status = f"Fetching {grp}…"; lim = MAX_PER.get(grp, 30)
            try:
                r = requests.get(url, timeout=14); r.raise_for_status()
                lines = r.text.strip().splitlines(); cnt = 0
                for j in range(0, len(lines)-2, 3):
                    if cnt >= lim: break
                    nm=lines[j].strip(); l1=lines[j+1].strip(); l2=lines[j+2].strip()
                    if not l1.startswith("1 ") or not l2.startswith("2 "): continue
                    try:
                        sat = Satrec.twoline2rv(l1, l2)
                        sats.append(Satellite(nm, grp, sat)); cnt+=1
                    except:
                        pass
            except:
                self.status = f"⚠ {grp}"
            self.progress = (i+1)/len(TLE_SOURCES)
        with self.lock: self.satellites = sats
        self.status = f"✓ {len(sats):,} loaded"

    def start(self):
        threading.Thread(target=self.fetch_all, daemon=True).start()

    def get_sats(self):
        with self.lock: return list(self.satellites)

# ── MINI FLAT MAP (for globe mode inset) ─────────────────────────────────────
class MiniFlatMap:
    W2=200; H2=110
    def __init__(self):
        s = pygame.Surface((self.W2, self.H2))
        for y in range(self.H2):
            pygame.draw.line(s, lerp_color((2,12,40),(1,7,22),y/self.H2), (0,y), (self.W2,y))
        for coast in COASTLINES:
            sub_segs = split_antimeridian(coast)
            for seg in sub_segs:
                pts = [(int((lo+180)/360*self.W2), int((90-la)/180*self.H2)) for la,lo in seg]
                if len(pts) > 2:
                    pygame.draw.polygon(s, (18,40,65), pts)
                if len(pts) > 1:
                    pygame.draw.lines(s, (35,65,100), False, pts, 1)
        self._surf = s

    def draw(self, surf, sats, sel, x, y):
        bg = pygame.Surface((self.W2+2, self.H2+2), pygame.SRCALPHA)
        bg.fill((2,8,22,200))
        surf.blit(bg, (x-1,y-1))
        surf.blit(self._surf, (x,y))
        pygame.draw.rect(surf, (0,80,180), (x-1,y-1,self.W2+2,self.H2+2), 1)
        for sat in sats:
            if not sat.visible: continue
            sx = int((sat.lon+180)/360*self.W2+x)
            sy = int((90-sat.lat)/180*self.H2+y)
            if x<=sx<x+self.W2 and y<=sy<y+self.H2:
                col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
                pygame.draw.circle(surf, col, (sx,sy), 3 if sat is sel else 1)

# ── FLAT OVERLAYS ─────────────────────────────────────────────────────────────
def ll_to_flat(lat, lon, W, H, zoom, ox, oy):
    return int((lon+180)/360*W*zoom+ox), int((90-lat)/180*H*zoom+oy)

def flat_grid(surf, font, W, H, zoom, ox, oy):
    gs = pygame.Surface((W, H), pygame.SRCALPHA)
    for lat in range(-90, 91, 30):
        y = int((90-lat)/180*H*zoom+oy); a = 35 if lat==0 else 12
        pygame.draw.line(gs, (255,255,255,a), (0,y), (W,y))
    for lon in range(-180, 181, 30):
        x = int((lon+180)/360*W*zoom+ox)
        pygame.draw.line(gs, (255,255,255,12), (x,0), (x,H))
    surf.blit(gs, (0,0))
    for lat in range(-60, 61, 30):
        y = int((90-lat)/180*H*zoom+oy)
        if 0 < y < H: draw_text(surf, font, f"{lat:+d}°", 4, y-6, (44,74,130), False)
    for lon in range(-150, 181, 30):
        x = int((lon+180)/360*W*zoom+ox)
        if 10 < x < W-30: draw_text(surf, font, f"{lon:+d}°", x-10, H-14, (44,74,130), False)

def flat_geo_labels(surf, font, W, H, zoom, ox, oy):
    for lat, label, col in GEO_LINES:
        x, y = ll_to_flat(lat, -160, W, H, zoom, ox, oy)
        if 0<y<H and 0<x<W: draw_text(surf, font, label, x, y-8, col)

def flat_cities(surf, font, W, H, zoom, ox, oy):
    for lat, lon, name, size in CITIES:
        x, y = ll_to_flat(lat, lon, W, H, zoom, ox, oy)
        if not (2<x<W-2 and 2<y<H-2): continue
        if size==1 and zoom<1.8: continue
        if size==2 and zoom<0.9: continue
        r = max(2, int(size*zoom*0.5))
        col = (255,200,80) if name in("Cape Canaveral","Baikonur","Jiuquan") else (170,190,225)
        pygame.draw.circle(surf, col, (x,y), r)
        pygame.draw.circle(surf, (255,255,255), (x,y), r, 1)
        if zoom>1.3 or size==3: draw_text(surf, font, name, x+r+2, y-6, col)

def flat_terminator(surf, zoom, ox, oy, W, H, sun_lat, sun_lon):
    slr = math.radians(sun_lat); sln = math.radians(sun_lon)
    ts = pygame.Surface((W, H), pygame.SRCALPHA)
    lon_d = np.arange(-180, 182, 2, dtype=np.float32)
    denom = math.sin(slr)
    if abs(denom) > 1e-6:
        dlon = np.radians(lon_d) - sln
        lat_t = np.degrees(np.arctan(-np.cos(slr)*np.cos(dlon)/denom))
    else:
        lat_t = np.full_like(lon_d, 90.0 if sun_lat>0 else -90.0)
    xs = ((lon_d+180)/360*W*zoom+ox).astype(int)
    ys = ((90-lat_t)/180*H*zoom+oy).astype(int)
    pts = [(int(xs[i]), int(ys[i])) for i in range(len(xs))]
    if len(pts)>1: pygame.draw.lines(ts, (255,210,50,55), False, pts, 2)
    surf.blit(ts, (0,0))
    sx, sy = ll_to_flat(sun_lat, sun_lon, W, H, zoom, ox, oy)
    if 0<sx<W and 0<sy<H:
        gs = pygame.Surface((28,28), pygame.SRCALPHA)
        for ri in range(13,0,-1):
            pygame.draw.circle(gs, (255,220,80,int(80*(1-ri/13)**1.5)), (14,14), ri)
        pygame.draw.circle(gs, (255,240,120), (14,14), 4)
        surf.blit(gs, (sx-14, sy-14))

def flat_footprint(surf, sat, zoom, ox, oy, W, H):
    col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
    n = 90; angles = np.linspace(0, 2*math.pi, n)
    la = sat.lat + sat.footprint_r*np.cos(angles)
    lo = sat.lon + sat.footprint_r*np.sin(angles)/max(0.01, math.cos(math.radians(sat.lat)))
    la = np.clip(la, -89, 89)
    xs = ((lo+180)/360*W*zoom+ox).astype(int)
    ys = ((90-la)/180*H*zoom+oy).astype(int)
    pts = list(zip(xs.tolist(), ys.tolist()))
    if len(pts) > 2:
        fp = pygame.Surface((W,H), pygame.SRCALPHA)
        pygame.draw.polygon(fp, (*col[:3],16), pts)
        pygame.draw.lines(fp, (*col[:3],88), True, pts, 1)
        surf.blit(fp, (0,0))

def flat_orbit(surf, sat, jd_base, fr_base, zoom, ox, oy, W, H, col):
    period_sec = sat.period_min*60; pts = []
    for i in range(141):
        fr = fr_base + (i/140-0.5)*period_sec/86400.0; jd = jd_base
        while fr >= 1.0: jd+=1; fr-=1.0
        while fr < 0.0:  jd-=1; fr+=1.0
        e, r, _ = sat.satrec.sgp4(jd, fr)
        if e != 0: continue
        xe, ye, ze = r
        gmst = math.radians((280.46061837+360.98564736629*(jd-2451545.0+fr))%360)
        lo_r = math.atan2(ye,xe)-gmst; lo_r = (lo_r+math.pi)%(2*math.pi)-math.pi
        pr = math.sqrt(xe*xe+ye*ye); la_r = math.atan2(ze, pr*(1-0.00669437999014))
        lo = math.degrees(lo_r); la = math.degrees(la_r)
        pts.append((int((lo+180)/360*W*zoom+ox), int((90-la)/180*H*zoom+oy), lo))
    orb = pygame.Surface((W,H), pygame.SRCALPHA)
    for i in range(1, len(pts)):
        if abs(pts[i][2]-pts[i-1][2]) > 180: continue
        pygame.draw.line(orb, (*col[:3],110), pts[i-1][:2], pts[i][:2], 2)
    surf.blit(orb, (0,0))

def globe_orbit_pts(sat, jd_base, fr_base):
    period_sec = sat.period_min*60; pts = []
    for i in range(141):
        fr = fr_base + (i/140-0.5)*period_sec/86400.0; jd = jd_base
        while fr >= 1.0: jd+=1; fr-=1.0
        while fr < 0.0:  jd-=1; fr+=1.0
        e, r, _ = sat.satrec.sgp4(jd, fr)
        if e != 0: continue
        xe, ye, ze = r
        gmst = math.radians((280.46061837+360.98564736629*(jd-2451545.0+fr))%360)
        lo_r = math.atan2(ye,xe)-gmst; lo_r=(lo_r+math.pi)%(2*math.pi)-math.pi
        pr = math.sqrt(xe*xe+ye*ye); la_r = math.atan2(ze, pr*(1-0.00669437999014))
        pts.append((math.degrees(la_r), math.degrees(lo_r)))
    return pts

# ── PASS PREDICTOR ────────────────────────────────────────────────────────────
def predict_passes(sat, obs_lat=51.5, obs_lon=-0.1, hours=24, step_sec=10):
    passes=[]; now=datetime.datetime.utcnow(); t_sec=0; in_pass=False; rise=None; max_el=0.0
    while t_sec < hours*3600:
        dt = now + datetime.timedelta(seconds=t_sec)
        jd_i, fr_i = jday(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second+dt.microsecond/1e6)
        e, r, _ = sat.satrec.sgp4(jd_i, fr_i)
        if e != 0: t_sec+=step_sec; continue
        olr=math.radians(obs_lat); oln=math.radians(obs_lon)
        gmst=math.radians((280.46061837+360.98564736629*(jd_i-2451545.0+fr_i))%360)
        ox2=EARTH_R*math.cos(olr)*math.cos(oln+gmst)
        oy2=EARTH_R*math.cos(olr)*math.sin(oln+gmst)
        oz2=EARTH_R*math.sin(olr)
        dx,dy,dz=r[0]-ox2, r[1]-oy2, r[2]-oz2
        rng=math.sqrt(dx*dx+dy*dy+dz*dz)
        upx=math.cos(olr)*math.cos(oln+gmst)
        upy=math.cos(olr)*math.sin(oln+gmst)
        upz=math.sin(olr)
        dot=(dx*upx+dy*upy+dz*upz)/rng
        el=math.degrees(math.asin(max(-1,min(1,dot))))
        if el > 0:
            if not in_pass: in_pass=True; rise=dt; max_el=el
            else: max_el=max(max_el,el)
        else:
            if in_pass:
                passes.append({"rise":rise,"set":dt,"max_el":round(max_el,1),"duration":int((dt-rise).seconds)})
                in_pass=False
            if len(passes) >= 5: break
        t_sec += step_sec
    return passes

# ── TELEMETRY PANEL ───────────────────────────────────────────────────────────
def draw_telemetry(surf, fonts, sat, x, y, passes, t_pulse):
    col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
    rows = [
        ("NORAD ID",        str(sat.norad_id)),
        ("GROUP",           sat.group),
        ("TYPE",            sat.get_type()),
        ("LAT / LON",       f"{sat.lat:+.3f}°  {sat.lon:+.3f}°"),
        ("ALTITUDE",        f"{sat.alt:.1f} km"),
        ("VELOCITY",        f"{sat.vel:.3f} km/s"),
        ("INCLINATION",     f"{sat.inclination:.2f}°"),
        ("PERIOD",          f"{sat.period_min:.2f} min"),
        ("APOGEE / PERIGEE",f"{sat.apogee:.0f} / {sat.perigee:.0f} km"),
        ("FOOTPRINT ∠",     f"{sat.footprint_r:.1f}°"),
    ]
    ph = 32 + len(rows)*21 + (len(passes)*16+20 if passes else 0) + 30
    draw_panel(surf, x, y, 272, ph, border=col, hdr=col)
    pulse = 0.5 + 0.5*math.sin(t_pulse*3)
    pygame.draw.circle(surf, (*col[:3],int(70+110*pulse)), (x+256,y+11), 4)
    draw_text(surf, fonts.lg, sat.name[:24], x+10, y+7, col)
    oy0 = y+26
    for i, (k, v) in enumerate(rows):
        ry = oy0 + i*21
        draw_text(surf, fonts.sm, k, x+10, ry, (65,115,170))
        draw_text(surf, fonts.md, v, x+145, ry, (215,240,255))
    bar_y = oy0 + len(rows)*21 + 4
    max_alt = 42164 if sat.get_type()=="GEO" else (35000 if sat.get_type()=="MEO" else 2000)
    fill = min(1.0, sat.alt/max_alt)
    bc = lerp_color((0,220,100),(255,80,0), fill)
    pygame.draw.rect(surf, (14,28,58), (x+10, bar_y, 250, 4))
    pygame.draw.rect(surf, bc,         (x+10, bar_y, int(250*fill), 4))
    draw_text(surf, fonts.sm, f"ORBIT: {sat.get_type()}", x+10, bar_y+6, (60,100,160))
    if passes:
        py0 = bar_y+20
        pygame.draw.line(surf, (25,55,110), (x+8,py0), (x+264,py0), 1)
        draw_text(surf, fonts.sm, "NEXT PASSES (London)", x+10, py0+3, (70,150,90))
        for i, p in enumerate(passes[:5]):
            ry = py0+16+i*16
            draw_text(surf, fonts.sm,
                      f"{p['rise'].strftime('%H:%M:%S')}  el:{p['max_el']:5.1f}°  {p['duration']}s",
                      x+10, ry, (140,210,150))

# ── SEARCH ────────────────────────────────────────────────────────────────────
class Search:
    def __init__(self, fonts):
        self.active=False; self.q=""; self.results=[]; self.cur=0; self.F=fonts

    def open(self): self.active=True; self.q=""; self.results=[]
    def close(self): self.active=False

    def update(self, sats):
        q = self.q.lower()
        self.results = [s for s in sats if q in s.name.lower()][:12]
        self.cur = max(0, min(self.cur, len(self.results)-1))

    def sel(self): return self.results[self.cur] if self.results else None

    def draw(self, surf, W, H):
        if not self.active: return
        ov = pygame.Surface((W,H), pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        surf.blit(ov, (0,0))
        bw, bh = 540, min(88+len(self.results)*26, 440)
        bx, by = W//2-bw//2, H//2-bh//2
        draw_panel(surf, bx, by, bw, bh, border=(0,150,255))
        draw_text(surf, self.F.lg, "SATELLITE SEARCH", bx+14, by+9, (80,175,255))
        pygame.draw.rect(surf, (8,18,45), (bx+12, by+32, bw-24, 26))
        pygame.draw.rect(surf, (0,120,220), (bx+12, by+32, bw-24, 26), 1)
        draw_text(surf, self.F.md, self.q+"▍", bx+18, by+37, (200,230,255))
        for i, sat in enumerate(self.results):
            ry = by+64+i*26
            if i == self.cur:
                hl = pygame.Surface((bw-24,24), pygame.SRCALPHA)
                hl.fill((0,60,140,120))
                surf.blit(hl, (bx+12, ry-2))
            col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
            pygame.draw.circle(surf, col, (bx+24, ry+9), 4)
            draw_text(surf, self.F.md, ("★ " if sat.is_famous() else "")+sat.name[:30], bx+36, ry, col)
            draw_text(surf, self.F.sm,
                      f"{sat.group} | {sat.get_type()} | {sat.alt:.0f}km | {sat.vel:.2f}km/s",
                      bx+36, ry+13, (90,130,180))
        if not self.results and self.q:
            draw_text(surf, self.F.md, "No results.", bx+22, by+68, (100,90,130))
        draw_text(surf, self.F.sm, "↑↓ Navigate   ENTER Select   ESC Close", bx+14, by+bh-17, (55,85,130))

# ── GROUP FILTER ──────────────────────────────────────────────────────────────
class GroupFilter:
    BW=145; BH=19
    def __init__(self, fonts):
        self.F=fonts; self.enabled={g:True for g in TLE_SOURCES}; self.rects={}

    def draw(self, surf, W, H, sats):
        bx = W-self.BW-5; by = H-len(self.enabled)*self.BH-40
        cnts = {}
        for s in sats:
            if s.visible: cnts[s.group] = cnts.get(s.group,0)+1
        ph = len(self.enabled)*self.BH + 20
        draw_panel(surf, bx-4, by-20, self.BW+8, ph+2, alpha=195, border=(0,55,135))
        draw_text(surf, self.F.xs, "GROUPS  ·  click to toggle", bx-2, by-16, (52,88,165))
        for i, (grp, en) in enumerate(self.enabled.items()):
            ry = by+i*self.BH
            rect = pygame.Rect(bx, ry, self.BW, self.BH-2)
            self.rects[grp] = rect
            col = SAT_COLORS.get(grp, SAT_COLORS["Other"])
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg.fill((*col[:3],42) if en else (10,20,40,75))
            surf.blit(bg, (rect.x, rect.y))
            pygame.draw.rect(surf, col if en else (40,58,88), rect, 1)
            pygame.draw.circle(surf, col if en else (40,58,80), (bx+8, ry+8), 3)
            cnt = cnts.get(grp, 0)
            draw_text(surf, self.F.xs, f"{grp:<11}{cnt:>3}", bx+17, ry+3,
                      col if en else (52,72,108))

    def handle(self, pos):
        for grp, rect in self.rects.items():
            if rect.collidepoint(pos):
                self.enabled[grp] = not self.enabled[grp]
                return True
        return False

# ── VIEW TOGGLE BUTTON ────────────────────────────────────────────────────────
def draw_view_btn(surf, font, W, mode):
    """Draw view toggle. Positioned right-of-center to avoid UTC overlap."""
    bw, bh = 188, 28
    # Placed at right-center area, not overlapping UTC (which is at x~165)
    bx = W//2 + 40; by = 7
    for i, (lbl, vmode, vx) in enumerate([
        ("FLAT MAP", VIEW_FLAT,  bx),
        ("3D GLOBE",  VIEW_GLOBE, bx+bw//2)
    ]):
        half = bw//2-1 if i==0 else bw//2
        active = (mode == vmode)
        col = (0,185,255) if vmode==VIEW_FLAT else (0,255,140)
        bg = pygame.Surface((half, bh), pygame.SRCALPHA)
        bg.fill((*col[:3],55) if active else (5,14,38,170))
        surf.blit(bg, (vx, by))
        pygame.draw.rect(surf, col, (vx, by, half, bh), 2 if active else 1)
        draw_text(surf, font, lbl, vx+8, by+6, col)
    return (pygame.Rect(bx, by, bw//2-1, bh),
            pygame.Rect(bx+bw//2, by, bw//2, bh))

# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf, fonts, sim_dt, W, H, warp_idx, paused, mode, zoom, status, sats):
    # Top bar background
    bg = pygame.Surface((W,44), pygame.SRCALPHA)
    bg.fill((2,5,18,215))
    surf.blit(bg, (0,0))

    # Logo — left side
    draw_text(surf, fonts.xl, "COSMO", 12, 3, (0,185,255))
    draw_text(surf, fonts.xl, "LENS",  92, 3, (228,244,255))
    draw_text(surf, fonts.sm, "SATELLITE TRACKER", 13, 28, (38,78,138))

    # UTC + Warp — left-center (fixed: no longer overlaps view button)
    draw_text(surf, fonts.lg, sim_dt.strftime("UTC  %Y-%m-%d  %H:%M:%S"), 168, 5, (150,210,255))
    wp_col = (210,75,75) if paused else (75,210,115)
    draw_text(surf, fonts.lg, "⏸ PAUSED" if paused else f"▶ {WARP_LABELS[warp_idx]}", 168, 24, wp_col)

    # Shortcuts — right side
    draw_text(surf, fonts.sm,
              "[H]Help [S]Search [SPACE]Pause [R]Reset [E]Export [ESC]Quit",
              W-420, 5, (38,68,128))
    draw_text(surf, fonts.sm,
              "[F]Foot [O]Orbit [T]Trail [G]Grid [N]Names [C]Cities [F1]Night [F2]Term",
              W-420, 20, (32,58,112))

    # Bottom bar
    bg2 = pygame.Surface((W,19), pygame.SRCALPHA)
    bg2.fill((2,5,18,200))
    surf.blit(bg2, (0, H-19))
    vis = [s for s in sats if s.visible]
    grps = {}
    for s in vis: grps[s.group] = grps.get(s.group,0)+1
    xp = 8
    xp += draw_text(surf, fonts.sm, f"TRACKING {len(vis):,} OBJECTS", xp, H-15, (60,128,215)) + 14
    for grp, cnt in sorted(grps.items()):
        col = SAT_COLORS.get(grp, SAT_COLORS["Other"])
        pygame.draw.circle(surf, col, (xp+3, H-9), 3)
        xp += draw_text(surf, fonts.sm, f" {grp}:{cnt}", xp+8, H-15, col) + 6
    draw_text(surf, fonts.sm, f"ZOOM {zoom:.2f}×", W-195, H-15, (68,108,165))
    draw_text(surf, fonts.sm, status[:42], W//2-160, H-15, (48,78,138))

# ── HELP OVERLAY ──────────────────────────────────────────────────────────────
HELP = [
    ("VIEW",None),  ("[V]","Flat Map ↔ 3D Globe"), ("",""),
    ("NAV",None),   ("Drag (flat)","Pan"), ("Drag (globe)","Rotate"),
    ("Scroll","Zoom"), ("[R]","Reset"), ("",""),
    ("TIME",None),  ("[SPACE]","Pause/Resume"), ("[1-9]","Warp"),
    ("[+]/[-]","Trail length"), ("",""),
    ("LAYERS",None),("[F]","Footprint"),("[O]","Orbit"),("[T]","Trails"),
    ("[G]","Grid"),("[N]","Names"),("[C]","Cities"),("[F1]","Night"),("[F2]","Terminator"),
    ("",""),
    ("OTHER",None), ("[S]","Search"), ("[TAB]","Next sat"),
    ("[E]","Export CSV"), ("[F3]","Screenshot"), ("[H]","Help"), ("[ESC]","Quit"),
]

def draw_help_ov(surf, fonts, W, H):
    bw, bh = 420, 30+len(HELP)*16
    bx, by = W//2-bw//2, H//2-bh//2
    draw_panel(surf, bx, by, bw, bh, border=(0,115,215))
    draw_text(surf, fonts.lg, "KEYBOARD SHORTCUTS", bx+14, by+7, (60,158,255))
    for i, (k, v) in enumerate(HELP):
        ry = by+25+i*16
        if v is None:
            draw_text(surf, fonts.sm, k, bx+12, ry, (52,92,172))
            pygame.draw.line(surf, (18,48,98), (bx+12, ry+12), (bx+bw-12, ry+12), 1)
        elif k and v:
            draw_text(surf, fonts.md, k, bx+16, ry, (175,212,255))
            draw_text(surf, fonts.md, v, bx+192, ry, (108,158,218))

# ── MINI GLOBE INSET for flat map ─────────────────────────────────────────────
def draw_mini_globe_inset(surf, fonts, W, H, sats, sel, sim_time, COASTLINES_REF):
    """Draw a small 3D globe in the BOTTOM-LEFT (not right, to avoid groups panel)."""
    gl_s = pygame.Surface((156,156), pygame.SRCALPHA)
    R2 = 72; c2x = R2+6; c2y = R2+6
    # Atmosphere glow
    for ri in range(R2+8, R2-1, -2):
        prog = (ri-R2)/8; a = int(55*prog*(1-prog)*4)
        if a > 0:
            pygame.draw.circle(gl_s, (40,100,255,min(a,55)), (c2x,c2y), ri, 2)
    pygame.draw.circle(gl_s, (3,14,50), (c2x,c2y), R2)
    n = (sim_time - datetime.datetime(2000,1,1,12)).total_seconds()/240
    lon_off2 = n % 360; tilt2 = 0.2

    def mp3(la, lo):
        lr = math.radians(la); ln = math.radians(lo+lon_off2)
        xv = math.cos(lr)*math.sin(ln)
        yv = math.sin(lr)
        zv = math.cos(lr)*math.cos(ln)
        ct = math.cos(tilt2); st = math.sin(tilt2)
        y3 = yv*ct - zv*st; z3 = yv*st + zv*ct
        if z3 < 0: return None
        return (c2x + int(xv*R2), c2y - int(y3*R2))

    for coast in COASTLINES_REF:
        sub = split_antimeridian(coast)
        for seg in sub:
            pts = [mp3(la, lo) for la, lo in seg]
            pts = [p for p in pts if p]
            if len(pts) > 2:
                pygame.draw.polygon(gl_s, (20,44,70), pts)
            if len(pts) > 1:
                pygame.draw.lines(gl_s, (38,70,108), False, pts, 1)

    for sat in sats:
        if not sat.visible: continue
        p = mp3(sat.lat, sat.lon)
        if p:
            col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
            pygame.draw.circle(gl_s, col, p, 3 if sat is sel else 1)

    pygame.draw.circle(gl_s, (30,80,200), (c2x,c2y), R2, 1)
    # Bottom-LEFT position
    surf.blit(gl_s, (10, H-160))
    draw_text(surf, fonts.xs, "3D VIEW", 22, H-18, (44,74,138))

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    global COASTLINES

    # ── Download Natural Earth coastlines for realistic maps ──────────────────
    ne = fetch_natural_earth()
    if ne:
        COASTLINES = ne
        print(f"[MAP] Using Natural Earth data ({len(COASTLINES)} land segments).")
    else:
        print(f"[MAP] Using built-in simplified coastlines ({len(COASTLINES)} segments).")

    pygame.init()
    flags = pygame.RESIZABLE
    try:
        test = pygame.display.set_mode((100,100), flags|pygame.HWSURFACE|pygame.DOUBLEBUF)
        flags |= pygame.HWSURFACE|pygame.DOUBLEBUF
    except:
        pass
    screen = pygame.display.set_mode((W0,H0), flags)
    pygame.display.set_caption("CosmoLens v6 — Realistic Maps + 3D Globe")
    clock = pygame.time.Clock(); fonts = Fonts()
    W, H = W0, H0

    print("[MAP] Building flat map texture…")
    flat_map = FlatMap(W, H)
    print("[MAP] Building globe…")
    globe = Globe(W, H)
    mini  = MiniFlatMap()
    mgr   = TLEManager(); mgr.start()
    search = Search(fonts); grpfilt = GroupFilter(fonts)
    glow_surf  = pygame.Surface((W,H), pygame.SRCALPHA)
    trail_surf = pygame.Surface((W,H), pygame.SRCALPHA)

    # ── State ─────────────────────────────────────────────────────────────────
    mode=VIEW_FLAT; zoom=1.0; ox,oy=0.0,0.0
    dragging=False; drag_start=(0,0); drag_ox_oy=(0.0,0.0)
    g_drag_start=(0,0); g_lon0=0.0; g_tilt0=0.2
    warp_idx=3; paused=False
    sim_time=datetime.datetime.utcnow(); prev_rt=time.time()
    t_pulse=0.0; auto_spin=True; idle_t=0.0
    show_trails=True; show_orbit=True; show_foot=False
    show_names=False; show_grid=True; show_inset=True
    show_night=True; show_term=True; show_help=False; show_hud=True
    show_cities=True; trail_len=MAX_TRAIL
    sel=None; passes_cache=[]; tab_i=0
    sats=[]; emsg=""; emsg_t=0
    btn_f=btn_g=None

    def get_jd():
        ep = datetime.datetime(2000,1,1,12)
        d  = sim_time - ep
        jf = 2451545.0 + d.total_seconds()/86400.0
        return int(jf), jf-int(jf)

    def do_export():
        fn = f"cosmo_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fn,"w",newline="") as f:
            w=csv.writer(f)
            w.writerow(["Name","Group","NORAD","Lat","Lon","Alt_km","Vel_km_s","Type"])
            for s in sats:
                if s.visible:
                    w.writerow([s.name,s.group,s.norad_id,
                                round(s.lat,4),round(s.lon,4),
                                round(s.alt,1),round(s.vel,3),s.get_type()])
        return fn

    def rebuild(W2, H2):
        nonlocal flat_map, globe, glow_surf, trail_surf, mini
        flat_map   = FlatMap(W2, H2)
        globe      = Globe(W2, H2)
        mini       = MiniFlatMap()
        glow_surf  = pygame.Surface((W2,H2), pygame.SRCALPHA)
        trail_surf = pygame.Surface((W2,H2), pygame.SRCALPHA)

    running = True
    while running:
        dt_rt = min(time.time()-prev_rt, 0.05); prev_rt=time.time(); t_pulse+=dt_rt
        if not paused:
            sim_time += datetime.timedelta(seconds=dt_rt*WARP_LEVELS[warp_idx])
        new_s = mgr.get_sats()
        if new_s and len(new_s) != len(sats): sats=new_s; tab_i=0
        jd, fr = get_jd()

        for sat in sats: sat.propagate(jd, fr)
        for sat in sats: sat.visible = grpfilt.enabled.get(sat.group, True)

        if mode==VIEW_GLOBE and auto_spin and not paused:
            globe.lon_off = (globe.lon_off + dt_rt*3.0) % 360
        idle_t = max(0, idle_t-dt_rt)
        sun_lat, sun_lon = get_sun_pos(sim_time)

        # ── EVENTS ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running=False

            elif event.type == pygame.VIDEORESIZE:
                W, H = event.w, event.h
                screen = pygame.display.set_mode((W,H), flags)
                rebuild(W, H)

            elif event.type == pygame.KEYDOWN:
                if search.active:
                    if event.key == pygame.K_ESCAPE: search.close()
                    elif event.key == pygame.K_RETURN:
                        s2=search.sel()
                        if s2: sel=s2; passes_cache=[]
                        search.close()
                    elif event.key == pygame.K_UP:   search.cur=max(0,search.cur-1)
                    elif event.key == pygame.K_DOWN: search.cur=min(len(search.results)-1,search.cur+1)
                    elif event.key == pygame.K_BACKSPACE:
                        search.q=search.q[:-1]; search.update(sats)
                    elif event.unicode and event.unicode.isprintable():
                        search.q+=event.unicode; search.update(sats)
                else:
                    k = event.key
                    if k == pygame.K_ESCAPE:
                        if show_help: show_help=False
                        elif sel: sel=None; passes_cache=[]
                        else: running=False
                    elif k == pygame.K_v:     mode = VIEW_GLOBE if mode==VIEW_FLAT else VIEW_FLAT
                    elif k == pygame.K_SPACE: paused = not paused
                    elif k == pygame.K_r:
                        zoom=1.0; ox=oy=0.0
                        globe.lon_off=0.0; globe.tilt=0.2; globe.zoom=1.0
                    elif k == pygame.K_f:  show_foot   = not show_foot
                    elif k == pygame.K_o:  show_orbit  = not show_orbit
                    elif k == pygame.K_t:  show_trails = not show_trails
                    elif k == pygame.K_g:  show_grid   = not show_grid
                    elif k == pygame.K_n:  show_names  = not show_names
                    elif k == pygame.K_m:  show_inset  = not show_inset
                    elif k == pygame.K_c:  show_cities = not show_cities
                    elif k == pygame.K_h:  show_help   = not show_help
                    elif k == pygame.K_a:  show_hud    = not show_hud
                    elif k == pygame.K_s:  search.open(); search.update(sats)
                    elif k == pygame.K_e:
                        emsg = f"✓ Exported → {do_export()}"; emsg_t=time.time()
                    elif k == pygame.K_TAB:
                        vis = [s for s in sats if s.visible]
                        if vis:
                            tab_i = (tab_i+1)%len(vis); sel=vis[tab_i]; passes_cache=[]
                            if mode==VIEW_GLOBE:
                                globe.lon_off=-sel.lon
                                globe.tilt=math.radians(-sel.lat*0.8)
                    elif k in (pygame.K_PLUS, pygame.K_EQUALS):
                        trail_len = min(MAX_TRAIL, trail_len+8)
                    elif k == pygame.K_MINUS:
                        trail_len = max(8, trail_len-8)
                    elif k == pygame.K_F1:  show_night = not show_night
                    elif k == pygame.K_F2:  show_term  = not show_term
                    elif k == pygame.K_F3:
                        fn = f"cosmo_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                        pygame.image.save(screen, fn); emsg=f"📷 {fn}"; emsg_t=time.time()
                    elif event.unicode in "123456789":
                        idx = int(event.unicode)-1
                        if 0 <= idx < len(WARP_LEVELS): warp_idx=idx

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if not search.active:
                    if btn_f and btn_f.collidepoint(mx,my): mode=VIEW_FLAT; continue
                    if btn_g and btn_g.collidepoint(mx,my): mode=VIEW_GLOBE; continue
                    if event.button == 1:
                        if not grpfilt.handle((mx,my)):
                            dragging=True; drag_start=(mx,my); drag_ox_oy=(ox,oy)
                            g_drag_start=(mx,my); g_lon0=globe.lon_off; g_tilt0=globe.tilt
                            auto_spin=False; idle_t=0.0
                    elif event.button == 3:
                        sel=None; passes_cache=[]
                    elif event.button in (4,5):
                        factor = 1.11 if event.button==4 else 1/1.11
                        if mode==VIEW_FLAT:
                            ox=(ox-mx)*factor+mx; oy=(oy-my)*factor+my
                            zoom=max(0.35, min(zoom*factor, 14.0))
                        else:
                            globe.zoom=max(0.5, min(globe.zoom*factor, 4.5))

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button==1 and dragging:
                    dragging=False; mx,my=event.pos
                    if abs(mx-drag_start[0])+abs(my-drag_start[1]) < 5:
                        best=None; best_d=16**2
                        for sat in sats:
                            if not sat.visible: continue
                            if mode==VIEW_FLAT:
                                sx,sy=ll_to_flat(sat.lat,sat.lon,W,H,zoom,ox,oy)
                            else:
                                sx,sy,z2=globe.project(sat.lat,sat.lon)
                                if sx is None: continue
                            d=(mx-sx)**2+(my-sy)**2
                            if d < best_d: best_d=d; best=sat
                        sel=best; passes_cache=[]
                    idle_t=2.0

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mx, my = event.pos
                    if mode==VIEW_FLAT:
                        ox=drag_ox_oy[0]+mx-drag_start[0]
                        oy=drag_ox_oy[1]+my-drag_start[1]
                    else:
                        dx=mx-g_drag_start[0]; dy=my-g_drag_start[1]
                        globe.lon_off=(g_lon0-dx*0.35)%360
                        globe.tilt=max(-1.4, min(1.4, g_tilt0+math.radians(dy*0.35)))

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                factor = 1.11 if event.y>0 else 1/1.11
                if mode==VIEW_FLAT:
                    ox=(ox-mx)*factor+mx; oy=(oy-my)*factor+my
                    zoom=max(0.35, min(zoom*factor, 14.0))
                else:
                    globe.zoom=max(0.5, min(globe.zoom*factor, 4.5))

        if idle_t <= 0 and not dragging and mode==VIEW_GLOBE:
            auto_spin = True

        # ── RENDER ───────────────────────────────────────────────────────────
        screen.fill((0,0,0))

        # ══════════════════════════════════════════════════════════════════════
        if mode == VIEW_FLAT:
        # ══════════════════════════════════════════════════════════════════════
            sm, mp = flat_map.get_scaled(zoom, ox, oy)
            screen.blit(sm, mp)
            if show_grid:   flat_grid(screen, fonts.xs, W, H, zoom, ox, oy)
            flat_geo_labels(screen, fonts.xs, W, H, zoom, ox, oy)
            if show_cities: flat_cities(screen, fonts.xs, W, H, zoom, ox, oy)
            if show_night:
                ns = NightCache.flat(W, H, zoom, ox, oy, sun_lat, sun_lon)
                screen.blit(ns, (0,0))
            if show_term:  flat_terminator(screen, zoom, ox, oy, W, H, sun_lat, sun_lon)
            if show_foot and sel: flat_footprint(screen, sel, zoom, ox, oy, W, H)
            if show_orbit and sel:
                col = SAT_COLORS.get(sel.group, SAT_COLORS["Other"])
                flat_orbit(screen, sel, jd, fr, zoom, ox, oy, W, H, col)

            trail_surf.fill((0,0,0,0))
            glow_surf.fill((0,0,0,0))
            mx0, my0 = pygame.mouse.get_pos(); hover=None; best_hd=14**2

            for sat in sats:
                if not sat.visible: continue
                sx, sy = ll_to_flat(sat.lat, sat.lon, W, H, zoom, ox, oy)
                col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
                sat.trail.append((sat.lon, sat.lat))
                if len(sat.trail) > MAX_TRAIL: sat.trail.pop(0)

                # ── FIXED: trails now visible with improved alpha formula ──
                if show_trails:
                    trail = sat.trail[-trail_len:]
                    n = len(trail)
                    for i in range(1, n):
                        if abs(trail[i][0]-trail[i-1][0]) > 180: continue
                        ax = int((trail[i-1][0]+180)/360*W*zoom+ox)
                        ay = int((90-trail[i-1][1])/180*H*zoom+oy)
                        bx_ = int((trail[i][0]+180)/360*W*zoom+ox)
                        by_ = int((90-trail[i][1])/180*H*zoom+oy)
                        # Improved formula: visible from the start, brighter near satellite
                        alpha = int(25 + 200*(i/n)**0.65)
                        pygame.draw.line(trail_surf, (*col[:3], alpha), (ax,ay), (bx_,by_), 1)

                is_sel = (sat is sel); fam = sat.is_famous()
                if fam:
                    pulse = 0.6 + 0.4*math.sin(t_pulse*2.5+sat.pulse_ph)
                    pygame.draw.circle(glow_surf, (*col,int(72*pulse)), (sx,sy), 14)
                    pygame.draw.line(screen, col, (sx-9,sy), (sx+9,sy), 2)
                    pygame.draw.line(screen, col, (sx,sy-9), (sx,sy+9), 2)
                    pygame.draw.circle(screen, col, (sx,sy), 5)
                else:
                    sz = 4 if sat.get_type()=="MEO" else 3 if sat.get_type()=="GEO" else 2
                    if is_sel: sz += 2
                    pygame.draw.circle(glow_surf, (*col,40), (sx,sy), sz+4)
                    pygame.draw.circle(screen, col, (sx,sy), sz)

                if is_sel:
                    pygame.draw.circle(screen, (255,255,255), (sx,sy), 11, 2)
                    p2 = 0.5 + 0.5*math.sin(t_pulse*4)
                    rs = pygame.Surface((38,38), pygame.SRCALPHA)
                    pygame.draw.circle(rs, (*col[:3],int(55+55*p2)), (19,19), 17, 1)
                    screen.blit(rs, (sx-19,sy-19))

                d2 = (mx0-sx)**2+(my0-sy)**2
                if d2 < best_hd: best_hd=d2; hover=sat
                if show_names or is_sel:
                    screen.blit(fonts.sm.render(sat.name[:20],True,col), (sx+6,sy-5))

            screen.blit(trail_surf, (0,0))
            screen.blit(glow_surf,  (0,0))

            # Hover tooltip
            if hover and hover is not sel:
                tx, ty = ll_to_flat(hover.lat, hover.lon, W, H, zoom, ox, oy)
                tc = SAT_COLORS.get(hover.group, SAT_COLORS["Other"])
                badge = "★ " if hover.is_famous() else ""
                l0 = badge+hover.name
                l1 = f"{hover.group}  {hover.get_type()}  {hover.alt:.0f}km  {hover.vel:.2f}km/s"
                tw = max(fonts.md.size(l)[0] for l in [l0,l1]) + 14
                tx2=min(tx+14,W-tw-4); ty2=max(ty-22,48)
                draw_panel(screen, tx2, ty2, tw, 36, border=tc, hdr=tc)
                draw_text(screen, fonts.md, l0, tx2+7, ty2+3, tc)
                draw_text(screen, fonts.sm, l1, tx2+7, ty2+19, (138,182,222))

            # Mini globe inset — BOTTOM LEFT (fixed: no longer overlaps groups panel)
            if show_inset:
                draw_mini_globe_inset(screen, fonts, W, H, sats, sel, sim_time, COASTLINES)

        # ══════════════════════════════════════════════════════════════════════
        else:  # GLOBE VIEW
        # ══════════════════════════════════════════════════════════════════════
            globe.draw_stars(screen)
            globe.draw_ocean(screen)
            globe.draw_land(screen)
            if show_grid:  globe.draw_grid(screen)
            if show_night:
                ns = NightCache.globe(globe.R2,globe.cx,globe.cy,globe.lon_off,
                                      globe.tilt,sun_lat,sun_lon,W,H)
                screen.blit(ns, (globe.cx-globe.R2, globe.cy-globe.R2))
            if show_term:  globe.draw_terminator(screen, sun_lat, sun_lon)
            if show_foot and sel: globe.draw_footprint(screen, sel)
            if show_orbit and sel:
                opts = globe_orbit_pts(sel, jd, fr)
                col  = SAT_COLORS.get(sel.group, SAT_COLORS["Other"])
                globe.draw_orbit(screen, opts, col)

            glow_surf.fill((0,0,0,0))
            trail_surf.fill((0,0,0,0))
            mx0, my0 = pygame.mouse.get_pos(); hover=None; best_hd=14**2

            for sat in sats:
                if not sat.visible: continue
                sx, sy, z2 = globe.project(sat.lat, sat.lon)
                if sx is None or z2 < 0: continue
                col = SAT_COLORS.get(sat.group, SAT_COLORS["Other"])
                dim = max(0.35, min(1.0, z2*1.8))
                dcol = tuple(int(c*dim) for c in col)
                sat.trail.append((sat.lon, sat.lat))
                if len(sat.trail) > MAX_TRAIL: sat.trail.pop(0)

                # ── FIXED: vectorised projection + proper index + None-check ──
                if show_trails and len(sat.trail) > 1:
                    trail = sat.trail[-trail_len:]
                    n = len(trail)
                    # Batch-project all trail points (much faster than single calls)
                    t_lons = np.array([p[0] for p in trail], dtype=np.float32)
                    t_lats = np.array([p[1] for p in trail], dtype=np.float32)
                    t_sx, t_sy, t_z2 = globe.project_batch(t_lats, t_lons)
                    prev_pt = None; prev_lon = None
                    for ti in range(n):
                        if t_z2[ti] > 0:
                            pt = (int(t_sx[ti]), int(t_sy[ti]))
                            if prev_pt is not None and abs(t_lons[ti]-(prev_lon or t_lons[ti])) < 180:
                                # Improved alpha formula — visible throughout, bright near sat
                                alpha = int(20 + 195*(ti/n)**0.65)
                                pygame.draw.line(trail_surf, (*col[:3], alpha), prev_pt, pt, 1)
                            prev_pt = pt; prev_lon = float(t_lons[ti])
                        else:
                            prev_pt = None

                is_sel = (sat is sel); fam = sat.is_famous()
                if fam:
                    pulse = 0.6 + 0.4*math.sin(t_pulse*2.5+sat.pulse_ph)
                    pygame.draw.circle(glow_surf, (*col,int(68*pulse)), (sx,sy), 13)
                    pygame.draw.line(screen, dcol, (sx-8,sy), (sx+8,sy), 2)
                    pygame.draw.line(screen, dcol, (sx,sy-8), (sx,sy+8), 2)
                    pygame.draw.circle(screen, dcol, (sx,sy), 5)
                else:
                    sz = 4 if sat.get_type()=="MEO" else 3 if sat.get_type()=="GEO" else 2
                    if is_sel: sz += 2
                    pygame.draw.circle(glow_surf, (*col,36), (sx,sy), sz+3)
                    pygame.draw.circle(screen, dcol, (sx,sy), sz)

                if is_sel:
                    pygame.draw.circle(screen, (255,255,255), (sx,sy), 11, 2)
                    p2 = 0.5 + 0.5*math.sin(t_pulse*4)
                    rs2 = pygame.Surface((36,36), pygame.SRCALPHA)
                    pygame.draw.circle(rs2, (*col[:3],int(50+50*p2)), (18,18), 16, 1)
                    screen.blit(rs2, (sx-18,sy-18))
                if show_names or is_sel:
                    screen.blit(fonts.sm.render(sat.name[:20],True,dcol), (sx+6,sy-5))
                d2 = (mx0-sx)**2+(my0-sy)**2
                if d2 < best_hd: best_hd=d2; hover=sat

            screen.blit(trail_surf, (0,0))
            screen.blit(glow_surf,  (0,0))
            globe.draw_atmosphere(screen)

            if hover and hover is not sel:
                tc = SAT_COLORS.get(hover.group, SAT_COLORS["Other"])
                badge = "★ " if hover.is_famous() else ""
                l0 = badge+hover.name
                l1 = f"{hover.group}  {hover.get_type()}  {hover.alt:.0f}km  {hover.vel:.2f}km/s"
                tw = max(fonts.md.size(l)[0] for l in [l0,l1]) + 14
                tx2=min(mx0+14,W-tw-4); ty2=max(my0-22,48)
                draw_panel(screen, tx2, ty2, tw, 36, border=tc, hdr=tc)
                draw_text(screen, fonts.md, l0, tx2+7, ty2+3, tc)
                draw_text(screen, fonts.sm, l1, tx2+7, ty2+19, (138,182,222))

            # Mini flat map inset — bottom left (no conflict with right-side groups)
            if show_inset:
                mini.draw(screen, sats, sel, 12, H-MiniFlatMap.H2-26)
                draw_text(screen, fonts.xs, "FLAT VIEW", 14, H-22, (44,74,138))

            draw_text(screen, fonts.sm,
                      f"Lon:{(-globe.lon_off)%360:.1f}°  Tilt:{math.degrees(globe.tilt):.1f}°  Zoom:{globe.zoom:.1f}×",
                      globe.cx-90, H-36, (48,88,158))

        # ── SHARED UI ────────────────────────────────────────────────────────
        if sel:
            if not passes_cache: passes_cache = predict_passes(sel, 51.5, -0.1)
            draw_telemetry(screen, fonts, sel, W-282, 46, passes_cache, t_pulse)

        grpfilt.draw(screen, W, H, sats)

        if show_hud:
            draw_hud(screen, fonts, sim_time, W, H, warp_idx, paused, mode,
                     zoom if mode==VIEW_FLAT else globe.zoom, mgr.status, sats)

        # ── View toggle button — positioned to NOT overlap UTC (fixed) ────────
        btn_f, btn_g = draw_view_btn(screen, fonts.btn, W, mode)

        if show_help: draw_help_ov(screen, fonts, W, H)
        search.draw(screen, W, H)

        if emsg and time.time()-emsg_t < 4:
            draw_text(screen, fonts.md, emsg, W//2-195, H-36, (100,255,148))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit(); sys.exit()


if __name__ == "__main__":
    print(__doc__)
    os.system(f"{sys.executable} -m pip install -q pygame sgp4 requests numpy")
    main()
