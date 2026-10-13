import sys,glob
from PIL import Image
fs=sorted(glob.glob(sys.argv[1]+'-*.png'),key=lambda f:int(f.rsplit('-',1)[1][:-4]))
ims=[Image.open(f) for f in fs];w,h=ims[0].size;c=int(sys.argv[3]) if len(sys.argv)>3 else 2
S=Image.new('RGB',(w*c+8*(c-1),(h+8)*((len(ims)+c-1)//c)),'#555')
for i,im in enumerate(ims):S.paste(im,((i%c)*(w+8),(i//c)*(h+8)))
S.save(sys.argv[2])
