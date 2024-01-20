import utils
import graphing
import json
import os

# Graph Theory Imports
import networkx as nx

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
        
def generateGraph(configuration, objects, switches, bitfields, enums):
    ################################################################################
    # Tracking Structures
    ################################################################################
    # Assumption, no duplicates

    # Nodes
    nodeInformation = {}
    objectNodes = []
    dependencyNodeInformation = {}
    # Connections due to type references
    referenceInformation = []
    depedencyReferenceInformation = []
    # Connections due to fields
    fieldsInformation = []
    # Connections due to other dependencies
    dependencyInformation = []
    
    ############################################################################
    # Load the structures as nodes
    ############################################################################
    if bool(configuration.customFieldTypes):
        for name in configuration.customFieldTypes:
            item = configuration.customFieldTypes[name]
            metaData = {
                "interpretingFunction": item.interpretingFunction,
                "returnType": item.returnType
            }
            graphing.addUserTypeNode(name, nodeInformation, metaData, configuration.customFieldTypes.keys())
    
    for normalizedScope in objects:
        for objectName in objects[normalizedScope]:
            currentObject = objects[normalizedScope][objectName]
            itemName = graphing.addItemNode(normalizedScope, currentObject,
                                   "object", nodeInformation, None,
                                   configuration.customFieldTypes.keys())
            objectNodes.append(graphing.normalizedKey3(normalizedScope, "object", itemName))
            # Look for references in the dependsOn section
            if len(currentObject.dependsOn) > 0:
                for dependency in currentObject.dependsOn:
                    graphing.addDependencyNode(normalizedScope, "object",
                                               itemName, dependency,
                                               dependencyNodeInformation,
                                               depedencyReferenceInformation,
                                               dependencyInformation,
                                               configuration.customFieldTypes.keys())
            # Process the fields
            for field in currentObject.fields:
                graphing.addFieldNode(normalizedScope, "object", itemName,
                                      field, "field", nodeInformation,
                                      referenceInformation, fieldsInformation,
                                      configuration.customFieldTypes.keys())
    
    for normalizedScope in switches:
        for switchName in switches[normalizedScope]:
            currentSwitch = switches[normalizedScope][switchName]
            itemName = graphing.addItemNode(normalizedScope, currentSwitch,
                                            "switch", nodeInformation, None,
                                            configuration.customFieldTypes.keys())
            # Process the main dependency
            dependsOnSection = currentSwitch.dependsOn
            graphing.addDependencyNode(normalizedScope, "switch", itemName,
                                       dependsOnSection,
                                       dependencyNodeInformation,
                                       depedencyReferenceInformation,
                                       dependencyInformation,
                                       configuration.customFieldTypes.keys())
            # Look for references in the additionalDependsOn section
            if len(currentSwitch.additionalDependsOn) > 0:
                for dependency in currentSwitch.additionalDependsOn:
                    graphing.addDependencyNode(normalizedScope, "switch",
                                               itemName, dependency,
                                               dependencyNodeInformation,
                                               depedencyReferenceInformation,
                                               dependencyInformation,
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
                                      
    ############################################################################
    # Create actual graph
    ############################################################################
    graph = nx.DiGraph()

    for node in nodeInformation:
        graph.add_node(node, label=nodeInformation[node][0],
                       metaData="\"{}\"".format(nodeInformation[node][1]))
        
    for connection in fieldsInformation:
        graph.add_edge(connection[0], connection[1], label=connection[2])
        
    for connection in referenceInformation:
        graph.add_edge(connection[0], connection[1], label=connection[2])
        
    return (graph, objectNodes, nodeInformation)
    
def calculatePathInformation(graph, objectNodes, entryPointScope, entryPointKey, nodeInformation):
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
        for path in nx.all_simple_paths(graph, source=entryPointKey, target=node):
            pathInfo = {}
            tempPath = []
            for element in path:
                tempPath.append(element)
            loggingParent = None
            parentReason = ""
            previousScope = None
            for element in tempPath[::-1]:
                parts = element.split(".")
                if len(parts) < 3:
                    continue
                scope = parts[0]
                #itemType = parts[1]
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
            paths.append(pathInfo)
        pathInformation["{0}::{1}".format(targetScope, targetName)] = paths
    return pathInformation
    
def determineTopLevelNodes(graph, expectedTopLevelNodes):
    unexpectedNodes = []
    expectedNodes = []
    missingNodes = []
    for node in graph:
        if graph.in_degree(node) == 0:
            if node in expectedTopLevelNodes:
                expectedNodes.append(node)
            else:
                unexpectedNodes.append(node)
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
    with open("paths.json", "w") as outFile:
        outFile.write(json.dumps(pathInformation, indent=4))
        
    if len(cycles) > 0:
     with open("cycles.txt", "w") as outFile:
        for cycle in cycles:
            cycleString = ""
            for index, node in enumerate(cycle):
                cycleString = cycleString + node
                if index < len(cycle) - 1:
                    cycleString += " -> "
            outFile.write(cycleString + "\n")
    
    if 0 != len(missingExpectedTopLevelNodes):
        with open("missing_expected_nodes.txt", "w") as outFile:
            for node in missingExpectedTopLevelNodes:
                outFile.write(node + "\n")
        
    if 0 != len(unexpectedTopLevelNodes):
        with open("unexpected_top_nodes.txt", "w") as outFile:
            for node in unexpectedTopLevelNodes:
                outFile.write(node + "\n")

    dotGraph = nx.nx_pydot.to_pydot(graph)
    dotGraph.write_svg("output_no_dependencies.svg")
    
def updateObjectsBasedOnGraphInformation(cycles, pathInformation, objects, entryPointScope, entryPointName):
    # Deal with cycles    
    for cycle in cycles:
        cycleParts = cycle[0].split(".")
        try:
            objects[cycleParts[0]][cycleParts[2]].needsSpecificExport = True
        except KeyError:
            print("Unknown cycle object: {}".format(cycle[0]))
            
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
    # currentScope -> dependentScope[] -> ["enum"/"object"/"custom"] -> referenceType[]
    crossScopeItems = {}
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        if normalScope in objects:
            print("Processing objects in scope: {0}".format(normalScope))
            for currentObjectName in objects[normalScope]:
                currentObject = objects[normalScope][currentObjectName]
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
    cmakeListsInputString = '''\
# Warning! This is an automatically generated file!
#
cmake_minimum_required(VERSION 3.15 FATAL_ERROR)

project({0} LANGUAGES C)

list(PREPEND CMAKE_MODULE_PATH "${{PROJECT_SOURCE_DIR}}/cmake")
find_package(SpicyPlugin REQUIRED)

# Set minimum versions that this plugin needs.
#spicy_required_version("1.2.0")
#zeek_required_version("6.0.0")

if(NOT CMAKE_BUILD_TYPE)
    # Default to the release build
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "")
endif(NOT CMAKE_BUILD_TYPE)

add_subdirectory(analyzer)
'''.format(utils.PROTOCOL_NAME)

    with open(os.path.join(outRootFolder, "CMakeLists.txt"), "w") as currentFile:
        currentFile.write(cmakeListsInputString)
        
    # Create cmake folder contents
    cmakeFolder = os.path.join(outRootFolder, "cmake")
    os.makedirs(cmakeFolder, exist_ok=True)

    findPluginString = '''\
# Warning! This is an automatically generated file!
#
# Find the Spicy plugin to get access to the infrastructure it provides.
#
# While most of the actual CMake logic for building analyzers comes with the Spicy
# plugin for Zeek, this code bootstraps us by asking "spicyz" for the plugin's
# location. Either make sure that "spicyz" is in PATH, set the environment
# variable SPICYZ to point to its location, or set variable ZEEK_SPICY_ROOT
# in either CMake or environment to point to its installation or build
# directory.
#
# This exports:
#
#     SPICY_PLUGIN_FOUND            True if plugin and all dependencies were found
#     SPICYZ                        Path to spicyz
#     SPICY_PLUGIN_VERSION          Version string of plugin
#     SPICY_PLUGIN_VERSION_NUMBER   Numerical version number of plugin

# Runs `spicyz` with the flags given as second argument and stores the output in the variable named
# by the first argument.
function (run_spicycz output)
    execute_process(COMMAND "${SPICYZ}" ${ARGN} OUTPUT_VARIABLE output_
                    OUTPUT_STRIP_TRAILING_WHITESPACE)

    string(STRIP "${output_}" output_)
    set(${output} "${output_}" PARENT_SCOPE)
endfunction ()

# Checks that the Spicy plugin version it at least the given version.
function (spicy_plugin_require_version version)
    string(REGEX MATCH "([0-9]*)\.([0-9]*)\.([0-9]*).*" _ ${version})
    math(EXPR version_number "${CMAKE_MATCH_1} * 10000 + ${CMAKE_MATCH_2} * 100 + ${CMAKE_MATCH_3}")

    if ("${SPICY_PLUGIN_VERSION_NUMBER}" LESS "${version_number}")
        message(FATAL_ERROR "Package requires at least Spicy plugin version ${version}, "
                            "have ${SPICY_PLUGIN_VERSION}")
    endif ()
endfunction ()

###
### Main
###

if (NOT SPICYZ)
    set(SPICYZ "$ENV{SPICYZ}")
endif ()

if (NOT SPICYZ)
    # Support an in-tree Spicy build.
    find_program(
        spicyz spicyz
        HINTS ${ZEEK_SPICY_ROOT}/bin ${ZEEK_SPICY_ROOT}/build/bin $ENV{ZEEK_SPICY_ROOT}/bin
              $ENV{ZEEK_SPICY_ROOT}/build/bin ${PROJECT_SOURCE_DIR}/../../build/bin)
    set(SPICYZ "${spicyz}")
endif ()

message(STATUS "spicyz: ${SPICYZ}")

if (SPICYZ)
    set(SPICYZ "${SPICYZ}" CACHE PATH "" FORCE) # make sure it's in the cache

    run_spicycz(SPICY_PLUGIN_VERSION "--version")
    run_spicycz(SPICY_PLUGIN_VERSION_NUMBER "--version-number")
    message(STATUS "Zeek plugin version: ${SPICY_PLUGIN_VERSION}")

    run_spicycz(spicy_plugin_path "--print-plugin-path")
    set(spicy_plugin_cmake_path "${spicy_plugin_path}/cmake")
    message(STATUS "Zeek plugin CMake path: ${spicy_plugin_cmake_path}")

    list(PREPEND CMAKE_MODULE_PATH "${spicy_plugin_cmake_path}")
    find_package(Zeek REQUIRED)
    find_package(Spicy REQUIRED)
    zeek_print_summary()
    spicy_print_summary()

    include(ZeekSpicyAnalyzerSupport)
endif ()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(SpicyPlugin DEFAULT_MSG SPICYZ ZEEK_FOUND)
'''

    with open(os.path.join(cmakeFolder, "FindSpicyPlugin.cmake"), "w") as currentFile:
        currentFile.write(findPluginString)
        
def writeTestFiles(outRootFolder):
    # Create test folder contents
    testingFolder = os.path.join(outRootFolder, "testing")
    os.makedirs(testingFolder, exist_ok=True)
    testsFolder = os.path.join(testingFolder, "tests")
    os.makedirs(testsFolder, exist_ok=True)
    scriptsFolder = os.path.join(testingFolder, "scripts")
    os.makedirs(scriptsFolder, exist_ok=True)

    btestConfigContent = '''\
[btest]
TestDirs    = tests
TmpDir      = %(testbase)s/.tmp
BaselineDir = %(testbase)s/Baseline
IgnoreDirs  = .tmp
IgnoreFiles = *.tmp *.swp #* *.trace .DS_Store

[environment]
ZEEKPATH=`%(testbase)s/scripts/get-zeek-env zeekpath`
ZEEK_PLUGIN_PATH=`%(testbase)s/scripts/get-zeek-env zeek_plugin_path`
ZEEK_SEED_FILE=%(testbase)s/files/random.seed
PATH=`%(testbase)s/scripts/get-zeek-env path`
PACKAGE=%(testbase)s/../scripts
TZ=UTC
LC_ALL=C
TRACES=%(testbase)s/Traces
TMPDIR=%(testbase)s/.tmp
TEST_DIFF_CANONIFIER=%(testbase)s/scripts/diff-remove-timestamps
DIST=%(testbase)s/..
# Set compilation-related variables to well-defined state.
CC=
CXX=
CFLAGS=
CPPFLAGS=
CXXFLAGS=
LDFLAGS=
DYLDFLAGS=
'''
    with open(os.path.join(testingFolder, "btest.cfg"), "w") as currentFile:
        currentFile.write(btestConfigContent)

    availabilityContent = '''\
# Warning! This is an automatically generated file!
#
# @TEST-DOC: Check that the {0} analyzer is available.
#
# @TEST-EXEC: zeek -NN | grep -Eqi 'ANALYZER_{1}'
'''.format(utils.PROTOCOL_NAME, utils.PROTOCOL_NAME.upper())

    with open(os.path.join(testsFolder, "availability.zeek"), "w") as currentFile:
        currentFile.write(availabilityContent)
    
    removeTimestampsScript = '''\
    #! /usr/bin/env bash
#
# Replace anything which looks like timestamps with XXXs (including the #start/end markers in logs).

# Get us "modern" regexps with sed.
if [ "$(uname)" == "Linux" ]; then
    sed="sed -r"
else
    sed="sed -E"
fi

$sed 's/(0\.000000)|([0-9]{9,10}\.[0-9]{2,8})/XXXXXXXXXX.XXXXXX/g' |
    $sed 's/^ *#(open|close).(19|20)..-..-..-..-..-..$/#\1 XXXX-XX-XX-XX-XX-XX/g'
'''
    with open(os.path.join(scriptsFolder, "diff-remove-timestamps"), "w") as currentFile:
        currentFile.write(removeTimestampsScript)
    
    getZeekEnvScript = '''\
#! /bin/sh
#
# BTest helper for getting values for Zeek-related environment variables.

# shellcheck disable=SC2002
base="$(dirname "$0")"
zeek_dist=$(cat "${base}/../../build/CMakeCache.txt" 2>/dev/null | grep ZEEK_DIST | cut -d = -f 2)

if [ -n "${zeek_dist}" ]; then
    if [ "$1" = "zeekpath" ]; then
        "${zeek_dist}/build/zeek-path-dev"
    elif [ "$1" = "zeek_plugin_path" ]; then
        (cd "${base}/../.." && pwd)
    elif [ "$1" = "path" ]; then
        echo "${zeek_dist}/build/src:${zeek_dist}/aux/btest:${base}/:${zeek_dist}/aux/zeek-cut:$PATH"
    else
        echo "usage: $(basename "$0") <var>" >&2
        exit 1
    fi
else
    # Use Zeek installation for testing. In this case zeek-config must be in PATH.
    if ! which zeek-config >/dev/null 2>&1; then
        echo "zeek-config not found" >&2
        exit 1
    fi

    if [ "$1" = "zeekpath" ]; then
        zeek-config --zeekpath
    elif [ "$1" = "zeek_plugin_path" ]; then
        # Combine the local tree and the system-wide path. This allows
        # us to test on a local build or an installation made via zkg,
        # which squirrels away the build.
        echo "$(cd "${base}/../.." && pwd)/build:$(zeek-config --plugin_dir)"
    elif [ "$1" = "path" ]; then
        echo "${PATH}"
    else
        echo "usage: $(basename "$0") <var>" >&2
        exit 1
    fi
fi
'''
    with open(os.path.join(scriptsFolder, "get-zeek-env"), "w") as currentFile:
        currentFile.write(getZeekEnvScript)

#     standaloneContent = '''\
# # Warning! This is an automatically generated file!
# #
# # @TEST-DOC: Test parsing behavior of {0}.
# #
# # @TEST-EXEC: spicyc ${{DIST}}/analyzer/{1}.spicy -j -d -o {1}.hlto
# #
# # TODO: Add/adapt standalone parsing tests here.
# # @TEST-EXEC: printf "test string" | spicy-dump -p {2}::{3} {1}.hlto > output 2>&1
# # @TEST-EXEC: TEST_DIFF_CANONIFIER= btest-diff output
# '''.format(utils.PROTOCOL_NAME, utils.PROTOCOL_NAME.lower(), utils.normalizedScope(entryPointScope, "object"), entryPointName)

#     with open(os.path.join(testsFolder, "standalone.spicy"), "w") as currentFile:
#         currentFile.write(standaloneContent)

    # TODO: Deal with trace tests?
    
def writeZeekFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, bitfields, enums, objects, switches):
    # Create basic zeek files 
    scriptsFolder = os.path.join(outRootFolder, "scripts")
    os.makedirs(scriptsFolder, exist_ok=True)
    
    scriptFiles = []
    scriptFiles.append("__load__.zeek")
    with open(os.path.join(scriptsFolder, "__load__.zeek"), "w") as currentFile:
        currentFile.write("@load ./main\n")
        if configuration.signatureFile is not None:
            currentFile.write("@load-sigs dpd.sig\n")

    scriptFiles.append("main.zeek")
    with open (os.path.join(scriptsFolder, "main.zeek"), "w") as currentFile:
        currentFile.write(zeekMainFileObject.generateMainFile(utils.USES_LAYER_2, configuration.ethernetProtocolNumber))
        currentFile.write("\n")
        currentFile.write(zeekMainFileObject.addLoggingFunction())
        
    if configuration.signatureFile is not None: 
        with open(os.path.join(scriptsFolder, "dpd.sig"), "w") as currentFile:
            currentFile.write(configuration.signatureFile)
            
    # Create all the other files
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        enumScope = utils.normalizedScope(scope, "enum")
        zeekProcessingFileName = normalScope.lower() + "_processing.zeek"
        zeekTypesFileName = normalScope.lower() + "_types.zeek"
        zeekObjects = zeekTypes[normalScope]
        scriptFiles.append(zeekTypesFileName)
        with open(os.path.join(scriptsFolder, zeekTypesFileName), "w") as currentFile:
            currentFile.write("module {};\n\nexport {{\n".format(normalScope))
            for zeekLog in zeekObjects.values():
                currentFile.write(zeekLog.createRecord())
            currentFile.write("}\n")
        scriptFiles.append(zeekProcessingFileName)
        with open(os.path.join(scriptsFolder, zeekProcessingFileName), "w") as currentFile:
            currentFile.write("module {};\n\n".format(normalScope))
            eventString = ""
            functionString = ""
            for zeekLog in zeekObjects.values():
                eventString += zeekLog.addHook()
                functionString += zeekLog.addFunctions(normalScope, enums, bitfields, objects, switches, configuration.scopes)
                functionString += "\n"
            currentFile.write(eventString)
            currentFile.write(functionString)
        if enumScope in enums:
            zeekEnumFile = normalScope.lower() + "_enum.zeek"
            scriptFiles.append(zeekEnumFile)
            with open(os.path.join(scriptsFolder, zeekEnumFile), "w") as currentFile:
                currentFile.write("module {0};\n\n".format(enumScope))   
                currentFile.write("export {\n") 
                for currentEnumName in enums[enumScope]:
                    currentFile.write(enums[enumScope][currentEnumName].createZeekEnumString(enumScope))
                currentFile.write("}")
            
    return scriptFiles
    
def writeSpicyFiles(configuration, outRootFolder, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName):
    # Create basic spicy files
    analyzerFolder = os.path.join(outRootFolder, "analyzer")
    os.makedirs(analyzerFolder, exist_ok=True)

    zeekConfirmationFile = "zeek_{}.spicy".format(utils.PROTOCOL_NAME.lower())
    with open(os.path.join(analyzerFolder, zeekConfirmationFile), "w") as currentFile:
        currentFile.write("module Zeek_{};\n\n".format(utils.PROTOCOL_NAME))
        currentFile.write("import {};\n".format(utils.normalizedScope(utils.DEFAULT_SCOPE, "")))
        currentFile.write("import spicy;\n\n")
        currentFile.write("on {}::Messages::%done {{\n".format(utils.normalizedScope(utils.DEFAULT_SCOPE, "")))
        currentFile.write("{}spicy::accept_input();\n".format(utils.SINGLE_TAB))
        currentFile.write("}\n\n")
        currentFile.write("on {}::Messages::%error {{\n".format(utils.normalizedScope(utils.DEFAULT_SCOPE, "")))
        currentFile.write("{}spicy::decline_input(\"error parsing {} message\");\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME))
        currentFile.write("}\n\n")

    sourceFiles = []
    sourceFiles.append(zeekConfirmationFile)
    
    normalScope = utils.normalizedScope(utils.CONVERSION_SCOPE, "")
    spicyConversionFile = normalScope.lower() + ".spicy"
    ccConversionFile = normalScope.lower() + ".cc"
    sourceFiles.append(spicyConversionFile)
    sourceFiles.append(ccConversionFile)
    with open(os.path.join(analyzerFolder, spicyConversionFile), "w") as spicyOut:
        spicyOut.write("module {0};\n\n".format(normalScope))
        spicyOut.write("public function generateId() : string &cxxname=\"{}::generateId\";\n\n".format(normalScope))
        if bool(configuration.customFieldTypes):
            for itemName in configuration.customFieldTypes:
                item = configuration.customFieldTypes[itemName]
                spicyOut.write("public function {0}(input: bytes) : {1} &cxxname=\"{2}::{0}\";\n\n".format(item.interpretingFunction, item.returnType, normalScope))
    
    if configuration.conversionFile is not None:
        with open(os.path.join(analyzerFolder, ccConversionFile), "w") as currentFile:
            currentFile.write(configuration.conversionFile)
    else:
        with open(os.path.join(analyzerFolder, ccConversionFile), "w") as currentFile:
            # TODO: Figure out actually useful paths for these includes
            #currentFile.write("#include <string>\n#include <iostream>\n#include <algorithm>\n#include <random>\n#include \"{0}\"\n#include \"{1}\"\n\n".format("/opt/zeek/include/spicy/rt/libspicy.h", "/opt/zeek/include/hilti/rt/libhilti.h"))
            currentFile.write("#include <string>\n#include <iostream>\n#include <algorithm>\n#include <random>\n#include {0}\n#include {1}\n\n".format("<hilti/rt/libhilti.h>", "<spicy/rt/libspicy.h>"))
            currentFile.write("namespace {0}\n{{\n#define ID_LEN 9\n".format(normalScope))
            currentFile.write(utils.generateIdFunction)
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
                    currentFile.write("{0}{1} {2}(const hilti::rt::Bytes &data)".format(utils.SINGLE_TAB, returnType, item.interpretingFunction))
                    currentFile.write("{0}{{\n{1}return {2};\n{0}}}\n".format(utils.SINGLE_TAB, utils.DOUBLE_TAB, emptyReturn))
            currentFile.write("}\n")
            
    transportProtocols = []

    if configuration.usesTCP:
        transportProtocols.append("TCP")

    if configuration.usesUDP:
        transportProtocols.append("UDP")
            
    # Create all the other files
    for scope in configuration.scopes:
        normalScope = utils.normalizedScope(scope, "")
        enumScope = utils.normalizedScope(scope, "enum")
        outputFileName = normalScope.lower() + ".spicy"
        evtFileName = normalScope.lower() + ".evt"
        sourceFiles.append(outputFileName)
        with open(os.path.join(analyzerFolder, outputFileName), "w") as currentFile:
            currentFile.write("module {0};\n\n".format(normalScope))
            currentFile.write("import spicy;\n\n")
            
            if normalScope in crossScopeItems:
                for usedScope in crossScopeItems[normalScope]:
                    if usedScope != "":
                        currentFile.write("import {0};\n".format(usedScope))
                currentFile.write("\n")
            
            if scope == entryPointScope:
                currentFile.write("public type {0}s = unit {{\n{1} : {0}[];\n}};\n\n".format(entryPointName, utils.SINGLE_TAB))
            if normalScope in objects:
                for currentObjectName in objects[normalScope]:
                    # TODO: Other cases where things need to be public?
                    shouldBePublic = currentObjectName == entryPointName
                    currentFile.write("{0}\n".format(objects[normalScope][currentObjectName].createSpicyString(configuration.customFieldTypes, bitfields, switches, enums, shouldBePublic)))
            currentFile.write("# vim: ai si tabstop=4 shiftwidth=4 softtabstop=4 expandtab colorcolumn=101 syntax=spicy\n")
        with open(os.path.join(analyzerFolder, evtFileName), "w") as currentFile:
            currentFile.write("import {};\n".format(normalScope))
            if normalScope in crossScopeItems:
                for usedScope in crossScopeItems[normalScope]:
                    if usedScope != "":
                        currentFile.write("import {0};\n".format(usedScope))
            currentFile.write("import Zeek_{};\n\n".format(utils.PROTOCOL_NAME))
            if normalScope == utils.normalizedScope(utils.DEFAULT_SCOPE, ""):
                currentFile.write(generateProtocolEvents(normalScope, entryPointScope, entryPointName, transportProtocols, configuration.ports, utils.USES_LAYER_2))
            scopedObjects = objects[normalScope]
            if scope == entryPointScope:
                currentFile.write("export {}::{}s;\n".format(normalScope, entryPointName))
            for object in scopedObjects:
                if not scopedObjects[object].logWithParent or scopedObjects[object].logIndependently:
                    if scopedObjects[object].needsSpecificExport:
                        exportString = "export {}::{} ".format(normalScope, object)
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
                        exportString += " };\n"
                        currentFile.write(exportString)
                    else:
                        currentFile.write("export {}::{};\n".format(normalScope, object))
            currentFile.write("\n".format())
            for object in scopedObjects.values():
                event = object.getEvent(normalScope)
                if event != []:
                    currentFile.write(event.generateEvent(bitfields))
        sourceFiles.append(evtFileName) 
        if enumScope in enums:
            enumOutputFileName = enumScope.lower() + ".spicy"
            sourceFiles.append(enumOutputFileName)
            with open(os.path.join(analyzerFolder, enumOutputFileName), "w") as currentFile:
                currentFile.write("module {0};\n\n".format(enumScope))
                for currentEnumName in enums[enumScope]:
                    currentFile.write("{0}\n".format(enums[enumScope][currentEnumName].createSpicyEnumString()))
                currentFile.write("# vim: ai si tabstop=4 shiftwidth=4 softtabstop=4 expandtab colorcolumn=101 syntax=spicy\n")
                
    return (analyzerFolder, sourceFiles)
        
def writeLastCMakeFile(analyzerFolder, scriptFiles, sourceFiles):
    # Create CMakeLists.txt file with all the sources and scripts

    buildContents = '''\
spicy_add_analyzer(
    NAME {0}
    PACKAGE_NAME {0}
    SOURCES {1}
    SCRIPTS {2}
)
'''.format(utils.PROTOCOL_NAME, " ".join(sourceFiles), " ".join(scriptFiles))
    with open(os.path.join(analyzerFolder, "CMakeLists.txt"), "w") as currentFile:
        currentFile.write(buildContents)
    
def writeParserFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName):
    # Create base folder
    os.makedirs(outRootFolder, exist_ok=True)
    # Fill in the rest of the structure
    writeCMakeFiles(outRootFolder)
    writeTestFiles(outRootFolder)
    # Must be called in this order...there are side effects of calling this one
    # that are required for the other one to work correctly
    folder, sourceFiles = writeSpicyFiles(configuration, outRootFolder, crossScopeItems, bitfields, enums, objects, switches, entryPointScope, entryPointName)
    # TODO: Figure out what is creating the side effects in the previous call
    scriptFiles = writeZeekFiles(configuration, outRootFolder, zeekTypes, zeekMainFileObject, bitfields, enums, objects, switches)
    writeLastCMakeFile(folder, scriptFiles, sourceFiles)
