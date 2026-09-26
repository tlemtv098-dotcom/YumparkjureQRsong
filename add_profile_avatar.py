import pathlib
p = pathlib.Path(r"D:\mysong\music\forms.py")
t = p.read_text(encoding="utf-8")

# Find the second clean_phone (ProfileForm) and add clean_avatar after it
old = """    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone


class UserForm(forms.ModelForm):"""

new = """    def clean_phone(self):
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
        return avatar


class UserForm(forms.ModelForm):"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("ProfileForm clean_avatar added")
