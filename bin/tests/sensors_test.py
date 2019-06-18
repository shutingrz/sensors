import unittest
import os
import sys
import json
import tempfile
from flask import Flask
import subprocess
import app as sensors_app
import time

# ここなんとかしたい・・・
tempDB = tempfile.mkstemp()
tempDBPath = tempDB[1]
dburl = "sqlite:///" + tempDBPath
result = subprocess.run(
    ["/bin/bash", "-c", "../scripts/init.sh %s" % tempDBPath])
time.sleep(1)

app = sensors_app.create_app(dburl)


class TestUserControl(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        rv = self.app.get("/api/")
        self.assertIn(b"Sensors", rv.data)

    def test_user_isexist(self):
        testuser = {"name": "test_user_isexist", "password": "testtest"}

        rv = self.app.get("/api/user/%s/isexist" % testuser["name"])
        json_data = rv.get_json()

        self.assertEqual(json_data["header"]["status"], "success")

    def test_user_register(self):
        testuser = {"name": "test_user_register", "password": "testtest"}

        # register
        rv = self.app.get("/api/register/user", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        # isexist
        rv = self.app.get("/api/user/%s/isexist" % testuser["name"])
        json_data = rv.get_json()
        self.assertTrue(json_data["response"])

    def test_admin_user_delete(self):
        testuser = {"name": "test_admin_user_delete", "password": "testtest"}

        # register
        rv = self.app.get("/api/register/user", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        # isexist
        rv = self.app.get("/api/user/%s/isexist" % testuser["name"])
        json_data = rv.get_json()
        self.assertTrue(json_data["response"])

        # delete
        rv = self.app.get("/api/admin/user/delete/%s" % testuser["name"])
        json_data = rv.get_json()

        # isexist
        rv = self.app.get("/api/user/%s/isexist" % testuser["name"])
        json_data = rv.get_json()
        self.assertFalse(json_data["response"])

    def test_user_login(self):
        testuser = {"name": "test_user_login", "password": "testtest"}

        # register
        rv = self.app.get("/api/register/user", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        # login
        rv = self.app.get("/api/login", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

    def test_auth_test(self):

        testuser = {"name": "test_auth_test", "password": "testtest"}

        # access login required page without session
        rv = self.app.get("/api/account/status")
        self.assertEqual(rv.status_code, 302)

        # register
        rv = self.app.get("/api/register/user", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        # login
        rv = self.app.get("/api/login", query_string=dict(
            username=testuser["name"],
            password=testuser["password"]
        ))
        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        session = rv.headers["Set-Cookie"]
        self.assertIn("session", session)

        # access login required page with session
        rv = self.app.get("/api/account/status", headers={"Cookie": session})
        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")


class TestAccountControl(unittest.TestCase):

    testuser = {"name": "test_account_control", "password": "testtest"}

    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()

        # register
        rv = cls.app.get("/api/register/user", query_string=dict(
            username=cls.testuser["name"],
            password=cls.testuser["password"]
        ))
        json_data = rv.get_json()
        assert json_data["header"]["status"] == "success"

        # login
        rv = cls.app.get("/api/login", query_string=dict(
            username=cls.testuser["name"],
            password=cls.testuser["password"]
        ))
        json_data = rv.get_json()
        assert json_data["header"]["status"] == "success"

        cls.session = rv.headers["Set-Cookie"]

    def test_device_register(self):
        testdevice = {"device_name": "testdev", "sensor_type": "1"}

        rv = self.app.get("/api/register/device",
                          headers={"Cookie": self.session}, query_string=dict(
                              device_name=testdevice["device_name"],
                              sensor_type=testdevice["sensor_type"]
                          ))

        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()

        self.assertEqual(json_data["header"]["status"], "success")

        # get device list
        rv = self.app.get("/api/account/status",
                          headers={"Cookie": self.session})
        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

    def test_temperature_view(self):

        testdevice = {"device_name": "testdev2", "sensor_type": "1"}

        # device register
        rv = self.app.get("/api/register/device",
                          headers={"Cookie": self.session}, query_string=dict(
                              device_name=testdevice["device_name"],
                              sensor_type=testdevice["sensor_type"]
                          ))

        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        device_id = json_data["response"]["device_id"]
        self.assertIsNotNone(device_id)

        # device view
        rv = self.app.get("/api/device/temperature/%s" % device_id,
                          headers={"Cookie": self.session})

        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

    def test_temperature_record(self):
        from datetime import datetime

        testdevice = {"device_name": "testdev3", "sensor_type": "1"}

        # create testdata
        test_records = []
        now = datetime.now()
        basetime = int(now.timestamp())

        for i in range(0, 101):  # prepare 101 records
            record = {
                "time": basetime + i*60,
                "value": str(20)
            }
            test_records.append(record)

        # device register
        rv = self.app.get("/api/register/device",
                          headers={"Cookie": self.session}, query_string=dict(
                              device_name=testdevice["device_name"],
                              sensor_type=testdevice["sensor_type"]
                          ))

        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        api_key = json_data["response"]["api_key"]
        device_id = json_data["response"]["device_id"]
        self.assertIsNotNone(api_key)
        self.assertIsNotNone(device_id)

        # temperature record
        for record in test_records:

            rv = self.app.get("/api/record/temperature", query_string=dict(
                api_key=api_key,
                time=record["time"],
                value=record["value"]
            ))

            self.assertEqual(rv.status_code, 200)
            json_data = rv.get_json()
            self.assertEqual(json_data["header"]["status"], "success")

        # device view
        rv = self.app.get("/api/device/temperature/%s" % device_id,
                          headers={"Cookie": self.session})

        self.assertEqual(rv.status_code, 200)

        json_data = rv.get_json()
        self.assertEqual(json_data["header"]["status"], "success")

        # max 100 records check
        res_records = json_data["response"]
        self.assertLess(len(res_records), 101)


if __name__ == '__main__':
    unittest.main()
