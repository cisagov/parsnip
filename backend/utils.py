# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import re
from math import ceil
TAB_SIZE = 4
SINGLE_TAB = " " * TAB_SIZE
DOUBLE_TAB = SINGLE_TAB * 2
PROTOCOL_NAME = ""
DEFAULT_SCOPE = "general"
CONVERSION_SCOPE = "conversion"
USES_LAYER_2 = False

scopesHaveCrossScopeLinks = {}

def getTabString(tabSize):
    return SINGLE_TAB * tabSize

spicyToZeek = {
    "addr"      : "addr", 
    "uint"      : "count",
    "uint8"     : "count", 
    "uint16"    : "count",
    "uint32"    : "count",
    "uint64"    : "count",
    "int8"      : "int",
    "int16"     : "int", 
    "int32"     : "int", 
    "int64"     : "int", 
    "int"       : "int",
    "bool"      : "bool", 
    "real"      : "double",
    "string"    : "string",
    "enum"      : "string",
    "float"     : "double",
    "bytes"     : "string"
}
customFieldTypes = {}

def zeekTypeMapping(spicyType):
    if spicyType in spicyToZeek:
        return spicyToZeek[spicyType]
    else:
        print("Unknown type {0}".format(spicyType))
        return spicyType

def commandNameToConst(commandName):
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', commandName)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    
def calculateColumn(nameLength):
    return ceil((nameLength + 1) / TAB_SIZE) * TAB_SIZE
    
def endingSpace(columns, nameLength):
    return " " * (columns - nameLength)
    
def normalizedScope(scope, itemType):
    if scope == "general" or PROTOCOL_NAME.upper() == scope:
        if "enum" == itemType:
            return PROTOCOL_NAME.upper() + "_ENUM"
        else:
            return PROTOCOL_NAME.upper()
    elif scope != "":
        if "enum" == itemType:
            scope = scope + "_enum"
        return PROTOCOL_NAME.upper() + "_" + scope.upper()
    else:
        return ""
        
def loggingParentScope(scope):
    if scope == "general" or PROTOCOL_NAME.upper() == scope:
        return "general"
    elif scope.startswith(PROTOCOL_NAME.upper()):
        temp = scope[len(PROTOCOL_NAME.upper()) + 1:]
        return temp.lower()
    else:
        print("Unexepected scope: {}".format(scope))
        return scope
        
def determineSpicyStringForAction(action, switch, inputs, actionColumn, customTypes, bitfields, switches, enums):
    if "void" == action.type:
        return "void"
    tempInputs = []
    mappedUntilValue = None
    if action.until is not None:
        mappedUntilValue = action.until
        if mappedUntilValue.get("indicator") is not None:
            if switch.dependsOn is not None and switch.dependsOn.name == mappedUntilValue.get("indicator"):
                mappedUntilValue["indicator"] = inputs[0].source
            else:
                for dependencyIndex in range(len(switch.additionalDependsOn)):
                    if switch.additionalDependsOn[dependencyIndex].name == mappedUntilValue.get("indicator"):
                        mappedUntilValue["indicator"] = inputs[1 + dependencyIndex].source
                        break
    for input in action.inputs:
        if switch.dependsOn is not None and switch.dependsOn.name == input.source:
            tempInputs.append(inputs[0])
        else:
            for dependencyIndex in range(len(switch.additionalDependsOn)):
                if switch.additionalDependsOn[dependencyIndex].name == input.source:
                    tempInputs.append(inputs[1 + dependencyIndex])
                    break
    _, typeString = determineSpicyStringForType(action.name, action.type, action.elementType, action.referenceType, action.scope, action.size, tempInputs, mappedUntilValue, actionColumn, customTypes, bitfields, switches, enums)
    return "{0}{1} : {2}".format(action.name, endingSpace(actionColumn, len(action.name)), typeString)
    
def determineSpicyStringForType(itemName, itemType, elementType, referenceType, scope, size, inputs, until, columns, customTypes, bitfields, switches, enums):
    if itemType in ["uint", "int"]:
        if size in [8, 16, 32, 64]:
            return ("", itemType + str(size))
        elif 24 == size:
            sizeInBytes = int(ceil(size / 8))
            returnString = "bytes &size={0} {{\n".format(sizeInBytes)
            returnString += "{0}{1}   self.{2} = $$.to_uint(spicy::ByteOrder::Big);\n".format(DOUBLE_TAB, endingSpace(columns, 0), itemName)
            returnString += "{0}{1}   }}".format(SINGLE_TAB, endingSpace(columns, 0))
            
            return (itemType + "64", returnString)
        else:
            print("Current unsupported (u)int size {0}".format(size))
            return ("","")
    elif itemType in ["object", "enum"]:
        outputString = ""
        if "enum" == itemType:
            reference = enums[scope][referenceType]
            outputString += "uint{0}".format(reference.size)
            if "little" == reference.endianness:
                outputString += " &byte-order=spicy::ByteOrder::Little"
            outputString += " &convert="
        outputString += "{0}::{1}".format(scope, referenceType)
        
        if "enum" == itemType:
            outputString += "($$)"
        elif 0 < len(inputs):
            outputString += "("
            for index, value in enumerate(inputs):
                outputString += value.source
                if index < len(inputs) - 1:
                    outputString += ", "
            outputString += ")"
        return ("", outputString)
    elif "bytes" == itemType:
        return ("", "bytes &size={0}".format(int(ceil(size / 8))))
    elif "float" == itemType:
        if 32 == size:
            return ("", "real &type=spicy::RealType::IEEE754_Single")
        elif 64 == size:
            return ("", "real &type=spicy::RealType::IEEE754_Double")
        else:
            print("Currently unknown float size {0}".format(size))
            return ("", "")
    elif "addr" == itemType:
        if size == 32:
            return ("", "addr &ipv4")
        elif size == 128:
            return ("", "addr &ipv6")
    elif "bits" == itemType:
        # Have to get size from the reference
        reference = bitfields[scope][referenceType]
        outputString = "bitfield({0}) {{\n".format(reference.size)
        for field in reference.fields:
            if field.notes is not None and "" != field.notes:
                outputString += "{0}{1}   # {2}\n".format(DOUBLE_TAB, endingSpace(columns, 0), field.notes)
            conversionString = ""
            if "enum" == field.type:
                conversionString = " &convert={0}::{1}($$)".format(field.scope, field.referenceType)
            elif "bool" == field.type:
                conversionString = " &convert=cast<bool>($$)"
            outputString += "{0}{1}   {2}{3} : {4}{5};\n".format(DOUBLE_TAB, endingSpace(columns, 0), field.name, endingSpace(reference.column, len(field.name)), field.bits, conversionString)
        outputString += "{0}{1}   }}".format(SINGLE_TAB, endingSpace(columns, 0))
        if "little" == reference.endianness:
            outputString += " &byte-order=spicy::ByteOrder::Little"
        return ("", outputString)
    elif "list" == itemType:
        varString, typeString = determineSpicyStringForType(itemName, elementType, None, referenceType, scope, size, inputs, None, 0, customTypes, bitfields, switches, enums)
        sizeString = ""
        conditionString = ""
        if until is not None and until.get("conditionType") is not None:
            conditionType = until.get("conditionType")
            if "ENDOFDATA" == conditionType:
                conditionString = " &eod"
            elif "COUNT" == conditionType:
                sizeString = until.get("indicator")
                if until.get("minus") is not None:
                    sizeString = "({} - {})".format(sizeString, until.get("minus"))
            else:
                print("Unknown list condition type of {0}".format(conditionType))
        typeString = "({0})[{1}]{2}".format(typeString, sizeString, conditionString)
        
        return (varString, typeString)
    elif "string" == itemType:
        return ("", "string")
    elif "switch" == itemType:
        reference = switches[scope][referenceType]
        outputString = "switch({0}) {{\n".format(inputs[0].source)
        for option in reference.options:
            if option.action.type != "void":
                preString = ""
                if "enum" == reference.dependsOn.type:
                    preString = "{0}::{1}::".format(reference.dependsOn.scope, reference.dependsOn.referenceType)
                outputString += "{0}{1}{2}{3} -> {4};\n".format(DOUBLE_TAB, preString, option.value, endingSpace(reference.column, len(str(option.value))), determineSpicyStringForAction(option.action, reference, inputs, reference.actionColumn, customTypes, bitfields, switches, enums))
        defaultActionString = "void"
        if reference.default is not None and reference.default.type != "void":
            defaultActionString = determineSpicyStringForAction(reference.default, reference, inputs, reference.actionColumn, customTypes, bitfields, switches, enums)
        outputString += "{0}*{1}{2} -> {3};\n".format(DOUBLE_TAB, " "*len(preString), endingSpace(reference.column, 1), defaultActionString)
        outputString += "{0}}}".format(SINGLE_TAB)
        return ("", outputString)
    elif itemType in customTypes:
        # See if it's custom type
        sizeInBytes = int(ceil(size / 8))
        return ("", "bytes &size={0} &convert={1}::{2}($$)".format(sizeInBytes, normalizedScope(CONVERSION_SCOPE, ""), customTypes[itemType].interpretingFunction))
    else:
        # Otherwise we don't know...
        print("Currently unknown itemType of {0}".format(itemType))
        return ("", "")

def getObject(referenceType, scopes, allObjects):
    referencedObject = None
    for scope in scopes:
        if referenceType in allObjects[normalizedScope(scope, "object")]:
                referencedObject = allObjects[normalizedScope(scope, "object")][referenceType]
                break
    return referencedObject

