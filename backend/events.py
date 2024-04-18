# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils

DEFAULT_ARGUMENTS = ["$conn", "$is_orig"]

class SpicyEvent:
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)


    def __init__(self, includedFields=[], linkFields=[]):
        self.name = ""
        self.trigger = "on"
        self.scope = ""
        if utils.USES_LAYER_2:
            self.arguments = []
        else:
            self.arguments = DEFAULT_ARGUMENTS
        self.eventFields = includedFields
        self.relatedBitfields = {}
        self.linkFields = linkFields

    def generateExport(self):
        fullScopeExport = "export {}::{};\n".format(self.scope, self.name)
        return fullScopeExport
    
    def generateEvent(self, allBitfields):
        basicEvent =  "on {}::{} -> event {}::{}Evt (\n".format(self.scope, self.name, self.scope, self.name)
        scopedArguments = []
        # for link in self.linkFields:
        #     basicEvent += "{}{},\n".format(utils.SINGLE_TAB, link.name)
        for item in self.arguments:
            scopedArguments.append(item)
        for link in self.linkFields:
            #basicEvent += "{}self.{},\n".format(utils.SINGLE_TAB, link.name)
            scopedArguments.append(link.name)
        if self.eventFields != []:
            for field in self.eventFields:
                if field.type == "bits":
                    referencedBitfield = allBitfields[utils.normalizedScope(field.scope, "bitfield")][field.referenceType]
                    for bitField in referencedBitfield.fields:
                        scopedArguments.append("self.{}.{}".format(field.name, bitField.name))
                    self.relatedBitfields[field.name] = self.relatedBitfields
                else:
                    scopedArguments.append("self.{}".format(field.name))
        else:
            scopedArguments.append("self".format(self.scope, self.name))
        for argument in scopedArguments:
            if argument != scopedArguments[-1]:
                basicEvent += "{}{},\n".format(utils.SINGLE_TAB, argument)
            else:
                basicEvent += "{}{}\n);\n\n".format(utils.SINGLE_TAB, argument)
        return basicEvent

    def getEventFunctionName(self, allBitfields):
        eventName = ""
        if utils.USES_LAYER_2:
            eventName += "event {}::{}Evt (".format(self.scope, self.name)
        else:
            eventName += "event {}::{}Evt (c: connection, is_orig: bool, ".format(self.scope, self.name)
        for link in self.linkFields:
            eventName += "{}: string, ".format(link.name)
        if self.eventFields != []:
            for field in self.eventFields:
                if field.type == "enum":
                    if field.scope != "":
                        eventName += "{}: {}::{}".format(field.name, field.scope, field.referenceType)
                    else:
                        print("Enum field: {} has no scope".format(field.name))
                elif field.type in utils.spicyToZeek:
                    eventName += "{}: {}".format(field.name, utils.spicyToZeek[field.type])
                elif field.type in utils.customFieldTypes:
                    eventName += "{}: {}".format(field.name, utils.zeekTypeMapping(utils.customFieldTypes[field.type].returnType))
                elif field.type == "bits":
                    referencedBitfield = allBitfields[utils.normalizedScope(field.scope, "bitfield")][field.referenceType]
                    for bitField in referencedBitfield.fields:
                        if bitField.type == "enum":
                            if field.scope != "":
                                eventName += "{}: {}::{}".format(bitField.name, bitField.scope, bitField.referenceType)
                            else:
                                print("Enum field: {} has no scope".format(bitField.name))
                        elif bitField.type in utils.spicyToZeek:
                            eventName += "{}: {}".format(bitField.name, utils.spicyToZeek[bitField.type])
                        elif bitField.type in utils.customFieldTypes:
                            eventName += "{}: {},".format(bitField.name, utils.zeekTypeMapping(utils.customFieldTypes[bitField.type].returnType))
                        elif bitField.type == "enum":
                            if field.scope != "":
                                eventName += "{}: {}::{}".format(bitField.name, bitField.scope, bitField.referenceType)
                            else:
                                print("Enum field: {} has no scope".format(bitField.name))
                        else:
                            print("Unknown Bitfield Option: {}".format(field.name))
                        if bitField != referencedBitfield.fields[-1]:
                            eventName += ","
                elif field.type == "object":
                    eventName += "{}: {}::{}".format(field.name,  utils.normalizedScope(field.scope), field.referenceType)
                elif "linking" in field.type:
                   continue
                else:
                    print("Unknown {}".format(field.type))
                if field != self.eventFields[-1]:
                    eventName += ", "
        else:
            eventName += "{}: {}::{}".format(self.name.lower(), self.scope, self.name)
        eventName += ") {\n"
        return eventName
