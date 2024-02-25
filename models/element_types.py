from .database import db

class ElementType(db.Model):
    __tablename__ = 'ElementTypes'

    element_type_id = db.Column('ElementTypeID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(50), nullable=False, unique=True)

    def __init__(self, name):   
        self.name = name

    @staticmethod
    def get_element_type_by_name(name):
        return ElementType.query.filter_by(name=name).first()

    def serialize(self):
        return {
            'element_type_id': self.element_type_id,
            'name': self.name
        }
