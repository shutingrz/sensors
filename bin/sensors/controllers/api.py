from flask import Blueprint, jsonify, url_for, request, redirect, current_app
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sensors.model.sensor import SensorModel
from sensors.model.user import UserModel
from sensors.model.device import DeviceModel
from sensors.model.sensor_temperature import SensorTemperatureModel
from sensors.model.flask_user import User as FlaskUser
from sensors.util import Util

api = Blueprint('sensors_api', __name__, url_prefix='/api/')

login_manager = LoginManager()

# @api.record_once
# def on_load(state):
#	login_manager.init_app(state.app)


@login_manager.user_loader
def load_user(user_hash):
    return FlaskUser(user_hash)


@api.record_once
def on_load(state):
    login_manager.init_app(state.app)


@api.route('/')
def api_index():
    msg = "Sensors"
    return jsonify(_makeResponseMessage(msg))

@api.route('/list')
def api_user_list():
    model = UserModel()

    page = request.args.get('page', None)

    msg, code = model.user_list(page)

    if msg is None:
        return jsonify(_makeErrorMessage(code))
    else:
        return jsonify(_makeResponseMessage(msg))

@api.route('/login')
def api_login():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    if username is None or password is None:
        return jsonify(_makeErrorMessage(11))

    if len(username) > Util.MaxUsernameLength or len(password) > Util.MaxUserPassLength:
        return jsonify(_makeErrorMessage(12))

    model = UserModel()
    user, code = model.user_login(username, password)

    if user is None:
        return jsonify(_makeErrorMessage(code))
    else:
        if user:
            login_user(user)
            msg = "login successful"
            return jsonify(_makeResponseMessage(msg))
        else:
            return jsonify(_makeErrorMessage(21))


@api.route('/logout')
@login_required
def logout():
    logout_user()
    msg = "logout successful"
    return jsonify(_makeResponseMessage(msg))

#todo. デザインとかできたらPOSTのフォームを受け付けるようにする
# todo. デザインとかできたらAPIから通常画面にする？
@api.route('/register/user')
def api_user_register():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    if username is None or password is None:
        return jsonify(_makeErrorMessage(11))

    if len(username) > Util.MaxUsernameLength or len(password) > Util.MaxUserPassLength:
        return jsonify(_makeErrorMessage(12))

    model = UserModel()

    # get first element, because user_isExist returns "True/False, code".
    if model.user_isExist(username)[0]:
        return jsonify(_makeErrorMessage(13))

    msg, code = model.user_register(username, password)

    if msg is None:
        return jsonify(_makeErrorMessage(code))

    return jsonify(_makeResponseMessage(msg))


# ユーザ削除, デバッグ用のためユーザ認証は不要.
# todo. 本番運用時は削除!!
@api.route('/admin/user/delete/<username>')
def api_admin_user_delete(username):
    if Util.DebugMode is False:
        return jsonify(_makeErrorMessage(0))

    model = UserModel()

    if model.user_isExist(username)[0]:
        msg, code = model.user_delete(username)

        if msg is None:
            return jsonify(_makeErrorMessage(code))
        else:
            return jsonify(_makeResponseMessage(msg))
    else:
        return jsonify(_makeErrorMessage(13))


'''
api_userid_isExist
ユーザの存在確認(重複登録防止)

todo: ブルートフォース攻撃対策
'''
@api.route('/user/<username>/isexist')
def api_userid_isExist(username):
    model = UserModel()
    msg, code = model.user_isExist(username)

    if msg is None:
        return jsonify(_makeErrorMessage(code))
    else:
        return jsonify(_makeResponseMessage(msg))


@api.route('/devices')
@login_required
def device_list():
    model = DeviceModel()
    msg, code = model.device_list(current_user.user_hash)

    if msg is None:
        return jsonify(_makeErrorMessage(code))
    else:
        return jsonify(_makeResponseMessage(msg))


@api.route('/register-device')
@login_required
def api_device_register():

    device_name = request.args.get('device_name', None)
    sensor_type = request.args.get('sensor_type', None)

    if device_name is None or sensor_type is None:
        return jsonify(_makeErrorMessage(11))

    if len(device_name) > Util.MaxUsernameLength:
        return jsonify(_makeErrorMessage(12))

    model = DeviceModel()

    msg, code = model.device_register(current_user.user_hash, device_name, sensor_type)

    if msg is None:
        return jsonify(_makeErrorMessage(code))
    else:
        return jsonify(_makeResponseMessage(msg))


@api.route('/delete-device')
@login_required
def api_device_delete():
    
    device_id = request.args.get('device_id', None)

    if device_id is None:
        return jsonify(_makeErrorMessage(11))

    deviceModel = DeviceModel()
    deviceData, code = deviceModel.device_get(current_user.user_hash, device_id)
    
    if deviceData is None or code != 0:
        return jsonify(_makeErrorMessage(code, msg))
    
    sensorType = deviceData["sensor_type"]

    # センタータイプに応じて記録データを削除
    if sensorType == Util.SensorType.Temperature:
        sensorTemperatureModel = SensorTemperatureModel()
        msg, code = sensorTemperatureModel.deleteAll(current_user.user_hash, device_id)

    if msg is None or code != 0:
        return jsonify(_makeErrorMessage(code, msg))


    # デバイス情報を削除
    msg, code = deviceModel.device_delete(current_user.user_hash, device_id)

    if msg is None:
        return jsonify(_makeErrorMessage(code))
    else:
        return jsonify(_makeResponseMessage(msg))
        


@api.route('/device/temperature/<device_id>')
@login_required
def api_device_temperature_view(device_id):

    model = SensorTemperatureModel()

    msg, code = model.view(current_user.user_hash, device_id)

    if msg is None or code != 0:
        return jsonify(_makeErrorMessage(code, msg))
    else:
        return jsonify(_makeResponseMessage(msg))


@api.route('/record/temperature')
def api_record_temperature():

    api_key = request.args.get("api_key", None)
    time = request.args.get("time", None)
    value = request.args.get("value", None)

    if api_key is None or time is None or value is None:
        return jsonify(_makeErrorMessage(11))
    
    model = SensorTemperatureModel()

    msg, code = model.record(api_key, time, value)

    if msg is None or code != 0:
        return jsonify(_makeErrorMessage(code, msg))
    else:
        return jsonify(_makeResponseMessage(msg))


@api.route('/delete-record/temperature/all')
@login_required
def api_delete_record_temperature_all():

    device_id = request.args.get('device_id', None)

    if device_id is None:
        return jsonify(_makeErrorMessage(11))
    
    model = SensorTemperatureModel()

    msg, code = model.deleteAll(current_user.user_hash, device_id)

    if msg is None or code != 0:
        return jsonify(_makeErrorMessage(code, msg))
    else:
        return jsonify(_makeResponseMessage(msg))


def _makeErrorMessage(code, msg = {}):
    data = {'header': {'status': 'error', 'errorCode': code}, 'response': msg}
    return data


def _makeResponseMessage(response):
    data = {'header': {'status': 'success',
                       'errorCode': 0}, 'response': response}
    return data
