import utils
import graphing
import json
import os
from string import Template

# Graph Theory Imports
import rustworkx as rx

def copyFile(source, destination):
    with open(source, "r") as inputFile, open(destination, "w") as currentFile:
        currentFile.write(inputFile.read())
    
def copyTemplateFile(source, data, destination):
    with open(source, "r") as inputFile, open(destination, "w") as currentFile:
        currentFile.write(Template(inputFile.read()).substitute(data))
        
def writeNodes(nodes, outFilePath):
    with open(outFilePath, "w") as outFile:
            for node in nodes:
                outFile.write(node + "\n")
                
def writeDataToFile(data, outFilePath):
    with open(outFilePath, "w") as outFile:
        outFile.write(data)
        
def createAndUseGraphInformation(configuration, objects, switches, bitfields, enums, entryPointScope, entryPointName, entryPointKey):
    ############################################################################
    # Load the structures as nodes
    ############################################################################
    graph, objectNodes, nodeInformation, nodeToIndex, indexToNode, connectionData = generateGraph(configuration, objects, switches, bitfields, enums)
    
    ############################################################################
    # Create actual graph
    ############################################################################
        
    # Determine paths for every node from the EntryPoint Node
    pathInformation = calculatePathInformation(graph, objectNodes, entryPointScope, entryPointKey, nodeInformation, nodeToIndex, indexToNode)
    
    # Look for cycles in the graph
    cycleIndices = rx.simple_cycles(graph)
    cycles = []
    for cycle in cycleIndices:
        mappedCycle = []
        for index in cycle:
            mappedCycle.append(indexToNode[index])
        cycles.append(mappedCycle)
    
    missingExpectedTopLevelNodes, expectedTopLevelNodes, unexpectedTopLevelNodes = determineTopLevelNodes(graph, [entryPointKey], indexToNode)
    
    ############################################################################
    # Use the graph information
    ############################################################################
    printGraphWarnings(cycles, missingExpectedTopLevelNodes, unexpectedTopLevelNodes)
    ############################################################################
    # This line outputs calculated graphing information to files.
    # This takes a while so should only be run for debugging.
    ############################################################################
    #saveGraphInformation(graph, pathInformation, cycles, missingExpectedTopLevelNodes, unexpectedTopLevelNodes)
    
    updateObjectsBasedOnGraphInformation(cycles, pathInformation, objects, entryPointScope, entryPointName)

def generateProtocolEvents(normalScope, entryPointScope, entryPointName, trasportProtos, ports=[], usesLayer2=False):
    eventString = ""
    for protocol in trasportProtos:
        eventString += "protocol analyzer spicy::{}_{} over {}:\n".format(utils.PROTOCOL_NAME.upper(), protocol, protocol)
        eventString += "{}parse with {}::{}".format(utils.SINGLE_TAB, normalScope, entryPointName + "s")
        if ports != []:
            tempPorts = []
            for port in ports:
                if port.get("protocol").lower() == protocol.lower():
                    tempPorts.append("{0}/{1}".format(port.get("port"), port.get("protocol").lower()))
            if tempPorts:
                eventString += ",\n{0}ports {{{1}}};\n".format(utils.SINGLE_TAB, ", ".join(tempPorts))
        else:
            eventString += ";\n"
        eventString += "\n"
    if usesLayer2:
        eventString += "packet analyzer spicy::{}:\n".format(utils.PROTOCOL_NAME.upper())
        eventString += "{}parse with {}::{};".format(utils.SINGLE_TAB, normalScope, entryPointName + "s")
        eventString += "\n\n"
    return eventString
    
def _addCrossScopeItem(currentScope, otherScope, itemType, itemReference, crossScopeList):
    if currentScope not in crossScopeList:
        crossScopeList[currentScope] = {}
    if otherScope not in crossScopeList[currentScope]:
        crossScopeList[currentScope][otherScope] = {}
    if itemType not in crossScopeList[currentScope][otherScope]:
        crossScopeList[currentScope][otherScope][itemType] = set()
    crossScopeList[currentScope][otherScope][itemType].add(itemReference)

def processDependency(item, currentScope, crossScopeList, customTypes, switches):
    if item.type in ["enum", "object"]:
        if item.scope != currentScope:
            # Crossing the scopes
            _addCrossScopeItem(currentScope, item.scope, item.type, item.referenceType, crossScopeList)
    elif item.type in ["list"] and item.elementType in ["enum", "object"]:
        if item.scope != currentScope:
            # Crossing the scopes
            _addCrossScopeItem(currentScope, item.scope, item.elementType, item.referenceType, crossScopeList)
    elif item.type in ["switch"] and \
         item.scope in switches and \
         item.referenceType in switches[item.scope]:
        for option in switches[item.scope][item.referenceType].options:
            processDependency(option.action, currentScope, crossScopeList, customTypes, switches)
    elif item.type in customTypes:
        normalConversionScope = utils.normalizedScope(utils.CONVERSION_SCOPE, "custom")
        _addCrossScopeItem(currentScope, normalConversionScope, "custom", item.type, crossScopeList)
        
def _addUserTypeNodes(configuration, nodeInformation):
    if bool(configuration.customFieldTypes):
        for name in configuration.customFieldTypes:
            item = configuration.customFieldTypes[name]
            metaData = {
                "interpretingFunction": item.interpretingFunction,
                "returnType": item.returnType
            }
            graphing.addUserTypeNode(name, nodeInformation, metaData, configuration.customFieldTypes.keys())
            
def _addObjectNodes(configuration, objects, nodeInformation, objectNodes, referenceInformation, fieldsInformation):
    for normalizedScope in objects:
        for objectName in objects[normalizedScope]:
            currentObject = objects[normalizedScope][objectName]
            itemName = graphing.addItemNode(normalizedScope, currentObject,
                                   "object", nodeInformation, None,
                                   configuration.customFieldTypes.keys())
            objectNodes.append(graphing.normalizedKey3(normalizedScope, "object", itemName))
            
            # Process the fields
            for field in currentObject.fields:
                graphing.addFieldNode(normalizedScope, "object", itemName,
                                      field, "field", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
                                      
def _addObjectDependencyNodes(configuration, objects, dependencyNodeInformation, dependencyReferenceInformation, dependencyInformation):
    for normalizedScope in objects:
        for objectName in objects[normalizedScope]:
            currentObject = objects[normalizedScope][objectName]
            itemName = graphing.getItemName(normalizedScope, currentObject, "object")
            
            # Look for references in the dependsOn section
            if len(currentObject.dependsOn) > 0:
                for dependency in currentObject.dependsOn:
                    graphing.addDependencyNode(normalizedScope, "object",
                                               itemName, dependency,
                                               dependencyNodeInformation,
                                               dependencyReferenceInformation,
                                               dependencyInformation,
                                               configuration.customFieldTypes.keys())
                                      
def _addSwitchNodes(configuration, switches, nodeInformation, referenceInformation, fieldsInformation):
    for normalizedScope in switches:
        for switchName in switches[normalizedScope]:
            currentSwitch = switches[normalizedScope][switchName]
            itemName = graphing.addItemNode(normalizedScope, currentSwitch,
                                            "switch", nodeInformation, None,
                                            configuration.customFieldTypes.keys())

            # Process the "fields"
            for option in currentSwitch.options:
                actionSection = option.action
                graphing.addFieldNode(normalizedScope, "switch", itemName,
                                      actionSection, "option", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
            if currentSwitch.default is not None:
                action = currentSwitch.default
                graphing.addFieldNode(normalizedScope, "switch", itemName,
                                      action, "option", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
                                      
def _addSwitchDependencyNodes(configuration, switches, dependencyNodeInformation, dependencyReferenceInformation, dependencyInformation):
    for normalizedScope in switches:
        for switchName in switches[normalizedScope]:
            currentSwitch = switches[normalizedScope][switchName]
            itemName = graphing.getItemName(normalizedScope, currentSwitch, "switch")
            # Process the main dependency
            dependsOnSection = currentSwitch.dependsOn
            graphing.addDependencyNode(normalizedScope, "switch", itemName,
                                       dependsOnSection,
                                       dependencyNodeInformation,
                                       dependencyReferenceInformation,
                                       dependencyInformation,
                                       configuration.customFieldTypes.keys())
            # Look for references in the additionalDependsOn section
            if len(currentSwitch.additionalDependsOn) > 0:
                for dependency in currentSwitch.additionalDependsOn:
                    graphing.addDependencyNode(normalizedScope, "switch",
                                               itemName, dependency,
                                               dependencyNodeInformation,
                                               dependencyReferenceInformation,
                                               dependencyInformation,
                                               configuration.customFieldTypes.keys())
                                      
def _addBitfieldNodes(configuration, bitfields, nodeInformation, referenceInformation, fieldsInformation):
    for normalizedScope in bitfields:
        for bitfieldName in bitfields[normalizedScope]:
            currentBitfield = bitfields[normalizedScope][bitfieldName]
            itemName = graphing.addItemNode(normalizedScope, currentBitfield,
                                            "bits", nodeInformation, None,
                                            configuration.customFieldTypes.keys())
            # No dependencies
            # Process the fields
            for field in currentBitfield.fields:
                graphing.addFieldNode(normalizedScope, "bits", itemName, field,
                                      "field", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
                                      
def _addEnumNodes(configuration, enums, nodeInformation, referenceInformation, fieldsInformation):
    for normalizedScope in enums:
        for enumName in enums[normalizedScope]:
            currentEnum = enums[normalizedScope][enumName]
            itemName = graphing.addItemNode(normalizedScope, currentEnum,
                                            "enum", nodeInformation, None,
                                            configuration.customFieldTypes.keys())
            # No dependencies
            # Process the fields
            for field in currentEnum.fields:
                graphing.addFieldNode(normalizedScope, "enum", itemName, field,
                                      "field", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
                                      
def _addNodes(configuration, objects, switches, bitfields, enums):    
    ################################################################################
    # Tracking Structures
    ################################################################################
    # Assumption, no duplicates

    # Nodes
    nodeInformation = {}
    objectNodes = []
    # Connections due to type references
    referenceInformation = []
    # Connections due to fields
    fieldsInformation = []
    
    _addUserTypeNodes(configuration, nodeInformation)
    
    _addObjectNodes(configuration, objects, nodeInformation, objectNodes, referenceInformation, fieldsInformation)
    
    _addSwitchNodes(configuration, switches, nodeInformation, referenceInformation, fieldsInformation)
    
    _addBitfieldNodes(configuration, bitfields, nodeInformation, referenceInformation, fieldsInformation)
    
    _addEnumNodes(configuration, enums, nodeInformation, referenceInformation, fieldsInformation)
    
    # Dependency Information
    # Not currently used, so removing for now
    #dependencyNodeInformation = {}
    #dependencyReferenceInformation = []
    # Connections due to other dependencies
    #dependencyInformation = []
    
    #_addObjectDependencyNodes(configuration, objects, dependencyNodeInformation, dependencyReferenceInformation, dependencyInformation)
    #_addSwitchDependencyNodes(configuration, switches, dependencyNodeInformation, dependencyReferenceInformation, dependencyInformation)
    
    return (objectNodes, nodeInformation, fieldsInformation, referenceInformation)
        
def generateGraph(configuration, objects, switches, bitfields, enums):
    ############################################################################
    # Load the structures as nodes
    ############################################################################
    objectNodes, nodeInformation, fieldsInformation, referenceInformation = \
        _addNodes(configuration, objects, switches, bitfields, enums)
                                      
    ############################################################################
    # Create actual graph
    ############################################################################
    graph = rx.PyDiGraph(multigraph=False)
    nodeToIndex = {}
    indexToNode = {}
    connectionData = {}

    for node in nodeInformation:
        if node not in nodeToIndex:
            nodeIndex = graph.add_node(node)
            nodeToIndex[node] = nodeIndex
            indexToNode[nodeIndex] = node

        
    for connection in fieldsInformation:
        connectionID = graph.add_edge(nodeToIndex[connection[0]], nodeToIndex[connection[1]], None)
        connectionData[connectionID] = connection[2]
        
    for connection in referenceInformation:
        connectionID = graph.add_edge(nodeToIndex[connection[0]], nodeToIndex[connection[1]], None)
        connectionData[connectionID] = connection[2]
        
    return (graph, objectNodes, nodeInformation, nodeToIndex, indexToNode, connectionData)
    
def _processPath(path, entryPointScope, targetScope, nodeInformation, indexToNode):
    tempPath = []
    for element in path:
        tempPath.append(indexToNode[element])
    loggingParent = None
    parentReason = ""
    previousScope = None
    pathInfo = {}
    for element in tempPath[::-1]:
        parts = element.split(".")
        if len(parts) < 3:
            continue
        scope = parts[0]
        referenceType = parts[2]
        if scope != targetScope:
            loggingParent = utils.loggingParentScope(previousScope)
            parentReason = "Scope Change"
            break
        metaData = nodeInformation[element][1]
        if metaData is not None:
            if "logIndependently" in metaData and True == metaData["logIndependently"]:
                loggingParent = referenceType
                parentReason = "Log Independently"
                break
        previousScope = scope
    pathInfo["path"] = tempPath
    if loggingParent is None:
        pathInfo["needsLoggingParent"] = False
        pathInfo["loggingParent"] = utils.loggingParentScope(entryPointScope)
    else:
        pathInfo["needsLoggingParent"] = True
        pathInfo["loggingParent"] = loggingParent
        pathInfo["reason"] = parentReason
        
    return pathInfo
    
def calculatePathInformation(graph, objectNodes, entryPointScope, entryPointKey, nodeInformation, nodeToIndex, indexToNode):
    # Determine paths for every node from the EntryPoint Node
    pathInformation = {}
    for node in objectNodes:
        if node == entryPointKey:
            continue
        paths = []
        targetParts = node.split(".")
        if len(targetParts) < 3:
            print("Bad Path Value '{0}'".format(node))
            continue
        targetScope = targetParts[0]
        targetType = targetParts[1]
        targetName = targetParts[2]
        for path in rx.all_simple_paths(graph, nodeToIndex[entryPointKey], nodeToIndex[node]):
            paths.append(_processPath(path, entryPointScope, targetScope, nodeInformation, indexToNode))
        pathInformation["{0}::{1}".format(targetScope, targetName)] = paths
    return pathInformation
    
def determineTopLevelNodes(graph, expectedTopLevelNodes, indexToNode):
    unexpectedNodes = []
    expectedNodes = []
    missingNodes = []
    for node in graph.node_indices():
        if graph.in_degree(node) == 0:
            if indexToNode[node] in expectedTopLevelNodes:
                expectedNodes.append(indexToNode[node])
            else:
                unexpectedNodes.append(indexToNode[node])
    for node in expectedTopLevelNodes:
        if node not in expectedNodes:
            missingNodes.append(node)
    return (missingNodes, expectedNodes, unexpectedNodes)
    
def printGraphWarnings(cycles, missingTopLevelNodes, unexpectedTopLevelNodes):
    if len(cycles) > 0:
         print()
         print("Warning: {} Cycles Found".format(len(cycles)))
         print()
         
         # Iterate over all cycles
         #for cycle in cycles:
         #    # Iterate over nodes within a cycle
         #    # First node is the node closest to the "Entry Point" node that we specify
         #    # Last node is the node that references the first node in the cycle
         #    # and creates the loop
         #    cycleStart = cycle[0]
         #    cycleEnd = cycle[-1]
         #    print("Cycle Start: {}, Cycle End: {}".format(cycleStart, cycleEnd))
         #    cycleString = ""
         #    for index, node in enumerate(cycle):
         #        cycleString = cycleString + node
         #        if index < len(cycle) - 1:
         #            cycleString += " -> "
         #    print(cycleString)
             
    if 0 != len(missingTopLevelNodes):
        print()
        print("Warning: {} Expected Top Level Nodes were Missing".format(len(missingTopLevelNodes)))
        print()
        
    if 0 != len(unexpectedTopLevelNodes):
        print()
        print("Warning: {} Unexpected Top Level Nodes Found".format(len(unexpectedTopLevelNodes)))
        print()
    
def saveGraphInformation(graph, pathInformation, cycles, missingExpectedTopLevelNodes, unexpectedTopLevelNodes):
    writeDataToFile(json.dumps(pathInformation, indent=4), "paths.json")
        
    if len(cycles) > 0:
        cycleString = ""
        for cycle in cycles:
            for index, node in enumerate(cycle):
                cycleString = cycleString + node
                if index < len(cycle) - 1:
                    cycleString += " -> "
            cycleString += "\n"
        writeDataToFile(cycleString, "cycles.txt"); 
    if 0 != len(missingExpectedTopLevelNodes):
        writeNodes(missingExpectedTopLevelNodes, "missing_expected_nodes.txt")
        
    if 0 != len(unexpectedTopLevelNodes):
        writeNodes(unexpectedTopLevelNodes, "unexpected_top_nodes.txt")

    # TODO: Update these to work with rustworkx
    #dotGraph = nx.nx_pydot.to_pydot(graph)
    #dotGraph.write_svg("output_no_dependencies.svg")
    
def updateObjectsBasedOnGraphInformation(cycles, pathInformation, objects, entryPointScope, entryPointName):
    # Deal with cycles    
    for cycle in cycles:
        takenCareOf = False
        for item in cycle:
            cycleParts = item.split(".")
            if "object" == cycleParts[1]:
                try:
                    objects[cycleParts[0]][cycleParts[2]].needsSpecificExport = True
                    takenCareOf = True
                    break
                except KeyError:
                    print("Unknown cycle object: {}".format(item))
        if not takenCareOf:
            print("Unable to process cycl")
            
    for normalizedScope in objects:
        for objectName in objects[normalizedScope]:
            if objectName == entryPointName:
                objects[normalizedScope][objectName].zeekStructure.append(entryPointScope)
                continue
            for path in pathInformation["{}::{}".format(normalizedScope,objectName)]:
                if "loggingParent" in path:
                    objects[normalizedScope][objectName].zeekStructure.append(path["loggingParent"])
                    
def determineInterScopeDependencies(configuration, bitfields, objects, switches):
    # Determine import requirements
    # currentScope -> dependentScope[] -> ["enum"/"object"/"custom"/"id"] -> referenceType[]
    crossScopeItems = {}
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        if normalScope in objects:
            print("Processing objects in scope: {0}".format(normalScope))
            for currentObjectName in objects[normalScope]:
                currentObject = objects[normalScope][currentObjectName]
                if currentObject.linkIds != []:
                    for link in currentObject.linkIds:
                        if not link.isEndLink:
                            normalIDScope = utils.normalizedScope(utils.ID_SCOPE, "")
                            if normalScope not in crossScopeItems:
                                crossScopeItems[normalScope] = {}
                            if normalIDScope not in crossScopeItems[normalScope]:
                                crossScopeItems[normalScope][normalIDScope] = {}
                            if "id" not in crossScopeItems[normalScope][normalIDScope]:
                                crossScopeItems[normalScope][normalIDScope]["id"] = set()
                for dependency in currentObject.dependsOn:
                    processDependency(dependency, normalScope, crossScopeItems, configuration.customFieldTypes, switches)
                for field in currentObject.fields:
                    processDependency(field, normalScope, crossScopeItems, configuration.customFieldTypes, switches)
                for link in currentObject.linkIds:
                    if not link.isEndLink:
                        normalConversionScope = utils.normalizedScope(utils.CONVERSION_SCOPE, "custom")
                        if normalScope not in crossScopeItems:
                                crossScopeItems[normalScope] = {}
                        if normalConversionScope not in crossScopeItems[normalScope]:
                            crossScopeItems[normalScope][normalConversionScope] = {}
                        if "custom" not in crossScopeItems[normalScope][normalConversionScope]:
                            crossScopeItems[normalScope][normalConversionScope]["custom"] = set()
                #if  currentObject.needsSpecificExport and currentObject.logWithParent:
                    #for path in pathInformation["{}::{}".format(utils.normalizedScope(scope, "object"),currentObject.name)]:
                        #print(path)
        if normalScope in switches:
            print("Processing switches in scope: {0}".format(normalScope))
            for currentSwitchName in switches[normalScope]:
                currentSwitch = switches[normalScope][currentSwitchName]
                for option in currentSwitch.options:
                    processDependency(option.action, normalScope, crossScopeItems, configuration.customFieldTypes, switches)
        if normalScope in bitfields:
            print("Processing bitfields in scope: {0}".format(normalScope))
            for currentBitfieldName in bitfields[normalScope]:
                currentBitfield = bitfields[normalScope][currentBitfieldName]
                for field in currentBitfield.fields:
                    processDependency(field, normalScope, crossScopeItems, configuration.customFieldTypes, switches)
    return crossScopeItems
    
def writeCMakeFiles(outRootFolder):
    # Create root CMakeLists.txt file    
    data = {"protocol": utils.PROTOCOL_NAME}
    copyTemplateFile(os.path.join("templates", "root_CMakeLists.txt.in"),
                     data,
                     os.path.join(outRootFolder, "CMakeLists.txt"))
        
    # Create cmake folder contents
    cmakeFolder = os.path.join(outRootFolder, "cmake")
    os.makedirs(cmakeFolder, exist_ok=True)

    copyFile(os.path.join("templates", "FindSpicyPlugin.cmake.in"),
             os.path.join(cmakeFolder, "FindSpicyPlugin.cmake"))
        
def writeTestFiles(outRootFolder):
    # Create test folder contents
    testingFolder = os.path.join(outRootFolder, "testing")
    os.makedirs(testingFolder, exist_ok=True)
    testsFolder = os.path.join(testingFolder, "tests")
    os.makedirs(testsFolder, exist_ok=True)
    scriptsFolder = os.path.join(testingFolder, "scripts")
    os.makedirs(scriptsFolder, exist_ok=True)
    filesFolder = os.path.join(testingFolder, "files")
    os.makedirs(filesFolder, exist_ok=True)

    copyFile(os.path.join("templates", "btest.cfg.in"),
             os.path.join(testingFolder, "btest.cfg"))
    
    data = {
        "protocolName": utils.PROTOCOL_NAME,
        "protocolNameUpper": utils.PROTOCOL_NAME.upper()
    }
    
    copyTemplateFile(os.path.join("templates", "availability.zeek.in"),
                     data,
                     os.path.join(testsFolder, "availability.zeek"))

    copyFile(os.path.join("templates", "diff-remove-timestamps.in"),
             os.path.join(scriptsFolder, "diff-remove-timestamps"))
    
    copyFile(os.path.join("templates", "get-zeek-env.in"),
             os.path.join(scriptsFolder, "get-zeek-env"))

    copyFile(os.path.join("templates", "random.seed.in"),
             os.path.join(filesFolder, "random.seed"))

def writePackagingFiles(configuration, outRootFolder):
    # Function to write out zkg.meta file
    if not utils.USES_LAYER_2:
        analyzerType = "protocol"
        if configuration.usesTCP and configuration.usesUDP:
            transportProtocolInformation = "\ntransport = IP"
        elif configuration.usesTCP:
            transportProtocolInformation = "\ntransport = TCP"
        elif configuration.usesUDP:
            transportProtocolInformation = "\ntransport = UDP"
    else:
        analyzerType = "packet"
        transportProtocolInformation = ""
    entryPointParts = configuration.entryPoint.split(".")
    if 2 != len(entryPointParts):
        entryPoint = ""
    else:
        entryPoint = entryPointParts[1]
    data = {
        "analyzerType": analyzerType,
        "transportProtocolInformation": transportProtocolInformation,
        "protocolName": utils.PROTOCOL_NAME,
        "protocolSummary": configuration.shortDescription.replace("\n", "\n    "),
        "protocolDescription": configuration.longDescription.replace("\n", "\n    "),
        "entryPoint": entryPoint,
        "protocolNameUpper": utils.PROTOCOL_NAME.upper()
    }
    copyTemplateFile(os.path.join("templates", "zkg.meta.in"),
                    data,
                    os.path.join(outRootFolder, "zkg.meta"))
    

    #data = {
    #    "protocolName": utils.PROTOCOL_NAME,
    #    "protocolNameLower": utils.PROTOCOL_NAME.lower(),
    #    "scope": utils.normalizedScope(entryPointScope, "object"),
    #    "entryPointName": entryPointName
    #}
    #
    #copyTemplateFile(os.path.join("templates", "standalone.spicy.in"),
    #                 data,
    #                 os.path.join(testsFolder, "standalone.spicy"))

    # TODO: Deal with trace tests?
    
def _writeCoreZeekFiles(configuration, scriptsFolder, zeekMainFileObject, allEnums):
    coreFiles = []
    coreFiles.append("__load__.zeek")
    sigsString = ""
    typesString = ""
    processingString = ""
    enumString = ""
    if configuration.signatureFile is not None:
        sigsString = "@load-sigs ./dpd.sig\n"
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")

        filePrefix = "@load ./" + normalScope.lower()

        typesString += filePrefix + "_types"
        processingString += filePrefix + "_processing"
        if utils.normalizedScope(scope, "enum") in allEnums:
            enumString += filePrefix + "_enum"
        if scope != configuration.scopes[-1]:
            typesString += "\n"
            processingString += "\n"

    data = { 
        "sigsString": sigsString,
        "enumString": enumString,
        "typesString": typesString,
        "processingString": processingString
    }
    copyTemplateFile(os.path.join("templates", "__load__.zeek.in"), data,
                     os.path.join(scriptsFolder, "__load__.zeek"))

    coreFiles.append("main.zeek")
    data = {
        "protocolName": utils.PROTOCOL_NAME.upper(),
        "mainContents": zeekMainFileObject.generateMainFile(utils.USES_LAYER_2, configuration.ethernetProtocolNumber),
        "loggingFunctions": zeekMainFileObject.addLoggingFunction()
    }
    copyTemplateFile(os.path.join("templates", "main.zeek.in"), data,
                     os.path.join(scriptsFolder, "main.zeek"))
        
    if configuration.signatureFile is not None:
        writeDataToFile(configuration.signatureFile,
                        os.path.join(scriptsFolder, "dpd.sig"))
    return coreFiles
    
def _writeZeekTypeFiles(scriptsFolder, normalScope, zeekObjects):
    contentString = ""
    for zeekLog in zeekObjects.values():
        # Is this creating the side effects?
        contentString += zeekLog.createRecord()
    data = {
        "scope": normalScope,
        "contents": contentString
    }
    zeekTypesFileName = normalScope.lower() + "_types.zeek"
    copyTemplateFile(os.path.join("templates", "zeek_types.zeek.in"), data,
                     os.path.join(scriptsFolder, zeekTypesFileName))
    return [zeekTypesFileName]
    
def _writeZeekProcessingFiles(scriptsFolder, normalScope, zeekObjects, enums, bitfields, objects, switches, configuration):
    eventString = ""
    functionString = ""
    for zeekLog in zeekObjects.values():
        eventString += zeekLog.addHook()
        functionString += "{0}\n".format(zeekLog.addFunctions(normalScope, enums, bitfields, objects, switches, configuration.scopes))
    data = {
        "scope": normalScope,
        "eventString": eventString,
        "functionString": functionString
    }
    zeekProcessingFileName = normalScope.lower() + "_processing.zeek"
    copyTemplateFile(os.path.join("templates", "zeek_processing.zeek.in"), data,
                     os.path.join(scriptsFolder, zeekProcessingFileName))
    return [zeekProcessingFileName]
    
def _writeZeekEnumFiles(scriptsFolder, scope, normalScope, enums):
    enumScope = utils.normalizedScope(scope, "enum")
    if enumScope in enums:
        contents = ""
        for currentEnumName in enums[enumScope]:
            contents += enums[enumScope][currentEnumName].createZeekEnumString(enumScope)
        data = {
            "scope": enumScope,
            "contents": contents
        }
        zeekEnumFile = normalScope.lower() + "_enum.zeek"
        copyTemplateFile(os.path.join("templates", "zeek_enum.zeek.in"),
                         data,
                         os.path.join(scriptsFolder, zeekEnumFile))
        return [zeekEnumFile]
    else:
        return []

# This is creating side effects somewhere...    
def writeZeekFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, bitfields, enums, objects, switches):
    # Create basic zeek files 
    scriptsFolder = os.path.join(outRootFolder, "scripts")
    os.makedirs(scriptsFolder, exist_ok=True)
    
    scriptFiles = _writeCoreZeekFiles(configuration, scriptsFolder, zeekMainFileObject, enums)
    
    # Create all the other files
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        zeekObjects = zeekTypes[normalScope]

        scriptFiles += _writeZeekTypeFiles(scriptsFolder, normalScope, zeekObjects)

        scriptFiles += _writeZeekProcessingFiles(scriptsFolder, normalScope, zeekObjects, enums, bitfields, objects, switches, configuration)
        
        scriptFiles += _writeZeekEnumFiles(scriptsFolder, scope, normalScope, enums)
            
    return scriptFiles
    
def generateBaseConversionFunctions(configuration):
    returnString = ""
    if bool(configuration.customFieldTypes):
        for itemName in configuration.customFieldTypes:
            item = configuration.customFieldTypes[itemName]
            returnType = item.returnType  
            emptyReturn = 0
            if "string" == returnType:
                returnType = "std::" + returnType
                emptyReturn = "\"\""
            elif "bytes" == returnType:
                returnType = "hilti::rt::Bytes"
                emptyReturn = "hilti::rt::Bytes()"
            returnString += "{0}{1} {2}(const hilti::rt::Bytes &data)".format(utils.SINGLE_TAB, returnType, item.interpretingFunction)
            returnString += "{0}{{\n{1}return {2};\n{0}}}\n".format(utils.SINGLE_TAB, utils.DOUBLE_TAB, emptyReturn)
    return returnString
    
def generateBaseSpicyConversionFunctions(configuration, scope):
    returnString = ""
    if bool(configuration.customFieldTypes):
        for itemName in configuration.customFieldTypes:
            item = configuration.customFieldTypes[itemName]
            returnString += "public function {0}(input: bytes) : {1} &cxxname=\"{2}::{0}\";\n\n".format(item.interpretingFunction, item.returnType, scope)
    return returnString
    
def _writeSpicyConfirmationFiles(analyzerFolder, entryPointName):
    zeekConfirmationFile = "zeek_{}.spicy".format(utils.PROTOCOL_NAME.lower())
    data = {
        "entryPoint": entryPointName + "s",
        "protocolName": utils.PROTOCOL_NAME,
        "scope": utils.normalizedScope(utils.DEFAULT_SCOPE, ""),
        "tab": utils.SINGLE_TAB
    }
    
    copyTemplateFile(os.path.join("templates", "zeekConfirmationFile.spicy.in"),
                     data,
                     os.path.join(analyzerFolder, zeekConfirmationFile))
                     
    return [zeekConfirmationFile]
    
def _writeConversionFiles(analyzerFolder, configuration):
    normalScope = utils.normalizedScope(utils.CONVERSION_SCOPE, "")
    spicyConversionFile = normalScope.lower() + ".spicy"
    ccConversionFile = normalScope.lower() + ".cc"
    
    data = {
        "scope": normalScope,
        "functions": generateBaseSpicyConversionFunctions(configuration, normalScope)
    }
    copyTemplateFile(os.path.join("templates", "conversion.spicy.in"), data,
                     os.path.join(analyzerFolder, spicyConversionFile))
    
    if configuration.conversionFile is not None:
        writeDataToFile(configuration.conversionFile,
                        os.path.join(analyzerFolder, ccConversionFile))
    else:
        data = {
            "scope": normalScope,
            "functions": generateBaseConversionFunctions(configuration)
        }
        copyTemplateFile(os.path.join("templates", "conversion.cc.in"), data,
                         os.path.join(analyzerFolder, ccConversionFile))
    return [spicyConversionFile, ccConversionFile]

def _writeGenerateIDFiles(analyzerFolder):
    normalScope = utils.normalizedScope(utils.ID_SCOPE, "")
    spicyFile = normalScope.lower() + ".spicy"
    ccFile = normalScope.lower() + ".cc"

    data = {
        "scope": normalScope
    }

    copyTemplateFile(os.path.join("templates", "generateid.spicy.in"), data,
                     os.path.join(analyzerFolder, spicyFile))

    copyTemplateFile(os.path.join("templates", "generateid.cc.in"), data,
                     os.path.join(analyzerFolder, ccFile))

    return [spicyFile, ccFile]
    
def determineTransportProtocols(configuration):
    returnValue = []

    if configuration.usesTCP:
        returnValue.append("TCP")

    if configuration.usesUDP:
        returnValue.append("UDP")
        
    return returnValue
    
def _determineScopeImportLines(normalScope, crossScopeItems):
    additionalScopes = ""
    if normalScope in crossScopeItems:
        for usedScope in crossScopeItems[normalScope]:
            if usedScope != "":
                additionalScopes += "import {0};\n".format(usedScope)
    return additionalScopes
    
def _writeSpicyScopeFiles(analyzerFolder, configuration, scope, normalScope, additionalScopeImports, entryPointScope, entryPointName, objects, bitfields, switches, enums):
    entryPointClass = ""
    if scope == entryPointScope:
        entryPointClass = "public type {0}s = unit {{\n{1} : {0}[];\n}};\n\n".format(entryPointName, utils.SINGLE_TAB)
    
    objectsString = ""
    if normalScope in objects:
        for currentObjectName in objects[normalScope]:
            # TODO: Other cases where things need to be public?
            shouldBePublic = currentObjectName == entryPointName
            objectsString += "{0}\n".format(objects[normalScope][currentObjectName].createSpicyString(configuration.customFieldTypes, bitfields, switches, enums, shouldBePublic))
    
    data = {
        "scope": normalScope,
        "additionalScopes": additionalScopeImports,
        "entryPoint": entryPointClass,
        "objectsString": objectsString
    }
    outputFileName = normalScope.lower() + ".spicy"
    copyTemplateFile(os.path.join("templates", "scope.spicy.in"),
                     data,
                     os.path.join(analyzerFolder, outputFileName))
                     
    return [outputFileName]
    
def _determineProtocolEventsString(normalScope, entryPointScope, entryPointName, transportProtocols, configuration):
    if normalScope == utils.normalizedScope(utils.DEFAULT_SCOPE, ""):
        return generateProtocolEvents(normalScope, entryPointScope, entryPointName, transportProtocols, configuration.ports, utils.USES_LAYER_2)
    else:
        return ""
        
def _determineEntryPointEventString(scope, normalScope, entryPointScope, entryPointName):
    if scope == entryPointScope:
        return "export {}::{}s;\n".format(normalScope, entryPointName)
    else:
        return ""
        
def _determineExportString(scopedObjects, normalScope):
    exportString = ""
    for object in scopedObjects:
        if not scopedObjects[object].logWithParent or scopedObjects[object].logIndependently:
            exportString += "export {}::{}".format(normalScope, object)
            if scopedObjects[object].needsSpecificExport:
                exportString += " "
                if len(scopedObjects[object].excludedFields) < len(scopedObjects[object].includedFields):
                    exportString += "without { "
                    for field in scopedObjects[object].excludedFields:
                        exportString += field
                        if field != scopedObjects[object].excludedFields[-1]:
                            exportString += ", "
                else:
                    exportString += "with { "
                    for field in scopedObjects[object].includedFields:
                        exportString += field.name
                        if field != scopedObjects[object].includedFields[-1]:
                            exportString += ", "
                exportString += " }"
            exportString += ";\n"
    exportString += "\n"
    
    return exportString
    
def _determineObjectEventsString(scopedObjects, normalScope, bitfields):
    objectEvents = ""
    for object in scopedObjects.values():
        event = object.getEvent(normalScope)
        if event != []:
            objectEvents += event.generateEvent(bitfields)
    return objectEvents
    
def _writeSpicyEventFiles(analyzerFolder, configuration, scope, normalScope, entryPointScope, entryPointName, additionalScopeImports, transportProtocols, objects, bitfields):
    protocolEvents = _determineProtocolEventsString(normalScope, entryPointScope, entryPointName, transportProtocols, configuration)
    
    entryPointEvent = _determineEntryPointEventString(scope, normalScope, entryPointScope, entryPointName)
    
    scopedObjects = objects[normalScope]
    
    exportString = _determineExportString(scopedObjects, normalScope)
    
    objectEvents = _determineObjectEventsString(scopedObjects, normalScope, bitfields)

    data = {
        "scope": normalScope,
        "additionalScopes": additionalScopeImports,
        "protocolName": utils.PROTOCOL_NAME,
        "protocolEvents": protocolEvents,
        "entryPointEvent": entryPointEvent,
        "exportString": exportString,
        "objectEvents": objectEvents
    }
    evtFileName = normalScope.lower() + ".evt"
    copyTemplateFile(os.path.join("templates", "events.evt.in"), data,
                     os.path.join(analyzerFolder, evtFileName))
    return [evtFileName]
    
def _writeSpicyEnumFiles(analyzerFolder, scope, enums):
    enumScope = utils.normalizedScope(scope, "enum")
    if enumScope in enums:
        enumOutputFileName = enumScope.lower() + ".spicy"
        contentString = ""
        for currentEnumName in enums[enumScope]:
            contentString += "{0}\n".format(enums[enumScope][currentEnumName].createSpicyEnumString())
        data = {
            "scope": enumScope,
            "contents": contentString
        }
        copyTemplateFile(os.path.join("templates", "enum.spicy.in"), data,
                         os.path.join(analyzerFolder, enumOutputFileName))
        return [enumOutputFileName]
    else:
        return []
    
def writeSpicyFiles(configuration, outRootFolder, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName):
    # Create basic spicy files
    analyzerFolder = os.path.join(outRootFolder, "analyzer")
    os.makedirs(analyzerFolder, exist_ok=True)
    
    sourceFiles = _writeSpicyConfirmationFiles(analyzerFolder, entryPointName)
    
    sourceFiles += _writeConversionFiles(analyzerFolder, configuration)

    sourceFiles += _writeGenerateIDFiles(analyzerFolder)
            
    transportProtocols = determineTransportProtocols(configuration)
            
    # Create all the other files
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        additionalScopeImports = _determineScopeImportLines(normalScope, crossScopeItems)
        
        # Figure out the scope file
        sourceFiles += _writeSpicyScopeFiles(analyzerFolder, configuration, scope, normalScope, additionalScopeImports, entryPointScope, entryPointName, objects, bitfields, switches, enums)
        
        # Figure out the event file
        sourceFiles += _writeSpicyEventFiles(analyzerFolder, configuration, scope, normalScope, entryPointScope, entryPointName, additionalScopeImports, transportProtocols, objects, bitfields)

        sourceFiles += _writeSpicyEnumFiles(analyzerFolder, scope, enums)
                
    return (analyzerFolder, sourceFiles)
        
def writeLastCMakeFile(analyzerFolder, scriptFiles, sourceFiles):
    # Create CMakeLists.txt file with all the sources and scripts
    
    data = {
        "protocolName": utils.PROTOCOL_NAME,
        "sources": " ".join(sourceFiles),
        "scripts": " ".join(scriptFiles)
    }
    
    copyTemplateFile(os.path.join("templates", "analyzer_CMakeLists.txt.in"),
                     data,
                     os.path.join(analyzerFolder, "CMakeLists.txt"))
    
def writeParserFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName):
    # Create base folder
    os.makedirs(outRootFolder, exist_ok=True)
    # Fill in the rest of the structure
    writeCMakeFiles(outRootFolder)
    writePackagingFiles(configuration, outRootFolder)
    writeTestFiles(outRootFolder)
    # Must be called in this order...there are side effects of calling this one
    # that are required for the other one to work correctly
    folder, sourceFiles = writeSpicyFiles(configuration, outRootFolder, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName)
    # TODO: Figure out what is creating the side effects in the previous call
    scriptFiles = writeZeekFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, bitfields, enums, objects, switches)
    writeLastCMakeFile(folder, scriptFiles, sourceFiles)
