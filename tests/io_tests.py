import unittest
import os
import sys
import dateutil.tz
import datetime
import numpy as np
import narwhal
from narwhal.cast import Cast, CTDCast, XBTCast, LADCP
from narwhal.cast import CastCollection
import narwhal.iohdf as hdf

from io import BytesIO
if sys.version_info[0] < 3:
    from cStringIO import StringIO
else:
    from io import StringIO

directory = os.path.dirname(__file__)
DATADIR = os.path.join(directory, "data")

class IOTests(unittest.TestCase):

    def setUp(self):
        p = np.arange(1, 1001, 2)
        temp = 10. * np.exp(-.008*p) - 15. * np.exp(-0.005*(p+100)) + 2.
        sal = -14. * np.exp(-.01*p) + 34.
        self.p = p
        self.temp = temp
        self.sal = sal
        dt = datetime.datetime(1993, 8, 18, 14, 42, 36)
        self.cast = Cast(pres=self.p, temp=self.temp, sal=self.sal, date=dt)
        self.ctd = CTDCast(self.p, self.sal, self.temp, date=dt)
        self.collection = CastCollection(self.ctd, self.ctd)
        return

    def assertFilesEqual(self, f1, f2):
        f1.seek(0)
        f2.seek(0)
        s1 = f1.read()
        s2 = f2.read()
        self.assertEqual(s1, s2)
        return

    def test_fromdict_cast(self):
        d = {"type": "cast",
             "properties": {"coordinates": (-10.0, 54.0),
                            "date": "2015-04-17 15:03 UTC",
                            "notes": "CTD touched bottom"},
             "data": {"depth": np.arange(1.0, 500.0, 2.0),
                      "temperature": np.linspace(8.0, 4.0, 250),
                      "salinity": np.linspace(32.1, 34.4, 250)}}
        cast = narwhal.cast.fromdict(d)
        self.assertEqual(cast.p["coordinates"], (-10.0, 54.0))
        self.assertEqual(cast.p["date"],
                         datetime.datetime(2015, 4, 17, 15, 3,
                                           tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(cast.p["notes"], "CTD touched bottom")

        self.assertTrue((cast["depth"] == d["data"]["depth"]).all())
        self.assertTrue((cast["temperature"] == d["data"]["temperature"]).all())
        self.assertTrue((cast["salinity"] == d["data"]["salinity"]).all())
        return

    def test_iojson_text(self):
        self.cast.save_json(os.path.join(DATADIR, "json_cast.nwl"), 
                            binary=False)

        cast = narwhal.load_json(os.path.join(DATADIR, "json_cast.nwl"))

        self.assertTrue(np.all(cast["pres"] == self.cast["pres"]))
        self.assertTrue(np.all(cast["temp"] == self.cast["temp"]))
        self.assertTrue(np.all(cast["sal"] == self.cast["sal"]))
        self.assertEqual(cast.p["date"], self.cast.p["date"])
        return

    def test_save_json_text(self):
        try:
            f = StringIO()
            self.cast.save_json(f, binary=False)
        finally:
            f.close()
        return

    def test_save_json_binary(self):
        try:
            f = BytesIO()
            self.cast.save_json(f)
        finally:
            f.close()
        return

    def test_save_collection_json_text(self):
        try:
            f = StringIO()
            self.collection.save_json(f, binary=False)
        finally:
            f.close()
        return

    def test_save_collection_json_binary(self):
        try:
            f = BytesIO()
            self.collection.save_json(f)
        finally:
            f.close()
        return

    #def test_save_zprimarykey(self):
    #    cast = Cast(np.arange(len(self.p)), temp=self.temp, sal=self.sal,
    #                primarykey="z", properties={})
    #    f = BytesIO()
    #    try:
    #        cast.save(f)
    #    finally:
    #        f.close()
    #    return

    #def test_load_text(self):
    #    cast = narwhal.read(os.path.join(DATADIR, "reference_cast_test.nwl"))
    #    ctd = narwhal.read(os.path.join(DATADIR, "reference_ctd_test.nwl"))
    #    xbt = narwhal.read(os.path.join(DATADIR, "reference_xbt_test.nwl"))
    #    self.assertEqual(cast, self.cast)
    #    self.assertEqual(ctd, self.ctd)
    #    self.assertEqual(xbt, self.xbt)
    #    return

    #def test_load_binary(self):
    #    cast = narwhal.read(os.path.join(DATADIR, "reference_cast_test.nwz"))
    #    ctd = narwhal.read(os.path.join(DATADIR, "reference_ctd_test.nwz"))
    #    xbt = narwhal.read(os.path.join(DATADIR, "reference_xbt_test.nwz"))
    #    self.assertEqual(cast, self.cast)
    #    self.assertEqual(ctd, self.ctd)
    #    self.assertEqual(xbt, self.xbt)
    #    return

    #def test_load_collection_text(self):
    #    coll = narwhal.read(os.path.join(DATADIR, "reference_coll_test.nwl"))
    #    self.assertEqual(coll, self.collection)
    #    return

    #def test_load_collection_binary(self):
    #    coll = narwhal.read(os.path.join(DATADIR, "reference_coll_test.nwz"))
    #    self.assertEqual(coll, self.collection)
    #    return

#   # def test_load_zprimarykey(self):
#   #     castl = narwhal.read(os.path.join(DATADIR, "reference_ctdz_test.nwl"))
#   #     cast = CTDCast(self.p, temp=self.temp, sal=self.sal,
#   #                    primarykey="z", properties={})
#   #     self.assertEqual(cast, castl)

#class HDFTests(unittest.TestCase):

    #def setUp(self):
    #    p = np.arange(1, 1001, 2)
    #    temp = 10. * np.exp(-.008*p) - 15. * np.exp(-0.005*(p+100)) + 2.
    #    sal = -14. * np.exp(-.01*p) + 34.
    #    self.p = p
    #    self.temp = temp
    #    self.sal = sal
    #    dt = datetime.datetime(1993, 8, 18, 14, 42, 36)
    #    self.cast = Cast(self.p, temp=self.temp, sal=self.sal, date=dt)
    #    self.ctd = CTDCast(self.p, temp=self.temp, sal=self.sal, date=dt)
    #    self.xbt = XBTCast(self.p, temp=self.temp, sal=self.sal, date=dt)
    #    self.collection = CastCollection(self.ctd, self.xbt, self.ctd)
    #    return

    #def assertFilesEqual(self, f1, f2):
    #    f1.seek(0)
    #    f2.seek(0)
    #    s1 = f1.read()
    #    s2 = f2.read()
    #    self.assertEqual(s1, s2)
    #    return

    #def test_write_cast_hdf(self):
    #    hdf.save_object(self.cast, "testcast.hdf", verbose=False)
    #    # Sorting of cast data and fields not deterministic
    #    #try:
    #    #    f1 = open("testcast.hdf", "rb")
    #    #    f2 = open(os.path.join(DATADIR, "reference_cast_test.hdf"), "rb")
    #    #    self.assertFilesEqual(f1, f2)
    #    #finally:
    #    #    f1.close()
    #    #    f2.close()
    #    return

    #def test_write_castcollection_hdf(self):
    #    hdf.save_object(self.collection, "testcoll.hdf", verbose=False)
    #    # Sorting of cast data and fields not deterministic
    #    #try:
    #    #    f1 = open("testcoll.hdf", "rb")
    #    #    f2 = open(os.path.join(DATADIR, "reference_coll_test.hdf"), "rb")
    #    #    self.assertFilesEqual(f1, f2)
    #    #finally:
    #    #    f1.close()
    #    #    f2.close()
    #    return

if __name__ == "__main__":
    unittest.main()
