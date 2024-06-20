# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

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
        
    def addInput(self, input):
        for existingInput in self.inputs:
            if existingInput.equal(input):
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
    def __init__(self, name, reference, notes, logIndependently, referenceCount, scope, logWithParent=False):
        self.name = name
        self.reference = reference
        self.zeekStructure = []
        self.notes = notes
        self.scope = scope
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
                    initFunctionString += "{}self.{} = {}_{}::generateId();\n".format(utils.DOUBLE_TAB, link.name, utils.PROTOCOL_NAME.upper(), utils.ID_SCOPE.upper())
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
        
    def _determineChildOverride(self, specificExportOverride):
        if specificExportOverride:
            childOverride = True
        else:
            childOverride = not self.needsSpecificExport
        return childOverride
        
    def _determineProcessingName(self, itemPrefix, specificExportOverride):
        if itemPrefix == "":
            if self.needsSpecificExport and not specificExportOverride:
                processingName = ""
            else:
                processingName = self.name.lower() + "$"
        else:
            processingName = itemPrefix + "$"
        return processingName
        
    def _adjustForNonFields(self, moduleName, zeekStructureName, allBitfields, tabSize):
        event = self.getEvent(moduleName)
        localVariableName = "info_{}".format(zeekStructureName.lower())
        convertingFunctionString = event.getEventFunctionName(allBitfields)
        if not utils.USES_LAYER_2:
            convertingFunctionString += "{}hook set_session_{}(c);\n\n".format(utils.getTabString(tabSize), zeekStructureName.lower())
            convertingFunctionString += "{}local {} = c${}_{};\n\n".format(utils.getTabString(tabSize), localVariableName, utils.PROTOCOL_NAME.lower(), zeekStructureName.lower())
        else: # utils.USES_LAYER_2:
            convertingFunctionString += "{}local {} = {}(\n".format(utils.getTabString(tabSize), localVariableName, zeekStructureName)
            convertingFunctionString += "{}$ts=network_time(),\n".format(utils.getTabString(tabSize + 1))
            convertingFunctionString += "{}$proto=\"{}\"\n{});\n".format(utils.getTabString(tabSize + 1), utils.PROTOCOL_NAME.lower(), utils.getTabString(tabSize))
        return (localVariableName, convertingFunctionString)
        
    def _finishForNonFields(self, localVariableName, tabSize, zeekStructureName):
        argument = "c"
        if utils.USES_LAYER_2:
            argument = localVariableName
        convertingFunctionString = "{}{}::emit_{}_{}({});\n".format(utils.getTabString(tabSize), utils.PROTOCOL_NAME.upper(), utils.PROTOCOL_NAME.lower(), zeekStructureName.lower(), argument)
        convertingFunctionString += "}\n"
        return convertingFunctionString
        
    def _getLinkIDConvertingFunctions(self, tabSize, localVariableName, processingName):
        convertingFunctionString = ""
        for linkId in self.linkIds:
            convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, utils.commandNameToConst(linkId.name).lower(), processingName, linkId.name)
        return convertingFunctionString
        
    def _updateOnConditionals(self, startingTabSize, field, specificExportOverride, processingName):
        tabSize = startingTabSize
        convertingFunctionString = ""
        if len(field.conditional) > 0:
            if self.needsSpecificExport and not specificExportOverride:
                pass
            else:
                convertingFunctionString += "{}if ({}?${}){{\n".format(utils.getTabString(tabSize), processingName[:-1], field.name)
                tabSize = startingTabSize + 1
        return (tabSize, convertingFunctionString)
        
    def _finishOnConditionals(self, field, specificExportOverride, tabSize):
        if len(field.conditional) > 0 and (not self.needsSpecificExport or specificExportOverride):
            return "{}}}\n".format(utils.getTabString(tabSize - 1))
        return ""
        
    def _makeEventBackendForBits(self, field, scopes, allBitfields, allEnums, specificExportOverride, localVariableName, processingName, tabSize):
        referenceType = field.referenceType
        fieldPrefix = utils.commandNameToConst(self.name).lower() + "_" +  utils.commandNameToConst(field.name).lower()
        referencedBitfield = None
        for scope in scopes:
            if referenceType in allBitfields[utils.normalizedScope(scope, "bitfield")]:
                referencedBitfield = allBitfields[utils.normalizedScope(scope, "bitfield")][referenceType]
                break
        convertingFunctionString = ""
        if referencedBitfield != None:
            for bitfieldItem in referencedBitfield.fields:
                argument = bitfieldItem.name
                if not self.needsSpecificExport or specificExportOverride:
                    argument = "{}{}${}".format(processingName, field.name, argument)
                convertingFunctionString += "{}{}${}_{} = ".format(utils.getTabString(tabSize), localVariableName, fieldPrefix, utils.commandNameToConst(bitfieldItem.name).lower())
                if bitfieldItem.type == "enum":
                    for scope in scopes: 
                        if bitfieldItem.referenceType in allEnums[utils.normalizedScope(scope, "enum")]:
                            enumScope = utils.normalizedScope(scope, "enum")
                            break
                    convertingFunctionString += "{}::{}[{}]".format(enumScope, utils.commandNameToConst(bitfieldItem.referenceType).upper(), argument)
                else:
                    convertingFunctionString += argument
                convertingFunctionString += ";\n"
        return convertingFunctionString
        
    def _makeEventBackendForEnum(self, field, scopes, allEnums, localVariableName, processingName, tabSize):
        zeekName = utils.commandNameToConst(self.name).lower() + "_" + utils.commandNameToConst(field.name).lower()
        for scope in scopes: 
            if field.referenceType in allEnums[utils.normalizedScope(scope, "enum")]:
                enumScope = utils.normalizedScope(scope, "enum")
                break
        return "{}{}${} = {}::{}[{}{}];\n".format(utils.getTabString(tabSize), localVariableName, zeekName, enumScope, utils.commandNameToConst(field.referenceType).upper(), processingName, field.name)
        
    def _makeEventBackendForList(self, field, processingName, tabSize, localVariableName, includeConditional = False):
        convertingFunctionString = ""
        zeekName = utils.commandNameToConst(self.name).lower() + "_" + utils.commandNameToConst(field.name).lower() 
        if field.elementType in utils.spicyToZeek:
            actionName = field.name
            if includeConditional:
                if not self.needsSpecificExport or self.logWithParent:
                    argument = "{}?${}".format(processingName[:-1], actionName)
                else:
                    argument = actionName
                convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize), argument)
                convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize + 1), localVariableName, zeekName, processingName, field.name)
                convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
            else:
               convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, zeekName, processingName, field.name)
            return convertingFunctionString
        if field.elementType == "object":
            return ""
        else:
            print("Invalid List element of type {}".format(field.elementType))
    def _makeEventBackendForObject(self, field, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride):
        referencedObject = None
        for scope in scopes:
            if field.referenceType in allObjects[utils.normalizedScope(scope, "object")]:
                referencedObject = allObjects[utils.normalizedScope(scope, "object")][field.referenceType]
                break
        if referencedObject != None:
            objectZeekStructureName = processingName + field.name
            return referencedObject.makeEventBackend(moduleName, objectZeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, False, localVariableName, objectZeekStructureName, startingTabSize, childOverride)
        return ""
        
    def _makeEventBackendForSwitchAction(self, action, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize):
        convertingFunctionString = ""
        if action.type == "object":
            objectName = action.referenceType
            for scope in scopes: 
                if objectName in allObjects[utils.normalizedScope(scope, "")]:
                    object = allObjects[utils.normalizedScope(scope, "")][objectName]
                    argument = action.name
                    if not self.needsSpecificExport or childOverride:
                        argument = "{}?${}".format(processingName[:-1], argument)
                    convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize), argument)
                    objectZeekStructureName = processingName + action.name
                    convertingFunctionString += object.makeEventBackend(moduleName, objectZeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, False, localVariableName, objectZeekStructureName, startingTabSize + 1, childOverride)
                    convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
        elif action.type in utils.spicyToZeek:
            argument = action.name
            zeekName = utils.commandNameToConst(self.name).lower() + "_" + utils.commandNameToConst(action.name).lower()
            if not self.needsSpecificExport or childOverride:
                argument = "{}?${}".format(processingName[:-1], argument)
                convertingFunctionString += "{}if ({}){{\n".format(utils.getTabString(tabSize), argument)
                tabSize += 1
            convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, zeekName, processingName, action.name)
            if not self.needsSpecificExport or childOverride:
                tabSize -= 1
                convertingFunctionString += "{}}}\n".format(utils.getTabString(tabSize))
        elif action.type == "list":
            includeConditional = True
            if self.needsSpecificExport and not childOverride:
                includeConditional = False
            convertingFunctionString += self._makeEventBackendForList(action, processingName, tabSize, localVariableName, includeConditional)
        elif action.type == "void":
            pass
        else:
            print("Invalid switch option type: {} in {}".format(action.type, object.name))
        return convertingFunctionString
        
    def _makeEventBackendForSwitchOptions(self, switch, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize):
        convertingFunctionString = ""
        for item in switch.options:
            convertingFunctionString += self._makeEventBackendForSwitchAction(item.action, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize)
        return convertingFunctionString
        
    def _makeEventBackendForSwitchDefault(self, switch, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize):
        return self._makeEventBackendForSwitchAction(switch.default, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize)
        
    def _makeEventBackendForSwitch(self, field, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize):
        convertingFunctionString = ""
        for switchScope in scopes: 
            if field.referenceType in allSwitches[utils.normalizedScope(switchScope, "")]:
                switch = allSwitches[utils.normalizedScope(switchScope, "")][field.referenceType]
                break
        switchType = ""            
        if switch != None:
            switchType = json_processing.getSwitchType(field.referenceType, field, self.scope, scopes, allObjects, allSwitches)
        if switchType == "contained":
            convertingFunctionString = self._makeEventBackendForSwitchOptions(switch, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize)
        
        if switch.default != None:
            convertingFunctionString += self._makeEventBackendForSwitchDefault(switch, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, startingTabSize, childOverride, tabSize)
        return convertingFunctionString
                
    def makeEventBackend(self, moduleName, zeekStructureName, allEnums, allBitfields, allObjects, allSwitches, scopes, includeNonFields = True, logObjectVariableName = "", itemPrefix = "", startingTabSize = 1, specificExportOverride=False):
        if "TrimPoints" in self.name:
            pass
        convertingFunctionString = ""
        localVariableName = logObjectVariableName
        tabSize = startingTabSize
        childOverride = self._determineChildOverride(specificExportOverride)
        processingName = self._determineProcessingName(itemPrefix, specificExportOverride)
        if includeNonFields:
            localVariableName, convertingFunctionString = self._adjustForNonFields(moduleName, zeekStructureName, allBitfields, tabSize)
        if self.linkIds != []:
            convertingFunctionString += self._getLinkIDConvertingFunctions(tabSize, localVariableName, processingName)
        for field in self.fields:
            if field.type == "switch":
                convertingFunctionString += self._makeEventBackendForSwitch(field, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, tabSize, childOverride, tabSize)
                continue
            tabSize, temp = self._updateOnConditionals(startingTabSize, field, specificExportOverride, processingName)
            convertingFunctionString += temp
            if field.type == "bits":
                convertingFunctionString += self._makeEventBackendForBits(field, scopes, allBitfields, allEnums, specificExportOverride, localVariableName, processingName, tabSize)
            elif field.type == "enum":
                convertingFunctionString += self._makeEventBackendForEnum(field, scopes, allEnums, localVariableName, processingName, tabSize)
            elif field.type == "object":
                convertingFunctionString += self._makeEventBackendForObject(field, processingName, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes, localVariableName, tabSize, childOverride)
            elif field.type == "list":
                convertingFunctionString += self._makeEventBackendForList(field, processingName, tabSize, localVariableName, False)
            else: 
                zeekName = utils.commandNameToConst(self.name).lower() + "_" + utils.commandNameToConst(field.name).lower()
                convertingFunctionString += "{}{}${} = {}{};\n".format(utils.getTabString(tabSize), localVariableName, zeekName, processingName, field.name)
            convertingFunctionString += self._finishOnConditionals(field, specificExportOverride, tabSize)
        if includeNonFields:
            convertingFunctionString += self._finishForNonFields(localVariableName, startingTabSize, zeekStructureName)
        return convertingFunctionString
 
