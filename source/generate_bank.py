import ctypes as C, numpy as np, subprocess, json, base64, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
p=Path(__file__).parent
lib=C.CDLL('libfluidsynth.so.3')
def fn(n,rest,args):
 f=getattr(lib,n); f.restype=rest; f.argtypes=args; return f
ptr=C.c_void_p; I=C.c_int; D=C.c_double; S=C.c_char_p
newset=fn('new_fluid_settings',ptr,[]); setnum=fn('fluid_settings_setnum',I,[ptr,S,D]); setint=fn('fluid_settings_setint',I,[ptr,S,I]); new=fn('new_fluid_synth',ptr,[ptr]); load=fn('fluid_synth_sfload',I,[ptr,S,I]); program=fn('fluid_synth_program_select',I,[ptr,I,I,I,I]); on=fn('fluid_synth_noteon',I,[ptr,I,I,I]); off=fn('fluid_synth_noteoff',I,[ptr,I,I]); reset=fn('fluid_synth_all_sounds_off',I,[ptr,I]); write=fn('fluid_synth_write_float',I,[ptr,I,ptr,I,I,ptr,I,I]); settings=newset(); sr=32000; setnum(settings,b'synth.sample-rate',sr); setnum(settings,b'synth.gain',0.8); setint(settings,b'synth.reverb.active',0); setint(settings,b'synth.chorus.active',0); synth=new(settings); sf=load(synth,str(sys.argv[1] if len(sys.argv)>1 else '/usr/share/sounds/sf2/TimGM6mb.sf2').encode(),1); assert sf>=0
programs={'piano':(0,36,95),'epiano':(4,36,95),'marimba':(12,48,84),'bell':(14,48,84),'pluck':(24,40,84),'harp':(46,36,96),'cello':(42,36,77),'flute':(73,60,95),'trumpet':(56,54,85),'clarinet':(71,50,92),'bass':(33,28,64),'distguitar':(30,40,84),'overdrive':(29,40,84),'choir':(52,48,83),'voice':(53,48,83),'trombone':(57,40,77)}
def render(n):
 a=np.empty((n,),np.float32); b=np.empty_like(a); write(synth,n,a.ctypes.data,0,1,b.ctypes.data,0,1); return (a+b)/2
jobs=[]
for key,(pr,lo,hi) in programs.items():
 program(synth,0,sf,0,pr)
 for n in sorted(set([lo,hi]+list(range(lo,hi+1,4)))):
  reset(synth,0); on(synth,0,n,85); a=render(int(sr*5.2)); off(synth,0,n); a=np.concatenate([a,render(int(sr*.35))]); blocks=a[:(len(a)//3200)*3200].reshape(-1,3200); level=np.percentile(np.sqrt(np.mean(blocks**2,axis=1)),85); peak=np.max(np.abs(a)); g=min(.15/max(level,.005),.85/max(peak,.001)); a*=g; a[-1600:]*=np.linspace(1,0,1600); jobs.append((key,n,(np.clip(a,-1,1)*32767).astype('<i2').tobytes()))
def encode(j):
 k,n,b=j; o=subprocess.run(['lame','--silent','-r','-s','32','--bitwidth','16','--signed','--little-endian','-m','m','-b','40','-','-'],input=b,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout; return k,n,base64.b64encode(o).decode()
bank={}
with ThreadPoolExecutor(max_workers=8) as ex:
 for k,n,s in ex.map(encode,jobs): bank.setdefault(k,{})[n]=s
(p/'bank.json').write_text(json.dumps(bank,separators=(',',':'))); print(len(jobs), (p/'bank.json').stat().st_size)
