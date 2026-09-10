# Generated UTC: 2026-09-10T02:14:50.330147+00:00
# short_mm = 6.0
# feed_mm = 4.5
# arm_mm = 13.7
# width_mm = 1.0
# position_mm = 3.5
# board_x_mm = 40.0
# board_y_min_mm = -30.0
# board_y_max_mm = 12.0
# thickness_mm = 1.6
# er = 4.3
# tan_delta = 0.02
# copper_m = 3.5e-05
# conductivity = 58000000.0
# z0 = 50.0
"""Standalone printed IFA openEMS simulation.
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
    substrate = csx.AddMaterial('FR4', epsilon=4.3,
        kappa=0.011482548572222022)
    substrate.AddBox(priority=0, start=[0.0, -30.0, 0.0],
                     stop=[40.0, 12.0, 1.6])
    copper = csx.AddConductingSheet('copper', conductivity=58000000.0, thickness=3.5e-05)
    copper.AddBox(priority=10, start=[0.0, -30.0, 1.6], stop=[40.0, 0.0, 1.6])  # ground
    copper.AddBox(priority=10, start=[3.5, 0.0, 1.6], stop=[4.5, 6.5, 1.6])  # short
    copper.AddBox(priority=10, start=[3.5, 5.5, 1.6], stop=[17.7, 6.5, 1.6])  # arm
    copper.AddBox(priority=10, start=[7.0, 1.5, 1.6], stop=[8.0, 6.5, 1.6])  # feed
    # In-plane y-directed port spans only the gap from ground to feed leg.
    port = fdtd.AddLumpedPort(1, 50.0, [7.0, 0.0, 1.6], [8.0, 1.5, 1.6],
                              'y', excite=1.0, priority=5, edges2grid='xy')
    mesh.AddLine('x', [0.0, 3.5, 4.5, 7.0, 8.0, 17.7, 40.0])
    mesh.AddLine('y', [-30.0, 0.0, 1.5, 5.5, 6.5, 12.0])
    mesh.AddLine('z', [0.0, 0.266666667, 0.533333333, 0.8, 1.066666667, 1.333333333, 1.6])
    # At least three cells across the narrowest trace and excitation gap.
    local_step = 0.3333333333333333
    mesh.AddLine('x', np.linspace(2.0, 19.7,
                 int(np.ceil((19.7-2.0)/local_step))+1))
    mesh.AddLine('y', np.linspace(-1.0, 7.5,
                 int(np.ceil((8.5)/local_step))+1))
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
