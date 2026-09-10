import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import streamlit as st
from antenna import DEFAULTS, geometry, model
from exporter import export_script

st.set_page_config(page_title='IF Antenna Lab by David Metts', page_icon='📡', layout='wide')
st.title('IF Antenna Lab by David Metts')
st.caption('2.4 GHz · Printed inverted-F · FR4')
st.info('Explore an educational lumped-circuit approximation. These curves are not full-wave simulation results; export the geometry for a separate openEMS study.')

p = DEFAULTS.copy()  # The one shared parameter dictionary for this render.
with st.sidebar:
    st.header('Geometry')
    st.caption('All dimensions in millimetres')
    p['short_mm'] = st.slider('Shorting stub length',4.,9.,6.,0.1)
    p['width_mm'] = st.slider('Trace width',0.5,2.,1.,0.1)
    p['arm_mm'] = st.slider('Top arm length',10.,24.,p['arm_mm'],0.1)
    feed_max = round(p['short_mm']-0.5,1)
    if 'feed' in st.session_state:
        st.session_state.feed = min(feed_max,st.session_state.feed)
    p['feed_mm'] = st.slider('Feed stub length',1.,feed_max,min(4.5,feed_max),0.1,key='feed')
    lo,hi = round(p['width_mm']+0.5,1),round(p['arm_mm']-p['width_mm'],1)
    if 'position' in st.session_state:
        st.session_state.position = max(lo,min(hi,st.session_state.position))
    p['position_mm'] = st.slider('Feed position',lo,hi,max(lo,min(3.5,hi)),0.1,key='position')
    st.caption('Feed position is measured from the short centre. Bounds keep traces separate and the feed gap ≥ 0.5 mm.')

ntw, components = model(p)
idx = int(np.flatnonzero(ntw.f == 2.4e9)[0])
z = ntw.z[idx,0,0]
gamma = ntw.s[:,0,0]
db = 20*np.log10(np.maximum(np.abs(gamma),1e-12))
c1,c2,c3 = st.columns(3)
c1.metric('Impedance at 2.400 GHz',f'{z.real:.2f} {z.imag:+.2f}j Ω')
c2.metric('S11 at 2.400 GHz',f'{db[idx]:.2f} dB')
c3.metric('Lowest S11 in sweep',f'{ntw.f[np.argmin(db)]/1e9:.3f} GHz')

left,right = st.columns(2)
with left:
    st.subheader('Reflection · S11')
    fig,ax=plt.subplots(figsize=(6,4))
    ax.plot(ntw.f/1e9,db,color='#087f8c',lw=2)
    ax.scatter([2.4],[db[idx]],color='#e68a2e',zorder=4)
    ax.axvline(2.4,color='#e68a2e',ls=':',alpha=.6)
    ax.axhline(-10,color='gray',ls='--',lw=.8,label='−10 dB reference')
    ax.set(xlabel='Frequency (GHz)',ylabel='S11 (dB)',xlim=(2,2.8))
    ax.grid(alpha=.2); ax.legend(); fig.tight_layout()
    st.pyplot(fig); plt.close(fig)
with right:
    st.subheader('Impedance · Smith chart')
    fig,ax=plt.subplots(figsize=(6,4))
    ntw.plot_s_smith(m=0,n=0,ax=ax,show_legend=False,color='#087f8c',lw=2)
    ax.scatter(gamma[idx].real,gamma[idx].imag,color='#e68a2e',s=55,zorder=5,label='2.400 GHz')
    ax.legend(loc='upper right'); fig.tight_layout()
    st.pyplot(fig); plt.close(fig)
    st.caption('Impedance chart normalized to 50 Ω. The orange marker is an exact sweep sample at 2.4 GHz.')

layout,explain=st.columns([1,1])
with layout:
    st.subheader('Your printed geometry')
    fig,ax=plt.subplots(figsize=(6,4))
    ax.add_patch(Rectangle((0,p['board_y_min_mm']),40,42,facecolor='#e4f0e8',edgecolor='#789'))
    for name,(x0,y0,x1,y1) in geometry(p).items():
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#e68a2e' if name=='port' else '#087f8c',alpha=.8))
    ax.text(20,-18,'Top-layer ground',ha='center',color='white')
    ax.set(xlim=(-1,41),ylim=(-31,13),xlabel='x (mm)',ylabel='y (mm)',aspect='equal')
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.caption('Copper is teal; the orange gap is the lumped feed port. No bottom-layer ground.')
    st.download_button('Download openEMS Python script',export_script(p),file_name='ifa_openems.py',mime='text/x-python',type='primary',on_click='ignore')
    st.caption('Generates a standalone file with numeric geometry and a UTC timestamp. Downloading does not run openEMS.')
with explain:
    st.subheader('What each control changes')
    st.markdown('''**Shorting stub length** sets the arm height above the ground edge and the grounded current-path length. Increasing it generally lowers the model resonance.

**Feed stub length** extends the feed leg downward from the arm, reducing the excitation gap. A longer leg adds series feed inductance in this model.

**Top arm length** extends the open-ended radiating arm from the short centre. A longer arm lowers the approximate quarter-wave resonance.

**Trace width** changes all three conductor widths. Wider traces reduce the heuristic inductance and conductor resistance and alter end loading.

**Feed position** moves the feed along the arm, measured from the short centre. Moving away from the short increases the model's impedance transformation ratio.''')
    st.write(f'**Live input impedance:** {z.real:.2f} {z.imag:+.2f}j Ω at 2.400 GHz.')

with st.expander('Assumptions and circuit details'):
    st.markdown('''40 × 42 mm board, 1.6 mm FR4, relative permittivity 4.3, loss tangent 0.02 and 35 μm copper. These are illustrative material assumptions, not a measured laminate specification. The ground covers y = −30…0 mm on the top layer; the antenna occupies the remaining board region.

The circuit is a series feed inductance and resistance driving a tapped parallel RLC resonator. Effective permittivity is approximated by (εr + 1)/2 and resonance by c/[4(short + arm + 0.4 width)√εeff]. The tap uses sin²(π position / 2 arm). RLC values and loss coefficients are heuristic, with no full-wave or measurement calibration. Connector parasitics, pattern, efficiency and higher resonances are omitted. The openEMS export uses the same geometry, but its independently computed result need not match this circuit.''')
    st.write({k:float(v) for k,v in components.items()})
    st.caption('Exporter follows the official openEMS Python API and conducting-sheet model. Mesh convergence and material characterization remain necessary for engineering use.')

