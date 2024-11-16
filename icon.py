import base64

with open("AutomaticSetup.ico", "rb") as icon_file:  # Replace with your .ico file's name
    encoded_string = base64.b64encode(icon_file.read()).decode("utf-8")
print(encoded_string)
