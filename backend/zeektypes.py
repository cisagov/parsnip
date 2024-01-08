# Copyright 2023, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from string import Template
from math import ceil 
import re
import utils

TYPE_TO_EMPTY  = {
    "string" : "",
    "count" : 0,
}
genericZeekField = Template("""
    # Timestamp for when the event happened.
    ts$padding: time &log;

    # Unique ID for the connection.
    uid$padding: string &log;

    # The connection's 4-tuple of endpoint addresses/ports.
    id$padding: conn_id &log;
    """)

class ZeekField:
    def __init__(self, name="", type=""):
        self.name = name
        self.type = type


class ZeekMain:
    def __init__(self):
        self.records = []
    
    def addRecord(self, record):
        for currentRecord in self.records:
            if record.name == currentRecord.name:
                return
        self.records.append(record)

    def generateMainFile(self, usesLayer2, ethernetProtocolNumber=0):
        fileString = """
## main.zeek
##
## ICSNPP-{}
##
## Zeek script type/record definitions describing the information
## that will be written to the log files.
##
## Author:   Melanie Pierce
## Contact:  melanie.pierce@inl.gov
##
## Copyright (c) 2023 Battelle Energy Alliance, LLC.  All rights reserved.\n
""".format(utils.PROTOCOL_NAME)
        fileString += "module {};\n\n".format(utils.PROTOCOL_NAME)
        fileString += "export {\n"
        logStreamString = ""
        logNamePadding = " " * 28
        if len(self.records) > 1:
            fileString += "{}redef enum Log::ID += {{\n".format(utils.SINGLE_TAB)
            for record in self.records:
                recordLogName = "LOG_{}".format(record.name.upper())
                if record != self.records[len(self.records) - 1]:
                    fileString += "{}{},\n".format(logNamePadding, recordLogName)
                else:
                    fileString += "{}{}\n".format(logNamePadding, recordLogName)
                logStreamString += "{}Log::create_stream({}::{},\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME, recordLogName)
                logStreamString += "{}[$columns={}{},\n".format(utils.SINGLE_TAB, record.scope, record.name)
                logStreamString += "{}$ev=log_{},\n".format(utils.SINGLE_TAB, record.name.lower())
                logStreamString += "{}$path=\"{}_{}\"]);\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower().replace("_log", ""))
            fileString += "{}}};\n".format((" " * 27))
        else: 
            logFunctionIndent = " " * 22
            recordLogName = "LOG_{}".format(self.records[0].name.upper())
            fileString += "{}redef enum Log::ID += {{ {} }};\n\n".format(utils.SINGLE_TAB, recordLogName)
            logStreamString += "{}Log::create_stream({}::{},\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME, recordLogName)
            logStreamString += "{}[$columns={}{},\n".format(logFunctionIndent, self.records[0].scope, self.records[0].name)
            logStreamString += "{}$ev=log_{},\n".format(logFunctionIndent, self.records[0].name.lower())
            logStreamString += "{}$path=\"{}_{}\"]);\n".format(logFunctionIndent, utils.PROTOCOL_NAME.lower(), self.records[0].name.lower())
           
        for record in self.records:
            recordLogEventName = "log_{}".format(record.name.lower())
            fileString += "{}global {}: event(rec: {}{});\n".format(utils.SINGLE_TAB, recordLogEventName, record.scope, record.name)
        for record in self.records:
            recordLogEventName = "log_{}".format(record.name.lower())
            if utils.USES_LAYER_2:
                if record.scope != "":
                    fileString += "{}global emit_{}_{}: function({}_record: {}::{});\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower(), record.scope, record.name.lower())
                else:
                    fileString += "{}global emit_{}_{}: function({}_record: {});\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower(), record.name.lower(), record.name)
            else:
                fileString += "{}global emit_{}_{}: function(c: connection);\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower())
        fileString += "\n}\n\n"
        fileString += "# redefine connection record to contain one of each of the {} records\n".format(utils.PROTOCOL_NAME.lower())
        fileString += "redef record connection += {\n"
        fileString += "{}{}_proto: string &optional;\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower())
        for record in self.records:
            fileString += "{}{}_{}: {}{} &optional;\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower(), record.scope, record.name)
        fileString += "};\n\n"
        # TODO add port-based detection stuff
        fileString += "#Put protocol detection information here\n"
        fileString += "event zeek_init() &priority=5 {\n"
        # Handle ethernet registration if necessary
        if usesLayer2:
            fileString += "{0}# Register on top of Ethernet\n".format(utils.SINGLE_TAB)
            fileString += "{0}if ( ! PacketAnalyzer::try_register_packet_analyzer_by_name(\"Ethernet\", {1}, \"spicy_{2}\") )\n".format(utils.SINGLE_TAB, ethernetProtocolNumber, utils.PROTOCOL_NAME.upper())
            fileString += "{0}Reporter::error(\"cannot register Spicy analyzer\");".format(utils.DOUBLE_TAB)
            fileString += "\n"
        fileString += "{}# initialize logging streams for all {} logs\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower())
        fileString += logStreamString
        fileString += "}\n"
        return fileString
    
    def addLoggingFunction(self):
        functionsString = ""
        for record in self.records:
            connectionName = "{}_{}".format(utils.PROTOCOL_NAME.lower(), record.name.lower())
            if utils.USES_LAYER_2:
                if record.scope != "":
                    recordScope = "{}_{}::".format(utils.PROTOCOL_NAME, record.name.upper())
                    fileString += "{}global emit_{}_{}: function({}_record: {}::{});\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), record.name.lower(), recordScope, record.name.lower())
                else:
                    functionsString += "function emit_{}_{}({}_record: {}) {{\n".format(utils.PROTOCOL_NAME.lower(), record.name.lower(), record.name.lower(), record.name)
                functionsString += "{}Log::write({}::LOG_{}, {}_record);\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME, record.name.upper(), record.name.lower())
            else:
                functionsString += "function emit_{}_{}(c: connection) {{\n".format(utils.PROTOCOL_NAME.lower(), record.name.lower())
                functionsString += "{}if (! c?${} )\n".format(utils.SINGLE_TAB, connectionName)
                functionsString += "{}return;\n".format(utils.DOUBLE_TAB)
                functionsString += "{}if ( c?${}_proto )\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower())
                functionsString += "{}c${}$proto = c${}_proto;\n".format(utils. DOUBLE_TAB, connectionName, utils.PROTOCOL_NAME.lower())
                functionsString += "{}Log::write({}::LOG_{}, c${});\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME, record.name.upper(), connectionName)
                functionsString += "{}delete c${};\n".format(utils.SINGLE_TAB, connectionName)
            functionsString += "}\n\n"
        return functionsString

class ZeekRecord:
    def initializeRecordFields(self):
        protocolField = ZeekField()
        protocolField.name = "proto"
        protocolField.type = "string"
        timestampField = ZeekField()
        timestampField.name = "ts"
        timestampField.type = "time"
        if utils.USES_LAYER_2:
            commonFields = [timestampField, protocolField]
        else:
            uidField = ZeekField()
            uidField.name = "uid"
            uidField.type = "string"
            idField = ZeekField()
            idField.name = "id"
            idField.type = "conn_id"
            commonFields = [timestampField, uidField, idField, protocolField]
        return commonFields

    def __init__(self, name, scope = ""):
        self.defaultRecords = self.initializeRecordFields()
        self.fields = []
        self.commandStructures = []
        self.column = 8
        self.name = utils.commandNameToConst(name).lower() + "_log"

        # self.subname = ""
        self.logName = ""
        self.protocol = ""
        if scope == "":
            scopeName = self.name
        else:
            scopeName = scope
        if scopeName != "general":
            self.scope = "{}_{}::".format(utils.PROTOCOL_NAME, scopeName.upper())
        else:
            self.scope = ""
        self.externalLinkFields = []

    def addExternalLinkFields(self, field):
        for existingField in self.externalLinkFields:
            if existingField.name == field.name:
                return
        if (ceil((len(field.name) + 1)/4) * 4) > self.column:
            self.column = (ceil((len(field.name) + 1)/4) * 4)
        self.externalLinkFields.append(field)     

    def addExternalLinkFieldList(self, fieldList):
        for field in fieldList:
            for existingField in self.externalLinkFields:
                if existingField.name == field.name:
                    break
            else:
                if (ceil((len(field.name) + 1)/4) * 4) > self.column:
                    self.column = (ceil((len(field.name) + 1)/4) * 4)
                self.externalLinkFields .append(field)

    def addField(self, field):
        for existingField in self.fields:
            if existingField.name == field.name:
                return
        if (ceil((len(field.name) + 1)/4) * 4) > self.column:
            self.column = (ceil((len(field.name) + 1)/4) * 4)
        self.fields.append(field)
    
    def addFieldList(self, fieldList):
        for field in fieldList:
            for existingField in self.fields:
                if existingField.name == field.name:
                    break
            else:
                if (ceil((len(field.name) + 1)/4) * 4) > self.column:
                    self.column = (ceil((len(field.name) + 1)/4) * 4)
                self.fields.append(field)

    def addHook(self):
        #TODO: Handle header information; Maybe add additional initial formatting
        hookString = ""
        if not utils.USES_LAYER_2:
            hookString = "hook set_session_{}(c: connection) {{\n".format(self.name.lower())
            hookString += "{}if ( ! c?${}_{} )\n".format(utils.SINGLE_TAB, utils.PROTOCOL_NAME.lower(), self.name.lower())
            hookString += "{}c${}_{} = {}(\n".format(utils.DOUBLE_TAB, utils.PROTOCOL_NAME.lower(), self.name.lower(), self.name)
            hookString += "{}$ts=network_time(),\n".format(utils.SINGLE_TAB * 3)
            hookString += "{}$uid=c$uid,\n".format(utils.SINGLE_TAB * 3)
            hookString += "{}$id=c$id,\n".format(utils.SINGLE_TAB * 3)
            hookString += "{}$proto=\"{}\");\n".format(utils.SINGLE_TAB * 3, utils.PROTOCOL_NAME.lower())
            hookString += "}\n\n"
        return hookString

    def addCommandStructure(self, commandStructure):
        if commandStructure not in self.commandStructures and (commandStructure.logIndependently or not commandStructure.logWithParent):
            self.commandStructures.append(commandStructure)
    
    def addFunctions(self, moduleName, allEnums, allBitfields, allObjects, allSwitches, scopes):
        functionString = ""
        for command in self.commandStructures:
            functionString += command.makeEventBackend(moduleName, self.name, allEnums, allBitfields, allObjects, allSwitches, scopes)
        return functionString

    def createRecord(self):
        recordString = ""
        recordString += "{}type {}: record {{\n".format(utils.SINGLE_TAB, self.name)
        for field in self.defaultRecords:
            paddingSize = (self.column - len(field.name))
            padding = paddingSize * ' '
            recordString += "{}{}{}: {} &log;\n".format(utils.DOUBLE_TAB, field.name, padding, field.type)
        for field in self.externalLinkFields:
            paddingSize = (self.column - len(field.name))
            padding = paddingSize * ' '
            recordString += "{}{}{}: {} &log &optional;\n".format(utils.DOUBLE_TAB, field.name, padding, field.type)
        for field in self.fields:
            paddingSize = (self.column - len(field.name))
            padding = paddingSize * ' '
            recordString += "{}{}{}: {} &log &optional;\n".format(utils.DOUBLE_TAB, field.name, padding, field.type)
        recordString += "{}}};\n\n".format(utils.SINGLE_TAB)
        return recordString
