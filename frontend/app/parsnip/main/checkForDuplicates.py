#!/usr/bin/env python3

# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import argparse
import os
import sys
import json


#Todo - make sure bits aren't being used twice in same bitfield.
def _processBitfields(snapshot, returnList):
    bitfields = snapshot.get("Structures").get("Bitfields")
    itemNames = set()
    if bitfields:
        for bitfield in bitfields:
            itemName = bitfield.get("name")
            if itemName in itemNames:
                returnList.append({"type": "Error",
                    "title": "Duplicate Bitfield",
                    "content": "Duplicate Bitfield with name {0}".format(itemName)})
            else:
                fieldNames = set()
                itemNames.add(itemName)
                fields = bitfield.get("fields")
                if fields:
                    for field in fields:
                        fieldName = field.get("name")
                        if fieldName in fieldNames:
                            returnList.append({"type": "Error",
                                "title": "Duplicate Field",
                                "content": "Duplicate field \"{0}\" in Bitfields.{1}".format(fieldName, itemName)})
                        else:
                            fieldNames.add(fieldName)
                else:
                    returnList.append({"type": "Warning",
                        "title": "Empty Bitfield",
                        "content": "No fields in Bitfield.{0}".format(itemName)})
    else:
        returnList.append({"type": "Warning",
            "title": "Empty Structure",
            "content": "No Items of Type: Bitfield"})

def _processEnums(snapshot, returnList):
    enums = snapshot.get("Structures").get("Enums")
    itemNames = set()
    if enums:
        for enum in enums:
            itemName = enum.get("name")
            if itemName in itemNames:
                returnList.append({"type": "Error",
                    "title": "Duplicate Enum",
                    "content": "Duplicate Enum with name {0}".format(itemName)})
            else:
                fieldNames = set()
                fieldValues = set()
                itemNames.add(itemName)
                fields = enum.get("fields")
                if fields:
                    for field in fields:
                        fieldName = field.get("name")
                        fieldValue = field.get("value")
                        if fieldName in fieldNames:
                            returnList.append({"type": "Warning",
                                "title": "Duplicate Field",
                                "content": "Duplicate field \"{0}\" in Enums.{1}".format(fieldName, itemName)})
                        else:
                            fieldNames.add(fieldName)
                        if fieldValue in fieldValues:
                            returnList.append({"type": "Error",
                                "title": "Duplicate Value",
                                "content": "Duplicate Value \"{0}\" in Enums.{1}".format(fieldValue, itemName)})
                        else:
                            fieldValues.add(fieldValue)
                else:
                    returnList.append({"type": "Warning",
                        "title": "Empty Enum",
                        "content": "No fields in Enums.{0}".format(itemName)})
    else:
        returnList.append({"type": "Warning",
            "title": "Empty Structure",
            "content": "No Items of Type: Enum"})

def _processSwitches(snapshot, returnList):
    switches = snapshot.get("Structures").get("Switches")
    itemNames = set()
    if switches:
        for switch in switches:
            itemName = switch.get("name")
            if itemName in itemNames:
                returnList.append({"type": "Error",
                    "title": "Duplicate Switch",
                    "content": "Duplicate Switch with name {0}".format(itemName)})
            else:
                fieldValues = set()
                itemNames.add(itemName)
                fields = switch.get("options")
                if fields:
                    for field in fields:
                        fieldValue = field.get("value")
                        if fieldValue in fieldValues:
                            returnList.append({"type": "Error",
                                "title": "Duplicate Value",
                                "content": "Duplicate Value \"{0}\" in Switches.{1}".format(fieldValue, itemName)})
                        else:
                            fieldValues.add(fieldValue)
                else:
                    returnList.append({"type": "Warning",
                        "title": "Empty Switch",
                        "content": "No options in Switches.{0}".format(itemName)})
    else:
        returnList.append({"type": "Warning",
            "title": "Empty Structure",
            "content": "No Items of Type: Switch"})

def _processObjects(snapshot, returnList):
    objects = snapshot.get("Structures").get("Objects")
    itemNames = set()
    if objects:
        for obj in objects:
            itemName = obj.get("name")
            if itemName in itemNames:
                returnList.append({"type": "Error",
                    "title": "Duplicate Object",
                    "content": "Duplicate Object with name {0}".format(itemName)})
            else:
                fieldNames = set()
                itemNames.add(itemName)
                fields = obj.get("fields")
                if fields:
                    for field in fields:
                        fieldName = field.get("name")
                        if fieldName in fieldNames:
                            returnList.append({"type": "Error",
                                "title": "Duplicate Field",
                                "content": "Duplicate field \"{0}\" in Objects.{1}".format(fieldName, itemName)})
                        else:
                            fieldNames.add(fieldName)
                else:
                    returnList.append({"type": "Warning",
                        "title": "Empty Object",
                        "content": "No fields in Objects.{0}".format(itemName)})
    else:
        returnList.append({"type": "Warning",
            "title": "Empty Structure",
            "content": "No Items of Type: Objects"})


def checkForDuplicates(snapshot, returnList):
    snapshot = json.loads(snapshot)
    _processBitfields(snapshot,returnList)
    _processEnums(snapshot, returnList)
    _processSwitches(snapshot, returnList)
    _processObjects(snapshot, returnList)
