from pathlib import Path
import struct,zlib,hashlib,math,collections

def decode(path):
 b=Path(path).read_bytes();pos=8;parts=[]
 while pos<len(b):
  n=struct.unpack(">I",b[pos:pos+4])[0];kind=b[pos+4:pos+8];data=b[pos+8:pos+8+n];pos+=n+12
  if kind==b"IHDR":w,h,depth,typ,comp,flt,interlace=struct.unpack(">IIBBBBB",data)
  elif kind==b"IDAT":parts.append(data)
 assert depth==8 and typ in (2,6) and interlace==0
 channels=3 if typ==2 else 4;stride=w*channels;raw=zlib.decompress(b"".join(parts));rows=[];prev=bytearray(stride);at=0
 for y in range(h):
  f=raw[at];at+=1;row=bytearray(raw[at:at+stride]);at+=stride
  if f==0:
   rows.append(bytes(row));prev=row;continue
  if f==2:
   row=bytearray((x+y)&255 for x,y in zip(row,prev));rows.append(bytes(row));prev=row;continue
  for x in range(stride):
   a=row[x-channels] if x>=channels else 0;b=prev[x];c=prev[x-channels] if x>=channels else 0
   if f==1:q=a
   elif f==2:q=b
   elif f==3:q=(a+b)//2
   elif f==4:
    v=a+b-c;pa=abs(v-a);pb=abs(v-b);pc=abs(v-c);q=a if pa<=pb and pa<=pc else b if pb<=pc else c
   else:q=0
   row[x]=(row[x]+q)&255
  rows.append(bytes(row));prev=row
 return w,h,channels,rows

def crop_key(decoded,rect):
 w,h,ch,rows=decoded;x0,y0,x1,y1=rect
 return hashlib.sha256(b"".join(r[x0*ch:x1*ch] for r in rows[y0:y1])).hexdigest()
