#!/usr/bin/env python3

# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import os
import sys
import json
import uuid
from shutil import rmtree
from io import BytesIO
from zipfile import ZipFile

DEFAULT_SCOPE = "general"

def copyIfExists(key, source, destination):
    if key in source:
        destination[key] = source[key]
        
def copyIfExistsOrDefault(key, source, destination, defaultValue):
    if key not in source:
        destination[key] = defaultValue
    else:
        copyIfExists(key, source, destination)        

def determineScope(item):
    if "scope" in item and "" != item["scope"]:
        return item.get("scope")
    else:
        return DEFAULT_SCOPE

def generateReferenceString(objectType, referenceType):
    return ".".join([objectType, referenceType])
    
def addScopeToObjectDependencies(items, referenceScopes):
    for item in items:
        # Look for references in the dependsOn section
        if "dependsOn" in item:
            for dependency in item.get("dependsOn"):
                itemScope = getReferenceScopeIfExists(dependency.get("type"), None, dependency.get("referenceType"), referenceScopes)
                if itemScope is not None:
                    dependency["scope"] = itemScope
        # Look for references in the fields
        for field in item.get("fields"):
            itemScope = getReferenceScopeIfExists(field.get("type"), field.get("elementType"), field.get("referenceType"), referenceScopes)
            if itemScope is not None:
                    field["scope"] = itemScope
        
def addScopeToBitfieldDependencies(items, referenceScopes):
    for item in items:
        # Look for references in the fields
        for field in item.get("fields"):
            itemScope = getReferenceScopeIfExists(field.get("type"), None, field.get("referenceType"), referenceScopes)
            if itemScope is not None:
                    field["scope"] = itemScope
        
def addScopeToSwitchDependencies(items, referenceScopes):
    for item in items:
        # Look for references in the dependsOn section
        dependsOnSection = item.get("dependsOn")
        itemScope = getReferenceScopeIfExists(dependsOnSection.get("type"), None, dependsOnSection.get("referenceType"), referenceScopes)
        if itemScope is not None:
            dependsOnSection["scope"] = itemScope
        # Look for references in the additionalDependsOn section
        if "additionalDependsOn" in item:
            for dependency in item.get("additionalDependsOn"):
                itemScope = getReferenceScopeIfExists(dependency.get("type"), None, dependency.get("referenceType"), referenceScopes)
                if itemScope is not None:
                    dependency["scope"] = itemScope
        # Look for references in the options section
        for option in item.get("options"):
            actionSection = option.get("action")
            itemScope = getReferenceScopeIfExists(actionSection.get("type"), None, actionSection.get("referenceType"), referenceScopes)
            if itemScope is not None:
                actionSection["scope"] = itemScope
        if "default" in item:
            defaultSection = item.get("default")
            itemScope = getReferenceScopeIfExists(defaultSection.get("type"), None, defaultSection.get("referenceType"), referenceScopes)
            if itemScope is not None:
                defaultSection["scope"] = itemScope

def addReferenceCount(objectType, items, referenceCounts):
    for item in items:
        key = generateReferenceString(objectType, item.get("name"))
        count = 0
        if key in referenceCounts:
            count = referenceCounts[key]
        item["referenceCount"] = count
        
def updateLogging(objectType, items, objectInList, objectInObject):
    for item in items:
        key = generateReferenceString(objectType, item.get("name"))
        if key in objectInList:
            item["logIndependently"] = True
            item["logWithParent"] = False
        if False == item["logIndependently"] and key in objectInObject:
            item["logWithParent"] = True

def addObjectToScope(item, saveLocation):
    name = item.get("name")
    scope = determineScope(item)
    if scope not in saveLocation:
        saveLocation[scope] = []
    saveLocation[scope].append(item)
    return (scope, name)
    
def getReferenceScopeIfExists(objectType, elementType, referenceType, referenceScope):
    if objectType is not None:
        if objectType in ["object", "enum", "bits", "switch"] and \
           referenceType is not None and \
           "" != referenceType:
            referenceString = generateReferenceString(objectType, referenceType)
            if referenceString in referenceScope:
                return referenceScope.get(referenceString)
        elif "list" == objectType and \
             elementType in ["object", "enum", "bits", "switch"] and \
             referenceType is not None and \
             "" != referenceType:
            referenceString = generateReferenceString(elementType, referenceType)
            if referenceString in referenceScope:
                return referenceScope.get(referenceString)
    return None

def updateReferenceCountIfNecessary(objectType, referenceType, referenceCounts):
    if objectType is not None and \
       objectType in ["object", "enum", "bits", "switch"] and \
       referenceType is not None and \
       "" != referenceType:
        referenceString = generateReferenceString(objectType, referenceType)
        if referenceString in referenceCounts:
            referenceCounts[referenceString] = referenceCounts[referenceString] + 1
        else:
            referenceCounts[referenceString] = 1
            
def updateObjectInListIfNecessary(objectType, elementType, referenceType, objectInList):
    if objectType is not None and "list" == objectType and \
       elementType is not None and "object" == elementType and \
       referenceType is not None and "" != referenceType:
        referenceString = generateReferenceString(elementType, referenceType)
        if referenceString not in objectInList:
            objectInList[referenceString] = True

def updateObjectInObjectIfNecessary(objectType, referenceType, objectInObject):
    if objectType is not None and "object" == objectType and \
       referenceType is not None and "" != referenceType:
        referenceString = generateReferenceString(objectType, referenceType)
        if referenceString not in objectInObject:
            objectInObject[referenceString] = True

def dumpContentsToFile(contents, filePath):
    with open(filePath, "w") as outFile:
        json.dump(contents, outFile, indent=4)

def getAllFilePaths(directory):
  
    # initializing empty file paths list
    filePaths = []
  
    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            filePaths.append(filepath)
  
    # returning all file paths
    return filePaths

def getParsnipFile(snapShot):

    fileID = str(uuid.uuid4())
    rootFolder = fileID
    os.makedirs(rootFolder, exist_ok=True)

    contents = json.loads(snapShot)

    # JSON Dictionaries
    configContents = {}
    objectContents = {}
    enumContents = {}
    bitfieldContents = {}
    switchContents = {}

    # Tracking Sets
    scopes = set()

    # Tracking Dictionaries
    references = {}
    referencesToScopes = {}
    objectInList = {}
    objectInObject = {}

    ################################################################################
    # Get information for the general config file
    ################################################################################
    copyIfExistsOrDefault("ParsnipVersion", contents, configContents, "1.0")
    # EntryPoint taken care of later
    copyIfExistsOrDefault("Protocol", contents, configContents, "")
    copyIfExistsOrDefault("protocolShortDescription", contents, configContents, "TODO: A summary of HART_IP in one line")
    copyIfExistsOrDefault("protocolLongDescription", contents, configContents, "TODO: A more detailed description of HART_IP.\nIt can span multiple lines, with this indentation.")
    copyIfExistsOrDefault("Ports", contents, configContents, [])
    copyIfExistsOrDefault("usesTCP", contents, configContents, False)
    copyIfExistsOrDefault("usesUDP", contents, configContents, False)
    copyIfExistsOrDefault("usesLayer2", contents, configContents, False)
    copyIfExists("ethernetProtocolNumber", contents, configContents)
    copyIfExists("conversionFile", contents, configContents)
    copyIfExists("signatureFile", contents, configContents)
    # TODO: Figure out other User Constants
    copyIfExistsOrDefault("CustomFieldTypes", contents, configContents, [])

    ################################################################################
    # Process the Structures
    ################################################################################
    structures = contents.get("Structures")

    #############################################
    # Process the Objects
    #############################################
    objects = structures.get("Objects")

    if objects:
        for currentObject in objects:
            if None == currentObject.get("skip") or False == currentObject.get("skip"):
                # Add item to scope and add the scope to the set of scopes
                itemScope, itemName = addObjectToScope(currentObject, objectContents)
                scopes.add(itemScope)
                referencesToScopes[generateReferenceString("object", itemName)] = itemScope
                # Look for references in the dependsOn section
                if "dependsOn" in currentObject:
                    for dependency in currentObject.get("dependsOn"):
                        updateReferenceCountIfNecessary(dependency.get("type"), dependency.get("referenceType"), references)
                # Look for references in the fields
                for field in currentObject.get("fields"):
                    updateReferenceCountIfNecessary(field.get("type"), field.get("referenceType"), references)
                    updateObjectInListIfNecessary(field.get("type"), field.get("elementType"), field.get("referenceType"), objectInList)
                    updateObjectInObjectIfNecessary(field.get("type"), field.get("referenceType"), objectInObject)

    #############################################
    # Process the Bitfields
    #############################################
    bitfields = structures.get("Bitfields")

    if bitfields:
        for bitfield in bitfields:
            if None == bitfield.get("skip") or False == bitfield.get("skip"):
                itemScope, itemName = addObjectToScope(bitfield, bitfieldContents)
                if itemScope not in scopes:
                    print("Warning: Bitfield Scope {0} does not match an Object Scope!".format(itemScope))
                    # TODO: Figure out how to show this on the frontend.
                referencesToScopes[generateReferenceString("bits", itemName)] = itemScope
                # Look for references in the fields
                for field in bitfield.get("fields"):
                    updateReferenceCountIfNecessary(field.get("type"), field.get("referenceType"), references)

    #############################################
    # Process the Enums
    #############################################
    enums = structures.get("Enums")

    if enums:
        for enum in enums:
            if None == enum.get("skip") or False == enum.get("skip"):
                itemScope, itemName = addObjectToScope(enum, enumContents)
                if itemScope not in scopes:
                    print("Warning: Enum Scope {0} does not match an Object Scope!".format(itemScope))
                    # TODO: Figure out how to show this on the frontend.
                referencesToScopes[generateReferenceString("enum", itemName)] = itemScope
                # Enum fields don't reference any types

    #############################################
    # Process the Switches
    #############################################
    switches = structures.get("Switches")

    if switches:
        for currentSwitch in switches:
            if None == currentSwitch.get("skip") or False == currentSwitch.get("skip"):
                itemScope, itemName = addObjectToScope(currentSwitch, switchContents)
                if itemScope not in scopes:
                    print("Warning: Enum Scope {0} does not match an Object Scope!".format(itemScope))
                    # TODO: Figure out how to show this on the frontend.
                referencesToScopes[generateReferenceString("switch", itemName)] = itemScope
                # Look for references in the dependsOn section
                dependsOnSection = currentSwitch.get("dependsOn")
                updateReferenceCountIfNecessary(dependsOnSection.get("type"), dependsOnSection.get("referenceType"), references)
                # Look for references in the additionalDependsOn section
                if "additionalDependsOn" in currentSwitch:
                    for dependency in currentSwitch.get("additionalDependsOn"):
                        updateReferenceCountIfNecessary(dependency.get("type"), dependency.get("referenceType"), references)
                # Look for references in the options section
                for option in currentSwitch.get("options"):
                    actionSection = option.get("action")
                    updateReferenceCountIfNecessary(actionSection.get("type"), actionSection.get("referenceType"), references)

    ################################################################################
    # Run some checks
    ################################################################################
    # Check EntryPoint Validity
    if "EntryPoint" not in contents or "" == contents.get("EntryPoint"):
        print("Error: No EntryPoint specified")
    else:
        entryPointObjectName = contents.get("EntryPoint")
        entryPointScope = referencesToScopes.get(generateReferenceString("object", entryPointObjectName))
        if DEFAULT_SCOPE != entryPointScope:
            print("Warning: EntryPoint not in default scope!")
        configContents["EntryPoint"] = ".".join([entryPointScope, contents.get("EntryPoint")])
        # Make sure that the EntryPoint entry is at the top of the corresponding objects information
        entryPointObjectsArea = objectContents.get(entryPointScope)
        entryPointIndex = next((index for index, value in enumerate(entryPointObjectsArea) if value.get("name") == entryPointObjectName), -1)

        if -1 == entryPointIndex:
            print("Error: EntryPoint Object not Found!")
        else:
            if 0 != entryPointIndex:
                # Need to move the EntryPoint to the front
                entryPointObjectsArea.insert(0, entryPointObjectsArea.pop(entryPointIndex))
            entryPointObjectsArea[0]["logWithParent"] = False

    # Add list of scopes
    tempScopeList = list(scopes)
    tempScopeList.sort()
    scopeIndex = next((index for index, value in enumerate(tempScopeList) if "general" == value), -1)
    if -1 != scopeIndex:
        tempScopeList.insert(0, tempScopeList.pop(scopeIndex))
    configContents["Scopes"] = tempScopeList

    #print(references)

    ################################################################################
    # Generate output
    ################################################################################
    #############################################
    # Main Config
    #############################################
    generalFolder = os.path.join(rootFolder, "general")

    os.makedirs(generalFolder, exist_ok=True)
    dumpContentsToFile(configContents, os.path.join(generalFolder, "config.json"))

    #############################################
    # Scope Files
    #############################################
    for scope in scopes:
        currentFolder = os.path.join(rootFolder, scope)
        os.makedirs(currentFolder, exist_ok=True)
        if scope in objectContents:
            # Update Reference Counts
            addReferenceCount("object", objectContents.get(scope), references)
            updateLogging("object", objectContents.get(scope), objectInList, objectInObject)
            addScopeToObjectDependencies(objectContents.get(scope), referencesToScopes)
            dumpContentsToFile(objectContents.get(scope), os.path.join(currentFolder, "objects.json"))
        if scope in enumContents:
            addReferenceCount("enum", enumContents.get(scope), references)
            dumpContentsToFile(enumContents.get(scope), os.path.join(currentFolder, "enums.json"))
        if scope in bitfieldContents:
            addReferenceCount("bits", bitfieldContents.get(scope), references)
            addScopeToBitfieldDependencies(bitfieldContents.get(scope), referencesToScopes)
            dumpContentsToFile(bitfieldContents.get(scope), os.path.join(currentFolder, "bitfields.json"))
        if scope in switchContents:
            addReferenceCount("switch", switchContents.get(scope), references)
            addScopeToSwitchDependencies(switchContents.get(scope), referencesToScopes)
            dumpContentsToFile(switchContents.get(scope), os.path.join(currentFolder, "switches.json"))
    
  
    # calling function to get all file paths in the directory
    filePaths = getAllFilePaths(rootFolder)
  
  
    # writing files to a in-memory zipfile
    memoryFile = BytesIO()
    with ZipFile(memoryFile, 'w') as zf:
        for fileName in filePaths:
            zf.write(fileName)
    memoryFile.seek(0)
    print(rootFolder)

    rmtree(rootFolder)

    return(memoryFile)

