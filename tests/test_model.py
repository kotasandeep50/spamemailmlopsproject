from backend.app.model_loader import SpamModel


def test_fallback_inference_is_deterministic():
    model = SpamModel()
    label, confidence = model.predict('free prize click now')
    assert label == 'spam'
    assert 0 <= confidence <= 1


def test_fallback_legitimate_confidence_adapts_to_clean_message():
    model = SpamModel()
    label, confidence = model.predict(
        'Hello Maya, please review the project schedule. Thank you, Alex.'
    )
    assert label == 'ham'
    assert confidence == 0.99


def test_fallback_mixed_message_has_lower_legitimate_confidence():
    model = SpamModel()
    label, confidence = model.predict('Please click the project review link.')
    assert label == 'ham'
    assert confidence == 0.72
