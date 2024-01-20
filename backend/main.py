# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils
import json_processing as processing
import graphing

import generation_utils
import config

# Graph Theory Imports
import networkx as nx

if __name__ == "__main__":
    import os
    import argparse
    
    ############################################################################
    # Parse Command Line Arguments
    ############################################################################
    parser = argparse.ArgumentParser()
    parser.add_argument("inputRootDirectory", type=str, help="Path to folder with '{0}' folder".format(utils.DEFAULT_SCOPE))
    parser.add_argument("outputRootDirectory", type=str, help="Root output directory")

    args = parser.parse_args()

    inRootFolder = args.inputRootDirectory
    outRootFolder = args.outputRootDirectory

    ############################################################################
    # Load the configuration file
    ############################################################################    
    configPath = os.path.join(inRootFolder, utils.DEFAULT_SCOPE, "config.json")
    
    loadSuccessful, configuration = config.loadConfig(configPath)
    if not loadSuccessful:
        print(configPath + " is a required file")
        exit(1)
        
    utils.PROTOCOL_NAME = configuration.protocol
    
    entryPointParts = configuration.entryPoint.split(".")
    if 2 != len(entryPointParts):
        print("EntryPoint must have scope and object name")
        exit(2)
        
    utils.USES_LAYER_2 = configuration.usesLayer2
    utils.customFieldTypes = configuration.customFieldTypes

    entryPointScope = entryPointParts[0]
    entryPointName = entryPointParts[1]
    entryPointKey = graphing.normalizedKey3(utils.normalizedScope(entryPointScope, "object"), "object", entryPointName)
    
    print(entryPointScope + " ---> " + entryPointName)
    ############################################################################
    # Process the data files
    ############################################################################    
    objects, switches, bitfields, enums = processing.loadFiles(inRootFolder, configuration.scopes)
    
    ############################################################################
    # Load the structures as nodes
    ############################################################################
    graph, objectNodes, nodeInformation = generation_utils.generateGraph(configuration, objects, switches, bitfields, enums)
                                      
    ############################################################################
    # Create actual graph
    ############################################################################
        
    # Determine paths for every node from the EntryPoint Node
    pathInformation = generation_utils.calculatePathInformation(graph, objectNodes, entryPointScope, entryPointKey, nodeInformation)
    
    # Look for cycles in the graph
    cycles = nx.recursive_simple_cycles(graph)
    
    missingExpectedTopLevelNodes, expectedTopLevelNodes, unexpectedTopLevelNodes = generation_utils.determineTopLevelNodes(graph, [entryPointKey])
    
    ############################################################################
    # Use the graph information
    ############################################################################
    generation_utils.printGraphWarnings(cycles, missingExpectedTopLevelNodes, unexpectedTopLevelNodes)
    #generation_utils.saveGraphInformation(graph, pathInformation, cycles, missingExpectedTopLevelNodes, unexpectedTopLevelNodes)
    
    generation_utils.updateObjectsBasedOnGraphInformation(cycles, pathInformation, objects, entryPointScope, entryPointName)
        
    ############################################################################
    # Work with the loaded data
    ############################################################################
    zeekTypes, zeekMainFileObject = processing.createZeekObjects(configuration.scopes, configuration.customFieldTypes, bitfields, objects, switches)
    
    zeekTypes, zeekMainFileObject = processing.createZeekObjects(configuration.scopes, configuration.customFieldTypes, bitfields, objects, switches)
    
    # Determine import requirements
    # currentScope -> dependentScope[] -> ["enum"/"object"/"custom"] -> referenceType[]
    crossScopeItems = generation_utils.determineInterScopeDependencies(configuration, bitfields, objects, switches)

    ############################################################################
    # Generate output
    ############################################################################
    generation_utils.writeParserFiles(configuration, outRootFolder,
                                      zeekTypes, zeekMainFileObject,
                                      crossScopeItems,
                                      bitfields, enums,
                                      objects, switches,
                                      entryPointScope, entryPointName)
