# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from flask_wtf import FlaskForm
from wtforms import (Form, FormField, StringField, IntegerField, BooleanField,
                     FieldList, HiddenField, SelectField)
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import InputRequired, Regexp, NumberRange, Optional

################################################################################
# Conditional Test Classes
################################################################################
class RequiredIfReferenceType(InputRequired):
    field_flags = ('requiredif',)
    
    def __init__(self, conditionalFieldName, message=None, *args, **kwargs):
        self.conditionalFieldName = conditionalFieldName
        self.message = message

    def __call__(self, form, field):
        checkField = form[self.conditionalFieldName]
        if checkField is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName)
        if checkField.data in ["object", "enum", "bits", "switch"]:
            super(RequiredIfReferenceType, self).__call__(form, field)

class RequiredIfSizedElement(InputRequired):
    field_flags = ('requiredif',)
    
    def __init__(self, conditionalFieldName, message=None, *args, **kwargs):
        self.conditionalFieldName = conditionalFieldName
        self.message = message

    def __call__(self, form, field):
        checkField = form[self.conditionalFieldName]
        if checkField is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName)
        if checkField.data in ["uint", "int", "real"]:
            super(RequiredIfSizedElement, self).__call__(form, field)
            
class RequiredIfSizedElement2(InputRequired):
    field_flags = ('requiredif',)
    
    def __init__(self, conditionalFieldName1, conditionalFieldName2, message=None, *args, **kwargs):
        self.conditionalFieldName1 = conditionalFieldName1
        self.conditionalFieldName2 = conditionalFieldName2
        self.message = message

    def __call__(self, form, field):
        checkField1 = form[self.conditionalFieldName1]
        checkField2 = form[self.conditionalFieldName2]
        if checkField1 is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName1)
        if checkField2 is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName2)
        if checkField1.data in ["uint", "int", "real"] or checkField2.data in ["uint", "int", "real"]:
            super(RequiredIfSizedElement2, self).__call__(form, field)
            
class RequiredIfBitfieldFieldTypeForBit(InputRequired):
    field_flags = ('requiredif',)

    def __init__(self, conditionalFieldName, message=None, *args, **kwargs):
        self.conditionalFieldName = conditionalFieldName
        self.message = message

    def __call__(self, form, field):
        checkField = form[self.conditionalFieldName]
        if checkField is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName)
        if "bool" == checkField.data:
            super(RequiredIfBitfieldFieldTypeForBit, self).__call__(form, field)
            
class RequiredIfBitfieldFieldTypeForBits(InputRequired):
    field_flags = ('requiredif',)

    def __init__(self, conditionalFieldName, message=None, *args, **kwargs):
        self.conditionalFieldName = conditionalFieldName
        self.message = message

    def __call__(self, form, field):
        checkField = form[self.conditionalFieldName]
        if checkField is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName)
        if checkField.data in ["enum", "uint"]:
            super(RequiredIfBitfieldFieldTypeForBits, self).__call__(form, field)
            
class RequiredIfBitfieldFieldTypeForReference(InputRequired):
    field_flags = ('requiredif',)

    def __init__(self, conditionalFieldName, message=None, *args, **kwargs):
        self.conditionalFieldName = conditionalFieldName
        self.message = message

    def __call__(self, form, field):
        checkField = form[self.conditionalFieldName]
        if checkField is None:
            raise Exception('no field named "%s" in form' % self.conditionalFieldName)
        if "enum" == checkField.data:
            super(RequiredIfBitfieldFieldTypeForReference, self).__call__(form, field)
            
################################################################################
# Sub-forms
################################################################################
class AddEnumFieldForm(Form):
    fieldName = StringField('Field Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    loggingValue = StringField('Value to Appear in the Log: ', validators=[InputRequired()])
    fieldValue = IntegerField('Field Value: ', validators=[InputRequired()])
    fieldNote = StringField('Field Note: ')
    
class AddBitfieldFieldForm(Form):
    fieldName = StringField('Field Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    fieldDescription = StringField('Field Description: ', validators=[InputRequired()])
    fieldNote = StringField('Field Note: ')
    fieldType = SelectField('Field Type: ', choices=[('', '---')], validate_choice=False)
    bit = IntegerField('Bit: ', validators=[RequiredIfBitfieldFieldTypeForBit("fieldType")])
    startingBit = IntegerField('Starting Bit: ', validators=[RequiredIfBitfieldFieldTypeForBits("fieldType")])
    endingBit = IntegerField('Ending Bit: ', validators=[RequiredIfBitfieldFieldTypeForBits("fieldType")])
    referenceType = SelectField("Reference Type: ", validators=[RequiredIfBitfieldFieldTypeForReference("fieldType")], choices=[('', '---')], validate_choice=False)
    
class DependencyForm(Form):
    dependencyName = StringField('Dependency Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    dependencyType = SelectField('Dependency Type: ', choices=[('', '---')], validate_choice=False)
    fieldSize = IntegerField('Field Size (Bits): ', validators=[RequiredIfSizedElement("dependencyType"), NumberRange(0)], default=8);
    referenceType = SelectField('Reference Type: ', choices=[('', '---')], validate_choice=False)
    
class OptionForm(Form):
    optionValueSelection = StringField('Value: ', validators=[InputRequired()], render_kw={'readonly': True})
    optionActionName = StringField('Action Name: ', validators=[InputRequired()])
    optionActionType = SelectField('Action Type: ', choices=[('', '---')], validate_choice=False)
    optionActionSize = IntegerField('Field Size (Bits): ', validators=[RequiredIfSizedElement("optionActionType"), NumberRange(0)], default=8);
    referenceType = SelectField('Reference Type: ', choices=[('', '---')], validate_choice=False)
    inputs = FieldList(SelectField('Input Value: ', choices=[('', '---')], validate_choice=False), min_entries=0, max_entries=65535)

################################################################################
# Forms
################################################################################
class EditConfigForm(FlaskForm):
    parserName = StringField('Parser Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    entryPoint = SelectField('Parser Entry Point Structure: ', choices=[("", "---")], validate_choice=False)
    usesTCP = BooleanField('Uses TCP Protocol? ')
    usesUDP = BooleanField('Uses UDP Protocol? ')
    
class AddPortForm(FlaskForm):
    protocolName = SelectField('Parent Protocol Name: ', choices=[('tcp', 'TCP'), ('udp', 'UDP')])
    portNumber = IntegerField('Port Number: ', validators=[InputRequired(), NumberRange(1)])
    
class AddUserTypeForm(FlaskForm):
    typeName = StringField('Type Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9\-]*$')])
    interpretingFunction = StringField('Interpreting Function: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    returnType = SelectField('Function Return Type: ', choices=[('string', 'string')])
    
class UploadSnapshotForm(FlaskForm):
    snapshot = FileField('Upload Snapshot', validators=[FileRequired(), FileAllowed(['json'])])
    
class AddEnumForm(FlaskForm):
    enumName = StringField('Enum Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    enumReference = StringField('Enum Reference: ')
    enumNote = StringField('Enum Note: ')
    enumScope = StringField('Enum Scope: ')
    enumSize = IntegerField('Field Size (Bits): ', validators=[InputRequired(), NumberRange(0)], default=8);
    fields = FieldList(FormField(AddEnumFieldForm), min_entries=1, max_entries=65535)
    
class AddBitfieldForm(FlaskForm):
    bitfieldName = StringField('Bitfield Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    bitfieldReference = StringField('Bitfield Reference: ')
    bitfieldNote = StringField('Bitfield Note: ')
    bitfieldSize = IntegerField('Bitfield Read Size (Bits): ', validators=[InputRequired(), NumberRange(0)], default=8);
    fields = FieldList(FormField(AddBitfieldFieldForm), min_entries=1, max_entries=65535)
    
class AddSwitchForm(FlaskForm):
    switchName = StringField('Switch Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    switchMainDependency = FormField(DependencyForm)
    switchAdditionalDependencies = FieldList(FormField(DependencyForm), min_entries=0, max_entries=65535)
    switchOptions = FieldList(FormField(OptionForm), min_entries=0, max_entries=65535)
    
class AddObjectForm(FlaskForm):
    objectName = StringField('Object Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    objectReference = StringField('Object Reference: ')
    objectNote = StringField('Object Note: ')
    objectScope = StringField('Object Scope: ', validators=[Regexp(r'^$|[a-zA-Z_][a-zA-Z_0-9]*$')])
    logIndependently = BooleanField('Should Log Independently? ')
    objectDependencies = FieldList(FormField(DependencyForm), min_entries=0, max_entries=65535)
    
class AddFieldForm(FlaskForm):
    ###################################################
    # General Fields
    ###################################################
    fieldName = StringField('Field Name: ', validators=[InputRequired(), Regexp(r'^[a-zA-Z_][a-zA-Z_0-9]*$')])
    fieldDescription = StringField('Field Reference: ')
    fieldNote = StringField('Field Note: ')
    isConditional = BooleanField('Is Field Conditional? ', default=False)
    conditionalIndicator = SelectField('Indicator: ', choices=[('', '---')], validate_choice=False)
    conditionalOperator = SelectField('Operator: ', choices=[('=', '='), ('!=', '!='), ('>=', '>='), ('<=', '<='), ('<', '<'), ('>', '>')])
    useConditionalTextValue = HiddenField('Use Conditional Text Value', default=False)
    useConditionalNumberValue = HiddenField('Use Conditional Number Value', default=False)
    conditionalValue = SelectField('Comparison Value: ', choices=[('', '---')], validate_choice=False)
    conditionalTextValue = StringField('Comparison Value: ')
    conditionalNumberValue = IntegerField('Comparison Value: ', default=0)
    fieldType = SelectField('Field Type: ', choices=[('', '---')], validate_choice=False)
    ###################################################
    # Non-reference-type-specific fields
    ###################################################
    fieldSize = IntegerField('Field Size (Bits): ', validators=[RequiredIfSizedElement2("fieldType", "elementType"), NumberRange(0)], default=8);
    ###################################################
    # List-specific fields
    ###################################################
    elementType = SelectField('List Element Type: ', choices=[('', '---')], validate_choice=False)
    untilConditionType = SelectField('List Condition Type: ', choices=[('COUNT', 'Count Field'), ('ENDOFDATA', 'Remaining Data')], validators=[Optional()])
    untilConditionIndicator = SelectField('Indicator Field: ', choices=[('', '---')], validate_choice=False)
    ###################################################
    # List- and reference-type-specific fields
    ###################################################
    referenceType = SelectField('Reference Type: ', choices=[('', '---')], validate_choice=False)
    # Can be used for "input", "additionalInputs", and "inputs" IL types
    inputs = FieldList(SelectField('Input Value: ', choices=[('', '---')], validate_choice=False), min_entries=0, max_entries=65535)
