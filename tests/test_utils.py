import io
import os
import ast
import json
import shutil
import hashlib
import requests
import logging as lg
import datetime as dt

import dummy
import pytest

###

@pytest.fixture
def destroy_folders():
    app_folder = dummy.settings["app_folder"]

    if os.path.exists(app_folder):
        shutil.rmtree(app_folder)

    assert not os.path.exists(app_folder)

###

def assert_file_structure():
    app_folder = dummy.settings["app_folder"]
    logs_folder = os.path.join(app_folder, dummy.settings["logs_folder_name"])
    data_folder = os.path.join(app_folder, dummy.settings["data_folder_name"])
    cache_folder = os.path.join(app_folder, dummy.settings["cache_folder_name"])

    assert os.path.exists(app_folder)
    assert os.path.exists(logs_folder)
    assert os.path.exists(data_folder)
    assert os.path.exists(cache_folder)

def assert_log_file():
    log_filename = os.path.join(dummy.settings["app_folder"], dummy.settings["logs_folder_name"], '{}_{}.log'.format(dummy.settings["app_name"], dt.datetime.today().strftime('%Y_%m_%d')))

    assert os.path.exists(log_filename)

###

def test_get_app_folder():
    dummy.settings["app_folder"] == os.path.expanduser("~/.pydummy")

###

def test_create_folders(destroy_folders):
    dummy.create_folders()
    assert_file_structure()
    destroy_folders

###

def test_config_immutable_setting():
    with pytest.raises(dummy.ImmutableSetting):
        dummy.config(app_name = "test")

###

def test_config_invalid_setting():
    with pytest.raises(dummy.InvalidSetting):
        dummy.config(verbose = True)

###

def test_config(destroy_folders):
    dummy.config(log_to_console = True)

    assert dummy.settings["log_to_console"] == True
    assert dummy.settings["cache_http"] == True
    assert dummy.settings["log_default_level"] == lg.INFO

    assert_file_structure()
    assert_log_file()
    destroy_folders

    dummy.config(app_folder = "/tmp/pydummy")

    assert_file_structure()
    assert_log_file()
    destroy_folders

###

def test_cache(destroy_folders):
    dummy.config(cache_http = True)

    url = requests.Request('GET', "https://nominatim.openstreetmap.org/?format=json&addressdetails=1&q=Newcastle+A186+Westgate+Rd").prepare().url

    response_json = requests.get(url).json()

    dummy.save_to_cache(url, response_json)

    cache_folder = os.path.join(dummy.settings["app_folder"], dummy.settings["cache_folder_name"])
    cache_file = os.path.join(cache_folder, os.extsep.join([hashlib.md5(url.encode('utf-8')).hexdigest(), 'json']))

    assert os.path.exists(cache_file)

    with io.open(cache_file, 'r', encoding='utf-8') as cache_file_handler:
        cache_content = json.load(cache_file_handler)

    json_str = json.dumps(response_json)
    json_str_from_cache = dummy.get_from_cache(url)

    try:
        # This fails in python2 for awkward reasons
        assert json_str == json.dumps(cache_content)
    except:
        assert response_json == json_str_from_cache

    assert cache_content == json_str_from_cache

    destroy_folders
