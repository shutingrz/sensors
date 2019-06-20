from flask import current_app
import sqlalchemy

from sensors.util import Util

from sensors import db
from sensors.db.orm.authentication import Authentication
from sensors.db.orm.user import User
from sensors.db.orm.device import Device
from sensors.db.orm.sensor_type import SensorType


class DeviceModel(object):

    def __init__(self):
        pass

    def device_get(self, user_hash, device_id):

        try:
            device_result = db.session.query(Device).filter(Device.user_hash == user_hash, Device.device_id == device_id).first()

            if not device_result:
                return "device not found", 110
        except Exception as exc:
            current_app.logger.critical("device_get: Unknown error: %s" % exc)
            return None, 199

        device_dict = { "device_name": device_result.device_name,
                            "device_id": device_result.device_id,
                            "sensor_type": device_result.sensor_type,
                            "api_key": device_result.api_key}
        return device_dict, 0


    def device_list(self, user_hash):

        try:
            device_result = db.session.query(Device).filter(Device.user_hash == user_hash).all()
        except Exception as exc:
            current_app.logger.critical("device_list: Unknown error: %s" % exc)
            return None, 199

        devices = []
        
        for device in device_result:
            device_dict = { "device_name": device.device_name,
                            "device_id": device.device_id,
                            "sensor_type": device.sensor_type,
                            "api_key": device.api_key}
            
            devices.append(device_dict)

            
        msg = {"devices": devices}

        return msg, 0


    def device_register(self, user_hash, device_name, sensor_type):

        device_id = Util.generateRandomString(32)
        api_key = Util.generateRandomString(32)

        try:
            # 存在するセンサータイプが指定されているか
            sensorType = db.session.query(SensorType)\
                .filter(SensorType.sensor_id == sensor_type)\
                .first()

            if not sensorType:
                return None, 99

            # デバイス登録
            db.session.add(Device(
                device_id=device_id,
                device_name=device_name,
                sensor_type=sensor_type,
                user_hash=user_hash,
                api_key=api_key))
            
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            current_app.logger.critical("SQL Integrity error: %s" % exc)
            return None, 110
        except Exception as exc:
            current_app.logger.critical("Unknown error: %s" % exc)
            return None, 199
        
        device_dict = { "device_name": device_name,
                        "device_id": device_id,
                        "sensor_type": sensor_type,
                        "api_key": api_key}

        return device_dict, 0


    def device_delete(self, user_hash, device_id):

        try:
            # 指定されたデバイスが存在するかチェック
            device_result = db.session.query(Device)\
                        .filter(Device.user_hash == user_hash)\
                        .filter(Device.device_id == device_id)\
                        .first()

            if not device_result:
                return None, 99

            # デバイス情報を削除
            db.session.query(Device)\
                .filter(Device.device_id == device_id)\
                .delete()
            
            db.session.commit()

        except sqlalchemy.exc.IntegrityError as exc:
            current_app.logger.critical("SQL Integrity error: %s" % exc)
            return None, 110
        except Exception as exc:
            current_app.logger.critical("Unknown error: %s" % exc)
            return None, 199
        
        msg = "ok"
        return msg, 0






        

