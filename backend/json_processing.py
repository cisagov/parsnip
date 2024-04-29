# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

# This file contains functions for reading each json file type
import json
import enums
import objects
import inputs
import switches
import bitfields
import zeektypes
import utils
import os

def loadFiles(rootFilePath, scopes):
    objects = {}
    switches = {}
    bitfields = {}
    enums = {}

    for scope in scopes:
        objectFilePath = os.path.join(rootFilePath, scope, "objects.json")
        switchesFilePath = os.path.join(rootFilePath, scope, "switches.json")
        bitfieldsFilePath = os.path.join(rootFilePath, scope, "bitfields.json")
        enumsFilePath = os.path.join(rootFilePath, scope, "enums.json")
        
        if os.path.isfile(objectFilePath):
            print("Processing {0}".format(objectFilePath))
            objects[utils.normalizedScope(scope, "object")] = processObjectsFile(objectFilePath, scope)
        if os.path.isfile(switchesFilePath):
            print("Processing {0}".format(switchesFilePath))
            switches[utils.normalizedScope(scope, "switch")] = processSwitchFile(switchesFilePath)
        if os.path.isfile(bitfieldsFilePath):
            print("Processing {0}".format(bitfieldsFilePath))
            bitfields[utils.normalizedScope(scope, "bitfield")] = processBitfieldFile(bitfieldsFilePath)
        if os.path.isfile(enumsFilePath):
            print("Processing {0}".format(enumsFilePath))
            enums[utils.normalizedScope(scope, "enum")] = processEnumFile(enumsFilePath)
            
    return (objects, switches, bitfields, enums)

def passThroughLink(switchName, objectField, scopes, allObjects, allSwitches, linkObjectField):
    for scope in scopes: 
        if switchName in allSwitches[utils.normalizedScope(scope, "")]:
            switch = allSwitches[utils.normalizedScope(scope, "")][switchName]
            break
    if switch != None:
        for item in switch.options:
            objectName = item.action.referenceType
            for scope in scopes: 
                if objectName in allObjects[utils.normalizedScope(scope, "")]:
                    object = allObjects[utils.normalizedScope(scope, "")][objectName]
                    object.addLinkField(linkObjectField)
                    dependencyJson =  {
                            "name": "parentLinkId",
                            "type": "string",
                            "size": 8
                        }
                    newInput = inputs.Input("parentLinkId")
                    objectField.addInput(newInput)
                    newAdditionalDependency = createDependencyFromJSON(dependencyJson)
                    switch.addAdditionalDependsOn(newAdditionalDependency)
                    object.addDependency(newAdditionalDependency)
                    item.action.addInput(newInput)
                    
def _getSwitchJson(spicyFieldName):
    objectDependencyJson =  {
        "name": "parentLinkId",
        "type": "string",
        "size": 8
    }
    switchDependencyJson =  {
        "name": spicyFieldName,
        "type": "string",
        "size": 8
    }
    
    return (objectDependencyJson, switchDependencyJson)
    
def _processNonUsageScope(switch, object, item, scope, objectField):
    spicyFieldName = switch.dependsOn.name[0].lower() + switch.dependsOn.name[1:] + "LinkID"
    linkObjectField = objects.Link(spicyFieldName, "parentLinkId", True)
    fieldInput = inputs.Input("self." + spicyFieldName)
    objectField.addInput(fieldInput)
    objectDependencyJson, switchDependencyJson = _getSwitchJson(spicyFieldName)
    newAdditionaObjectlDependency = createDependencyFromJSON(objectDependencyJson)
    object.addDependency(newAdditionaObjectlDependency)
    newAdditionalSwitchDependency = createDependencyFromJSON(switchDependencyJson)
    switch.addAdditionalDependsOn(newAdditionalSwitchDependency)
    newInput = inputs.Input(spicyFieldName)
    item.action.addInput(newInput)
    if scope not in utils.scopesHaveCrossScopeLinks:
        utils.scopesHaveCrossScopeLinks[scope] = []
    if spicyFieldName not in utils.scopesHaveCrossScopeLinks:
        utils.scopesHaveCrossScopeLinks[scope].append(spicyFieldName)
        
    return linkObjectField

def getSwitchType(switchName, objectField, switchUsageScope, scopes, allObjects, allSwitches):
    for scope in scopes: 
        if switchName in allSwitches[utils.normalizedScope(scope, "")]:
            switch = allSwitches[utils.normalizedScope(scope, "")][switchName]
            break
    isSkippedClass = True
    isSelfContained = True
    linkRequired = False
    if switch != None:
        for item in switch.options:
            objectName = item.action.referenceType
            for scope in scopes: 
                if objectName in allObjects[utils.normalizedScope(scope, "")]:
                    object = allObjects[utils.normalizedScope(scope, "")][objectName]
                    linkObjectField = None
                    if scope != switchUsageScope:
                        linkRequired = True
                        isSkippedClass = False
                        linkObjectField = _processNonUsageScope(switch, object, item, scope, objectField)
                    if not object.logWithParent:
                        isSelfContained = False
                    else:
                        isSkippedClass = False
                    if not isSkippedClass and linkObjectField != None:
                        if len(object.fields) == 1 and object.fields[0].type == "switch":
                            passThroughLink(object.fields[0].referenceType, object.fields[0], scopes, allObjects, allSwitches, linkObjectField)
                        else:
                            object.addLinkField(linkObjectField)
                    break
        if isSkippedClass:
            return "trivial" 
        elif linkRequired:
            return "link"
        elif isSelfContained and not linkRequired:
            return "contained"
        else:
            return "invalid"
            
def createDependencyFromJSON(dependency):
    if "referenceType" in dependency:
        newDependency = inputs.Dependency(dependency["name"], dependency["type"], 0, dependency["referenceType"], dependency["scope"])
    else: 
        newDependency = inputs.Dependency(dependency["name"], dependency["type"], dependency["size"])
    return newDependency

def processEnumFile(file):
    enumObject = {}
    with open(file, "r+") as file:
        enumList = json.load(file)
    for enum in enumList:
        newEnum = enums.Enums(enum["name"], enum["reference"], enum["size"])
        if "endianness" in enum:
            newEnum.endianness = enum["endianness"]
        if "notes" in enum:
            newEnum.notes = enum["notes"]
        for field in enum["fields"]:
            enumField = enums.EnumField(field["name"], field["loggingValue"], field["value"])
            if "notes" in field:
                enumField.notes = field["notes"]
            newEnum.addField(enumField)
        enumObject[enum["name"]] = newEnum
    return enumObject
    
def _processConditional(conditional, startingIndex):
    if "indicator" in conditional and "operator" in conditional and "value" in conditional:
        return _processRegularConditional(conditional, startingIndex)
    elif "and" in conditional:
        return _processJoiningConditional(conditional, "and", "&&", startingIndex)
    elif "or" in conditional:
        return _processJoiningConditional(conditional, "or", "||", startingIndex)
    else:
        print("Unrecognized conditional")
        return []
    
def _processRegularConditional(conditional, startingIndex):
    return [("indicator", conditional["indicator"], startingIndex + 4),
            ("space", " "),
            ("operator", conditional["operator"]),
            ("space", " "),
            ("value", conditional["value"])]
            
def _processJoiningConditional(conditional, key, joiner, startingIndex):
    returnValue = []
    if startingIndex > 0:
        returnValue.append(("start parantheses", "("))
        
    for index, value in enumerate(conditional[key]):
        returnValue.extend(_processConditional(value, startingIndex + len(returnValue)))
        if index < len(conditional[key]) - 1:
            returnValue.extend(
                [("space", " "),
                 (key, joiner),
                 ("space", " ")])
        
    if startingIndex > 0:
        returnValue.append(("end parantheses", ")"))
    
    return returnValue
    
def processConditional(conditional):
    return _processConditional(conditional, 0)

def processObjectsFile(file, scope):
    objectsDictionary = {}
    with open(file, "r+") as file:
        objectsList = json.load(file)
    for object in objectsList:
        if "logWithParent" in object:
            newObject = objects.Object(object["name"], object["reference"], object["notes"], object["logIndependently"], object["referenceCount"], scope, object["logWithParent"])
        else:
            newObject = objects.Object(object["name"], object["reference"], object["notes"], object["logIndependently"], object["referenceCount"], scope)
        if "dependsOn" in object:
            for dependency in object["dependsOn"]:
                newDependency = createDependencyFromJSON(dependency)
                newObject.addDependency(newDependency)
        for field in object["fields"]:
            if "scope" in field:
                newField = objects.ObjectField(field["name"], field["description"], field["type"], field["scope"])
            else:
               newField = objects.ObjectField(field["name"], field["description"], field["type"]) 
            if "referenceType" in field:
                newField.referenceType = field["referenceType"]
            if "elementType" in field:
                newField.elementType = field["elementType"]
            if "until" in field:
                newField.until = field["until"]
            if "size" in field:
                newField.size = field["size"]
            if "notes" in field:
                newField.notes = field["notes"]
            if "input" in field:
                minus = ""
                if "minus" in field["input"]:
                    minus = field["input"]["minus"]
                newInput = inputs.Input(field["input"]["source"], minus)
                newField.addInput(newInput)
            if "inputs" in field:
                for input in field["inputs"]:
                    minus = ""
                    if "minus" in input:
                        minus = input["minus"]
                    newInput = inputs.Input(input["source"], minus)
                    newField.addInput(newInput)
            if "additionalInputs" in field:
                for input in field["additionalInputs"]:
                    minus = ""
                    if "minus" in input:
                        minus = input["minus"]
                    newInput = inputs.Input(input["source"], minus)
                    newField.addInput(newInput)
            if "endianness" in field:
                newField.endianness = field["endianness"]
            if "conditional" in field:
                newField.conditional = processConditional(field["conditional"])
            newObject.addField(newField)
        objectsDictionary[object["name"]] = newObject
    return objectsDictionary

def processSwitchFile(file):
    switchDictionary = {}
    with open(file, "r+") as file:
        switchList = json.load(file)
    for switch in switchList:
        newSwitch = switches.Switch(switch["name"], switch["referenceCount"])
        newDependency = createDependencyFromJSON(switch["dependsOn"])
        newSwitch.dependsOn = newDependency
        if "additionalDependsOn" in switch:
            for additionalDependency in switch["additionalDependsOn"]:
                newAdditionalDependency = createDependencyFromJSON(additionalDependency)
                newSwitch.addAdditionalDependsOn(newAdditionalDependency)
        for option in switch["options"]:
            newSwitchOption = switches.SwitchOption(option["value"])
            newSwitchAction = switches.SwitchAction(option["action"]["name"], option["action"]["type"], option["action"]["referenceType"] if "referenceType" in option["action"] else "", option["action"]["scope"] if "scope" in option["action"] else "")
            if "size" in option["action"]:
                newSwitchAction.size = option["action"]["size"]
            if "inputs" in option["action"]:
                for input in option["action"]["inputs"]:
                    minus = ""
                    if "minus" in input:
                        minus = input["minus"]
                    newInput = inputs.Input(input["source"], minus)
                    newSwitchAction.addInput(newInput)
            if "elementType" in option["action"]:
                newSwitchAction.elementType = option["action"]["elementType"]
            if "until" in option["action"]:
                newSwitchAction.until = option["action"]["until"]
            newSwitchOption.action = newSwitchAction
            newSwitch.addOption(newSwitchOption)
        if "default" in switch:
            tempAction = switch["default"]
            defaultAction = switches.SwitchAction(tempAction["name"], tempAction["type"], tempAction["referenceType"] if "referenceType" in tempAction else "", tempAction["scope"] if "scope" in tempAction else "")
            if "size" in tempAction:
                defaultAction.size = tempAction["size"]
            if "inputs" in tempAction:
                for input in tempAction["inputs"]:
                    minus = ""
                    if "minus" in input:
                        minus = input["minus"]
                    newInput = inputs.Input(input["source"], minus)
                    defaultAction.addInput(newInput)
            if "elementType" in tempAction:
                defaultAction.elementType = tempAction["elementType"]
            if "until" in tempAction:
                defaultAction.until = tempAction["until"]
            newSwitch.default = defaultAction
        switchDictionary[switch["name"]] = newSwitch
    return switchDictionary
        
def processBitfieldFile(file):
    bitfieldDictionary = {}
    with open(file, "r+") as file:
        bitfieldList = json.load(file)
    for bitfield in bitfieldList:
        newBitfield = bitfields.Bitfield(bitfield["name"], bitfield["reference"], bitfield["notes"], bitfield["size"])
        if "endianness" in bitfield:
            newBitfield.endianness = bitfield["endianness"]
        for field in bitfield["fields"]:
            if "scope" in field:
                newField = bitfields.BitfieldField(field["name"], field["description"], field["type"], field["bits"], field["scope"])
            else:
               newField = bitfields.BitfieldField(field["name"], field["description"], field["type"], field["bits"]) 
            if "referenceType" in field:
                newField.referenceType = field["referenceType"]
            if "notes" in field:
                newField.notes = field["notes"]
            newBitfield.addField(newField)
        bitfieldDictionary[bitfield["name"]] = newBitfield
    return bitfieldDictionary
    
def _processBasicType(zeekFields, zeekField, object, field, type):
    zeekField.name = utils.commandNameToConst(object.name).lower() + "_" + utils.commandNameToConst(field.name).lower()
    field.zeekName = zeekField.name
    zeekField.type =  type
    zeekFields.append(zeekField)
    object.addIncludedField(field)
    
def _processCustomType(zeekFields, zeekField, object, field, customFieldTypes):
    _processBasicType(zeekFields, zeekField, object, field, utils.zeekTypeMapping(customFieldTypes[field.type].returnType))
       
def _processSpicyType(zeekFields, zeekField, object, field):
    _processBasicType(zeekFields, zeekField, object, field, utils.spicyToZeek[field.type])

def _processSwitchAction(type, action, zeekFields, object, linkingFields, scope, scopes, allObjects, zeekObjects, zeekMainFileObject):
    if action.type == "object":
        if type == "link":
            object.addExcludedField(action.name)
        else:
            object.addExcludedField(action.name)
    elif action.type in utils.spicyToZeek:
        zeekField = zeektypes.ZeekField()
        _processBasicType(zeekFields, zeekField, object, action.name, utils.spicyToZeek[action.type])
    elif action.type == "list":
        _processListType(zeekFields, action, linkingFields, object, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
    elif action.type == "void":
        pass
    else:
        print("Invalid switch option type: {} in {}".format(action.type, object.name))
    
def _processSwitchType(zeekFields, linkingFields, object, field, scope, scopes, allObjects, allSwitches, zeekObjects, zeekMainFileObject):
    switchType = getSwitchType(field.referenceType, field, scope, scopes, allObjects, allSwitches)
    if switchType == "invalid":
        print("Unknown switch")
        print(field.name)
    elif switchType == "link":
        for switchScope in scopes: 
            if field.referenceType in allSwitches[utils.normalizedScope(switchScope, "")]:
                referencedObject = allSwitches[utils.normalizedScope(switchScope, "")][field.referenceType]
                break
        spicyFieldName = referencedObject.dependsOn.name[0].lower() + referencedObject.dependsOn.name[1:] + "LinkID"
        linkObjectField = objects.Link(spicyFieldName, "parentLinkId")
        object.addLinkField(linkObjectField)
        object.needsSpecificExport = True
        for option in referencedObject.options:
            _processSwitchAction("link", option.action, zeekFields, object, linkingFields, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
        if referencedObject.default is not None:
            _processSwitchAction("link", referencedObject.default, zeekFields, object, linkingFields, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
        linkFieldName = utils.commandNameToConst(referencedObject.dependsOn.name).lower() + "_link_id"
        zeekLinkingField = zeektypes.ZeekField(linkFieldName, "string")
        linkingFields.append(zeekLinkingField)
    elif switchType == "contained":
        referencedObject = None
        for switchScope in scopes: 
            if field.referenceType in allSwitches[utils.normalizedScope(switchScope, "")]:
                referencedObject = allSwitches[utils.normalizedScope(switchScope, "")][field.referenceType]
                break
        if referencedObject is not None:
            for option in referencedObject.options:
                _processSwitchAction("contained", option.action, zeekFields, object, linkingFields, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
            if referencedObject.default is not None:
                _processSwitchAction("contained", referencedObject.default, zeekFields, object, linkingFields, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
    elif switchType == "trivial":
        # If a trivial switch is in an object that also contains fields, the switch objects should be logged with their parent
        referencedObject = None
        for switchScope in scopes: 
            if field.referenceType in allSwitches[utils.normalizedScope(switchScope, "")]:
                referencedObject = allSwitches[utils.normalizedScope(switchScope, "")][field.referenceType]
                break
        if referencedObject is not None:
            for option in referencedObject.options:
                if option.action.type == "object":
                    for objectScope in scopes:
                        if option.action.referenceType in allObjects[utils.normalizedScope(objectScope, "")]:
                            actionObject = allObjects[utils.normalizedScope(objectScope, "")][option.action.referenceType]
                            break
                    if actionObject is not None:
                        actionObject.logWithParent = True
                            
def _processBitsType(zeekFields, object, field, bitfields, scope, generalScope):
    referenceType = field.referenceType
    field.zeekName = utils.commandNameToConst(object.name).lower() + "_" +  utils.commandNameToConst(field.name).lower()
    try:
        reference = bitfields[scope][referenceType]
    except KeyError:
        try: 
           reference = bitfields[generalScope][referenceType]
        except KeyError:
            print("Unknown bitfield")
            return
    for bitField in reference.fields:
        zeekType = utils.spicyToZeek[bitField.type]
        fieldname = field.zeekName + "_" + utils.commandNameToConst(bitField.name).lower()
        zeekBitField = zeektypes.ZeekField(fieldname, zeekType)
        zeekFields.append(zeekBitField)
    object.addIncludedField(field)
    
def _processObjectLink(logStructure, zeekObjects, scope, zeekMainFileObject):
    if logStructure not in zeekObjects[utils.normalizedScope(scope, "object")]:
        zeekObject = zeektypes.ZeekRecord(logStructure, scope)
        zeekObjects[utils.normalizedScope(scope, "object")][logStructure] = zeekObject
        zeekMainFileObject.addRecord(zeekObject)
    else:
        zeekObject = zeekObjects[utils.normalizedScope(scope, "object")][logStructure]
    return zeekObject
    
    
def _processLinkingField(referencedObject, linkingFields, zeekObjects, scope, zeekMainFileObject):
    linkFieldName = utils.commandNameToConst(referencedObject.name).lower() + "_link_id"
    zeekLinkingField = zeektypes.ZeekField(linkFieldName, "string")
    linkingFields.append(zeekLinkingField)
    for logStructure in referencedObject.zeekStructure:
        zeekObject = _processObjectLink(logStructure, zeekObjects, scope, zeekMainFileObject)
        zeekObject.addExternalLinkFields(zeekLinkingField)

def _processObjectType(field, linkingFields, object, allObjects, generalScope, scope, scopes, scopedObjects, zeekObjects, zeekMainFileObject):
    referencedObject = None
    if field.referenceType in allObjects[generalScope]:
        referencedObject = allObjects[generalScope][field.referenceType]
    elif field.referenceType not in scopedObjects:
        print("Referencing out of scope object")
        for objectScope in scopes: 
            if field.referenceType in allObjects[utils.normalizedScope(objectScope, "object")]:
                referencedObject = allObjects[utils.normalizedScope(objectScope, "object")][field.referenceType]
                break
        if referencedObject == None:
            print("Unknown Reference: {}".format(field.referenceType))
            return
    else: 
        referencedObject = scopedObjects[field.referenceType]
    if referencedObject.logIndependently == True:
        linkingDependency = inputs.Dependency("objectParentLinkId", "string")
        referencedObject.addDependency(linkingDependency)
        spicyFieldName = referencedObject.name[0].lower() + referencedObject.name[1:] + "LinkID"
        linkObjectField = objects.Link(spicyFieldName, "parentLinkId")
        object.addLinkField(linkObjectField)
        linkEndObjectField = objects.Link(spicyFieldName, "parentLinkId", True)
        referencedObject.addLinkField(linkEndObjectField)
        object.addExcludedField(field.name)  
        object.needsSpecificExport = True
        # TODO: Double check this function for side effects
        _processLinkingField(referencedObject, linkingFields, zeekObjects, scope, zeekMainFileObject)
        field.zeekName = utils.commandNameToConst(object.name).lower() + "_" +  utils.commandNameToConst(field.name).lower()
        
def _processListType(zeekFields, field, linkingFields, object, scope, scopes, allObjects, zeekObjects, zeekMainFileObject):
    if field.elementType in utils.spicyToZeek:
        zeekFieldName = utils.commandNameToConst(object.name).lower() + "_" +  utils.commandNameToConst(field.name).lower()
        field.zeekName = zeekFieldName
        zeekType = "vector of {}".format(utils.spicyToZeek[field.elementType])
        zeekBitField = zeektypes.ZeekField(zeekFieldName, zeekType)
        object.addExcludedField(field.name)
        zeekFields.append(zeekBitField)
    elif field.elementType == "object":
        referencedObject, objectScope = utils.getObject(field.referenceType, scopes, allObjects)
        spicyFieldName = referencedObject.name[0].lower() + referencedObject.name[1:] + "LinkID"
        linkObjectField = objects.Link(spicyFieldName, "listParentLinkId")
        object.addLinkField(linkObjectField)
        linkEndObjectField = objects.Link(spicyFieldName, "listParentLinkId", True)
        referencedObject.addLinkField(linkEndObjectField)
        linkInput = inputs.Input("self." + spicyFieldName)
        field.addInput(linkInput)
        linkingDependency = inputs.Dependency("listParentLinkId", "string")
        referencedObject.addDependency(linkingDependency)
        referencedObject.logIndependently == True
        object.addExcludedField(field.name)
        object.needsSpecificExport = True
        _processLinkingField(referencedObject, linkingFields, zeekObjects, objectScope, zeekMainFileObject)
        
def _linkScope(scope, zeekObjects):
    # I know this is terrible practice but my graph theory sucks and I want this to work
    if scope in utils.scopesHaveCrossScopeLinks:
        zeekMainObject = zeekObjects[utils.normalizedScope(scope, "object")][scope]
        for item in utils.scopesHaveCrossScopeLinks[scope]:
            zeekLinkingField = zeektypes.ZeekField(utils.commandNameToConst(item).lower(), "string")
            zeekMainObject.addExternalLinkFields(zeekLinkingField)

def createZeekObjects(scopes, customFieldTypes, bitfields, allObjects, allSwitches):
    zeekObjects = {}
    zeekMainFileObject = zeektypes.ZeekMain()
    generalScope = utils.normalizedScope("general", "object")
    for scope in scopes:
        zeekObjects[utils.normalizedScope(scope, "object")] = {}
        # mainZeekRecord = zeektypes.ZeekRecord(scope)
        scopedObjects = allObjects[utils.normalizedScope(scope, "object")]
        for object in scopedObjects.values():
            zeekFields = []
            linkingFields = []
            if len(object.fields) == 1 and object.fields[0].type == "switch":
                switchType = getSwitchType(object.fields[0].referenceType, object.fields[0], scope, scopes, allObjects, allSwitches)
                if switchType == "trivial":
                    object.needsSpecificExport = False
                    continue
            for field in object.fields:
                zeekField = zeektypes.ZeekField()
                if field.type in customFieldTypes:
                    _processCustomType(zeekFields, zeekField, object, field, customFieldTypes)
                elif field.type in utils.spicyToZeek:
                    _processSpicyType(zeekFields, zeekField, object, field)
                elif field.type == "switch":
                    _processSwitchType(zeekFields, linkingFields, object, field, scope, scopes, allObjects, allSwitches, zeekObjects, zeekMainFileObject)
                elif field.type == "bits":
                    _processBitsType(zeekFields, object, field, bitfields, scope, generalScope)
                elif field.type == "object":
                    _processObjectType(field, linkingFields, object, allObjects, generalScope, scope, scopes, scopedObjects, zeekObjects, zeekMainFileObject)
                elif field.type == "list":
                    _processListType(zeekFields, field, linkingFields, object, scope, scopes, allObjects, zeekObjects, zeekMainFileObject)
            for logStructure in object.zeekStructure:
                zeekObject = _processObjectLink(logStructure, zeekObjects, scope, zeekMainFileObject)
                zeekObject.addExternalLinkFieldList(linkingFields)
                zeekObject.addCommandStructure(object)
                zeekObject.addFieldList(zeekFields)
    for scope in scopes:
        _linkScope(scope, zeekObjects)
    return zeekObjects, zeekMainFileObject
