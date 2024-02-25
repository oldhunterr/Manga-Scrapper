from .database import db

class SourceSetting(db.Model):
    __tablename__ = 'SourceSettings'

    source_setting_id = db.Column('SourceSettingID', db.Integer, primary_key=True)
    source_id = db.Column('SourceID', db.Integer, db.ForeignKey('Sources.SourceID'), nullable=False)
    selector_type = db.Column('SelectorType', db.Text, nullable=False)
    selector_value = db.Column('SelectorValue', db.Text, nullable=False)
    parent_selector_type = db.Column('ParentSelectorType', db.Text)
    parent_selector_value = db.Column('ParentSelectorValue', db.Text)
    element_type_id = db.Column('ElementTypeID', db.Integer, db.ForeignKey('ElementTypes.ElementTypeID'))

    def __init__(self):
        pass

    def serialize(self):
        return {
            'source_setting_id': self.source_setting_id,
            'source_id': self.source_id,
            'selector_type': self.selector_type,
            'selector_value': self.selector_value,
            'parent_selector_type': self.parent_selector_type,
            'parent_selector_value': self.parent_selector_value,
            'element_type_id': self.element_type_id
        }
