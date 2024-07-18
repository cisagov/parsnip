import os
import customtypes
import json
import base64

class Config:
    def __init__(self):
        self.protocol = ""
        self.scopes = []
        self.entryPoint = ""
        self.usesTCP = False
        self.usesUDP = False
        self.usesLayer2 = False
        self.ethernetProtocolNumber = 0
        self.ports = []
        self.customFieldTypes = {}
        self.signatureFile = None
        self.conversionFile = None
        self.shortDescription = ""
        self.longDescription = ""
        
def loadConfig(configFilePath):
    config = Config()
    if not (os.path.isfile(configFilePath)):
        return (False, config)
    
    with open(configFilePath, "r+") as file:
        configObject = json.load(file)

    config.protocol = configObject["Protocol"]
    config.scopes = configObject["Scopes"]
    config.entryPoint = configObject["EntryPoint"]

    if "usesTCP" in configObject and configObject["usesTCP"] == True:
        config.usesTCP = True

    if "usesUDP" in configObject and configObject["usesUDP"] == True:
        config.usesUDP = True
        
    if "usesLayer2" in configObject and configObject["usesLayer2"] == True:
        config.usesLayer2 = True
        
    if "ethernetProtocolNumber" in configObject:
        config.ethernetProtocolNumber = configObject["ethernetProtocolNumber"]
    
    if "Ports" in configObject:
        config.ports = configObject["Ports"]

    if "CustomFieldTypes" in configObject:
        for item in configObject["CustomFieldTypes"]:
            config.customFieldTypes[item.get("name")] = customtypes.CustomType(item.get("name"), item.get("interpretingFunction"), item.get("returnType"))
            
    if "signatureFile" in configObject and "" != configObject.get("signatureFile"):
        config.signatureFile = base64.b64decode(configObject.get("signatureFile")).decode()
        
    if "conversionFile" in configObject and "" != configObject.get("conversionFile"):
        config.conversionFile = base64.b64decode(configObject.get("conversionFile")).decode()

    if "protocolShortDescription" in configObject and "" != configObject.get("protocolShortDescription"):
        config.shortDescription = configObject["protocolShortDescription"]

    if "protocolLongDescription" in configObject and "" != configObject.get("protocolLongDescription"):
        config.longDescription = configObject["protocolLongDescription"]
    
    return (True, config)                        
