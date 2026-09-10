import ast
import itertools
import unittest
import numpy as np
from streamlit.testing.v1 import AppTest
from antenna import DEFAULTS, geometry, model
from exporter import export_script

class AntennaTests(unittest.TestCase):
    def test_extremes_and_export(self):
        for h,w,a in itertools.product((4.,9.),(.5,2.),(10.,24.)):
            for f,d in itertools.product((1.,h-.5),(w+.5,a-w)):
                p=DEFAULTS | dict(short_mm=h,width_mm=w,arm_mm=a,feed_mm=f,position_mm=d)
                n,_=model(p)
                self.assertEqual(n.f[400],2.4e9)
                self.assertTrue(np.isfinite(n.s).all())
                self.assertTrue((n.z.real>0).all())
                self.assertTrue((np.abs(n.s)<=1).all())
                g=geometry(p)
                self.assertGreaterEqual(g['port'][3],.5)
                self.assertGreaterEqual(g['feed'][0]-g['short'][2],.5-1e-9)
                for x0,y0,x1,y1 in g.values():
                    self.assertTrue(0<=x0<x1<=40)
                    self.assertTrue(-30<=y0<y1<=12)
                script=export_script(p,'2026-09-10T00:00:00+00:00')
                tree=ast.parse(script)
                self.assertNotIn('from antenna',script)
                boxes=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='AddBox']
                self.assertEqual(len(boxes),5)
                for box in boxes:
                    for kw in box.keywords:
                        if kw.arg in ('start','stop'):
                            self.assertEqual(len(ast.literal_eval(kw.value)),3)

    def test_every_control_changes_response(self):
        base,_=model(DEFAULTS)
        for key in ('short_mm','feed_mm','arm_mm','width_mm','position_mm'):
            n,_=model(DEFAULTS | {key:DEFAULTS[key]+.1})
            self.assertFalse(np.allclose(base.s,n.s),key)

    def test_app_and_dynamic_bounds(self):
        app=AppTest.from_file('app.py').run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.slider),5)
        initial=app.metric[0].value
        app.slider[0].set_value(4.).run()
        self.assertEqual(len(app.exception),0)
        self.assertLessEqual(app.slider[3].value,3.5)
        self.assertNotEqual(initial,app.metric[0].value)
        app.slider[2].set_value(24.).run()
        app.slider[4].set_value(20.).run()
        app.slider[2].set_value(10.).run()
        app.slider[1].set_value(2.).run()
        self.assertEqual(len(app.exception),0)
        self.assertLessEqual(app.slider[4].value,8.)

if __name__=='__main__':
    unittest.main()
