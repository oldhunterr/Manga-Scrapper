from flask_admin.model import ModelView
from models import source_setting, Element

class CustomSourceSettingView(ModelView):
    column_display_pk = True  # Display primary keys in the list view

    def _get_element_choices(self):
        # Query all elements from the database
        elements = Element.query.all()
        # Format elements as choices for the form field
        choices = [(element.id, element.name) for element in elements]
        return choices

    def on_form_prefill(self, form, id):
        # Populate choices for ElementTypeID field when editing a record
        form.ElementTypeID.choices = self._get_element_choices()

    def on_form_base(self, form):
        # Populate choices for ElementTypeID field when adding a new record
        form.ElementTypeID.choices = self._get_element_choices()