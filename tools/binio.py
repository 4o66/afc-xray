import numpy as np, struct
def rdbin(p):
    b=open(p,"rb").read(); nv,nt=struct.unpack_from("<II",b,0); lo=np.array(struct.unpack_from("<3f",b,8)); sc=np.array(struct.unpack_from("<3f",b,20))
    q=np.frombuffer(b,"<u2",nv*3,32).reshape(-1,3); o=32+nv*6+(2 if (nv*3)%2 else 0)
    F=np.frombuffer(b,"<u4",nt*3,o).reshape(-1,3); return lo+q*sc, F.astype(np.int64)
