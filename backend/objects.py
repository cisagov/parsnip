# Copyright 2023, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils
import events
import json_processing

#ADD_DEBUG=True
ADD_DEBUG=False

class Link:
    def __init__(self, name, parameterName, isEndLink = False):
        self.name = name
        self.parameterName = parameterName
        self.isEndLink = isEndLink

class ObjectField:
    def __init__(self, name, description, type, scope = ""):
        self.name = name
        self.description = description
        self.notes = ""
        self.type = type
        self.referenceType = ""
        self.elementType = ""
        self.size = 0
        self.inputs = []
        self.until = None
        self.scope = utils.normalizedScope(scope, type)
        self.conditional = []
        self.endianness = "big"
        self.zeekName = ""
        
    def addInput(self, input):
        for existingInput in self.inputs:
            if existingInput.source == input.source:
                return
        if input not in self.inputs:
            self.inputs.append(input)

    def createSpicyString(self, columns, customTypes, bitfields, switches, enums, dependsOn, fields):
        outputString = ""
        if self.notes is not None and "" != self.notes:
            outputString += "# {0}\n{1}".format(self.notes, utils.SINGLE_TAB)
        varString, typeString = utils.determineSpicyStringForType(self.name, self.type, self.elementType, self.referenceType, self.scope, self.size, self.inputs, self.until, columns + 4, customTypes, bitfields, switches, enums)
        conditionalString = ""
        if len(self.conditional) > 0:
            conditionalStringBuilder = self.conditional[:]
            for index in range(len(conditionalStringBuilder)):
                # Get the type and value
                entryType = conditionalStringBuilder[index][0]
                entryValue = conditionalStringBuilder[index][1]
                entryAssociatedValue = None
                if len(conditionalStringBuilder[index]) > 2:
                    entryAssociatedValue = conditionalStringBuilder[index][2]
                if "operator" == entryType and "=" == entryValue:
                    if "=" == entryValue:
                        # conditionalStringBuilder[index][1] = "=="
                        conditionalStringBuilder[index] = (conditionalStringBuilder[index][0], "==")
                elif "indicator" == entryType:
                    # See if we need to handle the value differently:
                    dependsOnIndex = next((index for index, value in enumerate(dependsOn) if value.name == entryValue), -1)
                    if -1 != dependsOnIndex and "enum" == dependsOn[dependsOnIndex].type and entryAssociatedValue is not None:
                        conditionalStringBuilder[entryAssociatedValue] = (conditionalStringBuilder[entryAssociatedValue][0], "{0}::{1}::{2}".format(dependsOn[dependsOnIndex].scope, dependsOn[dependsOnIndex].referenceType, conditionalStringBuilder[entryAssociatedValue][1]))
                    else:
                        fieldsIndex = next((index for index, value in enumerate(fields) if value.name == entryValue), -1)
                        if -1 != fieldsIndex and "enum" == fields[fieldsIndex].type and entryAssociatedValue is not None:
                            conditionalStringBuilder[entryAssociatedValue] = (conditionalStringBuilder[entryAssociatedValue][0], "{0}::{1}::{2}".format(fields[fieldsIndex].scope, fields[fieldsIndex].referenceType, conditionalStringBuilder[entryAssociatedValue][1]))
            for entry in conditionalStringBuilder:
                conditionalString += str(entry[1])
            conditionalString = " if ({0})".format(conditionalString)
        if "little" == self.endianness:
            conditionalString += " &byte-order=spicy::ByteOrder::Little"
        if "switch" == self.type:
            outputString += "{0}{1};".format(typeString, conditionalString)
        elif "linking" == self.type or "endlink" == self.type:
            outputString += "{}".format(typeString)
        else:
            if "" == varString:
                outputString += "{0}{1} : {2}{3};".format(self.name, utils.endingSpace(columns + 4, len(self.name)), typeString, conditionalString)
            else:
                outputString += "var {0}{1} : {2};\n{3}".format(self.name, utils.endingSpace(columns, len(self.name)), varString, utils.SINGLE_TAB)
                outputString += "{0} : {1}{2}".format(utils.endingSpace(columns + 4, 0), typeString, conditionalString)
        return outputString

class Object:
    def __init__(self, name, reference, notes, logIndependently, referenceCount, logWithParent=False):
        self.name = name
        self.reference = reference
        self.zeekStructure = []
        self.notes = notes
        self.logIndependently = logIndependently
        self.dependsOn = []
        self.fields = []
        self.referenceCount = referenceCount
        self.column = 0
        self.longestField = 0
        self.logWithParent = logWithParent
        self.linkIds = []
        self.excludedFields = []
        self.includedFields = []
        self.needsSpecificExport = False

    def addField(self, field):
        if field not in self.fields:
            calculatedColumn = utils.calculateColumn(len(field.name))
            if calculatedColumn > self.column:
                self.column = calculatedColumn
            if (len(field.name) > self.longestField):
                self.longestField = len(field.name)
            self.fields.append(field)

    def addFieldinLocation(self, index, field):
        for existingField in self.fields:
            if field.name == existingField.name:
                return
        self.fields.insert(index, field)
    
    def removeFieldinLocation(self, idx):
        self.fields.pop(idx)

    def addExcludedField(self, fieldName):
        if fieldName not in self.excludedFields and fieldName not in self.includedFields:
            self.excludedFields.append(fieldName)
    
    def addIncludedField(self, fieldName):
        if fieldName not in self.excludedFields and fieldName not in self.includedFields:
            self.includedFields.append(fieldName)

    def addDependency(self, dependency):
        for existingDependency in self.dependsOn:
            if existingDependency.name == dependency.name:
                return
        if dependency not in self.dependsOn:
            self.dependsOn.append(dependency)

    def addLinkField(self, field):
        for existingLink in self.linkIds:
            if field.name == existingLink.name:
                return
        self.linkIds.append(field)
            
    def createSpicyString(self, customTypes, bitfields, switches, enums, isPublic = False):
        outputString = ""
        if self.reference is not None and "" != self.reference:
            outputString += "# {0}\n".format(self.reference)
        if isPublic:
            outputString += "public "
        dependsPart = ""
        if 0 < len(self.dependsOn):
            dependsPart += " ("
            for index, depends in enumerate(self.dependsOn):
                if depends.type == "enum":
                    typeString = "{0}::{1}".format(depends.scope, depends.referenceType)
                else:
                    _, typeString = utils.determineSpicyStringForType(depends.name, depends.type, None, depends.referenceType, depends.scope, depends.size, [], None, self.column, customTypes, bitfields, switches, enums)
                dependsPart += "{0} : {1}".format(depends.name, typeString)
                if index < len(self.dependsOn) - 1:
                    dependsPart += ", "
            dependsPart += ")"
        outputString += "type {0} = unit{1} {{\n".format(self.name, dependsPart)
        if self.linkIds != []:
            varDeclarationString = ""
            initFunctionString = "{}on %init() {{\n".format(utils.SINGLE_TAB)
            for link in self.linkIds:
                varDeclarationString += "{}var {} : string;\n".format(utils.SINGLE_TAB, link.name)
                if link.isEndLink:
                    initFunctionString += "{}self.{} = {};\n".format(utils.DOUBLE_TAB, link.name, link.parameterName)
                else:
                    initFunctionString += "{}self.{} = {}_{}::generateId();\n".format(utils.DOUBLE_TAB, link.name, utils.PROTOCOL_NAME.upper(), utils.CONVERSION_SCOPE.upper())
            initFunctionString += "{}}}\n".format(utils.SINGLE_TAB)
            outputString += varDeclarationString
            outputString += initFunctionString
        for field in self.fields:
            outputString += "{0}{1}\n".format(utils.SINGLE_TAB, field.createSpicyString(self.column, customTypes, bitfields, switches, enums, self.dependsOn, self.fields))
        if ADD_DEBUG:
            outputString += "{0}on %done(){{print self;}}\n".format(utils.SINGLE_TAB)
        outputString += "};\n"
        return outputString

    def getEvent(self, moduleName):
        if self.logWithParent and not self.logIndependently:
            return []
        else:
            if self.needsSpecificExport:
                event = events.SpicyEvent(self.includedFields, self.linkIds)
            else:
                event = events.SpicyEvent()
            event.scope = moduleName
            event.name = self.name
        return event

    def makeEventBackend(self, moduleName, zeekStructureName, allEnums, allBitfields, allObjects,  allSwitches, scopes, includeNonFields = True, logObjectVariableName = "", itemPrefex = "", startingTabSize = 1, specificExportOverride=False):
        #pull this into a function
        convertingFunctionString = ""
        localVariableName = logObjectVariableName
        tabSize = startingTabSize
        if specificExportOverride:
            childOverride = True
        else:
            childOverride = not self.needsSpecificExport
        if itemPrefex == "":
            if self.needsSpecificExport and not specificExportOverride:
                processingName = ""   
                # processingName = self.name.lower() + "$"
            else:
                processingName = self.name.lower() + "$"
        else:
            processingName = itemPrefex + "$"
        if includeNonFields and not utils.USES_LAYER_2:
            event = self.getEvent(moduleName)        
            localVariableName = "info_{}".format(zeekStructureName.lower())
            convertingFunctionString += event.getEventFunctionName(allBitfields)
            convertingFunctionString += "{}hook set_session_{}(c);\n\n".format(utils.getTabString(tabSize), zeekStructureName.lower())
            convertingFunctionString += "{}local {} = c${}_{};\n\n".format(utils.getTabString(tabSize), localVariableName, utils.PROTOCOL_NAME.lower(), zeekStructureName.lower())
        elif includeNonFields and utils.USES_LAYER_2:
            event = self.getEvent(moduleName)
            convertingFunctionString += event.getEventFunctionName(allBitfields)     
            localVariableName = "info_{}".format(zeekStructureName.lower())
            convertingFunctionString += "{}local {} = {}(\n".format(utils.getTabString(tabSize), localVariableName, zeekStructureName)
            convertingFunctionString += "{}$ts=network_time(),\n".format(utils.getTabString(tabSize +1))
            convertingFunctionString += "{}$proto=\"{}\"\n{});\n".format(utils.getTabString(tabSize + 1), utils.PROTOCOL_NAME.lower(), utils.getTabString(tabSize))
        if self.linkIds != []:
            for linkId in self.linkIds:
                convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, utils.commandNameToConst(linkId.name).lower(), processingName, linkId.name)
        for field in self.fields:
            tabSize = startingTabSize
            if len(field.conditional) > 0:
                if self.needsSpecificExport and not specificExportOverride:
                    pass
                else:
                    convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], field.name)
                    tabSize = startingTabSize + 1
            if field.type == "bits":
                referenceType = field.referenceType
                referencedBitfield = None
                for scope in scopes: 
                    if referenceType in allBitfields[utils.normalizedScope(scope, "bitfield")]:
                        referencedBitfield = allBitfields[utils.normalizedScope(scope, "bitfield")][referenceType]
                        break
                if referencedBitfield != None:
                    for bitfieldItem in referencedBitfield.fields:
                            if bitfieldItem.type == "enum":
                                for scope in scopes: 
                                    if bitfieldItem.referenceType in allEnums[utils.normalizedScope(scope, "enum")]:
                                        enumScope = utils.normalizedScope(scope, "enum")
                                        break
                                if self.needsSpecificExport and not specificExportOverride:
                                    convertingFunctionString += "{}{}${}_{} = {}::{}[{}];\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, utils.commandNameToConst(bitfieldItem.name).lower(), enumScope, utils.commandNameToConst(bitfieldItem.referenceType).upper(), bitfieldItem.name)

                                else:
                                    convertingFunctionString += "{}{}${}_{} = {}::{}[{}{}${}];\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, utils.commandNameToConst(bitfieldItem.name).lower(), enumScope, utils.commandNameToConst(bitfieldItem.referenceType).upper(), processingName, field.name, bitfieldItem.name)
                            else:
                                if self.needsSpecificExport and not specificExportOverride:
                                    convertingFunctionString += "{}{}${}_{} = {};\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, utils.commandNameToConst(bitfieldItem.name).lower(), bitfieldItem.name)

                                else:                                        
                                    convertingFunctionString += "{}{}${}_{} = {}{}${};\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, utils.commandNameToConst(bitfieldItem.name).lower(), processingName, field.name, bitfieldItem.name)
            elif field.type == "enum":
                for scope in scopes: 
                    if field.referenceType in allEnums[utils.normalizedScope(scope, "enum")]:
                        enumScope = utils.normalizedScope(scope, "enum")
                        break
                if self.needsSpecificExport and not specificExportOverride:
                    convertingFunctionString += "{}{}${} = {}::{}[{}{}];\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, enumScope, utils.commandNameToConst(field.referenceType).upper(), processingName, field.name)
                else:
                    convertingFunctionString += "{}{}${} = {}::{}[{}{}];\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, enumScope, utils.commandNameToConst(field.referenceType).upper(), processingName, field.name)

            elif field.type == "object":
                referencedObject = None
                for scope in scopes:
                    if field.referenceType in allObjects[utils.normalizedScope(scope, "object")]:
                            referencedObject = allObjects[utils.normalizedScope(scope, "object")][field.referenceType]
                            break
                if referencedObject != None:
                    objectZeekStructureName = processingName + field.name
                    convertingFunctionString += referencedObject.makeEventBackend(moduleName, objectZeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, False, localVariableName, objectZeekStructureName, startingTabSize, childOverride)   

            elif field.type == "switch":
                for switchScope in scopes: 
                        if field.referenceType in allSwitches[utils.normalizedScope(switchScope, "")]:
                            switch = allSwitches[utils.normalizedScope(switchScope, "")][field.referenceType]
                            break
                switchType = ""            
                if switch != None:
                    switchType = json_processing.getSwitchType(field.referenceType, field, switchScope, scopes, allObjects, allSwitches)
                if switchType == "contained":
                    for item in switch.options:
                        if item.action.type == "object":
                            objectName = item.action.referenceType
                            for scope in scopes:
                                if objectName in allObjects[utils.normalizedScope(scope, "")]:
                                    object = allObjects[utils.normalizedScope(scope, "")][objectName]
                                    if object.needsSpecificExport:
                                        convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize),item.action.name)
                                    else:
                                        convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], item.action.name)
                                    objectZeekStructureName = processingName +  item.action.name
                                    convertingFunctionString += object.makeEventBackend(moduleName, objectZeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, False, localVariableName, objectZeekStructureName, startingTabSize + 1, childOverride)
                                    convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
                        else:
                            if object.needsSpecificExport:
                                convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize),item.action.name)
                            else:
                                convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], item.action.name)
                            convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize + 1), localVariableName, field.zeekName, processingName, item.action.name)
                            convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
                    if switch.default != None:
                        if switch.default.type == "object":
                            objectName = switch.default.referenceType
                            for scope in scopes: 
                                if objectName in allObjects[utils.normalizedScope(scope, "")]:
                                    object = allObjects[utils.normalizedScope(scope, "")][objectName]
                                    if object.needsSpecificExport:
                                        convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize),switch.default.name)
                                    else:
                                        convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], switch.default.name)
                                    objectZeekStructureName = processingName + switch.default.name
                                    convertingFunctionString += object.makeEventBackend(moduleName, objectZeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, False, localVariableName, objectZeekStructureName, startingTabSize + 1, childOverride)
                                    convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
                        else:
                            if object.needsSpecificExport:
                                convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize),item.action.name)
                            else:
                                convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], item.action.name)
                            convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize + 1), localVariableName, field.zeekName, processingName, item.action.name)
                            convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
            elif field.type == "list":
                pass
            else: 
                convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, field.zeekName, processingName, field.name)
            if len(field.conditional) > 0 and (not self.needsSpecificExport or specificExportOverride):
                convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize - 1))
        if includeNonFields and not utils.USES_LAYER_2:
            convertingFunctionString += "{}{}::emit_{}_{}(c);\n".format(utils.getTabString(tabSize), utils.PROTOCOL_NAME, utils.PROTOCOL_NAME.lower(), zeekStructureName.lower())
            convertingFunctionString += "}\n"
        elif includeNonFields and utils.USES_LAYER_2:
            convertingFunctionString += "{}{}::emit_{}_{}({});\n".format(utils.getTabString(tabSize), utils.PROTOCOL_NAME, utils.PROTOCOL_NAME.lower(), zeekStructureName.lower(), localVariableName)
            convertingFunctionString += "}\n" 
        return convertingFunctionString
