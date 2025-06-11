

def validate_input_text(app_instance):
    """
    Sprawdza poprawność tekstu z input_box za pomocą modelu AI i dedykowanego szablonu.
    """
    
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

    prompt = template_data["template"].format(process_description=input_text)
    app_instance.last_prompt_type = "InputValidation"
    app_instance.send_to_api_custom_prompt(prompt)