from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import hashlib, json, textwrap
BASE=Path('/mnt/data'); OUT=BASE/'reland_v6';OUT.mkdir(exist_ok=True)
SOURCE=BASE/'41769.jpg'
LOGO=BASE/'reland_v5/RELAND_user_logo_crop_v5.png'
IMG=Image.open(SOURCE).convert('RGB').resize((1600,900), Image.Resampling.LANCZOS)
LOG=Image.open(LOGO).convert('RGB')
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
R='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def font(sz,b=True):return ImageFont.truetype(F if b else R,sz,index=0)
categories=[
('분담금·감정평가','분담금·감정평가','추정 금액과 권리가액의 차이','기준일 · 평가자료 · 관리처분'),
('조합 갈등·총회','조합총회와 의결','총회 절차와 의결 요건 읽기','정족수 · 서류 · 의결 효력'),
('행정절차·정보공개','행정절차·정보공개','정보공개청구와 고시 확인','신청 절차 · 원문 · 기한'),
('행정심판·불복','행정심판과 불복','행정처분에 대응하는 절차','처분통지 · 이유 · 불복기간'),
('행정소송·인가취소','행정소송·인가취소','인가 효력을 다투는 쟁점','소송요건 · 처분성 · 증빙'),
('민사소송·소장 읽기','민사소송·소장 읽기','재개발 민사분쟁의 기초','청구취지 · 입증자료 · 절차'),
('형사고소·사실 확인','형사고소와 사실 확인','의혹과 확인된 사실 구별하기','자료 검증 · 진술 · 절차'),
('사업단계·도면 읽기','정비사업 단계·도면','사업 진행과 도면 이해','구역지정 · 사업시행 · 설계'),
('분양·관리처분','분양·관리처분','분양신청과 관리처분 읽기','신청기간 · 권리가액 · 부담금'),
('보상·이주·갈등관리','보상·이주·갈등관리','이주와 보상 절차 준비','협의 · 고지 · 권리 확인')]
palette=['#e9c889','#b4dcac','#a7d4d7','#e6c4ad','#bdd4fa','#e7bfe7','#d1d8c5','#ffdf9a','#b6e2cc','#eac6aa']
def rgba(x,a):return tuple(int(x[i:i+2],16) for i in (1,3,5))+(a,)
def draw_wrapped(draw,text,x,y,max_w,base_size,fill):
 sz=base_size
 while sz>34 and draw.textbbox((0,0),text,font=font(sz))[2]>max_w:sz-=2
 draw.text((x,y),text,font=font(sz),fill=fill,stroke_width=0)
 return sz

def card(num,category,title,subtitle,topics,clr,branding=True):
 # Exact same approved human bitmap in every variant; no text-to-image rendering of the person.
 im=IMG.copy().convert('RGBA');lay=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(lay)
 # Dark overlay reaches only the text zone; face right of x ~790 is unchanged.
 for x in range(0,800):
  a=242 if x<420 else int(242-(x-420)/380*242)
  d.line((x,0,x,900),fill=(4,33,30,max(0,a)))
 d.rounded_rectangle((56,42,358,137),radius=9,fill=(255,255,255,245))
 # Actual owner supplied logo, pasted without regeneration.
 logo=LOG.resize((282,107),Image.Resampling.LANCZOS).convert('RGBA')
 im=Image.alpha_composite(im,lay);im.alpha_composite(logo,(62,36));d=ImageDraw.Draw(im)
 d.text((60,175),'RE:LAND  |  KANG CLASS',font=font(26),fill=rgba(clr,255))
 d.text((60,226),'실전에서 배우는 재개발·재건축',font=font(35),fill='white')
 fontsz=draw_wrapped(d,title,56,300,690,75,'#ffffff')
 d.rounded_rectangle((57,420,705,425),radius=2,fill=clr)
 d.text((61,454),subtitle,font=font(31,b=False),fill='#f0f2ee')
 # four course topic chips, always kept in left text region
 d.rounded_rectangle((56,553,708,682),radius=16,fill=(240,247,243,235))
 for i,s in enumerate(topics[:4]):
  x=77+(i%2)*314;y=573+(i//2)*52
  d.ellipse((x,y+11,x+13,y+24),fill=clr)
  d.text((x+22,y),s,font=font(26),fill='#10392f')
 d.rounded_rectangle((61,726,416,792),radius=26,fill=(245,225,169,255))
 d.text((100,735),'강의 내용 확인  →',font=font(28),fill='#15392f')
 d.rounded_rectangle((62,827,440,873),radius=9,fill=(5,30,28,205))
 d.text((81,835),'© RE:LAND · 무단 복제·배포 금지',font=font(17,b=False),fill='#f1e8cc')
 # subtle bottom right stamp on existing photo; face completely untouched.
 d.rounded_rectangle((1242,835,1569,876),radius=9,fill=(5,30,28,165))
 d.text((1262,843),'RE:LAND  ·  교육 이미지',font=font(17),fill='white')
 return im.convert('RGB')
outputs=[]
for i,(category,title,subtitle,concept, ) in enumerate(categories,1):
 chips={'분담금·감정평가':['추정 분담금','종전자산','비례율','관리처분'],
 '조합 갈등·총회':['조합총회','의결요건','총회자료','회의록'],
 '행정절차·정보공개':['정보공개','공고원문','처분 절차','행정문서'],
 '행정심판·불복':['심판 절차','집행정지','기간 확인','증빙자료'],
 '행정소송·인가취소':['인가 처분','소송요건','원고 적격','결정문'],
 '민사소송·소장 읽기':['소장 읽기','사실관계','증거 정리','답변 기한'],
 '형사고소·사실 확인':['사실 확인','고소 절차','진술 대조','증거보존'],
 '사업단계·도면 읽기':['정비계획','사업시행','도면 이해','공정 파악'],
 '분양·관리처분':['분양 신청','권리가액','분담금','관리처분'],
 '보상·이주·갈등관리':['손실 보상','이주 계획','협의 절차','권리 확인']}.get(category,[])
 f=f'kang-identity-category-{i:02d}-v6.webp';card(i,category,title,subtitle,chips,palette[i-1]).save(OUT/f,'WEBP',quality=89,method=6);outputs.append(f)
# Home/marketing banners, same untouched face.
for name,t,sub,cb,c in [
 ('kang-class-promo-identity-v6.webp','강실장 클래스','재개발·재건축 실무를 60강으로 이해하세요',['60강 커리큘럼','재개발 실전','문서와 법령','학습 사례'],'#f0d997'),
 ('kang-education-inquiry-identity-v6.webp','강의·교육 문의','재개발·재건축 교육 콘텐츠 안내',['교육 문의','자료 개선','주제별 질문','강연 제안'],'#addfd0')]:
 card(0,'홍보',t,sub,cb,c).save(OUT/name,'WEBP',quality=88,method=6);outputs.append(name)
# Journal source screenshot-style image is already owned generated art; brand and watermark add via pixel-compositing.
raw=Image.open(BASE/'static_assets--editorial-journal-v5.webp').convert('RGBA');rw,rh=raw.size
layer=Image.new('RGBA',raw.size,(0,0,0,0));dr=ImageDraw.Draw(layer)
dr.rounded_rectangle((32,22,420,116),radius=13,fill=(3,40,31,218))
dr.text((57,34),'RE:LAND 저널',font=font(48),fill='white')
dr.rounded_rectangle((rw-485,rh-80,rw-24,rh-21),radius=13,fill=(3,40,31,220))
dr.text((rw-464,rh-68),'© RE:LAND · 무단 복제·배포 금지',font=font(26),fill='white')
combined=Image.alpha_composite(raw,layer)
combined.convert('RGB').save(OUT/'editorial-journal-watermark-v6.webp','WEBP',quality=87,method=6);outputs.append('editorial-journal-watermark-v6.webp')
# immutable exact master, copy byte-for-byte for future reproducible builds
(OUT/'kang-master-approved-20261111.jpg').write_bytes(SOURCE.read_bytes())
outputs.append('kang-master-approved-20261111.jpg')
(OUT/'manifest.json').write_text(json.dumps({'identity_master':'kang-master-approved-20261111.jpg','sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_dimensions':[1536,864],'do_not_recreate_face':True,'generated':outputs},ensure_ascii=False,indent=2),encoding='utf-8')
print('generated',len(outputs),'sha256',hashlib.sha256(SOURCE.read_bytes()).hexdigest())
