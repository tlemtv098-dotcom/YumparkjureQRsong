import pathlib
p = pathlib.Path(r"D:\mysong\music\forms.py")
t = p.read_text(encoding="utf-8")

old_user = "class UserForm(forms.ModelForm):\n    \"\"\"User basic info form for admin\"\"\"\n    class Meta:\n        model = User\n        fields = (\"username\", \"first_name\", \"last_name\", \"email\", \"is_active\")\n        widgets = {\n            \"username\": forms.TextInput(attrs={\n                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",\n            }),\n            \"first_name\": forms.TextInput(attrs={\n                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",\n            }),\n            \"last_name\": forms.TextInput(attrs={\n                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",\n            }),\n            \"email\": forms.EmailInput(attrs={\n                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",\n            }),\n            \"is_active\": forms.CheckboxInput(attrs={\n                \"class\": \"h-4 w-4 text-amber-500 border-slate-300 rounded focus:ring-amber-400\"\n            }),\n        }"

new_user = """class UserForm(forms.ModelForm):
    \"\"\"User basic info form for admin\"\"\"
    class Meta:
        model = User
        fields = (\"username\", \"first_name\", \"last_name\", \"email\", \"is_active\")
        widgets = {
            \"username\": forms.TextInput(attrs={
                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",
            }),
            \"first_name\": forms.TextInput(attrs={
                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",
            }),
            \"last_name\": forms.TextInput(attrs={
                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",
            }),
            \"email\": forms.EmailInput(attrs={
                \"class\": \"w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400\",
            }),
            \"is_active\": forms.CheckboxInput(attrs={
                \"class\": \"h-4 w-4 text-amber-500 border-slate-300 rounded focus:ring-amber-400\"
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get(\"email\")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(\"อีเมลนี้มีผู้ใช้งานแล้ว\")
        return email

    def clean_username(self):
        username = self.cleaned_data.get(\"username\")
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(\"ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว\")
        return username"""

assert t.count(old_user) == 1, "count=%d" % t.count(old_user)
t = t.replace(old_user, new_user)
p.write_text(t, encoding="utf-8")
print("UserForm validation added")
