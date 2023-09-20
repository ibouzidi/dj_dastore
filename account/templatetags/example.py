from django import template

register = template.Library()


@register.filter(name="add_attrs")
def add_attrs(value, attrs):

    attrs_dict = value.field.widget.attrs
    classes = attrs_dict.get("class", "").split()

    # Map field names to placeholders
    placeholders = {
        "username": "Enter your email",
        "password": "Enter your password",
        "otp_token": "Enter your token",
        "new_password1": "Enter your new password",
        "new_password2": "Enter confirmation password",
    }

    new_attrs = attrs.split(",")

    for attr in new_attrs:
        if attr.strip().startswith("class:"):
            new_classes = attr.strip()[6:].split(" ")
            for c in new_classes:
                if c not in classes:
                    classes.append(c)
            attrs_dict["class"] = " ".join(classes)

        elif attr.strip().startswith("placeholder:") and not attrs_dict.get(
                "placeholder", ""):
            # Look up the placeholder based on the field name
            placeholder = placeholders.get(value.name, "")
            attrs_dict["placeholder"] = placeholder
            # Debug line
            # print(f"Field name: {value.name}, Placeholder: {placeholder}")

    return value.as_widget(attrs=attrs_dict)