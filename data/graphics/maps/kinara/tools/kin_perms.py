import json, numpy as np
from PIL import Image
T='/home/claude/scratch/tiles/'
hits=json.load(open(T+'prop_hits.json')); B=json.load(open(T+'building_boxes.json'))
typ=np.zeros((32,32),np.uint8); col=np.zeros((32,32),np.uint8)
def blk(c,r):
    if 0<=c<32 and 0<=r<32: col[r,c]=0x80
# water: from ground pixels (teal)
g=np.asarray(Image.open(T+'ground_clean.png').convert('RGB')).astype(int)
for r in range(32):
  for c in range(32):
    cell=g[r*16:r*16+16,c*16:c*16+16]
    water=((cell[...,2]>cell[...,0]+15)&(cell[...,1]>cell[...,0]+15)).mean()
    if water>0.5: typ[r,c]=0x15
for r in (15,16):
  for c in range(25,32):
    if c<31: typ[r,c]=0
# paddy -> tall grass
for r,c in [(10,0),(10,1),(10,2),(11,0),(11,1),(11,2),(12,0),(12,1),(12,2),(29,18),(29,19),(30,18),(30,19)]:
    pass
pad=np.zeros((512,512),bool); pad[160:208,0:48]=True; pad[464:496,288:320]=True
for r in range(32):
  for c in range(32):
    pass  # paddy stays plain ground (no tall-grass rustle in town)
small={'coconut_palm_healthy','coconut_palm_drought','banana_plant','hibiscus_bush','marigold_pot','signpost','helion_pump','water_level_marker','well','laterite_wall_corner','bamboo_fence_corner'}
wide={'banyan_shrine':2,'houseboat_stranded':2,'canoe':1,'clothesline':1,'chinese_fishing_net':1,'bamboo_fence':1}
for p in hits:
    w,h=p['w'],p['h']
    for x,y,_ in p['hits']:
        nm=p['prop']
        if nm=='jetty_post': continue
        if nm in small or nm not in wide:
            blk(int((x+w/2)//16), int((y+h-3)//16))
        else:
            for rr in range(wide[nm]):
                for c in range(int((x+2)//16), int((x+w-3)//16)+1): blk(c, int((y+h-3)//16)-rr)
ART={'player_house':(146,128,222,191),'kabir_house':(258,144,318,191),'lab':(368,127,432,191),'neighbor':(114,320,174,367),'wall_h':(128,98,241,111),'wall_v':(127,98,136,128),'plant_x':(108,98,127,124)}
for k,(x0,y0,x1,y1) in ART.items():
    if k=='plant_x': blk(int(116//16), int(120//16)); continue
    for r in range(int((y0+4)//16), int((y1-2)//16)+1):
        for c in range(int((x0+3)//16), int((x1-4)//16)+1): blk(c,r)
# fix building boxes using actual art extents (from model gen printout)
doors={'player':(11,11),'kabir':(18,11),'lab':(25,11),'neighbor':(9,22)}
for c,r in doors.values(): typ[r,c]=0x69; col[r,c]=0x80
# edges
col[0,:]=0x80; col[31,:]=0x80
for r in range(32):
    if r not in (15,16): col[r,0]=0x80
# water tiles are not blocked (surf)
out=bytearray()
for r in range(32):
  for c in range(32): out+=bytes([typ[r,c],col[r,c]])
open('/home/claude/kin/land/permissions.bin','wb').write(out)
sym={0:'.',0x15:'~',0x02:'"',0x69:'D'}
for r in range(32): print(''.join(('D' if typ[r,c]==0x69 else '#') if col[r,c] else sym.get(typ[r,c],'?') for c in range(32)))
