"""Generate a standalone script; never import or execute openEMS here."""
from datetime import datetime, timezone
from antenna import geometry

def export_script(p, timestamp=None):
    g = geometry(p)
    stamp = timestamp or datetime.now(timezone.utc).isoformat()
    header = '# Generated UTC: '+stamp+'\n'
    header += ''.join(f'# {k} = {v!r}\n' for k,v in p.items())
    t = p['thickness_mm']
    boxes = ''
    for name, (x0,y0,x1,y1) in g.items():
        if name != 'port':
            boxes += f'    copper.AddBox(priority=10, start={[x0,y0,t]!r}, stop={[x1,y1,t]!r})  # {name}\n'
    x0,y0,x1,y1 = g['port']
    # Bake every geometry coordinate into the exported script, including mesh seeds.
    xs = sorted(set([0.,p['board_x_mm']]+[v for r in g.values() for v in (r[0],r[2])]))
    ys = sorted(set([p['board_y_min_mm'],p['board_y_max_mm']]+[v for r in g.values() for v in (r[1],r[3])]))
    return header + f'''"""Standalone printed IFA openEMS simulation.
Requires a separately installed openEMS + CSXCAD Python interface, numpy, matplotlib.
Run: python ifa_openems.py --output simulation
Replot existing results: python ifa_openems.py --output simulation --postprocess-only
Copper sheets lie on the top of FR4; no bottom ground, connector or solder mask.
Refine mesh and enlarge air box to establish convergence before design decisions.
"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from CSXCAD import ContinuousStructure
from openEMS import openEMS

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='ifa_simulation')
    parser.add_argument('--postprocess-only', action='store_true')
    args = parser.parse_args()
    path = Path(args.output).resolve()
    if not args.postprocess_only and path.exists() and any(path.iterdir()):
        parser.error('Choose an empty output directory; existing results are preserved.')
    if args.postprocess_only and not path.is_dir():
        parser.error('Existing simulation directory required.')
    path.mkdir(parents=True, exist_ok=True)
    fdtd = openEMS(NrTS=300000, EndCriteria=1e-5)
    fdtd.SetGaussExcite(2.4e9, 0.8e9)
    fdtd.SetBoundaryCond(['PML_8']*6)
    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(0.001)
    # 60 mm clearance to boundaries; PML is within this air region.
    mesh.AddLine('x', [-60.0, 100.0])
    mesh.AddLine('y', [-90.0, 72.0])
    mesh.AddLine('z', [-60.0, 61.6])
    substrate = csx.AddMaterial('FR4', epsilon={p['er']!r},
        kappa={2*3.141592653589793*2.4e9*8.8541878128e-12*p['er']*p['tan_delta']!r})
    substrate.AddBox(priority=0, start={[0.,p['board_y_min_mm'],0.]!r},
                     stop={[p['board_x_mm'],p['board_y_max_mm'],t]!r})
    copper = csx.AddConductingSheet('copper', conductivity={p['conductivity']!r}, thickness={p['copper_m']!r})
{boxes}    # In-plane y-directed port spans only the gap from ground to feed leg.
    port = fdtd.AddLumpedPort(1, {p['z0']!r}, {[x0,y0,t]!r}, {[x1,y1,t]!r},
                              'y', excite=1.0, priority=5, edges2grid='xy')
    mesh.AddLine('x', {xs!r})
    mesh.AddLine('y', {ys!r})
    mesh.AddLine('z', { [round(t*i/6,9) for i in range(7)]!r})
    # At least three cells across the narrowest trace and excitation gap.
    local_step = {min(p['width_mm'],p['short_mm']-p['feed_mm'])/3!r}
    mesh.AddLine('x', np.linspace(2.0, {4+p['arm_mm']+2!r},
                 int(np.ceil(({4+p['arm_mm']+2!r}-2.0)/local_step))+1))
    mesh.AddLine('y', np.linspace(-1.0, {p['short_mm']+p['width_mm']/2+1!r},
                 int(np.ceil(({p['short_mm']+p['width_mm']/2+2!r})/local_step))+1))
    mesh.SmoothMeshLines('all', 2.0, 1.3)
    if not args.postprocess_only:
        csx.Write2XML(str(path/'geometry.xml'))
        fdtd.Run(str(path), cleanup=False)
    frequency = np.linspace(2.0e9, 2.8e9, 801)
    port.CalcPort(str(path), frequency)
    s11 = port.uf_ref/port.uf_inc
    impedance = port.uf_tot/port.if_tot
    np.savetxt(path/'s11_impedance.csv',
        np.column_stack((frequency, s11.real, s11.imag, impedance.real, impedance.imag)),
        delimiter=',', header='frequency_Hz,S11_real,S11_imag,Z_real_ohm,Z_imag_ohm')
    fig, axes = plt.subplots(1,2,figsize=(10,4))
    axes[0].plot(frequency/1e9,20*np.log10(np.maximum(np.abs(s11),1e-12)))
    axes[0].set(xlabel='Frequency (GHz)',ylabel='S11 (dB)')
    axes[1].plot(frequency/1e9,impedance.real,label='Resistance')
    axes[1].plot(frequency/1e9,impedance.imag,label='Reactance')
    axes[1].set(xlabel='Frequency (GHz)',ylabel='Impedance (ohm)')
    axes[1].legend()
    for ax in axes:
        ax.grid(True)
    fig.tight_layout()
    fig.savefig(path/'response.png',dpi=160)
    print('Z at exactly 2.4 GHz:', impedance[400])
    print('Results:', path)

if __name__ == '__main__':
    main()
'''
