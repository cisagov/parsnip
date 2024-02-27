# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import argparse

import utils
import json_processing as processing
import graphing

import generation_utils
import config

# Graph Theory Imports
import networkx as nx

def _updateUtilValues(configuration):
    utils.PROTOCOL_NAME = configuration.protocol
    utils.USES_LAYER_2 = configuration.usesLayer2
    utils.customFieldTypes = configuration.customFieldTypes
    
def _parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputRootDirectory", type=str, help="Path to folder with '{0}' folder".format(utils.DEFAULT_SCOPE))
    parser.add_argument("outputRootDirectory", type=str, help="Root output directory")

    args = parser.parse_args()

    return (args.inputRootDirectory, args.outputRootDirectory)
    
def _generateData(inRootFolder, configuration, entryPointScope, entryPointName, entryPointKey):
    ############################################################################
    # Process the data files
    ############################################################################    
    objects, switches, bitfields, enums = processing.loadFiles(inRootFolder, configuration.scopes)
               
    ############################################################################
    # Use some Graph Theory to our advantage
    ############################################################################                       
    generation_utils.createAndUseGraphInformation(configuration, objects, switches, bitfields, enums, entryPointScope, entryPointName, entryPointKey)
        
    ############################################################################
    # Work with the loaded data
    ############################################################################
    zeekTypes, zeekMainFileObject = processing.createZeekObjects(configuration.scopes, configuration.customFieldTypes, bitfields, objects, switches)
    
    # Determine import requirements
    # currentScope -> dependentScope[] -> ["enum"/"object"/"custom"] -> referenceType[]
    crossScopeItems = generation_utils.determineInterScopeDependencies(configuration, bitfields, objects, switches)
    
    return (zeekTypes, zeekMainFileObject, crossScopeItems, bitfields, enums, objects, switches)
    
def determineEntryPointInformation(configuration):
    entryPointParts = configuration.entryPoint.split(".")
    if 2 != len(entryPointParts):
        return (False, "", "", "")

    entryPointScope = entryPointParts[0]
    entryPointName = entryPointParts[1]
    entryPointKey = graphing.normalizedKey3(utils.normalizedScope(entryPointScope, "object"), "object", entryPointName)
    
    return (True, entryPointScope, entryPointName, entryPointKey)
    
if __name__ == "__main__":
    import os
    
    ############################################################################
    # Parse Command Line Arguments
    ############################################################################
    inRootFolder, outRootFolder = _parseArgs()

    ############################################################################
    # Load the configuration file
    ############################################################################    
    configPath = os.path.join(inRootFolder, utils.DEFAULT_SCOPE, "config.json")
    
    loadSuccessful, configuration = config.loadConfig(configPath)
    if not loadSuccessful:
        print(configPath + " is a required file")
        exit(1)
        
    _updateUtilValues(configuration)
    
    entryPointParsingSuccessful, entryPointScope, entryPointName, entryPointKey = determineEntryPointInformation(configuration)
    
    if not entryPointParsingSuccessful:
        print("EntryPoint must have scope and object name")
        exit(2)
    
    print(entryPointScope + " ---> " + entryPointName)

    ############################################################################
    # Load and work with data
    ############################################################################
    zeekTypes, zeekMainFileObject, crossScopeItems, bitfields, enums, objects, switches = _generateData(inRootFolder, configuration, entryPointScope, entryPointName, entryPointKey)

    ############################################################################
    # Generate output
    ############################################################################
    generation_utils.writeParserFiles(configuration, outRootFolder,
                                      zeekTypes, zeekMainFileObject,
                                      crossScopeItems,
                                      bitfields, enums,
                                      objects, switches,
                                      entryPointScope, entryPointName)
