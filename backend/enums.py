# Copyright 2023, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils
from math import ceil 
class EnumField:
    # enumFields are different options inside an enumeration
    def __init__(self, name, loggingValue, value):
        self.name = name
        self.loggingValue = loggingValue
        self.value = value
        self.notes = ""

class Enums:
    def __init__(self, name, reference, size):
        self.name = name
        self.reference = reference
        self.notes = ""
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
        tempColumn = utils.calculateColumn(len(field.name))
        if tempColumn > self.column:
            self.column = tempColumn
        if (len(field.name) > self.longestField):
            self.longestField = len(field.name)
        self.fields.append(field)

    def createSpicyEnumString(self):
        # Create spicy-side structures
        if self.reference != "":
            enumString = "# {0}\n".format(self.reference)
        else:
            enumString = ""
        enumString += "public type {0} = enum {{\n".format(self.name)
        for index, field in enumerate(self.fields):
            padding_size = self.column - len(field.name)
            padding = " " * padding_size
            commaString=","
            if index == len(self.fields) - 1:
                commaString = ""
            enumString += "{0}{1}{2}= {3}{4}\n".format(utils.SINGLE_TAB, field.name, padding, field.value, commaString)
        enumString += "};\n"
        return enumString

    def createZeekEnumString(self, enumScope):
        # This function creates the zeek structure to change an enum into a human readable string
        zeekString = "{}const {} = {{\n".format(utils.SINGLE_TAB, utils.commandNameToConst(self.name).upper())
        scopingValue = "[{}::{}_".format(enumScope, self.name) #Indicates the exported zeek name for zeek-side enums
        for i, field in enumerate(self.fields):
            longestValue = len(scopingValue) + 1 + self.longestField #Scope + longest field + closing ]
            zeekColumn = ceil((longestValue + 1)/4) * 4
            padding_size = zeekColumn - (len(field.name) + len(scopingValue) + 1)
            padding = " " * padding_size
            lineEnd = ","
            if len(self.fields) - 1 == i:
                lineEnd = ""
            zeekString += "{}{}{}]{}= \"{}\"{}\n".format(utils.DOUBLE_TAB, scopingValue, field.name, padding, field.loggingValue, lineEnd)
        zeekString += "{}}}".format(utils.SINGLE_TAB)
        zeekString += " &default=function(i: {}::{}):string".format(enumScope, self.name)
        zeekString += "{return fmt(\"unknown-0x%x\", i); } &redef;\n\n"
        return zeekString
