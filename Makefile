inputs := __init__.py config.json manifest.json
output := adjust-sound-volume.ankiaddon

$(output): $(inputs)
	zip -FS $(output) $(inputs)
