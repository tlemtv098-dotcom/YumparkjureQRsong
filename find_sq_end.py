import pathlib
p = pathlib.Path(r'D:\mysong\music\forms.py')
t = p.read_text(encoding='utf-8')
idx1 = t.find('def clean_video_id(self):')
idx2 = t.find('class GenreForm(forms.ModelForm):', idx1)
if idx1 >= 0 and idx2 >= 0:
    print(repr(t[idx1:idx2]))
