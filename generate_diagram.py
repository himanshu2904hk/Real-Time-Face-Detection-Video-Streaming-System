"""Eye-catching architecture diagram with gradients, glows, icons."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1400, 780

# Palette - vibrant
BG1      = (10, 12, 24)
BG2      = (18, 14, 38)
SURFACE  = (22, 26, 46)
SURFACE2 = (30, 34, 58)
BORDER   = (60, 70, 110)
BLUE     = (88, 166, 255)
CYAN     = (56, 220, 240)
PURPLE   = (168, 130, 255)
PINK     = (255, 110, 180)
GREEN    = (54, 230, 150)
AMBER    = (255, 196, 80)
RED      = (255, 100, 110)
GREY     = (150, 158, 188)
TEXT     = (235, 240, 255)
TEXT2    = (160, 170, 200)
TEXT3    = (90, 100, 140)
WHITE    = (255, 255, 255)

# ── Background with vertical gradient + radial glows ──
img = Image.new("RGB", (W, H), BG1)
px = img.load()
for y in range(H):
    t = y / H
    r = int(BG1[0]*(1-t) + BG2[0]*t)
    g = int(BG1[1]*(1-t) + BG2[1]*t)
    b = int(BG1[2]*(1-t) + BG2[2]*t)
    for x in range(W):
        px[x,y] = (r,g,b)

# add radial glows
def glow(cx, cy, radius, color, intensity=0.25):
    layer = Image.new("RGB", (W,H), (0,0,0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(radius//2))
    base = img.load(); ov = layer.load()
    for y in range(H):
        for x in range(W):
            br = base[x,y]; o = ov[x,y]
            base[x,y] = (
                min(255, br[0]+int(o[0]*intensity)),
                min(255, br[1]+int(o[1]*intensity)),
                min(255, br[2]+int(o[2]*intensity)),
            )

glow(200, 200, 280, BLUE, 0.18)
glow(700, 400, 320, PURPLE, 0.15)
glow(1200, 250, 280, CYAN, 0.18)
glow(700, 700, 260, PINK, 0.10)

d = ImageDraw.Draw(img, 'RGBA')

def font(size, bold=False):
    names = (["arialbd.ttf","DejaVuSans-Bold.ttf"] if bold
             else ["arial.ttf","DejaVuSans.ttf"])
    for n in names:
        try: return ImageFont.truetype(n, size)
        except: pass
    return ImageFont.load_default()

F9=font(9); F10=font(10); F11=font(11); F12=font(12); F13=font(13); F14=font(14)
F11B=font(11,True); F12B=font(12,True); F13B=font(13,True); F14B=font(14,True)
F16B=font(16,True); F18B=font(18,True); F28B=font(28,True); F11I=font(11)

def tw(t,f):
    b=d.textbbox((0,0),t,font=f); return b[2]-b[0],b[3]-b[1]

def ctext(t,cx,cy,f,fill):
    w2,h2=tw(t,f); d.text((cx-w2//2,cy-h2//2),t,font=f,fill=fill)

def rr(x0,y0,x1,y1,r,fill,outline=None,ow=1):
    d.rounded_rectangle([x0,y0,x1,y1],radius=r,fill=fill,outline=outline,width=ow)

# subtle dot grid
for x in range(0,W,28):
    for y in range(0,H,28):
        d.point((x,y), fill=(40,46,80))

# ── Header band ──
ctext("REAL-TIME FACE DETECTION SYSTEM", W//2, 40, F28B, WHITE)
# accent bar
rr(W//2-220, 62, W//2+220, 66, 2, (88,166,255,255))
ctext("Architecture · React · FastAPI · MediaPipe · PostgreSQL · Docker", W//2, 84, F12, TEXT2)

# docker-compose chip top-left
rr(28, 28, 220, 58, 14, (30,40,90,255), (100,140,255,255), 2)
ctext("📦  docker-compose.yml", 124, 43, F12B, (140,180,255))

# live chip top-right
rr(W-220, 28, W-28, 58, 14, (10,50,30,255), (54,230,150,255), 2)
d.ellipse([W-208, 38, W-198, 48], fill=(54,230,150))
ctext("● LIVE PIPELINE", W-114, 43, F12B, (54,230,150))

# ── Glowing node helper ──
def glow_box(x0,y0,x1,y1,col,radius=22):
    layer = Image.new("RGBA",(W,H),(0,0,0,0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x0-6,y0-6,x1+6,y1+6], radius=radius, fill=col+(90,))
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    img.paste(layer, (0,0), layer)

def big_node(cx, cy, w, h, icon, title, sub, port, col, fill_dim):
    x0,y0,x1,y1 = cx-w//2, cy-h//2, cx+w//2, cy+h//2
    glow_box(x0,y0,x1,y1, col)
    rr(x0,y0,x1,y1, 16, fill_dim, col, 2)
    # icon circle
    rr(x0+12,y0+12, x0+44,y0+44, 8, col+(40,) if isinstance(col,tuple) and len(col)==3 else col, col, 2)
    ctext(icon, x0+28, y0+28, F18B, col)
    # title + sub
    d.text((x0+54, y0+12), title, font=F16B, fill=WHITE)
    d.text((x0+54, y0+34), sub, font=F11, fill=TEXT2)
    # port pill at bottom
    if port:
        pw,_ = tw(port, F10)
        rr(x0+12, y1-22, x0+12+pw+18, y1-6, 8, SURFACE2, col, 1)
        d.text((x0+21, y1-20), port, font=F10, fill=col)

# Re-init draw after paste
d = ImageDraw.Draw(img, 'RGBA')

# ── Layout ──
NODE_W, NODE_H = 220, 100
ROW_Y = 240

X_BROWSER  = 180
X_FRONTEND = 460
X_BACKEND  = 760
X_DB       = 1060
X_RIGHT    = 1280  # legend center

# Re-paste glows for nodes
def big_node2(cx, cy, w, h, icon, title, sub, port, col):
    x0,y0,x1,y1 = cx-w//2, cy-h//2, cx+w//2, cy+h//2
    # outer glow
    layer = Image.new("RGBA",(W,H),(0,0,0,0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x0-8,y0-8,x1+8,y1+8], radius=22, fill=col+(110,))
    layer = layer.filter(ImageFilter.GaussianBlur(14))
    img.paste(layer, (0,0), layer)
    nd = ImageDraw.Draw(img, 'RGBA')
    # body
    nd.rounded_rectangle([x0,y0,x1,y1], radius=16, fill=(28,32,54,255), outline=col, width=2)
    # top accent strip
    nd.rounded_rectangle([x0,y0,x1,y0+6], radius=16, fill=col)
    nd.rectangle([x0,y0+3,x1,y0+6], fill=col)
    # icon box
    nd.rounded_rectangle([x0+14,y0+22,x0+58,y0+66], radius=10, fill=col+(40,), outline=col, width=2)
    w2,h2 = tw(icon, F28B)
    nd.text((x0+36-w2//2, y0+44-h2//2), icon, font=F28B, fill=col)
    # text
    nd.text((x0+72, y0+22), title, font=F16B, fill=WHITE)
    nd.text((x0+72, y0+44), sub, font=F11, fill=TEXT2)
    if port:
        pw,_ = tw(port, F10)
        nd.rounded_rectangle([x0+72, y0+66, x0+72+pw+16, y0+82], radius=8, fill=(40,46,78,255), outline=col, width=1)
        nd.text((x0+80, y0+68), port, font=F10, fill=col)

big_node2(X_BROWSER,  ROW_Y, NODE_W, NODE_H, "🌐", "Browser",  "React + Vite client",     "localhost",     BLUE)
big_node2(X_FRONTEND, ROW_Y, NODE_W, NODE_H, "⚛",  "Frontend", "Nginx static + proxy",    "port 3000",     PURPLE)
big_node2(X_BACKEND,  ROW_Y, NODE_W, NODE_H, "⚡", "Backend",  "FastAPI · WebSocket",     "port 8000",     CYAN)
big_node2(X_DB,       ROW_Y, NODE_W, NODE_H, "🗄", "Database", "PostgreSQL 16 · SQLAlc.", "port 5432",     GREEN)

d = ImageDraw.Draw(img, 'RGBA')

# ── Arrows ──
def poly_arrow(points, col, label, dashed=False, label_offset=-12):
    for i in range(len(points)-1):
        x0,y0 = points[i]; x1,y1 = points[i+1]
        if dashed:
            n=12
            for s in range(n):
                t0=s/n; t1=(s+0.55)/n
                d.line([(x0+(x1-x0)*t0,y0+(y1-y0)*t0),(x0+(x1-x0)*t1,y0+(y1-y0)*t1)],fill=col,width=3)
        else:
            d.line([(x0,y0),(x1,y1)],fill=col,width=3)
    x0,y0=points[-2]; x1,y1=points[-1]
    ang=math.atan2(y1-y0,x1-x0); aw=12; aa=0.45
    p1=(x1-aw*math.cos(ang-aa),y1-aw*math.sin(ang-aa))
    p2=(x1-aw*math.cos(ang+aa),y1-aw*math.sin(ang+aa))
    d.polygon([(x1,y1),p1,p2],fill=col)
    # label on the longest horizontal segment
    best = 0; bi = 0
    for i in range(len(points)-1):
        if points[i][1]==points[i+1][1]:
            ln = abs(points[i+1][0]-points[i][0])
            if ln>best: best=ln; bi=i
    mx=(points[bi][0]+points[bi+1][0])//2
    my=points[bi][1] + label_offset
    w2,_=tw(label,F11B)
    rr(mx-w2//2-10,my-10,mx+w2//2+10,my+10,10,(20,24,42,235),col,2)
    ctext(label,mx,my,F11B,col)

# Browser ↔ Frontend (static bundle, dashed): direct between them
poly_arrow([(X_FRONTEND-NODE_W//2, ROW_Y),(X_BROWSER+NODE_W//2, ROW_Y)], PURPLE, "static bundle", dashed=True, label_offset=-20)

# Browser → Backend (JPEG) above
TOP = ROW_Y - NODE_H//2 - 32
poly_arrow([(X_BROWSER, ROW_Y-NODE_H//2),(X_BROWSER, TOP),(X_BACKEND, TOP),(X_BACKEND, ROW_Y-NODE_H//2)], BLUE, "WS  JPEG frames  10 fps")

# Backend → Browser (annotated) below
BOT = ROW_Y + NODE_H//2 + 32
poly_arrow([(X_BACKEND, ROW_Y+NODE_H//2),(X_BACKEND, BOT),(X_BROWSER, BOT),(X_BROWSER, ROW_Y+NODE_H//2)], GREEN, "WS  annotated frames", label_offset=14)

# Backend ↔ DB
poly_arrow([(X_BACKEND+NODE_W//2, ROW_Y-14),(X_DB-NODE_W//2, ROW_Y-14)], AMBER, "INSERT roi_records", label_offset=-16)
poly_arrow([(X_DB-NODE_W//2, ROW_Y+14),(X_BACKEND+NODE_W//2, ROW_Y+14)], GREY, "SELECT", dashed=True, label_offset=18)

# ── Section panels below ──
PANEL_Y = 410
PANEL_H = 280

def panel(x0, y0, x1, y1, title, accent, icon=""):
    # glow
    layer = Image.new("RGBA",(W,H),(0,0,0,0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x0-4,y0-4,x1+4,y1+4], radius=18, fill=accent+(60,))
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    img.paste(layer, (0,0), layer)
    nd = ImageDraw.Draw(img, 'RGBA')
    nd.rounded_rectangle([x0,y0,x1,y1], radius=14, fill=(22,26,46,235), outline=accent, width=2)
    # header strip
    nd.rounded_rectangle([x0,y0,x1,y0+34], radius=14, fill=accent+(35,))
    nd.rectangle([x0,y0+24,x1,y0+34], fill=(22,26,46,255))
    # title
    nd.text((x0+16, y0+9), f"{icon}  {title}" if icon else title, font=F13B, fill=accent)

# 4 panels: Browser UI | Frontend Build | Backend Services (large) | Database
P1_X = (60, 320)
P2_X = (340, 600)
P3_X = (620, 1020)   # bigger - center
P4_X = (1040, 1240)

panel(P1_X[0], PANEL_Y, P1_X[1], PANEL_Y+PANEL_H, "BROWSER UI", BLUE, "🌐")
panel(P2_X[0], PANEL_Y, P2_X[1], PANEL_Y+PANEL_H, "FRONTEND BUILD", PURPLE, "⚛")
panel(P3_X[0], PANEL_Y, P3_X[1], PANEL_Y+PANEL_H, "BACKEND SERVICES", CYAN, "⚡")
panel(P4_X[0], PANEL_Y, P4_X[1], PANEL_Y+PANEL_H, "DATABASE", GREEN, "🗄")

d = ImageDraw.Draw(img, 'RGBA')

def chip(x0, y0, x1, y1, label, col, sub=None):
    rr(x0,y0,x1,y1, 9, (32,38,62,255), col, 2)
    if sub:
        ctext(label, (x0+x1)//2, (y0+y1)//2 - 6, F11B, WHITE)
        ctext(sub, (x0+x1)//2, (y0+y1)//2 + 9, F9, TEXT2)
    else:
        ctext(label, (x0+x1)//2, (y0+y1)//2, F11B, col)

# Browser UI items
items_b = [("📹  Webcam Capture", "getUserMedia · 640×480"),
           ("📺  Live Video Feed", "annotated stream"),
           ("📊  ROI Dashboard", "stats · history · health")]
for i,(lbl,sub) in enumerate(items_b):
    chip(P1_X[0]+14, PANEL_Y+50+i*72, P1_X[1]-14, PANEL_Y+106+i*72, lbl, BLUE, sub)

# Frontend Build items
items_f = [("⚛  React App", "Vite bundler"),
           ("📦  Static Bundle", "JS · CSS · HTML"),
           ("🔀  nginx:alpine", "reverse proxy")]
for i,(lbl,sub) in enumerate(items_f):
    chip(P2_X[0]+14, PANEL_Y+50+i*72, P2_X[1]-14, PANEL_Y+106+i*72, lbl, PURPLE, sub)

# Backend services - endpoints + pipeline split into two columns
ep_x0 = P3_X[0]+14; ep_x1 = P3_X[0]+200
endpoints = [
    ("WS",   "/ws/ingest/{id}",   BLUE),
    ("WS",   "/ws/stream/{id}",   GREEN),
    ("POST", "/api/sessions",     PURPLE),
    ("GET",  "/api/.../roi",      AMBER),
]
ctext("ENDPOINTS", (ep_x0+ep_x1)//2, PANEL_Y+50, F11B, TEXT2)
for i,(verb, path, col) in enumerate(endpoints):
    y = PANEL_Y+72+i*42
    rr(ep_x0, y, ep_x1, y+34, 8, (32,38,62,255), col, 2)
    # verb badge
    rr(ep_x0+6, y+6, ep_x0+48, y+28, 6, col+(60,), col, 1)
    ctext(verb, ep_x0+27, y+17, F10, col)
    d.text((ep_x0+56, y+10), path, font=F11, fill=TEXT)

# Pipeline column
pp_x0 = P3_X[0]+220; pp_x1 = P3_X[1]-14
ctext("PROCESSING PIPELINE", (pp_x0+pp_x1)//2, PANEL_Y+50, F11B, TEXT2)
steps = [
    ("①", "Decode JPEG", "Pillow / io.BytesIO", BLUE),
    ("②", "Detect Face", "MediaPipe · short-range", PURPLE),
    ("③", "Draw ROI Box", "Pillow ImageDraw", AMBER),
    ("④", "Re-encode", "JPEG · q=0.7", PINK),
    ("⑤", "Persist + Broadcast", "DB write · WS push", GREEN),
]
for i,(num, name, sub, col) in enumerate(steps):
    y = PANEL_Y+72+i*36
    rr(pp_x0, y, pp_x1, y+30, 7, (32,38,62,255), col, 2)
    # num
    rr(pp_x0+6, y+5, pp_x0+30, y+25, 6, col+(60,), col, 1)
    ctext(num, pp_x0+18, y+15, F12B, col)
    d.text((pp_x0+38, y+5), name, font=F12B, fill=WHITE)
    d.text((pp_x0+38, y+18), sub, font=F9, fill=TEXT2)

# Database panel
ctext("TABLES", (P4_X[0]+P4_X[1])//2, PANEL_Y+50, F11B, TEXT2)
tables = [
    ("sessions", "id · label · created_at"),
    ("roi_records", "session_id · x,y,w,h · conf"),
]
for i,(name, cols) in enumerate(tables):
    y = PANEL_Y+72+i*54
    rr(P4_X[0]+14, y, P4_X[1]-14, y+44, 8, (32,38,62,255), GREEN, 2)
    ctext(name, (P4_X[0]+P4_X[1])//2, y+13, F12B, GREEN)
    ctext(cols, (P4_X[0]+P4_X[1])//2, y+30, F9, TEXT2)
# FK link
ctext("🔗  session_id  FK", (P4_X[0]+P4_X[1])//2, PANEL_Y+186, F10, AMBER)
# stack mini list
ctext("STACK", (P4_X[0]+P4_X[1])//2, PANEL_Y+214, F11B, TEXT2)
mini = ["MediaPipe", "Pillow", "SQLAlchemy"]
for i,s in enumerate(mini):
    ctext("· "+s, (P4_X[0]+P4_X[1])//2, PANEL_Y+234+i*14, F10, TEXT2)

# ── Right side: Legend + flow summary ──
LX0, LY0, LX1, LY1 = 1260, 130, 1380, 380
panel(LX0, LY0, LX1, LY1, "LEGEND", AMBER, "🔑")
d = ImageDraw.Draw(img, 'RGBA')
leg = [
    (BLUE,   "JPEG in (WS)"),
    (GREEN,  "Frames out (WS)"),
    (PURPLE, "Static / HTTP"),
    (AMBER,  "DB INSERT"),
    (GREY,   "DB SELECT"),
]
for i,(col,lbl) in enumerate(leg):
    y = LY0 + 50 + i*36
    d.line([(LX0+14, y),(LX0+44, y)], fill=col, width=3)
    d.polygon([(LX0+44,y),(LX0+38,y-4),(LX0+38,y+4)], fill=col)
    d.text((LX0+52, y-7), lbl, font=F10, fill=TEXT)

# ── Footer flow summary ──
FY = 720
ctext("END-TO-END FLOW", W//2, FY-2, F13B, TEXT)
flow = "📷  Webcam  →  🌐  Browser  →  ⚡  FastAPI  →  🧠  MediaPipe  →  🎨  Pillow Draw  →  💾  PostgreSQL  →  📺  Live View"
ctext(flow, W//2, FY+22, F12B, (200,210,240))

# tagline bottom-right
ctext("No OpenCV · Pure Python pipeline", W-200, H-22, F10, TEXT3)
ctext("orchestrated via docker-compose", 200, H-22, F10, TEXT3)

out = os.path.join(os.path.dirname(__file__), "architecture-diagram.png")
img.save(out, "PNG", dpi=(150,150))
print(f"Saved: {out}")
