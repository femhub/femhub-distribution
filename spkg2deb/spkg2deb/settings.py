# -*- coding: utf-8 *-*
import os
import sys
from xml.etree.ElementTree import ElementTree


class Settings():
    "This class encapsulates access to settings.xml file."
    def __init__(self):
        self.settings_xml = os.path.dirname(
            os.path.realpath(sys.argv[0])) + os.sep + 'settings.xml'
        self.tree = None
        self.__loadXML()
        self.debug = self.tree.find('debug').text

    def __loadXML(self):
        self.tree = ElementTree()
        self.tree.parse(self.settings_xml)

    def get_name(self):
        return self.tree.find('name').text

    def get_email(self):
        return self.tree.find('email').text

    def get_architecture(self):
        return self.tree.find('architecture').text

    def get_version(self):
        return self.tree.find('version').text

    def get_homepage(self):
        return self.tree.find('homepage').text

    def get_description(self):
        return self.tree.find('description').text

    def get_depends(self):
        return self.tree.find('depends').text

    def get_debug(self):
        return self.debug

    def set_debug(self, debug):
        if debug == True:
            self.debug = "1"
        else:
            self.debug = "0"

    def get_destination(self):
        return self.tree.find('destination').text
