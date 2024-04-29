#!/usr/bin/env python3

# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import os
import sys
import json

#spicyTypes = ["addr", "bitfield", "uint8", "uint16", "uint32", "uint64", "int8",
#              "int16", "int32", "int64", "bool", "bytes", "real"]

languageTypes = [
    ("addr", [32, 128]), # Passthrough Spicy Type
    ("uint", [8, 16, 24, 32, 64]), # Spicy built in for sizes 8, 16, 32, and 64; 24 we added
    ("int", [8, 16, 24, 32, 64]), # Spicy built in for sizes 8, 16, 32, and 64; 24 we added
    ("void", None), # Spicy type used to denote no fields
    ("bytes", None), # Passthrough Spicy Type, size will be converted to bytes from bits
    ("float", [32, 64]) # Maps to spicy "real" type with either float or double flag
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

DEFAULT_SCOPE = "general"

userDefinedTypes = []

################################################################################
# Function Declarations
################################################################################
def determineScope(item):
    if "scope" in item:
        return item.get("scope")
    else:
        return DEFAULT_SCOPE

def addObjectToScope(item, objectType, structuresToScope):
    name = item.get("name")
    scope = determineScope(item)

    if objectType not in structuresToScope:
        structuresToScope[objectType] = {}
    if name not in structuresToScope[objectType]:
        structuresToScope[objectType][name] = []
    structuresToScope[objectType][name].append(scope)
        
    return (scope, name)
    
def _addVerifiedDependency(parentInfo, itemInfo, dependencyInfo):
    if parentInfo[0] not in dependencyInfo:
        dependencyInfo[parentInfo[0]] = {}
    if parentInfo[1] not in dependencyInfo[parentInfo[0]]:
        dependencyInfo[parentInfo[0]][parentInfo[1]] = {}
    if parentInfo[2] not in dependencyInfo[parentInfo[0]][parentInfo[1]]:
        dependencyInfo[parentInfo[0]][parentInfo[1]][parentInfo[2]] = []
    dependencyInfo[parentInfo[0]][parentInfo[1]][parentInfo[2]].append(itemInfo)
    
def addDependencyToStructure(parentType, parentScope, parentName, dependentItem, dependencyInfo, returnValue):
    name = dependentItem.get("referenceType")
    itemName = dependentItem.get("name")
    itemType = dependentItem.get("type")
    size = dependentItem.get("size")
    
    typeIndex = next((index for index, value in enumerate(languageTypes) if value[0] == itemType), -1)
    
    if "bits" == parentType:
        if itemType not in bitfieldSpecificTypes:
            returnValue.append({"type": "Error",
                "title": "Unknown Bitfield Item Type",
                "content": "Unknown bitfield item type '{0}' in item '{1}.{2}.{3}'".format(itemType, parentType, parentScope, parentName)})
        elif "enum" == itemType:
            # Add the dependency
            _addVerifiedDependency((parentType, parentScope, parentName), (itemType, name), dependencyInfo)
    elif typeIndex != -1:
        # This is a known type
        if languageTypes[typeIndex][1] is None or \
           size in languageTypes[typeIndex][1]:
            # No size is expected or the size matches an expected size
            # Good to go
            return
        else:
            # Size is expected, but the one provided doesn't match
            returnValue.append({"type": "Error",
                "title": "Unknown Size for Language Type",
                "content": "Unknown Size '{0}' for language type '{1}' in item '{2}.{3}.{4}'".format(size, itemType, parentType, parentScope, parentName)})
    elif itemType in userDefinedTypes:
        # User defined type, good to go
        return
    elif itemType in structureTypes:
        # Add the dependency
        _addVerifiedDependency((parentType, parentScope, parentName), (itemType, name), dependencyInfo)
    elif itemType in otherReferenceTypes:
        itemType = dependentItem.get("elementType")
        _addVerifiedDependency((parentType, parentScope, parentName), (itemType, name), dependencyInfo)
    else:
        # Unknown type
        returnValue.append({"type": "Error",
            "title": "Unknown Object Type",
            "content": "Unknown object type '{0}' in '{1}' part of item '{2}.{3}.{4}'".format(itemType, itemName, parentType, parentScope, parentName)})


def checkForMissingDependencies(snapshot, returnValue):

    ################################################################################
    # Load the content
    ################################################################################
    contents = json.loads(snapshot)
        
    ################################################################################
    # Load information about the custom types the user has defined
    ################################################################################    
    userTypes = contents.get("CustomFieldTypes")

    if userTypes is not None:
        for userType in userTypes:
            userDefinedTypes.append(userType.get("name"))

    ################################################################################
    # Tracking Structures
    ################################################################################
    # Assumption, no duplicates
    structuresToScopes = {} # Type -> ObjectName -> Scopes[]
    structureDependencies = {} # Type -> Scope -> ObjectName -> Dependencies[]

    ################################################################################
    # Load information about the structures present
    ################################################################################
    structures = contents.get("Structures")

    #############################################
    # Process the Objects
    #############################################
    objects = structures.get("Objects")
    if objects:
        for currentObject in objects:
            # Add item to scope and add the scope to the set of scopes
            itemScope, itemName = addObjectToScope(currentObject, "object", structuresToScopes)
            # Look for references in the dependsOn section
            if "dependsOn" in currentObject:
                for dependency in currentObject.get("dependsOn"):
                    addDependencyToStructure("object", itemScope, itemName, dependency, structureDependencies, returnValue)
            # Look for references in the fields
            for field in currentObject.get("fields"):
                addDependencyToStructure("object", itemScope, itemName, field, structureDependencies, returnValue)

    #############################################
    # Process the Bitfields
    #############################################
    bitfields = structures.get("Bitfields")

    if bitfields:
        for bitfield in bitfields:
            itemScope, itemName = addObjectToScope(bitfield, "bits", structuresToScopes)
            # Look for references in the fields
            for field in bitfield.get("fields"):
                addDependencyToStructure("bits", itemScope, itemName, field, structureDependencies, returnValue)

    #############################################
    # Process the Enums
    #############################################
    enums = structures.get("Enums")

    if enums:
        for enum in enums:
            itemScope, itemName = addObjectToScope(enum, "enum", structuresToScopes)
            # Enum fields don't reference any types

    #############################################
    # Process the Switches
    #############################################
    switches = structures.get("Switches")

    if switches:
        for currentSwitch in switches:
            itemScope, itemName = addObjectToScope(currentSwitch, "switch", structuresToScopes)
            # Look for references in the dependsOn section
            dependsOnSection = currentSwitch.get("dependsOn")
            addDependencyToStructure("switch", itemScope, itemName, dependsOnSection, structureDependencies, returnValue)
            # Look for references in the additionalDependsOn section
            if "additionalDependsOn" in currentSwitch:
                for dependency in currentSwitch.get("additionalDependsOn"):
                    addDependencyToStructure("switch", itemScope, itemName, dependency, structureDependencies, returnValue)
            # Look for references in the options section
            for option in currentSwitch.get("options"):
                actionSection = option.get("action")
                addDependencyToStructure("switch", itemScope, itemName, actionSection, structureDependencies, returnValue)
            
    ################################################################################
    # Check the dependencies
    ################################################################################
    for structure in structureDependencies:
        for scope in structureDependencies[structure]:
            for objectName in structureDependencies[structure][scope]:
                for dependency in structureDependencies[structure][scope][objectName]:
                    dependencyType = dependency[0]
                    dependencyName = dependency[1]
                    
                    # See if we know about the dependency
                    # structuresToScopes: Type -> ObjectName -> Scopes[]
                    if dependencyType in structuresToScopes and \
                    dependencyName in structuresToScopes[dependencyType]:
                        # We know about it
                        # See if there is any confusion about it
                        scopes = structuresToScopes[dependencyType][dependencyName]
                        if 1 != len(scopes):
                            # Confusion about scope
                            returnValue.append({"type": "Error",
                                "title": "Scope Confusion",
                                "content": "Dependency {0}.{1} for Item {2}.{3}.{4} exists in multiple scopes: {5}".format(dependencyType, dependencyName, structure, scope, objectName, "'" + ("', ".join(scopes)) + "'")})
                    else:
                        # No idea...
                        returnValue.append({"type": "Error",
                            "title": "No Dependency",
                            "content": "Dependency {0}.{1} does not exist for Item {2}.{3}.{4}".format(dependencyType, dependencyName, structure, scope, objectName)})

    #print(languageTypes)
    #print(bitfieldSpecificTypes)
    #print(structureTypes)
    #print(userDefinedTypes)
    #print()
    #print(structuresToScopes)
    #print()
    #print(structureDependencies)
