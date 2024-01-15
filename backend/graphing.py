#!/usr/bin/env python3

# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

# Local Imports
import utils

# Standard Library Imports
import json

# Graph Theory Imports
import networkx as nx

################################################################################
# Type Declarations
################################################################################

languageTypes = [
    ("addr", [32, 128]), # Passthrough Spicy Type
    ("uint", [8, 16, 24, 32, 64]), # Spicy built in for sizes 8, 16, 32, and 64; 24 we added
    ("int", [8, 16, 24, 32, 64]), # Spicy built in for sizes 8, 16, 32, and 64; 24 we added
    ("void", None), # Spicy type used to denote no fields
    ("bytes", None), # Passthrough Spicy Type, size will be converted to bytes from bits
    ("float", [32, 64]), # Maps to spicy "real" type with either float or double flag
    ("time", None),
    ("date", None)
]

bitfieldSpecificTypes = ["bool", "uint", "enum"]

structureTypes = {
    "bits": "Bitfields", # Maps to bitfield structures
    "enum": "Enums", # Maps to enum structures
    "object": "Objects", # Maps to object structures
    "switch": "Switches" # Maps to switches structures
}

otherReferenceTypes = {
    "list" # A list of other types
}

################################################################################
# Function Declarations
################################################################################

def loadFile(filePath):
    with open(filePath, "r") as file:
        contents = json.load(file)
    return contents
    
def normalizedKey3(value1, value2, value3):
    return "{}.{}.{}".format(value1, value2, value3)
    
def normalizedType(itemType, referenceScope, referenceType, elementType,
                   itemSize, isReference, userDefinedTypes):
    returnValue = ""
    denoteReference = False
    isList = False
    returnReference = None
    if None == itemType:
        returnValue = None
    elif "object" == itemType:
        returnValue = "Object"
        denoteReference = isReference
        if isReference:
            #returnReference = normalizedKey3(utils.normalizedScope(referenceScope, itemType), itemType, referenceType)
            returnReference = normalizedKey3(referenceScope, itemType, referenceType)
    elif "bits" == itemType:
        returnValue = "Bitfield"
        denoteReference = isReference
        if isReference:
            #returnReference = normalizedKey3(utils.normalizedScope(referenceScope, itemType), itemType, referenceType)
            returnReference = normalizedKey3(referenceScope, itemType, referenceType)
    elif "enum" == itemType:
        returnValue = "Enum"
        denoteReference = isReference
        if isReference:
            returnReference = normalizedKey3(referenceScope, itemType, referenceType)
    elif "switch" == itemType:
        returnValue = "Switch"
        denoteReference = isReference
        if isReference:
            #returnReference = normalizedKey3(utils.normalizedScope(referenceScope, itemType), itemType, referenceType)
            returnReference = normalizedKey3(referenceScope, itemType, referenceType)
    elif "user" == itemType:
        returnValue = "UserType"
        denoteReference = isReference
    elif "list" == itemType:
        returnValue, returnReference, isList = \
            normalizedType(elementType, referenceScope, referenceType, None,
                           itemSize, isReference, userDefinedTypes)
        returnValue += "[]"
        isList = True
    elif itemType in userDefinedTypes:
        returnValue = itemType + "(" + str(itemSize) + ")"
        returnReference = itemType
    elif itemType in bitfieldSpecificTypes:
        returnValue = itemType
    else:
        typeIndex = next((index for index, value in enumerate(languageTypes) if value[0] == itemType), -1)
        if typeIndex != -1:
            returnValue = itemType
            # This is a known type
            if itemSize is not None:
                returnValue += str(itemSize)
        else:
            print("Unhandled Type: {} {} {}".format(itemType, elementType,
                                                    itemSize))

    if denoteReference:
        returnValue += "Reference"
    return (returnValue, returnReference, isList)
    
def normalizedLabel(itemType, referenceScope, referenceType, elementType,
                    itemSize, itemName, isReference, userDefinedTypes):
    returnType, returnReference, isList = \
        normalizedType(itemType, referenceScope, referenceType, elementType, itemSize,
                       isReference, userDefinedTypes)
    preString = ""
    if returnType is not None:
        preString = "{}:".format(returnType)
    return ('"{}{}"'.format(preString, itemName), returnReference, isList)
    
def addUserTypeNode(userType, nodeInformation, metaData, userDefinedTypes):
    label, _, _ = normalizedLabel("user", None, None, None, None, userType, False,
                                  userDefinedTypes)
    nodeInformation[userType] = (label, metaData)
    
def _valueOrDefault(item, key, default):
    if hasattr(item, key):
        return getattr(item, key)
    #if key in item:
    #    return item.get(key)
    return default
    
def addItemNode(itemScope, item, itemType, nodeInformation, metaData, userDefinedTypes):
    name = item.name
    if metaData is None:
        metaData = {}
    metaData["logIndependently"] = _valueOrDefault(item, "logIndependently", False)
    metaData["logWithParent"] = _valueOrDefault(item, "logWithParent", False)
    label, _, _ = normalizedLabel(itemType, None, None, None, None, name, False,
                                  userDefinedTypes)
    nodeReference = normalizedKey3(itemScope, itemType, name)
    nodeInformation[nodeReference] = (label, metaData)
    return name
    
def normalizedKey2(value1, value2):
    return "{}.{}".format(value1, value2)
    
def normalizedKey4(value1, value2, value3, value4):
    return "{}.{}.{}.{}".format(value1, value2, value3, value4)
    
def _addNodeItem(parentScope, parentType, parentName, item, storage,
                 userDefinedTypes):
    labelName = normalizedKey2(parentName, item.name)
    parentKeyName = normalizedKey3(parentScope, parentType, parentName)
    keyName = normalizedKey4(parentScope, parentType, parentName,
                             item.name)
    label, referenceType, isList = \
        normalizedLabel(_valueOrDefault(item, "type", None),
                        _valueOrDefault(item, "scope", None),
                        _valueOrDefault(item, "referenceType", None),
                        _valueOrDefault(item, "elementType", None),
                        _valueOrDefault(item, "size", None), labelName, True,
                        userDefinedTypes)
    metaData = {"isList": isList}
    storage[keyName] = (label, metaData)
    return (parentKeyName, keyName, referenceType)
    
def _addConnection(source, destination, label, storage):
    storage.append((source, destination, label))
    
def _addReferenceConnection(itemKey, referenceType, storage):
    if referenceType is not None:
        _addConnection(itemKey, referenceType, "reference", storage)
    
def addFieldNode(itemScope, itemType, itemName, field, fieldNameType,
                 nodeInformation, referenceInformation, fieldsInformation,
                 userDefinedTypes):
    parentKey, keyName, referenceType = _addNodeItem(itemScope, itemType,
                                                     itemName, field,
                                                     nodeInformation,
                                                     userDefinedTypes)

    _addReferenceConnection(keyName, referenceType, referenceInformation)
    _addConnection(parentKey, keyName, fieldNameType, fieldsInformation)
    
def addDependencyNode(itemScope, itemType, itemName, dependency,
                      dependencyNodeInformation, depedencyReferenceInformation,
                      dependencyInformation, userDefinedTypes):
    parentKey, keyName, referenceType = _addNodeItem(itemScope, itemType,
                                                     itemName, dependency,
                                                     dependencyNodeInformation,
                                                     userDefinedTypes)
    _addReferenceConnection(keyName, referenceType,
                            depedencyReferenceInformation)
    _addConnection(parentKey, keyName, "dependency", dependencyInformation)
