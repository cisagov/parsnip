# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils
        
class SwitchAction:
    def __init__(self, name, type, referenceType, scope=""):
        self.name = name
        self.type = type
        self.referenceType = referenceType
        self.elementType = ""
        self.inputs = []
        self.scope = utils.normalizedScope(scope, type)
        self.size = 0
        self.until = None
    
    def addInput(self, input):
        for existingInput in self.inputs:
            if existingInput.source == input.source:
                return
        if input not in self.inputs:
            self.inputs.append(input)

class SwitchOption:
    def __init__(self, value):
        self.value = value
        self.action = None

class Switch:
    def __init__(self, name, referenceCount):
        self.name = name
        self.dependsOn = None
        self.additionalDependsOn = []
        self.options = []
        self.default = None
        self.referenceCount = referenceCount
        self.column = 0
        self.longestOption = 0
        self.actionColumn = 0
        self.longestAction = 0
    
    def addAdditionalDependsOn(self, dependency):
        for existingDependency in self.additionalDependsOn:
            if existingDependency.equal(dependency):
                return
        if self.dependsOn.equal(dependency):
            return
        self.additionalDependsOn.append(dependency)
    
    def addOption(self, option):
        if option not in self.options:
            tempColumn = utils.calculateColumn(len(str(option.value)))
            if tempColumn > self.column:
                self.column = tempColumn
            if len(str(option.value)) > self.longestOption:
                self.longestOption = len(str(option.value))
            tempColumn = utils.calculateColumn(len(option.action.name))
            if tempColumn > self.actionColumn:
                self.actionColumn = tempColumn
            if len(option.action.name) > self.longestAction:
                self.longestAction = len(option.action.name)
            self.options.append(option)
