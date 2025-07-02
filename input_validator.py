
def validate_input_text(app_instance,diagram_type, LANG="pl"):
    """
    Sprawdza poprawność tekstu z input_box za pomocą modelu AI i dedykowanego szablonu.
    """
    if LANG == "en":
        from prompt_templates_en import get_diagram_specific_requirements
    else:
        from prompt_templates_pl import get_diagram_specific_requirements
    info_msg = ("**Przekazano opis procesu do weryfikacji**\n")
    app_instance.append_to_chat("System", info_msg)
    # Pobierz tekst z input_box
    input_text = app_instance.input_box.toPlainText().strip()
    if not input_text:
        app_instance.output_box.append("Brak tekstu do walidacji.\n\n")
        return

    # Pobierz szablon walidacji (np. "Weryfikacja opisu procesu")
    template_data = app_instance.prompt_templates.get("Weryfikacja opisu procesu")
    if not template_data:
        app_instance.output_box.append("Brak szablonu do weryfikacji opisu procesu.\n\n")
        return
    prompt = template_data["template"].format(
        process_description=input_text,
        diagram_type=diagram_type,
        diagram_specific_requirements=get_diagram_specific_requirements(diagram_type))
    app_instance.last_prompt_type = "InputValidation"
    app_instance.send_to_api_custom_prompt(prompt)