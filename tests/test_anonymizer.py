from core.anonymizer import ContentAnonymizer

def test_anonymize_email():
    anon = ContentAnonymizer()
    text = "Contact me at test.user@example.com immediately."
    res = anon.anonymize(text)
    assert res == "Contact me at [REDACTED_EMAIL] immediately."

def test_anonymize_phone():
    anon = ContentAnonymizer()
    text = "My number is 555-123-4567, call me."
    res = anon.anonymize(text)
    assert res == "My number is [REDACTED_PHONE], call me."

def test_anonymize_credit_card():
    anon = ContentAnonymizer()
    text = "Here is my card 1234-5678-9012-3456 to buy it."
    res = anon.anonymize(text)
    assert res == "Here is my card [REDACTED_CREDIT_CARD] to buy it."

def test_anonymize_disabled():
    anon = ContentAnonymizer(active=False)
    text = "Email test@example.com"
    res = anon.anonymize(text)
    assert res == "Email test@example.com"
