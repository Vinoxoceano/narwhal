import unittest
from narwhal import Bathymetry, Cast, CastCollection
import numpy as np

try:
    from karta import Line
    from karta.crs import LonLatWGS84
except ImportError:
    from narwhal.geo import Line, LonLatWGS84

class BathymetryTests(unittest.TestCase):

    def setUp(self):
        x = [-17.41933333, -17.42628333, -17.42573333, -17.4254,
             -17.42581667, -17.42583333, -17.4269    , -17.4437,
             -17.44126667, -17.44416667, -17.44673333, -17.46633333, -17.48418333]
        y = [80.07101667,  80.0878    ,  80.09245   ,  80.10168333,
             80.10895   ,  80.11108333,  80.11398333,  80.12305   ,
             80.12928333,  80.1431    ,  80.1534    ,  80.16636667,  80.16741667]
        depth = [102.0,  95.0,  90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0,
                 170.0, 160.0, 140.0, 130.0]
        self.bathymetry = Bathymetry(depth, Line(list(zip(x, y)), crs=LonLatWGS84))
        return

    def test_add_to_castcollection(self):
        cc = CastCollection(
                Cast(P=np.arange(100), T=np.random.rand(100), S=np.random.rand(100),
                     coordinates=(-17.42, 80.09)),
                Cast(P=np.arange(100), T=np.random.rand(100), S=np.random.rand(100),
                     coordinates=(-17.426, 80.112)),
                Cast(P=np.arange(100), T=np.random.rand(100), S=np.random.rand(100),
                     coordinates=(-17.45, 80.16)))
        cc.add_bathymetry(self.bathymetry)
        correctresult = np.array([92.93171145156435, 123.1639348135739, 150.2982311721252])
        depths = [c.properties["depth"] for c in cc]
        self.assertTrue(np.allclose(depths, correctresult))
        return

    # def test_project_along_cruise(self):
    #     cruiseline = Line([(0,0), (4,3), (6,2), (6,5)], crs=LonLatWGS84)
    #     bath = Bathymetry([(0,0), (2,1), (3,3), (5,3), (7,3), (5,4), (7,4.5)],
    #                       depth=[100, 120, 130, 135, 115, 127, 119])
    #
    #     P, Q = bath.project_along_cruise(cruiseline)
    #
    #     Pans = [0.,244562.46558282,465910.74224686,654663.50946077,
    #             914121.2637559,1024716.52731376,1080015.10269574]
    #     Qans = [0.,44497.10923469,66363.58647208,49450.41134166,
    #             111167.93504577,111050.1033939,110978.58197409]
    #     for (pa,qa),(p,q) in zip(zip(Pans, Qans), zip(P, Q)):
    #         self.assertAlmostEqual(pa, p, 4)
    #         self.assertAlmostEqual(qa, q, 4)
    #     return

if __name__ == "__main__":
    unittest.main()
