# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils

class Input:
    def __init__(self, source):
        self.source = source

class Dependency:
    def __init__(self, name, type, size="", referenceType = "", scope = ""):
        self.name = name
        self.type = type
        self.size = size
        self.referenceType = referenceType
        self.scope = utils.normalizedScope(scope, type)
    
    def equal(self, other):
        return self.name == other.name and \
               self.type == other.type and \
               self.size == other.size and \
               self.referenceType == other.referenceType and \
               self.scope == other.scope
