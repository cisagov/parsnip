# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from parsnip.main.forms import (AddEnumForm, AddBitfieldForm)
from parsnip.main.checkForMissingDependencies import (checkForMissingDependencies)
from parsnip.main.checkForDuplicates import (checkForDuplicates)

from flask import session

import json

def _createPortsIfNecessary():
    if session.get("Ports") is None:
        session["Ports"] = []

def _createCustomFieldTypesIfNecessary():
    if session.get("CustomFieldTypes") is None:
        session["CustomFieldTypes"] = []

def _createStructureIfNecessary():
    if session.get("Structures") is None:
        session["Structures"] = {}
        
def _createSwitchStructureIfNecessary():
    _createStructureIfNecessary()
    if session["Structures"].get("Switches") is None:
        session["Structures"]["Switches"] = []
        
def _createEnumStructureIfNecessary():
    _createStructureIfNecessary()
    if session["Structures"].get("Enums") is None:
        session["Structures"]["Enums"] = []
        
def _createBitfieldStructureIfNecessary():
    _createStructureIfNecessary()
    if session["Structures"].get("Bitfields") is None:
        session["Structures"]["Bitfields"] = []
        
def _createObjectStructureIfNecessary():
    _createStructureIfNecessary()
    if session["Structures"].get("Objects") is None:
        session["Structures"]["Objects"] = []
        
def _processDependencyForm(dependencyForm):
    returnValue = {}
    dataType = dependencyForm.dependencyType.data
    returnValue["name"] = dependencyForm.dependencyName.data
    returnValue["type"] = dataType
    if "object" == dataType or \
       "bits" == dataType or \
       "switch" == dataType or \
       "enum" == dataType:
        returnValue["referenceType"] = dependencyForm.referenceType.data
    else:
        returnValue["size"] = dependencyForm.fieldSize.data
    
    return returnValue
    
def _processOptionForm(optionForm):
    returnValue = {}
    returnValue["value"] = optionForm.optionValueSelection.data
    actionValue = {}
    actionValue["name"] = optionForm.optionActionName.data
    dataType = optionForm.optionActionType.data
    actionValue["type"] = dataType
    if "object" == dataType or \
       "bits" == dataType or \
       "switch" == dataType or \
       "enum" == dataType:
        actionValue["referenceType"] = optionForm.referenceType.data
    elif "void" != dataType:
        actionValue["size"] = optionForm.optionActionSize.data
    if optionForm.inputs is not None and 0 < len(optionForm.inputs):
        actionInputs = []
        for tempInput in optionForm.inputs:
            actionInputs.append({"source": tempInput.data})
        actionValue["inputs"] = actionInputs
    returnValue["action"] = actionValue
    return returnValue
    
def getStructuresOfAType(structureTypeName):
    tempType = structureTypeName
    if "object" == tempType:
        tempType = "Objects"
    elif "enum" == tempType:
        tempType = "Enums"
    elif "switch" == tempType:
        tempType = "Switches"
    elif "bits" == tempType:
        tempType = "Bitfields"
    if "Structures" in session and tempType in session["Structures"]:
        return session["Structures"][tempType]
    else:
        return []
        
def getStructuresOfATypeAsDictionary(structureTypeName):
    returnValue = {}
    tempType = structureTypeName
    if "object" == tempType:
        tempType = "Objects"
    elif "enum" == tempType:
        tempType = "Enums"
    elif "switch" == tempType:
        tempType = "Switches"
    elif "bits" == tempType:
        tempType = "Bitfields"
    if "Structures" in session and tempType in session["Structures"]:
        for item in session["Structures"][tempType]:
            returnValue[item["name"]] = item
    return returnValue
    
def getObjectInputs():
    returnValue = {}
    if "Structures" in session and "Objects" in session.get("Structures"):
        for tempObject in session.get("Structures").get("Objects"):
            if "dependsOn" in tempObject:
                returnValue[tempObject["name"]] = tempObject["dependsOn"]
            else:
                returnValue[tempObject["name"]] = []
    return returnValue
    
def getActionTypeSelectorTypes():
    choices=[
        ('void', 'Nothing'),
        ('object', 'Object')
    ]
    
    return choices
        
def getBitfieldTypeSelectorTypes():
    choices=[
        ('uint', 'Unsigned Integer'),
        ('enum', 'Enumeration'),
        ('bool', 'Boolean')
    ]
        
    return choices
        
def getAllBuiltInTypeSelectorTypes(includeType=False):
    builtinTypes = [
        ('uint', 'Unsigned Integer'),
        ('int', 'Signed Integer'),
        ('real', 'Decimal')
    ]
    
    typePart = ""
    if includeType:
        typePart = " (Built-in)"
    return [(item[0], "{0}{1}".format(item[1], typePart)) for item in builtinTypes]
        
def getAllCustomTypeSelectorTypes(includeType=False):
    typePart = ""
    if includeType:
        typePart = " (Custom)"
    returnValue = []
    
    if "CustomFieldTypes" in session:
        for item in session["CustomFieldTypes"]:
            returnValue.append((item.get("name"), "{0}{1}".format(item.get("name"), typePart)))
    
    return returnValue
    
def getStructureNamesOfAType(structureType):
    returnValue = []
    if "Structures" in session and structureType in session["Structures"]:
        for item in session["Structures"][structureType]:
            returnValue.append(item["name"])
    return returnValue
        
def getReferenceSelectorTypes(structureType, includeScope=False, includeType=False):
    returnValue = []
    if "Structures" in session and structureType in session["Structures"]:
        for item in session["Structures"][structureType]:
            scopedValue = item["name"]
            displayValue = item["name"]
            if includeScope and "scope" in item and "" != item["scope"]:
                scopedValue = "{0}.{1}".format(item["scope"], scopedValue)
            if includeType:
                displayType = ""
                if "Objects" == structureType:
                    displayType = "Object"
                elif "Bitifields" == structureType:
                    displayType = "Bitifield"
                elif "Enums" == structureType:
                    displayType = "Enum"
                elif "Switches" == structureType:
                    displayType = "Choice"
                displayValue = "{0} ({1})".format(displayValue, displayType)
            returnValue.append((scopedValue, displayValue))
        returnValue = sorted(returnValue, key=lambda x: x[1])
    return returnValue
    
def getAllFieldTypeSelectorTypes(includeListType=True, includeChoiceType=True, includeType=False):
    returnValue = []
    returnValue.extend(getAllBuiltInTypeSelectorTypes(includeType))
    returnValue.extend(getAllCustomTypeSelectorTypes(includeType))
    returnValue.extend(getAllFieldStructuresTypes(includeListType, includeChoiceType, includeType))
    return returnValue
        
def getAllReferenceSelectorTypes(includeScope=False, includeType=True):
    returnValue = []
    returnValue.extend(getReferenceSelectorTypes("Objects", includeScope=includeScope, includeType=includeType))
    returnValue.extend(getReferenceSelectorTypes("Bitfields", includeScope=includeScope, includeType=includeType))
    returnValue.extend(getReferenceSelectorTypes("Enums", includeScope=includeScope, includeType=includeType))
    returnValue.extend(getReferenceSelectorTypes("Switches", includeScope=includeScope, includeType=includeType))
    return returnValue
    
def getAllFieldStructuresTypes(includeListType=False, includeChoiceType=False, includeType=False):
    structureTypes = [
        ('enum', 'Enumeration'),
        ('bits', 'Bitfield'),
        ('object', 'Object')
    ]
    if includeListType:
        structureTypes.append(('list', 'List'))
    if includeChoiceType:
        structureTypes.append(('switch', 'Choice'))
    
    typePart = ""
    if includeType:
        typePart = " (Structure)"
    return [(item[0], "{0}{1}".format(item[1], typePart)) for item in structureTypes]
    
def getDependencyStructureTypes(includeType=False):
    structureTypes = [
        ('enum', 'Enumeration')
    ]
    
    typePart = ""
    if includeType:
        typePart = " (Structure)"
    return [(item[0], "{0}{1}".format(item[1], typePart)) for item in structureTypes]
    
def getAllStructureTypes(includeType=False):
    structureTypes = [
        ('bits', 'Bits'),
        ('switch', 'Choice')
    ]
    
    typePart = ""
    if includeType:
        typePart = " (Structure)"
    returnValue = [(item[0], "{0}{1}".format(item[1], typePart)) for item in builtinTypes]
    returnValue.extend(getDependencyStructureTypes(includeType=includeType))
    return returnValue
    
def getAllDependencySelectorTypes(includeType=True):
    returnValue = []
    returnValue.extend(getAllBuiltInTypeSelectorTypes(includeType=includeType))
    returnValue.extend(getAllCustomTypeSelectorTypes(includeType=includeType))
    returnValue.extend(getDependencyStructureTypes(includeType=includeType))
    
    return returnValue
        
def getSnapshot():
    returnValue = {}
    returnValue["version"] = "1.0"
    if "Protocol" in session:
        returnValue["Protocol"] = session["Protocol"]
    if "EntryPoint" in session:
        returnValue["EntryPoint"] = session["EntryPoint"]
    if "usesTCP" in session:
        returnValue["usesTCP"] = session["usesTCP"]
    if "usesUDP" in session:
        returnValue["usesUDP"] = session["usesUDP"]
    if "Ports" in session:
        returnValue["Ports"] = session["Ports"]
    if "CustomFieldTypes" in session:
        returnValue["CustomFieldTypes"] = session["CustomFieldTypes"]
    if "Structures" in session:
        returnValue["Structures"] = session["Structures"]
    return json.dumps(returnValue, indent=4)
    
def setSnapshot(snapshotData):
    print(snapshotData)
    jsonValue = json.load(snapshotData)
    print("Received String: " + json.dumps(jsonValue))
    if "Protocol" in jsonValue:
        session["Protocol"] = jsonValue["Protocol"]
    if "EntryPoint" in jsonValue:
        session["EntryPoint"] = jsonValue["EntryPoint"]
    if "usesTCP" in jsonValue:
        session["usesTCP"] = jsonValue["usesTCP"]
    if "usesUDP" in jsonValue:
        session["usesUDP"] = jsonValue["usesUDP"]
    if "Ports" in jsonValue:
        session["Ports"] = jsonValue["Ports"]
    if "CustomFieldTypes" in jsonValue:
        session["CustomFieldTypes"] = jsonValue["CustomFieldTypes"]
    if "Structures" in jsonValue:
        _createStructureIfNecessary()
        session["Structures"] = jsonValue["Structures"]
        
def updateConfig(configForm):
    session["Protocol"] = configForm.parserName.data
    session["EntryPoint"] = configForm.entryPoint.data
    session["usesTCP"] = configForm.usesTCP.data
    session["usesUDP"] = configForm.usesUDP.data
    
def addUserTypeToSession(userTypeForm):
    _createCustomFieldTypesIfNecessary()
    entry = {}
    entry["name"] = userTypeForm.typeName.data
    entry["interpretingFunction"] = userTypeForm.interpretingFunction.data
    entry["returnType"] = userTypeForm.returnType.data
    session["CustomFieldTypes"].append(entry)
    session.modified = True
    
def removeUserTypeFromSession(index):
    if "CustomFieldTypes" in session:
        if index < len(session["CustomFieldTypes"]):
            session["CustomFieldTypes"].pop(index)
            session.modified = True
            
def addPortToSession(portForm):
    _createPortsIfNecessary()
    entry = {}
    entry["protocol"] = portForm.protocolName.data
    entry["port"] = portForm.portNumber.data
    session["Ports"].append(entry)
    session.modified = True
    
def removePortFromSession(index):
    if "Ports" in session:
        if index < len(session["Ports"]):
            session["Ports"].pop(index)
            session.modified = True

def addBitfieldToStructure(bitfieldForm):
    _createBitfieldStructureIfNecessary()
    entry = {}
    entry["name"] = bitfieldForm.bitfieldName.data
    if bitfieldForm.bitfieldReference.data is not None:
        entry["reference"] = bitfieldForm.bitfieldReference.data
    if bitfieldForm.bitfieldNote.data is not None:
        entry["notes"] = bitfieldForm.bitfieldNote.data
    entry["size"] = bitfieldForm.bitfieldSize.data
    entry["fields"] = []
    for field in bitfieldForm.fields:
        fieldEntry = {}
        fieldEntry["name"] = field.fieldName.data
        fieldEntry["description"] = field.fieldDescription.data
        fieldEntry["notes"] = field.fieldNote.data
        fieldEntry["type"] = field.fieldType.data
        fieldEntry["referenceType"] = field.referenceType.data
        bits = ""
        if field.bit.data is not None:
            bits = field.bit.data
        else:
            # Using starting and ending bits instead
            bits = str(field.startingBit.data) + ".." + str(field.endingBit.data)
        fieldEntry["bits"] = bits
        entry["fields"].append(fieldEntry)
    session["Structures"]["Bitfields"].append(entry)
    session.modified = True
    
def removeBitfieldFromStructure(index):
    if "Structures" in session and "Bitfields" in session["Structures"]:
        if index < len(session["Structures"]["Bitfields"]):
            session["Structures"]["Bitfields"].pop(index)
            session.modified = True
    
def addEnumToStructure(enumForm):
    _createEnumStructureIfNecessary()
    entry = {}
    entry["name"] = enumForm.enumName.data
    if enumForm.enumReference.data is not None:
        entry["reference"] = enumForm.enumReference.data
    if enumForm.enumNote.data is not None:
        entry["notes"] = enumForm.enumNote.data
    if enumForm.enumScope.data is not None:
        entry["scope"] = enumForm.enumScope.data
    entry["size"] = enumForm.enumSize.data
    entry["fields"] = []
    for field in enumForm.fields:
        fieldEntry = {}
        fieldEntry["name"] = field.fieldName.data
        fieldEntry["loggingValue"] = field.loggingValue.data
        fieldEntry["value"] = field.fieldValue.data
        if field.fieldNote.data is not None:
            fieldEntry["notes"] = field.fieldNote.data
        entry["fields"].append(fieldEntry)
    session["Structures"]["Enums"].append(entry)
    session.modified = True
    
def removeEnumFromStructure(index):
    if "Structures" in session and "Enums" in session["Structures"]:
        if index < len(session["Structures"]["Enums"]):
            session["Structures"]["Enums"].pop(index)
            session.modified = True
            
def addObjectToStructure(objectForm):
    _createObjectStructureIfNecessary()
    entry = {}
    entry["name"] = objectForm.objectName.data
    if objectForm.objectReference.data is not None:
        entry["reference"] = objectForm.objectReference.data
    if objectForm.objectNote.data is not None:
        entry["notes"] = objectForm.objectNote.data
    if objectForm.objectScope.data is not None:
        entry["scope"] = objectForm.objectScope.data
    entry["logIndependently"] = objectForm.logIndependently.data
    entry["logWithParent"] = bool(not objectForm.logIndependently.data and (objectForm.objectScope.data is None or "" == objectForm.objectScope.data))
    dependsOn = []
    if objectForm.objectDependencies is not None and 0 < len(objectForm.objectDependencies):
        for dependency in objectForm.objectDependencies:
            dependsOn.append(_processDependencyForm(dependency))
    entry["dependsOn"] = dependsOn
    # Add empty fields array for now
    entry["fields"] = []
    session["Structures"]["Objects"].append(entry)
    session.modified = True
            
def removeObjectFromStructure(index):
    if "Structures" in session and "Objects" in session["Structures"]:
        if index < len(session["Structures"]["Objects"]):
            session["Structures"]["Objects"].pop(index)
            session.modified = True
            
def addFieldToObject(objectIndex, fieldForm):
    if "Structures" in session and "Objects" in session["Structures"]:
        if objectIndex < len(session["Structures"]["Objects"]):
            if session["Structures"]["Objects"][objectIndex].get("fields") is None:
                session["Structures"]["Objects"][objectIndex]["fields"] = []
            entry = {}
            entry["name"] = fieldForm.fieldName.data
            if fieldForm.fieldDescription.data is not None:
                entry["description"] = fieldForm.fieldDescription.data
            if fieldForm.fieldNote.data is not None:
                entry["notes"] = fieldForm.fieldNote.data
            if fieldForm.isConditional.data:
                conditionalEntry = {}
                conditionalEntry["indicator"] = fieldForm.conditionalIndicator.data
                conditionalEntry["operator"] = fieldForm.conditionalOperator.data
                if fieldForm.useConditionalNumberValue.data:
                    conditionalEntry["value"] = fieldForm.conditionalNumberValue.data
                elif fieldForm.useConditionalTextValue.data:
                    conditionalEntry["value"] = fieldForm.conditionalTextValue.data
                else:
                    conditionalEntry["value"] = fieldForm.conditionalValue.data
                entry["conditional"] = conditionalEntry
            entry["type"] = fieldForm.fieldType.data
            isReferenceType = False
            isSplitInput = False
            if "list" == entry["type"]:
                entry["elementType"] = fieldForm.elementType.data
                if entry["elementType"] in ["switch", "object", "enum", "bits"]:
                    isReferenceType = True
                    if "switch" == entry["elementType"]:
                        isSplitInput = True
                untilEntry = {}
                untilEntry["conditionType"] = fieldForm.untilConditionType.data
                if "COUNT" == untilEntry["conditionType"]:
                    untilEntry["indicator"] = fieldForm.untilConditionIndicator.data
                entry["until"] = untilEntry
            elif entry["type"] in ["switch", "object", "enum", "bits", "list"]:
                isReferenceType = True
                if "switch" == entry["type"]:
                    isSplitInput = True
                
            if isReferenceType:
                entry["referenceType"] = fieldForm.referenceType.data
            else:
                entry["size"] = fieldForm.fieldSize.data
                
            if fieldForm.inputs is not None and 0 < len(fieldForm.inputs):
                inputs = []
                startingIndex = 0
                if isSplitInput:
                    entry["input"] = {"source": fieldForm.inputs[0].data}
                    startingIndex = 1
                if startingIndex < len(fieldForm.inputs):
                    for index in range(startingIndex, len(fieldForm.inputs)):
                        inputs.append({"source": fieldForm.inputs[index].data})
                if isSplitInput:
                    entry["additionalInputs"] = inputs
                else:
                    entry["inputs"] = inputs
            print(entry)
            session["Structures"]["Objects"][objectIndex]["fields"].append(entry)
            session.modified = True
    
def removeFieldFromObject(objectIndex, fieldIndex):
    if "Structures" in session and "Objects" in session["Structures"]:
        if objectIndex < len(session["Structures"]["Objects"]) and \
           fieldIndex < len(session["Structures"]["Objects"][objectIndex]["fields"]):
            session["Structures"]["Objects"][objectIndex]["fields"].pop(fieldIndex)
            session.modified = True
            
def addSwitchToStructure(switchForm):
    _createSwitchStructureIfNecessary()
    entry = {}
    entry["name"] = switchForm.switchName.data
    entry["dependsOn"] = _processDependencyForm(switchForm.switchMainDependency)
    additionDependsOn = []
    if switchForm.switchAdditionalDependencies is not None and 0 < len(switchForm.switchAdditionalDependencies):
        for dependency in switchForm.switchAdditionalDependencies:
            additionDependsOn.append(_processDependencyForm(dependency))
    entry["additionalDependsOn"] = additionDependsOn
    options = []
    if switchForm.switchOptions is not None and 0 < len(switchForm.switchOptions):
        for option in switchForm.switchOptions:
            options.append(_processOptionForm(option))
    entry["options"] = options
    session["Structures"]["Switches"].append(entry)
    session.modified = True

def removeSwitchFromStructure(index):
    if "Structures" in session and "Switches" in session["Structures"]:
        if index < len(session["Structures"]["Switches"]):
            session["Structures"]["Switches"].pop(index)
            session.modified = True
        
################################################################################
# Functions to check
################################################################################
    
def __processMissingReferencesForBitfield(bitfield, enumNames, bitfieldNames):
    returnValue = []
    bitfieldName = bitfield["bitfieldName"]
    for field in bitfield.get("fields"):
        entryName = field.get("fieldName")
        entryFormat = field.get("fieldType")
        entryReference = field.get("fieldReference")
        if "enum" == entryFormat:
            if not entryReference in enumNames:
                returnValue.append({"bitfieldName": bitfieldName,
                                    "fieldName": entryName,
                                    "reference": entryReference,
                                    "referenceType": "enum"})
    return returnValue
                
"""def _findMissingReferences(commands, enums, bitfields):
    returnValue = []
    # Simple approach for now?
    # Get Enum Names
    seenEnumNames = []
    for i in range(len(enums)):
        currentEnumName = enums[i].get("enumName")
        if currentEnumName is not None:
            seenEnumNames.append(currentEnumName)
    
    # Get Bitfield Names
    seenBitfieldNames = []
    for i in range(len(bitfields)):
        currentBitfieldName = bitfields[i].get("bitfieldName")
        if currentBitfieldName is not None:
            seenBitfieldNames.append(currentBitfieldName)
    
    # Process the commands
    for i in range(len(commands)):
        tempOutput = __processMissingReferencesForCommand(commands[i], seenEnumNames, seenBitfieldNames)
        for entry in tempOutput:
            returnValue.append({"path": "Command {0}.{1}.{2}".format(entry["commandName"], entry["structureType"], entry["fieldName"]),
                                "reference": entry["reference"],
                                "referenceType": entry["referenceType"]})
            
    # Process the bitfields
    for i in range(len(bitfields)):
        tempOutput =  __processMissingReferencesForBitfield(bitfields[i], seenEnumNames, seenBitfieldNames)
        for entry in tempOutput:
            returnValue.append({"path": "Bitfield {0}.{1}".format(entry["bitfieldName"], entry["fieldName"]),
                                "reference": entry["reference"],
                                "referenceType": entry["referenceType"]})
    
    return returnValue"""

def _checkForDuplicates(items, itemType, returnList):
    if items is not None:
        itemNames = set()
        for item in items:
            itemName = item.get("name")
            if itemName in itemNames:
                returnList.append({"type": "Error",
                    "title": "Duplicate {0}".format(itemType),
                    "content": "Duplicte {0} with name {1}".format(itemType, itemName)})
            else:
                itemNames.add(itemName)
    else:
        print("No Items of Type: {0}".format(itemType))
        returnList.append({"type": "Warning",
        "title": "Empty Structure",
        "content": "Duplicte {0} with name {1}".format(itemType, itemName)})
        
def reviewStructure():
    returnValue = []
    # Issue Structure
    # {
    #   "content": "",
    #   "title": "",
    #   "type": ""
    # }
    
    if "Structures" in session:

        #Check For Duplicates
        checkForDuplicates(getSnapshot(), returnValue)
                          
        # Find missing references
        checkForMissingDependencies(getSnapshot(), returnValue)

        
    else:
        entry = {}
        entry["type"] = "Warning"
        entry["title"] = "No Structure"
        entry["content"] = ""
        
        returnValue.append(entry)
    
    if not returnValue:
        returnValue.append({"type": "No Issue",
                    "title": "Passed",
                    "content": "All reviews were passed."})

    return returnValue
