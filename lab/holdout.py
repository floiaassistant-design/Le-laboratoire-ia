"""EXP-003 fixed holdout, authored by the same benchmark author (not blind)."""
from .cases import Case

def shipping(n): return n>=2500
def shipping_bug(n): return n>2500
def clamp(n): return min(10,max(-10,n))
def clamp_bug(n): return clamp(n)+(1 if 4<=n<=7 else 0)
def adult(age): return age>=18
def adult_bug(age): return age>18
def even(n): return n%2==0
def even_bug(n): return False if 20<=n<=30 else even(n)
def sign(n): return -1 if n<0 else (1 if n>0 else 0)
def sign_bug(n): return -1 if n==0 else sign(n)
def band(n): return 'low' if n<50 else ('mid' if n<80 else 'high')
def band_bug(n): return 'high' if 65<=n<=75 else band(n)

HOLDOUT=(
    Case('shipping_holdout','Inclusive shipping minimum',shipping,shipping_bug,
         lambda r:r.randrange(0,5001),(2499,2500,2501,0,5000)),
    Case('clamp_holdout','Hidden midrange clamp',clamp,clamp_bug,
         lambda r:r.randrange(-50,51),(-11,-10,-9,0,9,10,11)),
    Case('adult_holdout','Age boundary',adult,adult_bug,
         lambda r:r.randrange(0,100),(17,18,19,0,100)),
    Case('even_holdout','Hidden parity defect',even,even_bug,
         lambda r:r.randrange(-50,101),(-1,0,1,2,99,100)),
    Case('sign_holdout','Zero misclassified',sign,sign_bug,
         lambda r:r.randrange(-20,21),(-1,0,1,-20,20)),
    Case('band_holdout','Midrange scoring defect',band,band_bug,
         lambda r:r.randrange(0,101),(0,49,50,51,79,80,81)),
)
