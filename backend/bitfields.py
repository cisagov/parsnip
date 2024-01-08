# Copyright 2023, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils
from math import ceil

class BitfieldField:
    # enumFields are different options inside an enumeration
    def __init__(self, name, description, fieldType, bits, scope = ""):
        self.name = name
        self.description = description
        self.notes = ""
        self.type = fieldType
        self.bits = bits
        self.referenceType = ""
        self.scope = utils.normalizedScope(scope, fieldType)

class Bitfield:
    def __init__(self, name, reference, notes, size):
        self.name = name
        self.reference = reference
        self.notes = notes
        self.size = size
        self.fields = []
        self.column = 0
        self.scope = ""
        self.longestField = 0
        self.endianness = "big"
        
    def addField(self, field):
        # Adds a field into the enum structure 
        for existingField in self.fields:
            if existingField.name == field.name:
                return
        if (ceil((len(field.name) + 1)/4) * 4) > self.column:
            self.column = (ceil((len(field.name) + 1)/4) * 4)
        if (len(field.name) > self.longestField):
            self.longestField = len(field.name)
        self.fields.append(field)
        
