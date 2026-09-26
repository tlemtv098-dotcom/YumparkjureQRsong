import pathlib
p = pathlib.Path(r"D:\mysong\music\forms.py")
t = p.read_text(encoding="utf-8")

# Add clean methods to RegisterForm
old_register = """    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone

    def save(self, commit=True):"""

new_register = """    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว")
        if len(username) < 3:
            raise ValidationError("ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")
        if not username.isalnum():
            raise ValidationError("ชื่อผู้ใช้ต้องเป็นตัวอักษรภาษาอังกฤษหรือตัวเลขเท่านั้น")
        return username

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise ValidationError("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        if not any(c.isupper() for c in password):
            raise ValidationError("รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว")
        if not any(c.islower() for c in password):
            raise ValidationError("รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว")
        if not any(c.isdigit() for c in password):
            raise ValidationError("รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("รหัสผ่านไม่ตรงกัน")
        return password2

    def save(self, commit=True):"""

assert t.count(old_register) == 1, "count=%d" % t.count(old_register)
t = t.replace(old_register, new_register)
print("RegisterForm validation added")

# Add clean_avatar to ProfileForm
old_profile = """    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone"""

new_profile = """    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            # Check file size (max 2MB)
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError("ไฟล์รูปภาพต้องไม่เกิน 2 MB")
            # Check file type
            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            if avatar.content_type not in allowed_types:
                raise ValidationError("รองรับเฉพาะไฟล์ JPEG, PNG, WebP เท่านั้น")
            # Check dimensions (optional - requires Pillow)
            try:
                from PIL import Image
                img = Image.open(avatar)
                if img.width > 1000 or img.height > 1000:
                    raise ValidationError("ขนาดรูปภาพต้องไม่เกิน 1000x1000 พิกเซล")
            except Exception:
                pass
        return avatar"""

assert t.count(old_profile) == 1, "count=%d" % t.count(old_profile)
t = t.replace(old_profile, new_profile)
print("ProfileForm clean_avatar added")

p.write_text(t, encoding="utf-8")
print("ProfileForm validation added")
