
from language.translations_pl import TRANSLATIONS as PL
from language.translations_en import TRANSLATIONS as EN

def tr(key, LANG="pl"):
    return EN[key] if LANG == "en" else PL[key]

def validate_input_text(app_instance,diagram_type, LANG):
    """
    Sprawdza poprawność tekstu z input_box za pomocą modelu AI i dedykowanego szablonu.
    """
    if LANG == "en":
        from prompt_templates_en import get_diagram_specific_requirements
    else:
        from prompt_templates_pl import get_diagram_specific_requirements

    info_msg = (tr("msg_info_sending_description_for_verification", LANG=LANG))
    app_instance.append_to_chat("System", info_msg)
    # Pobierz tekst z input_box
    input_text = app_instance.input_box.toPlainText().strip()
    if not input_text:
        app_instance.output_box.append(tr("msg_error_no_text_for_validation"))
        return

    # Pobierz szablon walidacji (np. "Weryfikacja opisu procesu")
    template_data = app_instance.prompt_templates.get(tr("proces_description_validation", LANG=LANG))
    if not template_data:
        app_instance.output_box.append(tr("msg_error_no_template_for_validation", LANG=LANG))
        return
    prompt = template_data["template"].format(
        process_description=input_text,
        diagram_type=diagram_type,
        diagram_specific_requirements=get_diagram_specific_requirements(diagram_type))
    app_instance.last_prompt_type = "InputValidation"
    app_instance.send_to_api_custom_prompt(prompt)

