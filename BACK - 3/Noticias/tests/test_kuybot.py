from app.services.kuybot import _classify_research_level, _extract_official_sources, _infer_question_intent


def test_infers_verification_intent_from_question() -> None:
    intent = _infer_question_intent('¿Es verdad que el CNE confirmó fraude electoral?')
    assert intent == 'verification'


def test_classifies_simple_questions_as_level_1() -> None:
    level = _classify_research_level('¿Qué significa “candidatura” en el contexto electoral?')
    assert level == 'level_1'


def test_classifies_specific_sources_as_level_2() -> None:
    level = _classify_research_level('¿Qué dijo el CNE sobre la inscripción de Jorge Yunda?')
    assert level == 'level_2'


def test_classifies_verification_questions_as_level_3() -> None:
    level = _classify_research_level('¿Es verdad que Yunda fue inscrito por el movimiento Amigo?')
    assert level == 'level_3'


def test_extracts_official_sources_with_priority() -> None:
    payload = {
        'news': {
            'related_news': [
                {'title': 'El Comercio', 'url': 'https://www.elcomercio.com/', 'source': 'El Comercio', 'source_type': 'medio_radar'},
                {'title': 'Comunicado CNE', 'url': 'https://www.cne.gob.ec/', 'source': 'CNE', 'source_type': 'gobierno'},
                {'title': 'Primicias', 'url': 'https://www.primicias.ec/', 'source': 'Primicias', 'source_type': 'medio_nativo'},
            ]
        }
    }

    official = _extract_official_sources(payload)
    assert official[0]['url'] == 'https://www.cne.gob.ec/'
    assert any(item['source'] == 'CNE' for item in official)
