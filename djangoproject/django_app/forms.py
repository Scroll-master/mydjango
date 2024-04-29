from django import forms
from .models import Media, NodeGroup, Node, Event

class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['file', 'tags']  # Указываем поля, которые будут в форме
        widgets = {
            'tags': forms.TextInput(attrs={'placeholder': 'Введите теги'})
        }
        

class NodeGroupForm(forms.ModelForm):
    node_ids = forms.ModelMultipleChoiceField(queryset=Node.objects.all(), widget=forms.CheckboxSelectMultiple(), required=False)
    event_ids = forms.ModelMultipleChoiceField(queryset=Event.objects.all(), widget=forms.CheckboxSelectMultiple(), required=False)

    class Meta:
        model = NodeGroup
        fields = ['name']        