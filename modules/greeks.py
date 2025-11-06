import math

def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def _norm_pdf(x):
    return (1 / math.sqrt(2*math.pi)) * math.exp(-0.5 * x**2)

def d1_d2(S, K, r, q, sigma, T):
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return float("nan"), float("nan")
    d1 = (math.log(S/K) + (r - q + 0.5*sigma*sigma)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return d1, d2

def greeks(S, K, r, q, sigma, T, call=True):
    d1, d2 = d1_d2(S,K,r,q,sigma,T)
    if any(map(lambda x: math.isnan(x), [d1,d2])):
        return None, None, None
    if call:
        delta = math.exp(-q*T) * _norm_cdf(d1)
    else:
        delta = -math.exp(-q*T) * _norm_cdf(-d1)
    vega = S * math.exp(-q*T) * _norm_pdf(d1) * math.sqrt(T)
    theta = -(S*math.exp(-q*T)*_norm_pdf(d1)*sigma)/(2*math.sqrt(T))
    return delta, theta, vega
