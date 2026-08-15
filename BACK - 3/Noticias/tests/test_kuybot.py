from app.services.kuybot import (
    _classify_research_level,
    _extract_claims_from_news,
    _extract_official_sources,
    _evaluate_claim_status,
    _infer_question_intent,
)


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


def test_extracts_claims_with_temporal_metadata() -> None:
    payload = {
        'news': {
            'title': 'Primicias: El 60% de pedidos de alianzas ha sido aprobado por el CNE',
            'summary': 'La elección se realizará el 29 de noviembre de 2026.',
            'main_claims': ['El 60% de pedidos de alianzas fue aprobado por el CNE.', 'Las elecciones serán el 29 de noviembre de 2026.'],
            'claims': [{'claim': 'El 60% de pedidos de alianzas fue aprobado por el CNE.', 'type': 'evento'}],
        }
    }

    claims = _extract_claims_from_news(payload)
    assert claims
    assert any('2026' in claim['dateContext'] for claim in claims)
    assert any(claim['type'] in {'numeric', 'event', 'date'} for claim in claims)


def test_claim_status_distinguishes_2023_context_from_2026_event() -> None:
    claim = {
        'claimId': 'claim-2026-date',
        'claim': 'Las elecciones se realizarán el 29 de noviembre de 2026.',
        'entities': ['CNE', 'elecciones'],
        'event': 'elecciones seccionales',
        'dateContext': '2026',
        'type': 'date',
    }
    evidence = [
        {'title': 'Elecciones Seccionales 2023', 'snippet': 'Las elecciones seccionales de 2023 se realizaron el 29 de noviembre.', 'url': 'https://example.com/2023'},
    ]

    status = _evaluate_claim_status(claim, evidence, official_sources=[{'source': 'CNE'}])
    assert status['status'] == 'contexto_insuficiente'
    assert '2026' in status['reasoning'] and '2023' in status['reasoning']


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
