import os
import re
import json

from minigalaxy.config import Config
from minigalaxy.paths import CONFIG_DIR


class Game:
    def __init__(self, name: str, url: str = "", md5sum=None, game_id: int = 0, install_dir: str = "",
                 image_url="", platform="linux", dlcs=None):
        self.name = name
        self.url = url
        self.md5sum = {} if md5sum is None else md5sum
        self.id = game_id
        self.install_dir = install_dir
        self.image_url = image_url
        self.platform = platform
        self.dlcs = [] if dlcs is None else dlcs
        self.status_file_name = "{}.json".format(self.get_install_directory_name())
        self.status_file_path = os.path.join(CONFIG_DIR, self.status_file_name)

    def get_stripped_name(self):
        return self.__strip_string(self.name)

    def get_install_directory_name(self):
        return re.sub('[^A-Za-z0-9 ]+', '', self.name)

    def load_minigalaxy_info_json(self):
        json_dict = {}
        if os.path.isfile(self.status_file_path):
            staus_file = open(self.status_file_path, 'r')
            json_dict = json.load(staus_file)
            staus_file.close()
        return json_dict

    def save_minigalaxy_info_json(self, json_dict):
        status_file = open(self.status_file_path, 'w')
        json.dump(json_dict, status_file)
        status_file.close()

    @staticmethod
    def __strip_string(string):
        return re.sub('[^A-Za-z0-9]+', '', string)

    def is_installed(self, dlc_title="") -> bool:
        installed = False
        if dlc_title:
            dlc_version = self.get_dlc_info("version", dlc_title)
            installed = True if dlc_version else False
        else:
            if self.install_dir and os.path.exists(self.install_dir):
                installed = True
        return installed

    def is_update_available(self, version_from_api, dlc_title="") -> bool:
        update_available = False
        if dlc_title:
            installed_version = self.get_dlc_info("version", dlc_title)
        else:
            installed_version = self.get_info("version")
            if not installed_version:
                installed_version = self.fallback_read_installed_version()
                self.set_info("version", installed_version)
        if installed_version and version_from_api and version_from_api != installed_version:
            update_available = True

        return update_available

    def fallback_read_installed_version(self):
        gameinfo = os.path.join(self.install_dir, "gameinfo")
        gameinfo_list = []
        if os.path.isfile(gameinfo):
            with open(gameinfo, 'r') as file:
                gameinfo_list = file.readlines()
        if len(gameinfo_list) > 1:
            version = gameinfo_list[1].strip()
        else:
            version = "0"
        return version

    def set_info(self, key, value):
        json_dict = self.load_minigalaxy_info_json()
        json_dict[key] = value
        self.save_minigalaxy_info_json(json_dict)

    def set_dlc_info(self, key, value, dlc_title):
        json_dict = self.load_minigalaxy_info_json()
        if "dlcs" not in json_dict:
            json_dict["dlcs"] = {}
        if dlc_title not in json_dict["dlcs"]:
            json_dict["dlcs"][dlc_title] = {}
        json_dict["dlcs"][dlc_title][key] = value
        self.save_minigalaxy_info_json(json_dict)

    def get_info(self, key):
        value = ""
        json_dict = self.load_minigalaxy_info_json()
        if key in json_dict:
            value = json_dict[key]
        # Start: Code for compatibility with minigalaxy 1.0.1 and 1.0.2
        elif os.path.isfile(os.path.join(self.install_dir, "minigalaxy-info.json")):
            staus_file = open(os.path.join(self.install_dir, "minigalaxy-info.json"), 'r')
            json_dict = json.load(staus_file)
            staus_file.close()
            if key in json_dict:
                value = json_dict[key]
                # Lets move this value to new config
                self.set_info(key, value)
        # End: Code for compatibility with minigalaxy 1.0.1 and 1.0.2
        return value

    def get_dlc_info(self, key, dlc_title):
        value = ""
        json_dict = self.load_minigalaxy_info_json()
        if "dlcs" in json_dict:
            if dlc_title in json_dict["dlcs"]:
                if key in json_dict["dlcs"][dlc_title]:
                    value = json_dict["dlcs"][dlc_title][key]
        # Start: Code for compatibility with minigalaxy 1.0.1 and 1.0.2
        if os.path.isfile(os.path.join(self.install_dir, "minigalaxy-info.json")) and not value:
            staus_file = open(os.path.join(self.install_dir, "minigalaxy-info.json"), 'r')
            json_dict = json.load(staus_file)
            staus_file.close()
            if "dlcs" in json_dict:
                if dlc_title in json_dict["dlcs"]:
                    if key in json_dict["dlcs"][dlc_title]:
                        value = json_dict["dlcs"][dlc_title][key]
                        # Lets move this value to new config
                        self.set_dlc_info(key, value, dlc_title)
        # End: Code for compatibility with minigalaxy 1.0.1 and 1.0.2
        return value

    def set_install_dir(self):
        if not self.install_dir:
            self.install_dir = os.path.join(Config.get("install_dir"), self.get_install_directory_name())

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if self.id > 0 and other.id > 0:
            if self.id == other.id:
                return True
            else:
                return False
        if self.name == other.name:
            return True
        # Compare names with special characters and capital letters removed
        if self.get_stripped_name().lower() == other.get_stripped_name().lower():
            return True
        if self.install_dir and other.get_stripped_name() in self.__strip_string(self.install_dir):
            return True
        if other.install_dir and self.get_stripped_name() in self.__strip_string(other.install_dir):
            return True
        return False

    def __lt__(self, other):
        names = [str(self), str(other)]
        names.sort()
        if names[0] == str(self):
            return True
        return False
