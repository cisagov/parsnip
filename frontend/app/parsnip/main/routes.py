# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from parsnip.main.forms import (AddEnumForm, AddBitfieldForm, AddSwitchForm,
                                AddObjectForm, AddFieldForm,
                                UploadSnapshotForm,
                                EditConfigForm, AddUserTypeForm, AddPortForm)
from parsnip.main.utils import (addEnumToStructure, removeEnumFromStructure,
                                addBitfieldToStructure,
                                removeBitfieldFromStructure,
                                getSnapshot, setSnapshot,
                                reviewStructure,
                                updateConfig,
                                addUserTypeToSession, removeUserTypeFromSession,
                                addObjectToStructure, removeObjectFromStructure,
                                addFieldToObject, removeFieldFromObject,
                                addPortToSession, removePortFromSession,
                                addSwitchToStructure, removeSwitchFromStructure,
                                getReferenceSelectorTypes,
                                getAllReferenceSelectorTypes,
                                getBitfieldTypeSelectorTypes,
                                getAllDependencySelectorTypes,
                                getDependencyStructureTypes,
                                getActionTypeSelectorTypes,
                                getAllFieldTypeSelectorTypes,
                                getObjectInputs,
                                getStructuresOfAType,
                                getStructuresOfATypeAsDictionary,
                                getStructureNamesOfAType)

from parsnip.main.convert import (getParsnipFile)


from flask import render_template
from flask import url_for # Used in the render_template function
#from flask import flash
#from flask import request # Used for "get args"
from flask import redirect
from flask import Blueprint
from flask import session
from flask import abort
from flask import Response

main = Blueprint('main', __name__)

@main.add_app_template_global
def getTypeStructuresDictionary(structureTypeName):
    return getStructuresOfATypeAsDictionary(structureTypeName)

@main.add_app_template_global
def getTypeStructures(structureTypeName):
    return getStructuresOfAType(structureTypeName)
    
@main.add_app_template_global
def getNames(structureTypeName):
    return getStructureNamesOfAType(structureTypeName)

@main.add_app_template_global
def findStructureItemIndex(structureTypeName, itemName):
    tempStructures = getStructuresOfAType(structureTypeName)
    if len(tempStructures) > 0:
        return next((index for index, value in enumerate(tempStructures) if value.get("name") == itemName), -1)
    else:
        return -1

@main.route("/", methods=['GET'])
def index(title=""):
    uploadSnapshotForm = UploadSnapshotForm()
    return render_template('index.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm)
                           
@main.route("/import/<string:importType>", methods=['POST'])
def importData(importType):
    if "snapshot" == importType:
        uploadSnapshotForm = UploadSnapshotForm()
        if uploadSnapshotForm.validate_on_submit():
            setSnapshot(uploadSnapshotForm.snapshot.data)
        else:
            print(uploadSnapshotForm.snapshot.errors)
        return redirect(url_for('main.index'))
    else:
        abort(404)
                           
@main.route("/config", methods=['GET'])
def config(title="Parser Configuration"):
    uploadSnapshotForm = UploadSnapshotForm()
    editConfigForm = EditConfigForm()
    if "Protocol" in session and "" != session["Protocol"]:
        editConfigForm.parserName.data = session["Protocol"]
    editConfigForm.entryPoint.choices = getReferenceSelectorTypes("Objects")
    if "EntryPoint" in session and "" != session["EntryPoint"]:
        editConfigForm.entryPoint.data = session["EntryPoint"]
    if "usesTCP" in session:
        editConfigForm.usesTCP.data = session["usesTCP"]
    if "usesUDP" in session:
        editConfigForm.usesUDP.data = session["usesUDP"]
    addPortForm = AddPortForm()
    addUserTypeForm = AddUserTypeForm()
    return render_template('config.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, editConfigForm=editConfigForm, addPortForm=addPortForm, \
                           addUserTypeForm=addUserTypeForm)
    
@main.route("/editConfig", methods=['POST'])
def editConfig():
    editConfigForm = EditConfigForm()
    
    if editConfigForm.validate_on_submit():
        updateConfig(editConfigForm)
    else:
        print(editConfigForm.errors)
    return redirect(url_for('main.config'))
    
@main.route("/addUserType", methods=['POST'])
def addUserType():
    addUserTypeForm = AddUserTypeForm()
    
    if addUserTypeForm.validate_on_submit():
        addUserTypeToSession(addUserTypeForm)
    else:
        print(addUserTypeForm.errors)
    return redirect(url_for('main.config'))
    
@main.route("/removeUserType/<int:index>", methods=['GET'])
def removeUserType(index):
    removeUserTypeFromSession(index)
    return redirect(url_for('main.config'))
    
@main.route("/addPort", methods=['POST'])
def addPort():
    addPortForm = AddPortForm()
    
    if addPortForm.validate_on_submit():
        addPortToSession(addPortForm)
    else:
        print(addPortForm.errors)
    return redirect(url_for('main.config'))
    
@main.route("/removePort/<int:index>", methods=['GET'])
def removePort(index):
    removePortFromSession(index)
    return redirect(url_for('main.config'))
                           
@main.route("/enums", methods=['GET'])
def enums(title="Enums"):
    uploadSnapshotForm = UploadSnapshotForm()
    addEnumForm = AddEnumForm()
    
    return render_template('enums.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, \
                           addEnumForm=addEnumForm)
                           
@main.route("/objects", methods=['GET', 'POST'])
def objects(title="Objects"):
    uploadSnapshotForm = UploadSnapshotForm()
    addObjectForm = AddObjectForm()
    
    enumReferences = getReferenceSelectorTypes("Enums")
    
    dependencyTypes = getAllDependencySelectorTypes()
    
    for dependency in addObjectForm.objectDependencies:
        dependency.dependencyType.choices = dependencyTypes
        dependency.referenceType.choices = enumReferences
    
    return render_template('objects.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, \
                           addObjectForm=addObjectForm, \
                           dependencyTypes=dependencyTypes, \
                           enumReferences=enumReferences)
                           
@main.route("/addObject", methods=['POST'])
def addObject():
    addObjectForm = AddObjectForm()
    
    if addObjectForm.validate_on_submit():
        addObjectToStructure(addObjectForm)
    else:
        print(addObjectForm.errors)
    
    return redirect(url_for('main.objects'))

@main.route("/removeObject/<int:index>", methods=['GET'])
def removeObject(index):
    removeObjectFromStructure(index)
    return redirect(url_for('main.objects'))
                           
@main.route("/bitfields", methods=['GET'])
def bitfields(title="Bitfields"):
    uploadSnapshotForm = UploadSnapshotForm()
    addBitfieldForm = AddBitfieldForm()
    typeChoices = getBitfieldTypeSelectorTypes()
    referenceChoices = getReferenceSelectorTypes("Enums")
    for field in addBitfieldForm.fields:
        field.referenceType.choices = referenceChoices
        field.fieldType.choices = typeChoices
    
    return render_template('bitfields.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, \
                           addBitfieldForm=addBitfieldForm, referenceChoices=referenceChoices, typeChoices=typeChoices)
                           
@main.route("/viewFields/<int:index>", methods=['Get'])
def viewFields(index, title="Fields"):
    uploadSnapshotForm = UploadSnapshotForm()
    addFieldForm = AddFieldForm()
    addFieldForm.fieldType.choices = getAllFieldTypeSelectorTypes()
    addFieldForm.elementType.choices = getAllFieldTypeSelectorTypes(includeListType=False, includeChoiceType=False)
    
    return render_template('fields.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, \
                           objectIndex=index, addFieldForm=addFieldForm)

@main.route("/addField/<int:objectIndex>/<int:displayIndex>", methods=['POST'])
def addField(objectIndex, displayIndex):
    addFieldForm = AddFieldForm()
    
    if addFieldForm.validate_on_submit():
        addFieldToObject(objectIndex, addFieldForm)
    else:
        for field in addFieldForm:
            print("field {0}: {1}".format(field.id, field.data))
        print(addFieldForm.errors)
    
    return redirect(url_for('main.viewFields', index=displayIndex))
                           
@main.route("/removeField/<int:objectIndex>/<int:index>/<int:displayIndex>", methods=['GET'])
def removeField(objectIndex, index, displayIndex):
    removeFieldFromObject(objectIndex, index)
    return redirect(url_for('main.viewFields', index=displayIndex))
                           
@main.route("/switches", methods=['GET'])
def switches(title="Switches"):
    uploadSnapshotForm = UploadSnapshotForm()
    addSwitchForm = AddSwitchForm()
    
    addSwitchForm.switchMainDependency.dependencyType.choices = getDependencyStructureTypes()
    
    enumReferences = getReferenceSelectorTypes("Enums")
    
    addSwitchForm.switchMainDependency.referenceType.choices = enumReferences
    
    dependencyTypes = getAllDependencySelectorTypes()
    
    for dependency in addSwitchForm.switchAdditionalDependencies:
        dependency.dependencyType.choices = dependencyTypes
        dependency.referenceType.choices = enumReferences
    
    return render_template('switches.html', title=title, \
                           uploadSnapshotForm=uploadSnapshotForm, \
                           addSwitchForm=addSwitchForm, \
                           dependencyTypes=dependencyTypes, \
                           enumReferences=enumReferences, \
                           enumValues=getStructuresOfATypeAsDictionary("enum"), \
                           actionTypes=getActionTypeSelectorTypes(), \
                           objectReferences=getReferenceSelectorTypes("Objects"),
                           objectInputs=getObjectInputs())
                           
@main.route("/addEnum", methods=['POST'])
def addEnum():
    addEnumForm = AddEnumForm()
    
    if addEnumForm.validate_on_submit():
        addEnumToStructure(addEnumForm)
    return redirect(url_for('main.enums'))
    
@main.route("/removeEnum/<int:index>", methods=['GET'])
def removeEnum(index):
    removeEnumFromStructure(index)
    return redirect(url_for('main.enums'))
    
@main.route("/addBitfield", methods=['POST'])
def addBitfield():
    addBitfieldForm = AddBitfieldForm()
    
    if addBitfieldForm.validate_on_submit():
        addBitfieldToStructure(addBitfieldForm)
    else:
        print(addBitfieldForm.errors)
    return redirect(url_for('main.bitfields'))
    
@main.route("/removeBitfield/<int:index>", methods=['GET'])
def removeBitfield(index):
    removeBitfieldFromStructure(index)
    return redirect(url_for('main.bitfields'))
    
@main.route("/addSwitch", methods=['POST'])
def addSwitch():
    addSwitchForm = AddSwitchForm()
    
    if addSwitchForm.validate_on_submit():
        addSwitchToStructure(addSwitchForm)
    else:
        print(addSwitchForm.errors)
    return redirect(url_for('main.switches'))
    
@main.route("/removeSwitch/<int:index>", methods=['GET'])
def removeSwitch(index):
    removeSwitchFromStructure(index)
    return redirect(url_for('main.switches'))
                           
################################################################################
# WIP
################################################################################

#Route for edit 
@main.route("/editEnum/<int:index>", methods=['POST'])
def editEnum():
    editEnumForm = AddEnumForm()

    if editEnumForm.validate_on_submit():
        addEnumToStructure(editEnumForm)

    removeEnumFromStructure(index)  
    return redirect(url_for('main.enums'))


@main.route("/export/<string:exportType>", methods=['GET'])
def exportData(exportType):
    if "snapshot" == exportType:
        return Response(getSnapshot(),
                       mimetype="application/json",
                       headers={"Content-Disposition":
                                    "attachment;filename=snapshot.json"})
    elif "parsnip" == exportType:
        parsnip = getParsnipFile(getSnapshot())
        return Response(parsnip,
                        mimetype='application/zip', 
                        headers={'Content-Disposition': 'attachment;filename=parsnip.zip'})
    else:
        abort(404)
    
@main.route("/review", methods=['GET'])
def review(title="Review"):
    issues = reviewStructure()
    uploadSnapshotForm = UploadSnapshotForm()
    return render_template('review.html', title=title, issues=issues, uploadSnapshotForm=uploadSnapshotForm)
    
@main.route("/notice", methods=['GET'])
def notice(title="Notice"):
    uploadSnapshotForm = UploadSnapshotForm()
    return render_template('notice.html', title=title, uploadSnapshotForm=uploadSnapshotForm)
