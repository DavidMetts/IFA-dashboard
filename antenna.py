"""Shared geometry and explicitly heuristic lumped IFA model. Lengths in mm."""
import numpy as np
import skrf as rf

DEFAULTS = dict(short_mm=6.0, feed_mm=4.5, arm_mm=13.7, width_mm=1.0,
                position_mm=3.5, board_x_mm=40.0, board_y_min_mm=-30.0,
                board_y_max_mm=12.0, thickness_mm=1.6, er=4.3, tan_delta=0.02,
                copper_m=35e-6, conductivity=5.8e7, z0=50.0)

def validate(p):
    if not all(np.isfinite(v) for v in p.values()):
        raise ValueError('Parameters must be finite')
    assert 4 <= p['short_mm'] <= 9
    assert 0.5 <= p['width_mm'] <= 2
    assert 10 <= p['arm_mm'] <= 24
    assert 1 <= p['feed_mm'] <= p['short_mm']-0.5
    assert p['width_mm']+0.5 <= p['position_mm'] <= p['arm_mm']-p['width_mm']

def geometry(p):
    """Conductor rectangles (xmin, ymin, xmax, ymax); source for plot and export."""
    validate(p)
    x, h, a, w, f, d = 4., p['short_mm'], p['arm_mm'], p['width_mm'], p['feed_mm'], p['position_mm']
    return dict(ground=(0.,p['board_y_min_mm'],p['board_x_mm'],0.),
                short=(x-w/2,0.,x+w/2,h+w/2),
                arm=(x-w/2,h-w/2,x+a,h+w/2),
                feed=(x+d-w/2,h-f,x+d+w/2,h+w/2),
                port=(x+d-w/2,0.,x+d+w/2,h-f))

def model(p):
    """Series feed inductance + transformed parallel RLC resonator.

    Coefficients are educational heuristics, not fitted EM results.
    scikit-rf converts the resulting impedance into a 50-ohm one-port.
    """
    validate(p)
    h,a,w,f,d = (p[k] for k in ('short_mm','arm_mm','width_mm','feed_mm','position_mm'))
    ee = (p['er']+1)/2  # crude air/substrate field mixture
    length = (h+a+0.4*w)*1e-3
    f_res = 299792458/(4*length*np.sqrt(ee))
    L = 8e-9*(h+a)/21/w**0.25
    C = 1/((2*np.pi*f_res)**2*L)
    R = 900/(1+8*p['tan_delta'])
    tap = np.sin(np.pi*d/(2*a))**2
    Lfeed = 0.22e-9*f/w**0.3
    freq = rf.Frequency(2,2.8,801,unit='ghz')
    omega = 2*np.pi*freq.f
    zin = 0.4/w + 1j*omega*Lfeed + tap/(1/R + 1j*(omega*C-1/(omega*L)))
    network = rf.Network(frequency=freq,z=zin[:,None,None],z0=p['z0'],name='Lumped approximation')
    return network, dict(f_res=f_res,L=L,C=C,R=R,tap=tap,Lfeed=Lfeed)

