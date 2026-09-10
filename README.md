# IFA Antenna Lab

Streamlit-only educational 2.4 GHz printed inverted-F dashboard. Five constrained geometry sliders drive one shared parameter dictionary, the scikit-rf lumped model, geometry preview and standalone openEMS exporter. No solver is run by the app.

## Run locally

Use Python 3.11–3.13:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud

Upload this directory's contents (including `.streamlit/config.toml`) to a new GitHub repository. In [Community Cloud](https://share.streamlit.io/), choose **Create app**, that repository, branch `main`, and entrypoint `app.py`. Choose Python 3.13 in Advanced settings and deploy. Make the app public in sharing settings so viewers need neither installation nor sign-in. Copy the actual `https://…streamlit.app` URL after it is live.

Once a repository exists, its one-click deployment link is:
`https://share.streamlit.io/deploy?repository=OWNER/REPO&branch=main&mainModule=app.py`
Replace OWNER/REPO with the real repository, or run `python deploy_link.py OWNER/REPO` to print the ready-to-use link. This opens deployment setup; it is not a published dashboard URL. No secrets, external services or openEMS installation are needed on Community Cloud.

## Geometry and approximation

All lengths are mm. Board: x=0…40, y=−30…12, z=0…1.6. Copper is a 35 μm sheet at z=1.6, conductivity 5.8e7 S/m. Top ground occupies y≤0; the bottom has no copper. Short centre x=4; default short=6, arm=13.7, width=1, feed leg=4.5 and feed position=3.5. The feed port spans y=0…(short−feed), directed +y. Arm length is from the short centre to the open tip; strip joins overlap. Sliders preserve ≥0.5 mm separation of short/feed edges, ≥0.5 mm port gap and board clearance.

FR4 εr=4.3 and tanδ=0.02 are nominal educational assumptions, not vendor guarantees. The exporter models dielectric conductivity at 2.4 GHz (constant conductivity, so effective loss tangent varies with frequency). The circuit uses an air/FR4 permittivity average, a heuristic quarter-wave resonance, a parallel RLC with position-dependent tap, and series feed inductance/resistance. See `antenna.py` for every coefficient. No circuit calibration, accuracy claim, radiation pattern or efficiency estimate is provided. Compare a converged EM model with measurements before fabrication decisions.

## Export and validation

The download is self-contained: every coordinate is a literal, with parameters and timestamp in comments. Install openEMS and its CSXCAD Python bindings separately following the official instructions. Then `python ifa_openems.py --output simulation` runs the solver and produces CSV plus S11/impedance plots. `--postprocess-only` reuses matching existing results. The script refuses to overwrite a nonempty simulation folder. Check energy convergence, mesh refinement, port sensitivity and air-box size. The dashboard never imports or executes openEMS.

Run `python -m unittest discover -s tests -v` for numeric/passivity, bounds, slider reactivity and export syntax/geometry checks. These tests do not execute openEMS; its runtime behavior has not been solver-validated.

## Primary API references

- [scikit-rf Networks](https://scikit-rf.readthedocs.io/en/latest/tutorials/Networks.html)
- [openEMS Python API](https://docs.openems.de/python/openEMS/openEMS.html)
- [Conducting sheets](https://docs.openems.de/python/CSXCAD/CSProperties/CSPropConductingSheet.html)
- [Official antenna example](https://github.com/thliebig/openEMS/blob/master/python/Tutorials/Simple_Patch_Antenna.py)
- [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

